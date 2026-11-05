# F2 Skills

The source of truth for F2 Strategy's Claude skills. Every skill that reaches users
is built, reviewed, tested and released from this repository. Git keeps the record of
what changed, when, who made the change and who approved it.

## How it is organized

```
.
├── .claude-plugin/
│   └── marketplace.json          # the catalog: which plugins this repo publishes
├── plugins/
│   └── example-plugin/           # one folder per plugin (copy this to start a new one)
│       ├── .claude-plugin/
│       │   └── plugin.json       # name, description, version  <- the release number
│       ├── skills/
│       │   └── example-skill/
│       │       └── SKILL.md      # the skill itself, plus any supporting files
│       ├── evals/
│       │   └── evals.json        # test prompts and what a passing answer contains
│       └── CHANGELOG.md          # one entry per version
├── scripts/
│   ├── validate.py               # the checks CI runs on every pull request
│   └── bump_version.py           # bumps the version and adds a changelog stub
├── deploy/
│   └── managed-settings.example.json   # how admins push the marketplace to Claude Code
├── .github/
│   ├── CODEOWNERS                # who must approve changes to each plugin
│   ├── pull_request_template.md
│   └── workflows/
│       ├── validate.yml          # runs validate.py on every PR and push
│       └── release.yml           # tags and releases new versions on merge to main
└── CONTRIBUTING.md               # the day-to-day workflow
```

A **plugin** is the unit you version and ship. It can hold one skill or several related ones.

## The lifecycle

```
branch ──► pull request ──► CI checks + code-owner review ──► merge to staging
   ──► pilot users try it ──► merge staging to main ──► auto tag + GitHub Release
   ──► admins enable or update it for the organization
```

| Stage | What happens | Record it leaves |
|---|---|---|
| Develop | Work on a branch, test with `claude --plugin-dir ./plugins/<name>` | Commits with author and message |
| Review | PR with template; CI runs `validate.py`; code owners approve | PR, reviewers, CI result |
| Stage | Merge to `staging`; pilot group uses it | Merge commit |
| Release | Merge `staging` to `main`; `release.yml` tags `<plugin>-v<version>` | Tag + GitHub Release with changelog notes |
| Deploy | Admin enables the plugin for the org | Admin console |
| Roll back | Revert on `main` and bump the version, or re-point to an older tag | Revert commit + new release |

## Who changed what

- **Line by line:** `git blame plugins/<name>/skills/<skill>/SKILL.md`
- **History of a skill:** `git log --follow -p plugins/<name>/skills/<skill>/SKILL.md`
- **What shipped in a version:** the GitHub Release for `<plugin>-v<version>`, or `git diff <plugin>-v1.2.0 <plugin>-v1.3.0 -- plugins/<plugin>/`
- **Why and who approved:** the pull request linked from the merge commit

## One-time setup (repository admin)

1. **Create the repo** in the F2 GitHub organization (private) and push this skeleton.
2. **Replace placeholders:**
   - `.github/CODEOWNERS`: real team and user handles
   - `deploy/managed-settings.example.json`: `your-org/f2-skills` → the real repo
3. **Create the `staging` branch** from `main`.
4. **Protect `main` and `staging`** (Settings > Branches > add rule for each):
   - Require a pull request before merging, with at least 1 approval
   - Require review from Code Owners
   - Require status checks to pass: `validate`
   - Do not allow bypassing the above settings
5. **Allow the release workflow to push tags:** Settings > Actions > General >
   Workflow permissions > Read and write.
6. **Turn on secret scanning** (Settings > Code security) as a second layer behind `validate.py`.

## Deploying to users

Two paths, depending on where people use Claude:

- **claude.ai, desktop and Cowork:** an org admin turns plugins on under
  Organization settings > Plugins & skills. Those also sync to Claude Code.
- **Claude Code across machines:** an admin registers this repo as a marketplace through
  managed settings (Organization settings > Claude Code > Managed settings). See
  `deploy/managed-settings.example.json`. With `autoUpdate` on, users pick up new
  versions at the start of their next session.

Uploading a single skill zip in admin settings also works, but it bypasses review,
history and rollback. Use this repo as the only path to production.

Pinning a pilot group to `staging` (a branch or commit) is configured in the marketplace
source; check the current Claude Code plugin docs for the exact syntax before relying on it.

## Starting a new plugin

```bash
cp -r plugins/example-plugin plugins/my-new-plugin
# edit plugins/my-new-plugin/.claude-plugin/plugin.json  (name, description, version 0.1.0)
# rename skills/example-skill to your skill name and rewrite SKILL.md
# rewrite evals/evals.json and CHANGELOG.md
# add an entry to .claude-plugin/marketplace.json
# add a line to .github/CODEOWNERS
python scripts/validate.py
```

Then follow CONTRIBUTING.md.
