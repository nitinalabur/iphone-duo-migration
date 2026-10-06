# Use Apple's exported resizability guidance

Use this reference when the selected Xcode can export agent skills. Apple's `app-resizability` skill provides detailed API-modernization rules; this package adds Duo task design, fold geometry, state preservation, capability checks, and pose verification. Read the local Apple guidance rather than copying its files into this package.

## Discover and export

First select a capable toolchain using this package's checker. Substitute its developer directory below; do not change global `xcode-select`.

```bash
DUO_XCODE_DEVELOPER_DIR="/path/to/Xcode.app/Contents/Developer"
DEVELOPER_DIR="$DUO_XCODE_DEVELOPER_DIR" xcrun agent skills export --help
```

If supported, export into a new temporary directory so existing skills cannot be overwritten:

```bash
DUO_APPLE_SKILLS_DIR="$(mktemp -d "${TMPDIR:-/tmp}/duo-apple-skills.XXXXXX")"
DEVELOPER_DIR="$DUO_XCODE_DEVELOPER_DIR" xcrun agent skills export \
  --output-dir "$DUO_APPLE_SKILLS_DIR"
```

The export can launch or connect to Xcode. Verify which Xcode is running and record its version; selecting `DEVELOPER_DIR` alone does not establish the provenance of a running agent session. If launching fails inside a sandbox, report the access failure and use the host's normal permission mechanism when authorized. Do not diagnose a corrupt installation from that error alone, replace Xcode, or restart services as an automatic repair.

Read the exported `app-resizability/SKILL.md` and the references relevant to the destination app. Skill names and CLI availability may change: inspect the actual export. Exporting writes files; it does not install them into an agent's global configuration. The capability checker deliberately does not run the export or launch Xcode.

If export is unavailable, continue with this package, current Apple documentation, and SDK inspection. Missing exported skills do not mean the SDK lacks Duo support. Preserve the user's scope when applying another skill: an audit stays read-only, and a targeted migration does not authorize unrelated cleanup or distribution.

## Baseline checks to carry into the migration

Inspect the resolved target settings as well as its plist and configuration sources:

- Confirm a launch-screen declaration exists.
- Check the supported orientation declarations for each platform, including all four iPad orientations where applicable. Do not treat the iPhone declaration as an iPad declaration.
- Report full-screen opt-out keys and scene lifecycle configuration. Do not remove opt-outs or change deployment behavior before the app handles resizing.

Audit layout-related global screen, orientation, and device-idiom reads. Prefer the consuming view's geometry or traits. Distinguish layout decisions from camera direction, motion, analytics, and deliberate non-layout product policies. A scene-based SwiftUI app does not need a new UIKit SceneDelegate merely to satisfy a lifecycle checklist.

## Safe areas and vertical bars

The Xcode 27.1 RC export documents these iOS 27.1 APIs, also checked against that SDK:

| Need | API |
| --- | --- |
| SwiftUI system-preferred vertical bar edge | `@Environment(\.toolbarVerticalEdge)` |
| UIKit system-preferred vertical bar edge | `traitCollection.verticalBarEdge` |
| UIKit observation outside automatic layout tracking | `UITraitCollection.systemTraitsAffectingVerticalBarEdge` |

These report the preferred edge, not proof that a bar is visible or how much space it occupies. Use ordinary safe-area layout for clearance; only read the edge when the task actually needs it. Check availability and declarations in the chosen SDK before using an API. These optional APIs are not additional requirements of this package's baseline Duo compile probe.

Respect each edge independently. Bar placement or safe areas can change without a change in window size, and a presented sheet or split-view child can have different insets from its parent. Avoid cached insets, assumed left/right symmetry, and deriving bar position from orientation. In SwiftUI, let safe-area modifiers position content; do not subtract the reported insets from `GeometryProxy.size` or reapply them as padding inside the same view. Full-bleed backgrounds can remain full bleed while controls stay within the safe area.

Test both multitasking sides, an edge change without resizing, right-to-left layout, and presented content. The [verification matrix](../assets/verification-matrix.md) records these separately from physical fold tests.

## Verified export

On October 6, 2026, Xcode 27.1 RC (27A9275) exported ten skills. `app-resizability` explicitly named iPhone Duo and included the baseline and safe-area guidance above. That export did not include `ArrangementView`, `reservedRegions`, or Laptop/Tent-specific layout instructions. This is an observation of that export, not a promise about future Xcodes.
