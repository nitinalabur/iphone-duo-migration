#!/usr/bin/env python3
"""Read-only Xcode/Duo capability discovery. Python 3.9+, standard library only."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import NamedTuple, Optional


PROBE = """import SwiftUI

@available(iOS 27.1, *)
func verifyArrangement() -> some View {
    ArrangementView {
        Text("Primary")
    } secondary: {
        Text("Secondary")
    }
    .arrangementViewStyle(.split)
}

@available(iOS 27.1, *)
func verifyRegions(_ geometry: GeometryProxy) -> [ReservedRegion] {
    geometry.reservedRegions(kind: .division)
}
"""


class CommandResult(NamedTuple):
    returncode: Optional[int]
    stdout: str
    stderr: str
    error: str = ""


def run_command(args, env=None, timeout=60):
    try:
        completed = subprocess.run(args, env=env, capture_output=True, text=True,
                                   timeout=timeout, check=False)
        return CommandResult(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired:
        return CommandResult(None, "", "", "timed out after {} seconds".format(timeout))
    except (OSError, UnicodeError) as exc:
        return CommandResult(None, "", "", str(exc))


def diagnostics(result):
    return (result.error or result.stderr or result.stdout).strip()[:4000]


def brief_diagnostic(message):
    lines = message.splitlines()
    line = next((line for line in lines if "error:" in line), lines[0] if lines else "")
    return line[:240]


def normalize_developer_dir(value, require_valid=False):
    path = Path(value).expanduser().resolve()
    if path.suffix.lower() == ".app":
        path = path / "Contents/Developer"
    if require_valid and not (path / "usr/bin/xcodebuild").is_file():
        raise ValueError("Not an Xcode app or developer directory: {}".format(value))
    return str(path.resolve())


def discover_toolchains(explicit=None, search_roots=None, runner=run_command, default_roots=None):
    """Inspect immediate Xcode app bundles in roots; normalize aliases and deduplicate."""
    found = {}
    errors = []
    selected = None

    def add(value, source, required=False):
        try:
            path = normalize_developer_dir(value, require_valid=True)
        except (ValueError, OSError) as exc:
            if required:
                raise ValueError(str(exc))
            errors.append(str(exc))
            return
        entry = found.setdefault(path, {"developer_dir": path, "sources": []})
        if source not in entry["sources"]:
            entry["sources"].append(source)
        return entry

    env_selection = os.environ.get("DEVELOPER_DIR")
    if env_selection:
        selected = normalize_developer_dir(env_selection)
        add(env_selection, "selected_env")

    selection = runner(["/usr/bin/xcode-select", "-p"])
    if selection.returncode == 0 and selection.stdout.strip():
        if selected is None:
            selected = normalize_developer_dir(selection.stdout.strip())
        add(selection.stdout.strip(), "selected_xcode_select")
    elif selection.returncode != 0:
        errors.append("xcode-select: {}".format(diagnostics(selection) or "selection unavailable"))

    for index, value in enumerate(explicit or []):
        entry = add(value, "explicit", required=True)
        entry.setdefault("explicit_order", index)

    roots = default_roots if default_roots is not None else ["/Applications", "~/Applications"]
    for value in list(roots) + list(search_roots or []):
        root = Path(value).expanduser()
        try:
            if root.suffix.lower() == ".app":
                add(str(root), "discovered")
                continue
            if not root.exists():
                if value in (search_roots or []):
                    errors.append("Search root does not exist: {}".format(root))
                continue
            for app in sorted(root.glob("*.app")):
                if (app / "Contents/Developer/usr/bin/xcodebuild").is_file():
                    add(str(app), "discovered")
        except OSError as exc:
            errors.append("Cannot inspect {}: {}".format(root, exc))
    return list(found.values()), selected, errors


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d+(?:\.\d+)*", value.strip()):
        return None
    return tuple(int(part) for part in value.strip().split("."))


def is_missing_api(result):
    """Distinguish a missing API from infrastructure/compiler failures."""
    for line in (result.stderr + "\n" + result.stdout).splitlines():
        if "error:" not in line:
            continue
        if "no such module 'SwiftUI'" in line:
            return True
        if any(symbol in line for symbol in
               ("ArrangementView", "ReservedRegion", "reservedRegions", "division", "split")):
            if any(marker in line for marker in
                   ("cannot find", "has no member", "not a member", "unavailable", "not available")):
                return True
    return False


def inspect_toolchain(candidate, runner=run_command, timeout=60, skip_simulator=False):
    developer = candidate["developer_dir"]
    env = dict(os.environ, DEVELOPER_DIR=developer)
    report = dict(candidate)
    result = runner([str(Path(developer) / "usr/bin/xcodebuild"), "-version"], env, timeout)
    version = re.search(r"^Xcode\s+(.+)$", result.stdout, re.MULTILINE)
    build = re.search(r"^Build version\s+(.+)$", result.stdout, re.MULTILINE)
    report["xcode"] = {"status": "ok" if result.returncode == 0 and version and build else "error",
                       "version": version.group(1).strip() if version else None,
                       "build": build.group(1).strip() if build else None,
                       "diagnostics": diagnostics(result) if result.returncode != 0 else ""}
    sdk_path = runner(["/usr/bin/xcrun", "--sdk", "iphoneos", "--show-sdk-path"], env, timeout)
    sdk_version = runner(["/usr/bin/xcrun", "--sdk", "iphoneos", "--show-sdk-version"], env, timeout)
    path = sdk_path.stdout.strip() if sdk_path.returncode == 0 else None
    sdk = sdk_version.stdout.strip() if sdk_version.returncode == 0 else None
    sdk_ok = bool(path) and version_tuple(sdk) is not None
    sdk_error = "\n".join(filter(None, [diagnostics(r) for r in (sdk_path, sdk_version)
                                      if r.returncode != 0]))
    missing_sdk = bool(re.search(r"SDK.*(?:cannot be located|not found|does not exist)",
                                 sdk_error, re.IGNORECASE))
    report["sdk"] = {"status": "ok" if sdk_ok else "missing" if missing_sdk else "error",
                     "version": sdk, "path": path,
                     "diagnostics": sdk_error or ("Unrecognized SDK response" if not sdk_ok else "")}
    report["build_status"] = "unknown"
    probe = {"status": "error", "compiler_path": None, "diagnostics": "Device SDK could not be determined"}
    if missing_sdk:
        report["build_status"] = "unsupported"
        probe = {"status": "unsupported", "compiler_path": None, "diagnostics": "No iPhoneOS SDK"}
    elif sdk_ok:
        compiler = runner(["/usr/bin/xcrun", "--toolchain", "XcodeDefault", "--find", "swiftc"], env, timeout)
        swiftc = compiler.stdout.strip() if compiler.returncode == 0 else None
        if swiftc:
            try:
                with tempfile.TemporaryDirectory(prefix="iphone-duo-probe-") as directory:
                    source = Path(directory) / "DuoAPIProbe.swift"
                    source.write_text(PROBE, encoding="utf-8")
                    cache = str(Path(directory) / "module-cache")
                    probe_env = dict(env, CLANG_MODULE_CACHE_PATH=cache)
                    checked = runner([swiftc, "-typecheck", "-sdk", path,
                                      "-target", "arm64-apple-ios{}".format(sdk),
                                      "-module-cache-path", cache, str(source)], probe_env, timeout)
                if checked.returncode == 0:
                    report["build_status"] = "supported"
                    status = "passed"
                elif checked.returncode is not None and is_missing_api(checked):
                    report["build_status"] = "unsupported"
                    status = "unsupported"
                else:
                    status = "error"
                probe = {"status": status, "compiler_path": swiftc, "diagnostics": diagnostics(checked)}
            except OSError as exc:
                probe["diagnostics"] = "Could not create temporary compiler probe: {}".format(exc)
        else:
            probe["diagnostics"] = diagnostics(compiler) or "swiftc could not be located"
    report["compile_probe"] = probe
    if skip_simulator:
        report["simulator"] = {"status": "skipped", "device_types": [], "runtimes": [],
                               "devices": [], "diagnostics": "Not checked; this does not establish simulator or pose QA."}
    else:
        inventory = runner(["/usr/bin/xcrun", "simctl", "list", "--json"], env, timeout)
        try:
            if inventory.returncode != 0:
                raise ValueError(diagnostics(inventory) or "simctl inventory failed")
            report["simulator"] = simulator_inventory(json.loads(inventory.stdout))
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            report["simulator"] = {"status": "unknown", "device_types": [], "runtimes": [],
                                   "devices": [], "diagnostics": str(exc)[:4000]}
    return report


def runtime_bound(device_type, key):
    text = version_tuple(device_type.get(key + "String"))
    if text is not None:
        return text
    number = device_type.get(key)
    if isinstance(number, int) and not isinstance(number, bool) and number >= 0:
        return (number >> 16, (number >> 8) & 255, number & 255)
    return None


def available(item):
    if isinstance(item.get("isAvailable"), bool):
        return item["isAvailable"]
    return False if item.get("availabilityError") else None


def compatible_runtime(runtime, device_type, devices):
    supported = runtime.get("supportedDeviceTypes")
    identifier = device_type.get("identifier")
    if isinstance(supported, list):
        return any((item.get("identifier") if isinstance(item, dict) else item) == identifier
                   for item in supported)
    if any(device.get("deviceTypeIdentifier") == identifier for device in devices):
        return True
    lower = runtime_bound(device_type, "minRuntimeVersion")
    upper = runtime_bound(device_type, "maxRuntimeVersion")
    version = version_tuple(runtime.get("version"))
    if lower is None or version is None:
        return None
    # Pad tuple components so 27.1 and 27.1.0 compare identically.
    normalized = version + (0,) * max(0, 3 - len(version))
    lower = lower + (0,) * max(0, 3 - len(lower))
    if normalized < lower:
        return False
    if upper is not None:
        upper = upper + (0,) * max(0, 3 - len(upper))
        if normalized > upper:
            return False
    return True


def simulator_inventory(inventory):
    if not isinstance(inventory, dict) or any(key not in inventory for key in ("devicetypes", "runtimes", "devices")):
        raise ValueError("simctl returned incomplete inventory")
    types = [item for item in inventory["devicetypes"]
             if "iphone" in item.get("name", "").lower() and "duo" in item.get("name", "").lower()]
    type_ids = {item.get("identifier") for item in types}
    devices = []
    runtimes = []
    for runtime in inventory["runtimes"]:
        if not runtime.get("name", "").startswith("iOS "):
            continue
        runtime_devices = inventory["devices"].get(runtime.get("identifier"), [])
        matches = [compatible_runtime(runtime, dtype, runtime_devices) for dtype in types]
        compatible = True if True in matches else None if None in matches else False
        runtimes.append({"name": runtime.get("name"), "identifier": runtime.get("identifier"),
                         "version": runtime.get("version"), "is_available": available(runtime),
                         "compatible": compatible, "availability_error": runtime.get("availabilityError")})
        for device in runtime_devices:
            if device.get("deviceTypeIdentifier") in type_ids:
                devices.append({"name": device.get("name"), "udid": device.get("udid"),
                                "device_type_identifier": device.get("deviceTypeIdentifier"),
                                "runtime_identifier": runtime.get("identifier"),
                                "is_available": available(device), "state": device.get("state")})
    ready = any(r["compatible"] is True and r["is_available"] is True for r in runtimes)
    uncertain = any(r["compatible"] is None and r["is_available"] is not False or
                    r["compatible"] is True and r["is_available"] is None for r in runtimes)
    status = "available" if ready else "unknown" if types and uncertain else "missing"
    return {"status": status, "device_types": types, "runtimes": runtimes, "devices": devices,
            "diagnostics": "Inventory only; no device is created/booted and no UI or pose QA is implied."}


def choose_toolchain(reports, selected):
    capable = [report for report in reports if report["build_status"] == "supported"]
    if not capable:
        return {"developer_dir": None, "reason": "No capability-proven toolchain found."}
    for report in capable:
        if report["developer_dir"] == selected:
            return {"developer_dir": selected, "reason": "Selected Xcode passed the required API probe."}
    explicit = [report for report in capable if "explicit" in report["sources"]]
    if explicit:
        explicit.sort(key=lambda report: report.get("explicit_order", len(reports)))
        return {"developer_dir": explicit[0]["developer_dir"],
                "reason": "Selected Xcode was unavailable or did not pass; first explicit capable Xcode preferred."}
    ranked = sorted(capable, key=lambda report: (version_tuple(report["sdk"].get("version")) or (),
                                                report["developer_dir"]), reverse=True)
    return {"developer_dir": ranked[0]["developer_dir"],
            "reason": "Selected Xcode was unavailable or did not pass; newest SDK among capability-proven discovered Xcodes preferred."}


def result_exit_code(reports, discovery_errors):
    if any(report["build_status"] == "supported" for report in reports):
        return 0
    if discovery_errors or any(report["build_status"] == "unknown" for report in reports):
        return 2
    return 1


def positive_timeout(value):
    seconds = float(value)
    if not 0 < seconds <= 600:
        raise argparse.ArgumentTypeError("timeout must be greater than 0 and at most 600 seconds")
    return seconds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xcode", action="append", default=[], metavar="PATH",
                        help="Xcode app or Contents/Developer directory; repeatable")
    parser.add_argument("--search-root", action="append", default=[], metavar="DIR",
                        help="Additional directory containing Xcode app bundles; repeatable")
    parser.add_argument("--skip-simulator-check", action="store_true",
                        help="Only check build capability; do not query CoreSimulator inventory")
    parser.add_argument("--timeout", type=positive_timeout, default=60,
                        help="Timeout in seconds per subprocess (default: 60)")
    parser.add_argument("--json", action="store_true", help="Output schema-versioned JSON")
    args = parser.parse_args(argv)
    try:
        candidates, selected, errors = discover_toolchains(args.xcode, args.search_root)
        reports = [inspect_toolchain(item, timeout=args.timeout, skip_simulator=args.skip_simulator_check)
                   for item in candidates]
        code = result_exit_code(reports, errors)
        output = {"schema_version": 1, "selected_developer_dir": selected,
                  "discovery": {"status": "partial" if errors else "ok", "errors": errors},
                  "toolchains": reports, "recommendation": choose_toolchain(reports, selected),
                  "build_capable": True if code == 0 else False if code == 1 else None,
                  "exit_code": code}
    except (ValueError, OSError) as exc:
        code = 2
        output = {"schema_version": 1, "selected_developer_dir": None,
                  "discovery": {"status": "error", "errors": [str(exc)]}, "toolchains": [],
                  "recommendation": {"developer_dir": None, "reason": "Invalid invocation or discovery failed."},
                  "build_capable": None, "exit_code": code}
    if args.json:
        print(json.dumps(output, indent=2))
    else:
        for report in output["toolchains"]:
            print("{}: build={}, SDK={}, simulator={}".format(
                report["developer_dir"], report["build_status"], report["sdk"]["version"] or "unknown",
                report["simulator"]["status"]))
            print("  Xcode {} ({})".format(report["xcode"]["version"] or "unknown", report["xcode"]["build"] or "unknown"))
            print("  SDK path: {}; compiler probe: {}".format(report["sdk"]["path"] or "unknown",
                                                             report["compile_probe"]["status"]))
            if report["compile_probe"]["diagnostics"]:
                print("  Probe: {}".format(brief_diagnostic(report["compile_probe"]["diagnostics"])))
            if report["simulator"]["status"] == "unknown":
                print("  Simulator: {}".format(brief_diagnostic(report["simulator"]["diagnostics"])))
            simulator = report["simulator"]
            if simulator["status"] not in ("unknown", "skipped"):
                usable = [runtime for runtime in simulator["runtimes"]
                          if runtime["compatible"] is True and runtime["is_available"] is True]
                print("  Duo types: {}; compatible available runtimes: {}; existing Duo devices: {}".format(
                    ", ".join(item.get("name", "unknown") for item in simulator["device_types"]) or "none",
                    ", ".join(item["name"] or "unknown" for item in usable) or "none",
                    len(simulator["devices"])))
                for device in simulator["devices"]:
                    print("    {}: {} ({}, available={})".format(device["name"], device["udid"],
                                                                  device["state"], device["is_available"]))
        for error in output["discovery"]["errors"]:
            print("Discovery: {}".format(error))
        recommendation = output["recommendation"]
        print("Recommended: {}. {}".format(recommendation["developer_dir"] or "none", recommendation["reason"]))
        print("Build capability only; simulator inventory is separate. No pose QA or App Store eligibility is established.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
