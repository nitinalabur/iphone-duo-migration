"""Mocked preflight tests; do not require macOS or modify simulator state."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "skills/iphone-duo-migration/scripts/check_xcode.py"
SPEC = importlib.util.spec_from_file_location("check_xcode", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class FakeRunner:
    def __init__(self, version="27.1", sdk="27.1", probe_code=0, probe_error="", inventory=None):
        self.version = version
        self.sdk = sdk
        self.probe_code = probe_code
        self.probe_error = probe_error
        self.inventory = inventory if inventory is not None else {"devicetypes": [], "runtimes": [], "devices": {}}
        self.calls = []

    def __call__(self, args, env=None, timeout=60):
        self.calls.append((args, env))
        if args[-1] == "-version":
            return checker.CommandResult(0, "Xcode {}\nBuild version TEST\n".format(self.version), "")
        if "--show-sdk-version" in args:
            return checker.CommandResult(0, self.sdk, "")
        if "--show-sdk-path" in args:
            return checker.CommandResult(0, "/mock/iPhoneOS.sdk", "")
        if "--find" in args:
            return checker.CommandResult(0, "/mock/swiftc", "")
        if args[0].endswith("swiftc"):
            return checker.CommandResult(self.probe_code, "", self.probe_error)
        if "simctl" in args:
            if isinstance(self.inventory, checker.CommandResult):
                return self.inventory
            return checker.CommandResult(0, json.dumps(self.inventory), "")
        if args[0] == "/usr/bin/xcode-select":
            return checker.CommandResult(0, "", "")
        raise AssertionError("Unexpected command: {!r}".format(args))


def candidate(path="/mock/Xcode.app/Contents/Developer", sources=None):
    return {"developer_dir": path, "sources": sources or ["discovered"]}


class CapabilityTests(unittest.TestCase):
    def test_new_version_with_missing_apis_is_unsupported(self):
        runner = FakeRunner(version="99.0", sdk="27.0", probe_code=1,
                            probe_error="error: cannot find 'ArrangementView' in scope")
        report = checker.inspect_toolchain(candidate(), runner, skip_simulator=True)
        self.assertEqual(report["build_status"], "unsupported")
        self.assertEqual(report["compile_probe"]["status"], "unsupported")
        self.assertTrue(any("-typecheck" in args for args, _ in runner.calls))

    def test_future_version_is_accepted_by_actual_probe(self):
        runner = FakeRunner(version="42.7", sdk="42.7")
        report = checker.inspect_toolchain(candidate(), runner, skip_simulator=True)
        self.assertEqual(report["build_status"], "supported")
        self.assertEqual(report["xcode"]["version"], "42.7")
        self.assertEqual(report["simulator"]["status"], "skipped")
        compile_args = next(args for args, _ in runner.calls if "-typecheck" in args)
        self.assertIn("arm64-apple-ios42.7", compile_args)
        self.assertIn("-module-cache-path", compile_args)

    def test_broken_probe_is_unknown_not_unsupported(self):
        runner = FakeRunner(probe_code=1, probe_error="error: module cache is inaccessible")
        report = checker.inspect_toolchain(candidate(), runner, skip_simulator=True)
        self.assertEqual(report["build_status"], "unknown")
        self.assertEqual(report["compile_probe"]["status"], "error")

    def test_timeout_is_unknown_and_temp_probe_is_removed(self):
        class TimeoutRunner(FakeRunner):
            def __call__(self, args, env=None, timeout=60):
                if args[0].endswith("swiftc"):
                    self.probe_file = Path(args[-1])
                    return checker.CommandResult(None, "", "", "timed out")
                return super().__call__(args, env, timeout)
        runner = TimeoutRunner()
        report = checker.inspect_toolchain(candidate(), runner, skip_simulator=True)
        self.assertEqual(report["build_status"], "unknown")
        self.assertFalse(runner.probe_file.exists())

    def test_missing_simulator_does_not_block_build(self):
        report = checker.inspect_toolchain(candidate(), FakeRunner())
        self.assertEqual(report["build_status"], "supported")
        self.assertEqual(report["simulator"]["status"], "missing")
        self.assertEqual(checker.result_exit_code([report], []), 0)

    def test_simulator_service_error_is_unknown_independently(self):
        runner = FakeRunner(inventory=checker.CommandResult(1, "", "CoreSimulator service unavailable"))
        report = checker.inspect_toolchain(candidate(), runner)
        self.assertEqual(report["build_status"], "supported")
        self.assertEqual(report["simulator"]["status"], "unknown")
        self.assertEqual(checker.result_exit_code([report], []), 0)

    def test_unavailable_duo_runtime_does_not_block_build(self):
        inventory = {
            "devicetypes": [{"name": "iPhone Duo", "identifier": "duo", "minRuntimeVersionString": "27.1"}],
            "runtimes": [{"name": "iOS 27.1", "identifier": "ios", "version": "27.1",
                          "isAvailable": False, "availabilityError": "Runtime unavailable"}],
            "devices": {}
        }
        report = checker.inspect_toolchain(candidate(), FakeRunner(inventory=inventory))
        self.assertEqual(report["build_status"], "supported")
        self.assertEqual(report["simulator"]["status"], "missing")
        self.assertTrue(report["simulator"]["runtimes"][0]["compatible"])
        self.assertEqual(checker.result_exit_code([report], []), 0)

    def test_incomplete_inventory_is_unknown_independently(self):
        report = checker.inspect_toolchain(candidate(), FakeRunner(inventory={"devices": {}}))
        self.assertEqual(report["build_status"], "supported")
        self.assertEqual(report["simulator"]["status"], "unknown")


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.app = self.root / "Xcode Future.app"
        self.developer = self.app / "Contents/Developer"
        (self.developer / "usr/bin").mkdir(parents=True)
        (self.developer / "usr/bin/xcodebuild").touch()

    def tearDown(self):
        self.temp.cleanup()

    def test_selected_explicit_and_discovered_paths_are_deduplicated(self):
        with patch.dict(os.environ, {"DEVELOPER_DIR": str(self.app)}):
            found, selected, errors = checker.discover_toolchains(
                [str(self.app), str(self.developer)], [str(self.root)],
                runner=FakeRunner(), default_roots=[])
        self.assertEqual(len(found), 1)
        self.assertEqual(selected, str(self.developer.resolve()))
        self.assertEqual(errors, [])
        self.assertIn("explicit", found[0]["sources"])
        self.assertIn("selected_env", found[0]["sources"])
        self.assertIn("discovered", found[0]["sources"])

    def test_selected_supported_choice_wins_over_newer_discovery(self):
        selected = dict(candidate("/selected"), build_status="supported", sdk={"version": "27.1"})
        newer = dict(candidate("/newer"), build_status="supported", sdk={"version": "50.0"})
        recommendation = checker.choose_toolchain([newer, selected], "/selected")
        self.assertEqual(recommendation["developer_dir"], "/selected")

    def test_explicit_supported_choice_wins_when_selected_is_unsupported(self):
        broken = dict(candidate("/selected"), build_status="unsupported", sdk={"version": "27.0"})
        explicit = dict(candidate("/explicit", ["explicit"]), build_status="supported", sdk={"version": "27.1"})
        newer = dict(candidate("/newer"), build_status="supported", sdk={"version": "50.0"})
        recommendation = checker.choose_toolchain([broken, newer, explicit], "/selected")
        self.assertEqual(recommendation["developer_dir"], "/explicit")

    def test_explicit_argument_order_survives_prior_discovery(self):
        first = dict(candidate("/first", ["explicit"]), build_status="supported",
                     sdk={"version": "27.1"}, explicit_order=0)
        earlier_discovery = dict(candidate("/second", ["selected_xcode_select", "explicit"]),
                                 build_status="supported", sdk={"version": "28"}, explicit_order=1)
        recommendation = checker.choose_toolchain([earlier_discovery, first], "/unavailable")
        self.assertEqual(recommendation["developer_dir"], "/first")

    def test_no_match_and_uncertainty_have_different_exits(self):
        self.assertEqual(checker.result_exit_code([], []), 1)
        self.assertEqual(checker.result_exit_code([], ["discovery failed"]), 2)
        self.assertEqual(checker.result_exit_code([{"build_status": "unknown"}], []), 2)
        self.assertEqual(checker.result_exit_code([{"build_status": "unsupported"}], []), 1)

    def test_invalid_explicit_path_is_rejected(self):
        with self.assertRaises(ValueError):
            checker.normalize_developer_dir(str(self.root / "missing.app"), require_valid=True)

    def test_symlink_alias_is_deduplicated(self):
        alias = self.root / "Xcode Alias.app"
        alias.symlink_to(self.app, target_is_directory=True)
        with patch.dict(os.environ, {}, clear=True):
            found, _, _ = checker.discover_toolchains(
                [str(alias)], [str(self.root)], runner=FakeRunner(), default_roots=[])
        self.assertEqual(len(found), 1)

    def test_renamed_xcode_is_found_and_manager_is_ignored(self):
        renamed = self.root / "My IDE.app"
        self.app.rename(renamed)
        (self.root / "Xcodes.app/Contents").mkdir(parents=True)
        with patch.dict(os.environ, {}, clear=True):
            found, _, errors = checker.discover_toolchains(
                [], [str(self.root)], runner=FakeRunner(), default_roots=[])
        self.assertEqual(len(found), 1)
        self.assertIn("My IDE.app", found[0]["developer_dir"])
        self.assertEqual(errors, [])


class InventoryTests(unittest.TestCase):
    def test_device_type_runtime_and_device_are_reported_separately(self):
        dtype = "com.apple.CoreSimulator.SimDeviceType.iPhone-Duo"
        runtime = "com.apple.CoreSimulator.SimRuntime.iOS-27-1"
        inventory = {
            "devicetypes": [{"name": "iPhone Duo", "identifier": dtype, "minRuntimeVersionString": "27.1"}],
            "runtimes": [
                {"identifier": "old", "name": "iOS 27.0", "version": "27.0", "isAvailable": True},
                {"identifier": runtime, "name": "iOS 27.1", "version": "27.1", "isAvailable": True},
                {"identifier": "future", "name": "iOS 28", "version": "28.0", "isAvailable": False}
            ],
            "devices": {runtime: [{"name": "My Duo", "udid": "TEST-ID", "deviceTypeIdentifier": dtype,
                                   "isAvailable": True, "state": "Shutdown"}]}
        }
        report = checker.simulator_inventory(inventory)
        self.assertEqual(report["status"], "available")
        self.assertEqual(len(report["device_types"]), 1)
        self.assertFalse(report["runtimes"][0]["compatible"])
        self.assertTrue(report["runtimes"][1]["compatible"])
        self.assertEqual(report["devices"][0]["state"], "Shutdown")

    def test_unknown_runtime_compatibility_is_not_assumed(self):
        report = checker.simulator_inventory({
            "devicetypes": [{"name": "iPhone Duo", "identifier": "duo"}],
            "runtimes": [{"name": "iOS future", "identifier": "future", "version": "42", "isAvailable": True}],
            "devices": {}
        })
        self.assertEqual(report["status"], "unknown")
        self.assertIsNone(report["runtimes"][0]["compatible"])

    def test_runtime_supported_device_types_override_version_assumption(self):
        report = checker.simulator_inventory({
            "devicetypes": [{"name": "iPhone Duo", "identifier": "duo", "minRuntimeVersionString": "27.1"}],
            "runtimes": [{"name": "iOS 50", "identifier": "future", "version": "50", "isAvailable": True,
                          "supportedDeviceTypes": [{"identifier": "other"}]}],
            "devices": {}
        })
        self.assertFalse(report["runtimes"][0]["compatible"])
        self.assertEqual(report["status"], "missing")


if __name__ == "__main__":
    unittest.main()
