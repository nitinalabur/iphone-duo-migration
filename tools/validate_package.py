#!/usr/bin/env python3
"""Check package integrity without Xcode, network access, or third-party modules."""

import json
from pathlib import Path
import re
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    errors = []
    try:
        portable = json.loads((root / "plugin.json").read_text())
        compat = json.loads((root / ".codex-plugin/plugin.json").read_text())
        catalog = json.loads((root / ".agents/plugins/marketplace.json").read_text())
        for key in ("name", "version", "description", "author", "license"):
            if not portable.get(key) or portable[key] != compat.get(key):
                errors.append("Missing or mismatched manifest field: " + key)
        if compat.get("skills") != "./skills/":
            errors.append("Compatibility manifest must resolve the packaged skills directory")
        entries = catalog.get("plugins", [])
        if len(entries) != 1 or entries[0].get("name") != portable["name"]:
            errors.append("Marketplace must identify the packaged plugin")
        elif entries[0].get("source") != {"source": "local", "path": "./"}:
            errors.append("Marketplace must resolve the plugin at its repository root")
        skill = root / "skills" / portable["name"]
        content = (skill / "SKILL.md").read_text()
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            errors.append("Skill is missing YAML frontmatter")
        else:
            frontmatter = content.split("---", 2)[1]
            if not re.search(r"(?m)^name: *[\"']?" + re.escape(portable["name"]) + r"[\"']? *$", frontmatter):
                errors.append("Skill frontmatter name does not match its directory")
            if not re.search(r"(?m)^description: *\S", frontmatter):
                errors.append("Skill is missing its discovery description")
        for resource in ("agents/openai.yaml", "scripts/check_xcode.py", "references/migration-guide.md",
                         "assets/project-brief.md", "assets/verification-matrix.md"):
            if not (skill / resource).is_file():
                errors.append("Missing skill resource: " + resource)
        for doc in root.rglob("*.md"):
            if ".git" in doc.parts:
                continue
            text = doc.read_text()
            if text.count("```") % 2:
                errors.append(str(doc.relative_to(root)) + ": unbalanced code fences")
            for link in re.findall(r"\]\(([^\s)]+)\)", text):
                if "://" in link or link.startswith(("#", "mailto:")):
                    continue
                target = (doc.parent / link.split("#", 1)[0]).resolve()
                if not target.is_relative_to(root) or not target.exists():
                    errors.append(str(doc.relative_to(root)) + ": invalid local link " + link)
    except (OSError, ValueError, KeyError) as exc:
        errors.append(str(exc))
    if errors:
        print("Package validation failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print("Package integrity checks passed (manifests, skill entrypoint, resources, local links).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
