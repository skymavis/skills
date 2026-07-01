# Contributing a skill

This guide is the concrete authoring workflow. For the rules, see `AGENTS.md`; for the contract, see
`scripts/validate_skills.py` (the source of truth).

## Prerequisites

- Python 3.12+
- `python -m pip install pre-commit ruff pytest` then `pre-commit install`

## Anatomy of a skill

```
skills/<name>/
  SKILL.md            # entry point: what it does + when to use it (lean, < 500 lines)
  scripts/            # the executable tool(s)
  references/         # depth, loaded on demand (progressive disclosure)
  assets/             # templates / files the skill emits
  tests/
    conftest.py       # puts scripts/ on sys.path so `import <module>` works
  requirements-dev.txt
```

`SKILL.md` is the entry point an agent reads first; `references/` holds the detail it pulls in only
when needed; `scripts/` is the runnable logic; `assets/` are artifacts the skill produces.

## Quickstart

1. `cp -r template/skill-name skills/<your-skill>` (folder name = your kebab-case skill name).
1. Edit `skills/<your-skill>/SKILL.md`: set `name` to equal the folder, and write a third-person
   `description` (≤ 1024 chars) that says **what it does and when to use it** — this is the trigger
   surface, so be specific.
1. Fill the body (keep it under 500 lines; push depth into `references/`).
1. Add a row to the catalog table in `README.md`.

## Frontmatter contract

Allowed keys only: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`.
`name` + `description` required. `name` must be kebab-case, ≤ 64 chars, and equal the folder name.
Run the validator on your skill:

```sh
python scripts/validate_skills.py skills/<your-skill>/SKILL.md
```

## Tests

- Keep the provided `tests/conftest.py` — it puts `scripts/` on `sys.path` so `import <module>`
  works without a symlink.
- Put pytest tests under `tests/`; add only-needed deps to `requirements-dev.txt` (CI always
  installs `pytest`).
- Run: `cd skills/<your-skill> && python -m pytest -q`.
- A skill with no `tests/` is allowed (validator-only), but tests are expected for any skill that
  ships a script.

## Optional: a CI-safe check

If your skill ships a tool with a stale/lint/validation check (the model is `decisions.py check`
from `decision-records`), document the command so it can be wired into `.pre-commit-config.yaml` and
CI.

## Local dev loop (in order)

```sh
python scripts/validate_skills.py        # 1. contract
cd skills/<name> && python -m pytest -q   # 2. tests
pre-commit run --all-files                # 3. lint/format/hooks
```

Run with no path, `validate_skills.py` checks every skill and the template. CI runs the same
validator over every skill and the touched skill's pytest suite, so green locally means green in CI.

## Commits

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org)
(`type(scope): summary`) with the subject and body lines wrapped at 72. Every commit needs a body —
explain *why*, not just what the diff already shows. This is enforced by `gitlint` — a `commit-msg`
hook locally and a CI gate on every PR (config in `.gitlint`). `pre-commit install` wires the hook
automatically. For the rare unbreakable body line (a long URL), add a `gitlint-ignore: B1` footer to
that commit.
