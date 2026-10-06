---
name: iphone-duo-migration
description: Audit or adapt an iOS app for iPhone Duo's outer, inner, and folded layouts while preserving user state and older-iOS behavior. Use for a Duo readiness review or migration, not for an unrelated iOS change.
---

# iPhone Duo migration

Honor the requested scope. An audit-only request produces findings and a test plan; it does not edit the app, install a runtime, or distribute a build. For implementation, make the smallest changes that improve the app's main tasks. Create a goal only if the user explicitly asks for one.

1. Read the destination repository's instructions and identify its main tasks, UI framework, minimum OS, supported platforms, and delivery request. Use [the project brief](assets/project-brief.md) when these decisions are not already recorded.
2. Verify Apple's current [preparation guide](https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo) and [design guidance](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo). Inspect the installed toolchains before using a Duo API. Locate the bundled read-only `scripts/check_xcode.py` relative to this `SKILL.md`, then run it with `--json`; it discovers installed Xcode/SDK candidates and compiles an API probe. Pass repeatable `--xcode PATH` options when targeting specific installations. Check its result and the relevant SDK declarations. Do not require a particular Xcode filename, infer SDK support from Swift version alone, or download/install software as part of detection.
3. When available, consult [Apple's locally exported resizability skill](references/apple-skills.md) for the baseline API and safe-area audit. Export is optional and separate from the read-only capability checker; preserve the user's audit or implementation scope. Read [the migration guide](references/migration-guide.md) for pose-aware layout, state ownership, camera, testing, and delivery decisions. Choose layouts from available scene geometry and active reserved regions, not device-model or orientation labels. Keep essential actions available in compact and older-OS fallbacks.
4. Record acceptance criteria and outcomes in [the verification matrix](assets/verification-matrix.md). Automated rotation/state tests do not prove a physical hinge transition; distinguish simulator visuals, manually operated poses, and physical-device checks. Use [the completion record](assets/completion-record.md) to report exact evidence and unknowns.

Use the destination project's normal build and release workflow. Ship, submit, or modify external services only when requested; an audit or local build is not authorization to distribute. Do not restart host services, remove simulator data, or alter global Xcode selection as routine migration steps. Preserve unrelated work and treat dated beta observations in the guide as examples, not current platform rules.
