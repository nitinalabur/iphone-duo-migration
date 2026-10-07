# iPhone Duo verification matrix

For each primary task, mark **Pass**, **Fail**, **Not tested**, or **Not applicable**. Record evidence for a pass and the reason for any untested or inapplicable row. Distinguish a requested orientation change from an actual fold or display transition.

| Configuration or transition | Observable check | Status | Evidence / reason |
| --- | --- | --- | --- |
| Closed outer display | Complete task; navigation and commit/cancel reachable | [status] | [path or reason] |
| Flat inner, portrait | Useful space, readable content, reachable actions | [status] | [path or reason] |
| Flat inner, landscape | Useful space, readable content, reachable actions | [status] | [path or reason] |
| Book partial fold | Content avoids division; each active pane usable | [status] | [path or reason] |
| Laptop partial fold | Controls and content usable above/below division | [status] | [path or reason] |
| Tent and laptop-to-tent | Active display and orientation observed; task usable | [status] | [path or reason] |
| Outer-to-inner with unfinished work | Draft, selection, media, destination retained | [status] | [path or reason] |
| Fold with keyboard, sheet, or alert open | Focus, dismiss, and commit remain reachable | [status] | [path or reason] |
| Light/dark, larger text, accessibility | Legible layout and sensible reading/focus order | [status] | [path or reason] |
| Reduced window width / multitasking | Essential content remains reachable | [status] | [path or reason] |
| Partially folded, app in left and right multitasking panes | A division at/outside the window edge does not force paired panes; scroll and commit remain reachable | [status] | [path or reason] |
| Vertical bar changes edge without resizing | Controls follow current local safe areas; no cached or symmetric inset assumptions | [status] | [path or reason] |
| Right-to-left layout and asymmetric safe areas | Leading/trailing behavior is correct; no doubled clearance or clipped controls | [status] | [path or reason] |
| Sheet or child pane with its own safe area | Local controls use their container's safe area rather than the parent/window's | [status] | [path or reason] |
| Conventional iPhone on minimum supported iOS | Complete compact flow and runtime fallback | [status] | [path or reason] |
| Physical Duo camera, if relevant | Intended direction, preview, capture, selected media | [status] | [path or reason] |

Evidence header: source revision [revision] · Xcode/SDK [versions] · OS/runtime [version] · device/display [identity] · pose [observed pose] · appearance [mode].
