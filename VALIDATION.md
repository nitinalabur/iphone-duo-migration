# Validation for 0.1.0

Checked October 2, 2026. This records plugin/checker evidence, not a certification that arbitrary apps support iPhone Duo.

| Check | Result |
| --- | --- |
| Python 3.9 unit tests | 19 passed: API-based qualification, future-version fixture, missing APIs, unknown/timeout errors, path aliases, renamed bundles, explicit ordering, runtime compatibility and availability |
| Live Xcode 27.1 beta, build 27A9269, iOS SDK 27.1 | Swift API probe passed |
| Live Xcode 26.5, build 17F42, iOS SDK 26.5 | Correctly unsupported: required API declarations absent |
| Live Xcode 27.0 builds 27A5237l, 27A5252f, 27A266a | Correctly unsupported: required API declarations absent |
| Live simulator inventory | Compatible available Duo runtime and existing Duo devices found; inventory only |
| Generic SwiftUI example | Type-checked with iOS 27.1 SDK and iOS 15 simulator deployment target |
| Skill validator | Passed frontmatter/name/scaffold checks |
| Portable manifest | Passed the published Agent Plugins 1.0.0 JSON schema |
| Package integrity | Manifest identity/version, catalog path, resources, and local links checked |
| Codex plugin discovery | CLI recognized the local marketplace and uninstalled plugin version 0.1.0 using temporary command-line configuration overrides |
| Independent behavioral evaluation | Audit-only request on a synthetic, unrelated SwiftUI notes fixture identified fixed-screen geometry, orientation-driven layout, draft ownership, and missing task completion; made no edits/builds and left runtime checks untested |

The future-Xcode test uses a fixture; it is not proof about an unreleased SDK. The sample audit fixture was not a buildable production app. Physical Duo behavior, a second full production-app migration, and installation in other agent hosts were not tested for this package release. Codex discovery does not mean installation in a user's account or public directory approval.

CI additionally runs unit tests and package integrity checks on Python 3.9 and 3.13. Its live result is visible in the repository's Actions tab. Raw local SDK reports are not published because they include local installation and device paths.
