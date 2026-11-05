#!/usr/bin/env python3
"""Bump a plugin's version and add a CHANGELOG stub.

Usage:
  python scripts/bump_version.py example-plugin patch
  python scripts/bump_version.py example-plugin minor
  python scripts/bump_version.py example-plugin major

Edits plugins/<name>/.claude-plugin/plugin.json and inserts a dated
'## [x.y.z]' section at the top of plugins/<name>/CHANGELOG.md for you to fill in.
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[2] not in ("patch", "minor", "major"):
        print(__doc__)
        return 1
    name, part = sys.argv[1], sys.argv[2]
    pdir = ROOT / "plugins" / name
    manifest_path = pdir / ".claude-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    major, minor, patch = (int(x) for x in manifest["version"].split("-")[0].split("."))
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    new = f"{major}.{minor}.{patch}"
    old = manifest["version"]
    manifest["version"] = new
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    changelog = pdir / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    stub = (
        f"## [{new}] - {datetime.date.today().isoformat()}\n"
        "### Changed\n- TODO: describe the change and why.\n\n"
    )
    idx = text.find("## [")
    text = text[:idx] + stub + text[idx:] if idx != -1 else text.rstrip() + "\n\n" + stub
    changelog.write_text(text, encoding="utf-8")

    print(f"{name}: {old} -> {new}. Fill in the TODO in {changelog.relative_to(ROOT)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
