# Validation for 0.1.2

Release 0.1.2 was checked October 6, 2026 using Xcode 27.1 RC (27A9275). The Python suite, geometry cases, SwiftUI example type-check, optional Apple skill export, live toolchain/simulator discovery, skill validator, and package validation were rerun for this release. Earlier checks below are explicitly dated or marked retained. These results describe this package, not a certification that arbitrary apps support iPhone Duo.

| Check | Result |
| --- | --- |
| Swift geometry regression cases (0.1.2) | 20 passed, including both fold axes, edge/outside regions, short windows, and insufficient pane space. New cramped-pane assertions failed against the earlier predicate, then passed after the fix |
| Optional Apple export (0.1.2) | `xcrun agent skills export --output-dir` exported ten skills into a temporary directory; `app-resizability` present; no Apple skill files packaged |
| Python 3.9 unit tests | 19 passed: API-based qualification, future-version fixture, missing APIs, unknown/timeout errors, path aliases, renamed bundles, explicit ordering, runtime compatibility and availability |
| Live Xcode 27.1 RC, build 27A9275, iOS SDK 27.1 (October 6) | Explicitly selected RC passed the Swift API probe; checker recommended that selected toolchain |
| Live Xcode 27.1 beta, build 27A9269, iOS SDK 27.1 | Swift API probe passed; narrow Duo declaration comparison with RC found no changes |
| Live Xcode 26.5, build 17F42, iOS SDK 26.5 | Correctly unsupported: required API declarations absent |
| Live Xcode 27.0 builds 27A5237l, 27A5252f, 27A266a | Correctly unsupported: required API declarations absent |
| Live simulator inventory (October 2) | Compatible available Duo runtime and existing Duo devices found; inventory only |
| Live simulator inventory (October 6, RC; rerun outside sandbox) | iOS 27.1 runtime and iPhone Duo simulator device type are available; an existing Duo simulator was booted. Inventory-only check; no app pose or UI behavior was tested |
| App Store Connect eligibility (October 6) | Apple release notes allow uploads built with Xcode 27.1 RC and iOS 27.1 SDK for App Store review and internal/external TestFlight; this is not review approval ([source](https://developer.apple.com/help/app-store-connect/release-notes/)) |
| Generic SwiftUI example | View and layout helper type-checked together with iOS 27.1 SDK and iOS 15 simulator deployment target (0.1.2) |
| Skill validator | Passed frontmatter/name/scaffold checks |
| Portable manifest (retained from 0.1.0; metadata version updated) | Passed the published Agent Plugins 1.0.0 JSON schema |
| Package integrity | Manifest identity/version, catalog path, resources, and local links checked |
| Codex plugin discovery (retained from 0.1.0) | CLI recognized the local marketplace and uninstalled plugin version 0.1.0 using temporary command-line configuration overrides |
| Independent behavioral evaluation (0.1.2) | Strict audit-only notes-app scenario with unavailable Apple export reported fold/geometry/state risks, skipped prohibited writes and Xcode launch, and left runtime capability and pose coverage unverified. Separate code review caught and rechecked insufficient pane space; all 20 geometry cases then passed |

The future-Xcode test uses a fixture; it is not proof about an unreleased SDK. The sample audit fixture was not a buildable production app. Physical Duo behavior, a second full production-app migration, and installation in other agent hosts were not tested for this package release. Codex discovery does not mean installation in a user's account or public directory approval.

CI runs unit tests and package integrity checks on Python 3.9 and 3.13, plus the geometry cases on macOS. Its live result is visible in the repository's Actions tab. Raw local SDK reports are not published because they include local installation and device paths.
