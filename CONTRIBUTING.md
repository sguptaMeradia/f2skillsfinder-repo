# Contributing

How to change a skill, from first edit to release.

## Roles

| Role | Does |
|---|---|
| **Contributor** | Branches, edits, adds eval cases, opens the PR |
| **Plugin owner** (named in CODEOWNERS) | Reviews and approves changes to their plugin, keeps the changelog honest, decides when it is ready to release |
| **Release manager** | Merges `staging` into `main`, watches the release workflow, tells the admin what changed |
| **Org admin** | Enables or updates the plugin in Claude admin settings. Does not edit skill content |

## Branches

- `main`: what users have. Only `staging` merges here.
- `staging`: what the pilot group has. Feature branches merge here.
- `feature/<plugin>-<short-description>`: your work, for example `feature/example-plugin-owner-handling`.

Nobody pushes to `main` or `staging` directly. Branch protection enforces it.

## Making a change

1. **Branch from `staging`**
   ```bash
   git checkout staging && git pull
   git checkout -b feature/example-plugin-owner-handling
   ```

2. **Edit the skill.** Keep `SKILL.md` focused on steps Claude should follow. Put long
   reference material in separate files next to it and point to them.

3. **Add or update an eval case** in `evals/evals.json`. A bug fix gets a case that fails
   before the fix and passes after it.

4. **Test locally**
   ```bash
   claude --plugin-dir ./plugins/example-plugin
   ```
   Try the eval prompts and at least one prompt that should *not* trigger the skill.

5. **Bump the version** and write the changelog entry
   ```bash
   python scripts/bump_version.py example-plugin patch   # or minor / major
   ```
   Then replace the TODO in `CHANGELOG.md` with what changed and why.

6. **Validate**
   ```bash
   pip install pyyaml
   python scripts/validate.py --base origin/staging
   ```

7. **Commit with a clear message and open a PR into `staging`**
   ```bash
   git commit -am "example-plugin: never invent an owner for unassigned actions"
   git push -u origin HEAD
   ```
   Fill in the PR template. CI runs and the plugin owner is requested automatically.

8. **After approval, merge.** Use "Squash and merge" so each change is one commit on
   `staging` with the PR number in its message.

## Releasing

1. The pilot group uses `staging` for an agreed period (suggest one week, or until the
   owner signs off).
2. The release manager opens a PR from `staging` into `main` titled
   `Release: <plugin> <version>[, <plugin> <version>]`.
3. On merge, `release.yml` creates a tag `<plugin>-v<version>` and a GitHub Release using
   that version's changelog section, for every plugin whose version is new.
4. The release manager sends the admin the release link. The admin updates or enables the
   plugin in Claude admin settings, or confirms auto-update picked it up.

## Hotfix

For a skill that is causing harm or wrong output in production:

1. Branch from `main`: `hotfix/<plugin>-<issue>`.
2. Fix, add the eval case, bump the **patch** version, update the changelog.
3. PR into `main` (owner approval still required), then merge `main` back into `staging`.

## Rolling back

Prefer a forward fix: revert the bad commit on `main` with `git revert`, bump the patch
version, and let the release workflow publish it. That keeps history linear and every
version number points at one exact state.

## Rules for skill content

- No client names, account numbers, SSNs, card numbers or personal data anywhere: skill text,
  examples, evals or test fixtures. Use made-up placeholders. `validate.py` catches the
  obvious patterns; it does not catch names, so reviewers check for those.
- No API keys or tokens in the repo. Use GitHub secrets for CI.
- The skill `name` matches its folder, is lowercase-kebab-case, and does not contain
  "claude" or "anthropic".
- The `description` says what the skill does **and** when to use it, under 1024 characters.
  It is what decides when the skill triggers, so changing it is a behavior change
  (minor version at least).
