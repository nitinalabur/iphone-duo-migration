# iPhone Duo Migration

A reusable coding-agent skill, packaged as a plugin, for adapting iOS apps to iPhone Duo. It combines an Xcode capability check with practical UI guidance and a verification workflow.

Use it to audit an existing app, implement focused layout changes, or review a migration. The skill follows the requested scope; an audit request does not authorize implementation or distribution.

## What it does

- Finds installed Xcode toolchains and type-checks the required Duo APIs against their actual SDKs.
- Suggests useful paired layouts for the app's main tasks across compact, open, and partially folded displays.
- Guides state preservation, reserved-region handling, system bars, and older-iOS fallbacks.
- Produces a pose-testing matrix with evidence and explicit gaps.
- Separates build capability, simulator availability, device verification, and App Store eligibility.

The checker does not depend on an exact Xcode version or app filename. The API baseline first passed on Xcode 27.1 beta and was rechecked with Xcode 27.1 RC (build 27A9275) on October 6, 2026. A narrow comparison of the Duo-related declarations found no changes between those builds; this does not claim the full SDK is unchanged. Recheck Apple documentation when APIs or submission rules change.

## Requirements

- A coding agent that supports skills or this plugin format.
- macOS, a full Xcode installation, and Python 3.9+ for the local capability checker.
- A compatible Duo runtime/device for simulator verification, and physical hardware for camera/handling checks where relevant.

The Python checker uses only the standard library. The package has no MCP server, service account, telemetry, or automatic installation hooks. Documentation can be read anywhere; Xcode checks run on the Mac that will build the app. The coding agent retains its own tool permissions and data-handling behavior.

## Install in Codex

With a Codex CLI that supports plugin marketplaces:

```bash
codex plugin marketplace add nitinalabur/iphone-duo-migration --ref v0.1.2
codex plugin add iphone-duo-migration@iphone-duo-migration
```

Start a new session after installation. If your client exposes marketplace installation through the Plugins UI, choose the **iPhone Duo Migration** marketplace and install its plugin there. Plugin support varies by client; consult the [current packaging documentation](https://developers.openai.com/plugins/build/plugins).

The repository includes both a portable root `plugin.json` and a Codex compatibility manifest. Its marketplace points to the package at the repository root. GitHub distribution is separate from approval or listing in the public OpenAI plugin directory.

### Install only the skill

For a project using Codex's repository skill layout, clone this repository and copy the complete `skills/iphone-duo-migration` directory into the destination project's `.agents/skills/`. For other agents, use their documented skill installation directory. Include the references, templates, and script rather than copying only `SKILL.md`.

Do not overwrite an existing skill without reviewing the differences. Other agents may require different plugin metadata even when they support the underlying skill format; those integrations are not claimed as tested.

## Use it

In the destination project's coding-agent session:

```text
Use $iphone-duo-migration to audit this app's three main tasks for iPhone Duo.
Report the proposed changes and a verification plan before editing.
```

Or request implementation:

```text
Use $iphone-duo-migration to adapt this app for iPhone Duo. Preserve its
minimum iOS version and existing behavior. Implement focused changes,
test on Duo and a conventional iPhone, and report the evidence and gaps.
```

Useful resources:

- [Skill instructions](skills/iphone-duo-migration/SKILL.md)
- [Migration guide](skills/iphone-duo-migration/references/migration-guide.md)
- [Project brief](skills/iphone-duo-migration/assets/project-brief.md)
- [Verification matrix](skills/iphone-duo-migration/assets/verification-matrix.md)
- [SwiftUI layout example](skills/iphone-duo-migration/assets/DuoReviewExample.swift)

## How this complements Apple's Xcode skill

Xcode 27.1 RC can export Apple-authored skills with `xcrun agent skills export`. Its `app-resizability` skill already explicitly supports iPhone Duo and provides detailed modernization rules for screen, orientation, device-idiom, lifecycle, and safe-area code.

This repository is a practical Duo migration companion to that guidance, with capability checks, fold-aware examples, and a repeatable verification workflow.

| What this repository adds | Practical value |
| --- | --- |
| [Xcode capability detection](skills/iphone-duo-migration/scripts/check_xcode.py) | Finds installed toolchains and compiles real Duo APIs rather than relying on a version number. Reports simulator availability separately. |
| [Duo-specific task design](skills/iphone-duo-migration/references/migration-guide.md) | Helps choose useful paired workflows with `ArrangementView` and reserved-region examples. Guides preservation of drafts, selections, and media across compact, open, and partially folded layouts. |
| [Tested fold geometry](tests/layout/main.swift) | Covers narrow multitasking windows, divisions at or outside window edges, and insufficient space for usable panes. |
| [Migration verification](skills/iphone-duo-migration/assets/verification-matrix.md) | Provides a test plan for poses, keyboard and sheet interactions, accessibility, older iPhones, and physical-device checks, with evidence and explicit gaps. |

For API modernization alone, Apple's skill may be sufficient. Use this repository alongside it when you also want to redesign and validate the app's Duo experience. For example, a photo-review flow needs a decision about when paired panes should become one scrolling form, plus checks that selected photos and unfinished edits survive the transition.

This comparison is based on the Xcode 27.1 RC (27A9275) export inspected on October 6, 2026. That export did not include `ArrangementView`, `reservedRegions`, or Laptop/Tent-specific layout instructions; Apple's coverage may expand. The bundled geometry tests do not automatically verify an app's UI or physical-device behavior.

Follow the [optional Apple-skill workflow](skills/iphone-duo-migration/references/apple-skills.md) to export into a new temporary directory using your selected Xcode, inspect its actual contents, and preserve audit-only scope. Exporting may launch Xcode; it is separate from the read-only SDK checker and is not a required installation step. Apple skills are not bundled or relicensed by this repository.

The example now includes [DuoPaneLayout.swift](skills/iphone-duo-migration/assets/DuoPaneLayout.swift). Include it alongside the view. A division at or outside a multitasking window's edge must not force that narrow window into paired panes.

## Run the Xcode checker directly

From a clone of this repository:

```bash
python3 skills/iphone-duo-migration/scripts/check_xcode.py
python3 skills/iphone-duo-migration/scripts/check_xcode.py --json
```

Discovery includes `DEVELOPER_DIR`, `xcode-select`, Xcode bundles under `/Applications` and `~/Applications`, and any additional search roots. For a custom installation:

```bash
python3 skills/iphone-duo-migration/scripts/check_xcode.py \
  --xcode "/Volumes/Development Tools/Xcode.app" --json
```

Use repeatable `--xcode` arguments for explicit candidates, `--search-root` for additional locations, or `--skip-simulator-check` when you only need SDK capability. `--timeout` bounds individual tool invocations.

An explicit path adds a candidate; it does not change your active toolchain. Recommendations prefer the selected capable Xcode, then an explicit capable candidate, then the newest SDK that passes. Apply the recommended developer directory to individual project build commands after checking project compatibility.

The compile probe verifies `ArrangementView`, the split arrangement style, and the division reserved-region query. It does not certify every optional camera, UIKit, or future Duo API. Verify additional APIs used by your project against its selected SDK.

| Exit code | Meaning |
| --- | --- |
| `0` | At least one toolchain passed the SDK capability probe |
| `1` | No capable toolchain was found and the result is determinate |
| `2` | Invalid invocation or capability could not be determined |

Simulator status is reported separately. Missing runtimes, absent devices, service errors, and skipped checks do not become a false claim of simulator readiness. A successful SDK check does not prove that your project builds, that the UI works in each pose, or that Apple accepts the build for distribution.

Apple announced on October 5, 2026 that apps built with Xcode 27.1 RC and the iOS 27.1 SDK can be uploaded for App Store review and internal or external TestFlight. This is upload eligibility, not approval of a specific app. Check the current [App Store Connect release notes](https://developer.apple.com/help/app-store-connect/release-notes/) before distributing with a prerelease SDK.

The checker leaves global Xcode selection and simulator configuration unchanged. It uses temporary compiler files and cache, then cleans them up. Full JSON reports contain local installation paths; review them before posting publicly.

## Verification and maintenance

Run portable unit tests and package checks:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_package.py
```

On a Mac with Xcode, run the example's geometry regression cases:

```bash
bash tools/test_swift_layout.sh
```

Unit tests use mocked tool responses and can run without Xcode. A live check on a Mac is separate evidence. CI checks portable behavior and runs the geometry cases on macOS; it does not claim to test the Duo UI or hardware.

See [release validation](VALIDATION.md) for the checks completed for this package and their limits.

For a new release:

1. Check current Apple SDK declarations and documentation; update examples only when verified.
2. Run tests, the live preflight, and a representative migration in another app when changing workflow behavior.
3. Keep plugin manifest versions aligned, update the changelog, and tag the release.
4. Record the exact toolchain and observed limitations. Do not convert one machine's simulator failure into a universal device rule.

Use GitHub issues for reproducible problems and pull requests for improvements. Include the plugin version and relevant tool versions, and redact private project paths or data. Changes to installation, host configuration, or distribution behavior should remain explicit and reviewable.

## Sources and license

- [Apple: Preparing your app for iPhone Duo](https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo)
- [Apple: Designing for iPhone Duo](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo)
- [Apple: Xcode release notes](https://developer.apple.com/documentation/xcode-release-notes)
- [Apple: App Store Connect release notes](https://developer.apple.com/help/app-store-connect/release-notes/)
- [OpenAI: Plugin packaging](https://developers.openai.com/plugins/build/plugins)

[MIT license](LICENSE). This is an independent community project. Apple and OpenAI documentation remains subject to its respective terms; linked documentation and installed SDKs are not redistributed by this package.
