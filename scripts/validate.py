#!/usr/bin/env python3
"""Validate the skills marketplace before merge.

Checks:
  1. .claude-plugin/marketplace.json parses and lists plugins with valid names and sources.
  2. Each plugin has .claude-plugin/plugin.json with a matching name and a semver version.
  3. Each skill folder has a SKILL.md with valid frontmatter (name, description).
  4. Each plugin has a CHANGELOG.md entry for its current version.
  5. Each plugin has evals/evals.json with at least one case.
  6. No obvious sensitive data (SSNs, card numbers, private keys, API keys) in any file.
  7. With --base REF: any plugin whose files changed since REF must have a higher version.

Usage:
  python scripts/validate.py                  # checks 1-6
  python scripts/validate.py --base origin/main   # also check 7 (used in CI on pull requests)

Exit code 0 = pass, 1 = errors found.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml  # PyYAML
except ImportError:
    sys.exit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z.-]+)?$")
RESERVED_WORDS = ("claude", "anthropic")

SENSITIVE_PATTERNS = {
    "US SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "card number": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Anthropic API key": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{10,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
}
SCAN_SUFFIXES = {".md", ".json", ".txt", ".yml", ".yaml", ".py", ".sh", ".csv", ".html", ".js", ".ts"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        err(f"{rel(path)}: file missing")
    except json.JSONDecodeError as e:
        err(f"{rel(path)}: invalid JSON ({e})")
    return None


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def semver_tuple(v: str) -> tuple[int, int, int]:
    m = SEMVER.match(v)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (-1, -1, -1)


def parse_frontmatter(text: str) -> dict | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def check_skill(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        err(f"{rel(skill_dir)}: missing SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        err(f"{rel(skill_md)}: missing or invalid YAML frontmatter (must start with --- and close with ---)")
        return
    name = fm.get("name")
    desc = fm.get("description")
    if not name:
        err(f"{rel(skill_md)}: frontmatter has no 'name'")
    else:
        if name != skill_dir.name:
            err(f"{rel(skill_md)}: name '{name}' must match folder name '{skill_dir.name}'")
        if not KEBAB.match(name):
            err(f"{rel(skill_md)}: name '{name}' must be lowercase-kebab-case")
        if len(name) > 64:
            err(f"{rel(skill_md)}: name is {len(name)} chars (max 64)")
        if any(w in name for w in RESERVED_WORDS):
            err(f"{rel(skill_md)}: name must not contain 'claude' or 'anthropic'")
    if not desc:
        err(f"{rel(skill_md)}: frontmatter has no 'description'")
    else:
        desc = str(desc)
        if len(desc) > 1024:
            err(f"{rel(skill_md)}: description is {len(desc)} chars (max 1024)")
        if "<" in desc or ">" in desc:
            err(f"{rel(skill_md)}: description must not contain angle brackets")
        if len(desc) < 40:
            warn(f"{rel(skill_md)}: description is very short; say what it does AND when to use it")
    body = text.split("---", 2)[2].strip()
    if len(body) < 50:
        warn(f"{rel(skill_md)}: body is nearly empty")


def check_plugin(entry: dict) -> tuple[str, Path, str] | None:
    name = entry.get("name", "")
    source = entry.get("source")
    if not KEBAB.match(name or ""):
        err(f"marketplace.json: plugin name '{name}' must be lowercase-kebab-case")
    if not isinstance(source, str) or not source.startswith("./"):
        err(f"marketplace.json: plugin '{name}' source must be a relative path starting with ./ (got {source!r})")
        return None
    pdir = (ROOT / source).resolve()
    if not pdir.is_dir():
        err(f"marketplace.json: plugin '{name}' source {source} does not exist")
        return None

    manifest = load_json(pdir / ".claude-plugin" / "plugin.json")
    if manifest is None:
        return None
    if manifest.get("name") != name:
        err(f"{rel(pdir)}/.claude-plugin/plugin.json: name '{manifest.get('name')}' does not match marketplace entry '{name}'")
    version = str(manifest.get("version", ""))
    if not SEMVER.match(version):
        err(f"{rel(pdir)}/.claude-plugin/plugin.json: version '{version}' is not semver (e.g. 1.2.0)")
    if "version" in entry and str(entry["version"]) != version:
        err(f"marketplace.json: '{name}' lists version {entry['version']} but plugin.json says {version}")
    if not manifest.get("description"):
        err(f"{rel(pdir)}/.claude-plugin/plugin.json: missing description")

    skills_root = pdir / "skills"
    skill_dirs = [d for d in skills_root.iterdir() if d.is_dir()] if skills_root.is_dir() else []
    if not skill_dirs:
        warn(f"{rel(pdir)}: no skills/ folders found")
    for sd in sorted(skill_dirs):
        check_skill(sd)

    changelog = pdir / "CHANGELOG.md"
    if not changelog.exists():
        err(f"{rel(pdir)}: missing CHANGELOG.md")
    elif version and f"## [{version}]" not in changelog.read_text(encoding="utf-8"):
        err(f"{rel(changelog)}: no '## [{version}]' entry for the current version")

    evals = pdir / "evals" / "evals.json"
    if not evals.exists():
        err(f"{rel(pdir)}: missing evals/evals.json (every plugin ships with test cases)")
    else:
        data = load_json(evals)
        if data is not None and not data.get("cases"):
            err(f"{rel(evals)}: has no cases")

    return name, pdir, version


def scan_sensitive() -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if path.name == "validate.py":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SENSITIVE_PATTERNS.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    err(f"{rel(path)}:{lineno}: looks like a {label}; remove it or use an obvious placeholder")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def check_version_bumps(base: str, plugins: list[tuple[str, Path, str]]) -> None:
    try:
        changed = git("diff", "--name-only", f"{base}...HEAD").splitlines()
    except subprocess.CalledProcessError as e:
        err(f"could not diff against {base}: {e.stderr.strip()}")
        return
    for name, pdir, version in plugins:
        prefix = rel(pdir) + "/"
        if not any(f.startswith(prefix) for f in changed):
            continue
        manifest_path = f"{prefix}.claude-plugin/plugin.json"
        try:
            base_manifest = json.loads(git("show", f"{base}:{manifest_path}"))
        except subprocess.CalledProcessError:
            continue  # new plugin, nothing to compare
        old = str(base_manifest.get("version", "0.0.0"))
        if semver_tuple(version) <= semver_tuple(old):
            err(f"{name}: files changed but version is still {version} (base has {old}); bump it in plugin.json and add a CHANGELOG entry")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", help="git ref to compare against for the version-bump check, e.g. origin/main")
    args = ap.parse_args()

    market = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    plugins: list[tuple[str, Path, str]] = []
    if market is not None:
        for key in ("name", "owner", "plugins"):
            if key not in market:
                err(f"marketplace.json: missing '{key}'")
        names = [p.get("name") for p in market.get("plugins", [])]
        for dup in {n for n in names if names.count(n) > 1}:
            err(f"marketplace.json: plugin '{dup}' listed more than once")
        for entry in market.get("plugins", []):
            result = check_plugin(entry)
            if result:
                plugins.append(result)

        listed = {p[1] for p in plugins}
        plugins_root = ROOT / "plugins"
        if plugins_root.is_dir():
            for d in plugins_root.iterdir():
                if d.is_dir() and d.resolve() not in listed:
                    warn(f"{rel(d)}: folder exists but is not listed in marketplace.json")

    scan_sensitive()
    if args.base:
        check_version_bumps(args.base, plugins)

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    status = "FAILED" if errors else "PASSED"
    print(f"\n{status}: {len(plugins)} plugin(s) checked, {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
