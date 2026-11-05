## What changed

<!-- One or two lines. Which plugin and skill, and what is different for the person using it. -->

## Why

<!-- The problem, request or bug this fixes. Link the issue if there is one. -->

## Version

- Plugin: `________`
- Version: `x.y.z` → `x.y.z`
- Bump type: [ ] patch  [ ] minor  [ ] major

## Checklist

- [ ] Version bumped in `plugin.json` (`python scripts/bump_version.py <plugin> <patch|minor|major>`)
- [ ] `CHANGELOG.md` entry written for the new version
- [ ] Eval case added or updated in `evals/evals.json` (a bug fix gets a case that would have caught it)
- [ ] Tested locally with `claude --plugin-dir ./plugins/<plugin>`
- [ ] `python scripts/validate.py` passes
- [ ] No client names, account numbers or personal data in the skill, examples or evals

## How to test

<!-- The prompt a reviewer should try, and what a good answer looks like. -->
