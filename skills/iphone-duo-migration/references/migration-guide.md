# Adapting an iOS app for iPhone Duo

This is a reusable decision guide, not a device-specific UI recipe. Start with the destination app's three most important tasks and the [project brief](../assets/project-brief.md). Apple's [preparation guide](https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo) and [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo) are the current authorities; recheck them when doing the work. The observations near the end are dated examples from one migration.

## Choose work by user benefit

When a runnable environment is available and within the requested scope, run the unchanged app on a Duo simulator and a conventional iPhone. Walk through task entry, editing, errors, sheets, keyboard, completion, and navigation. Record which controls are blocked or which work is lost during resizing. Repair those failures before adding a split layout. Extra space is useful when it exposes *related* information without making the compact task harder.

| Available configuration | Opportunity to evaluate |
| --- | --- |
| Closed outer display or narrow window | Keep the whole task available as a clear compact sequence. |
| Flat inner display | Pair useful content: list and detail, source and editor, map and results, chart and explanation. A tall inner view may benefit from stacked panes or one bounded reading pane instead. |
| Book-like partial fold | Let distinct tasks occupy the areas beside the division, each with its own scrolling when needed. |
| Laptop-style partial fold | Let content and controls follow a horizontal division while keeping commit and dismiss actions reachable. |
| Tent | Verify which display is active and whether the ordinary task remains usable; do not assume an orientation or a special tent-only screen. |
| Multitasking or reduced width | Collapse by available view size while keeping the detail and every essential action reachable. |

Treat poses as test cases, not layout enum values. The same inner display can have different available geometry, and orientation alone does not identify fold direction. Prefer the containing scene/view's size, size class, safe areas, and *active* reserved regions over model identifiers, full-screen dimensions, or hinge-angle guesses. This is consistent with Apple's [Duo design guidance](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo).

## Inspect capabilities, then design the container

Run the bundled read-only `scripts/check_xcode.py` relative to the skill directory with `--json`; optionally pass one or more `--xcode PATH` choices. It discovers installed Xcode/SDK candidates and compiles a probe for the required APIs. Check its result and current SDK declarations before coding. Do not require an Xcode installation with a particular name. If the SDK lacks an API, choose an available layout or explicitly arrange a compatible build configuration; a runtime `#available` branch cannot make missing symbols compile. Swift compiler version alone is not an SDK feature test.

The source migration used these iOS 27.1 APIs; validate their declarations and target availability in the destination toolchain:

| Need | Native direction |
| --- | --- |
| List/detail navigation | SwiftUI `NavigationSplitView` or UIKit `UISplitViewController`; these precede Duo-specific APIs. |
| Two complementary panes | SwiftUI `ArrangementView` with split style or UIKit `UIArrangementViewController`. See Apple's [arrangement guidance](https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo) and [ArrangementView reference](https://developer.apple.com/documentation/swiftui/arrangementview). |
| Custom fold avoidance | Query SwiftUI `GeometryProxy.reservedRegions(kind: .division)` or the corresponding UIKit view regions; respond to active regions. |
| Camera or hardware occlusion | Respect system safe areas and query occlusion regions if custom placement still needs more information. |
| Navigation and actions | Use native bars, semantic toolbar placements, and meaningful titles plus symbols; the system may move controls to a vertical bar or overflow. |

Give an arrangement a bounded area and scroll *inside* each pane. A long editor should not displace a reference pane or its Save action. Apple advises against putting an arrangement inside a navigation split view, list, scroll view, or another container that could make part of it inaccessible; choose a structure that preserves reachability. A split arrangement can adapt beside or across a fold. An axis-restricted arrangement may intentionally hide a secondary pane in one direction; provide another route if that content is essential. Avoid an outline or full-pane opaque card that appears to cross the hinge or hides the app's usual page background.

Keep the task's state above geometry-dependent branches: draft values, selected IDs, media identities, navigation destination, chart/filter state, and any in-progress operation. Pass bindings or stable models into compact and expanded compositions. A branch replacement can still reset focus, scroll offset, or zoom; preserve those separately when their loss matters. Do not key an entire task view by orientation or fold. Guard newer APIs by OS availability while retaining a complete compact path for the project's existing minimum OS and other supported platforms.

The [SwiftUI example](../assets/DuoReviewExample.swift) demonstrates parent-owned draft and selection state, a native split arrangement, and a complete compact fallback. It was type-checked with the iOS 27.1 SDK and an iOS 15 deployment target. Its 700-point breakpoint is an example content decision, not a hardware constant. It uses placeholder reference imagery and needs the destination app's model, saving, accessibility, and visual testing.

## Camera and presentation paths

For a system camera picker, keep camera selection with the system and test the real result on hardware. For custom capture, audit what front and rear mean relative to the display a person is viewing. The source SDK contained AVKit's `AVCaptureDeviceDirectionCoordinator`; inspect the current declaration and Apple's [camera-direction guidance](https://developer.apple.com/documentation/avkit/choosing-a-camera-by-the-direction-it-faces) before adapting a capture session. Verify orientation, mirroring, preview framing, permissions, and interruption handling. A simulator cannot prove physical camera direction.

Products built specifically around capture can investigate Apple's [camera capture accessory](https://developer.apple.com/documentation/avfoundation/registering-a-camera-capture-accessory-on-iphone-duo). It is not a general way for any app to place arbitrary content on both displays.

Test alerts, confirmation dialogs, sheets, and keyboards during size and pose changes. Choose the intended save prompt before presenting it; requesting a second dialog while an alert is still shown can lose the decision. Keep commit, cancel, and dismiss controls reachable regardless of bar placement. Do not add an orientation lock or counter-rotation to compensate for an unexplained simulator transition; compare another app and physical hardware first.

## Verify what actually happened

Use [the matrix](../assets/verification-matrix.md) for every main task. Automated tests should create an unfinished task, choose a destination and media/filter state, request a layout transition, assert those values remain, and complete the task. Inspect each pane visually for hinge spacing, clipped actions, independent scrolling, camera occlusion, and light/dark backgrounds. Test Dynamic Type and assistive technologies where the app supports them. Run the compact flow on a conventional iPhone at the minimum supported iOS version.

Record the source revision, Xcode/SDK and runtime, device, active display, pose, appearance, and evidence path. On a multi-display simulator, identify the active display before capturing it; a black screenshot does not validate layout. XCTest orientation requests are not hinge operations. If fold controls cannot be operated or hardware is unavailable, mark those matrix rows **Not tested** with the reason rather than silently promoting orientation coverage into pose coverage.

## Delivery is a separate scope

Use the destination app's signing and release workflow only when delivery is requested. Report compiled, installed, tested, uploaded, processed, available to testers, submitted, and released as separate states. Verify current App Store Connect build audience and group access; an upload receipt is not proof of tester availability. An export configured as internal-only is not an external/App Store candidate; consult Apple's [internal testing guidance](https://developer.apple.com/help/app-store-connect/test-a-beta-version/add-internal-testers). Before distributing with a prerelease SDK, check the current [App Store Connect release notes](https://developer.apple.com/help/app-store-connect/release-notes/) and Apple's submission guidance. On October 5, 2026, Apple announced upload eligibility for Xcode 27.1 RC builds using the iOS 27.1 SDK; this is not approval of an individual app.

The source migration on October 2, 2026 used an Xcode 27.1 beta SDK. Its simulator and capture observations were specific to that run: direct XCTest captures were black while the app was visible on another Duo display, UI automation could not operate the fold controls, and a reported laptop-to-tent rotation remained unexplained. These observations are not confirmed platform defects. On October 6, the Xcode 27.1 RC (build 27A9275) passed the bundled API compile probe. A fresh simulator inventory on that host could not connect to CoreSimulatorService, so runtime/device availability was unknown for that check. A narrow comparison against the beta found no changes in the Duo-related declarations, not in the entire SDK. See Apple's [Xcode 27.1 RC release](https://developer.apple.com/news/releases/?id=10052026g), [Duo submission guidance](https://developer.apple.com/news/?id=kkphp5qo), and [Device Hub guidance](https://developer.apple.com/documentation/xcode/interacting-with-your-app-in-device-hub). Device Hub orientation controls do not replace testing actual fold poses. Physical camera behavior also requires separate device evidence.
