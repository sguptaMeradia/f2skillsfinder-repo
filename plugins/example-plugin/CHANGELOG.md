# Changelog: example-plugin

Every pull request that changes this plugin adds an entry here and bumps `version`
in `.claude-plugin/plugin.json`. Newest version first.

Versioning (semver):
- **Patch** (0.1.0 → 0.1.1): wording fixes, clearer steps, no change in behavior.
- **Minor** (0.1.0 → 0.2.0): new behavior, new skill, new supporting file.
- **Major** (0.x → 1.0.0, 1.x → 2.0.0): changes how people invoke it, removes a skill, or changes output format others depend on.

## [0.1.0] - 2026-11-04
### Added
- `example-skill`: meeting notes to recap template.
- Two eval cases: basic recap, no owner named.
