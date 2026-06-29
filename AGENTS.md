# AGENTS.md — the skills repo

You are an agent authoring and maintaining reusable agent skills in this repo. **This file governs
how to work _here_; each skill's own `SKILL.md` governs how to _use_ that skill.**

## Read order (every task)

1. This file.
1. `README.md` — the catalog and layout.
1. `scripts/validate_skills.py` — the contract you must satisfy.
1. `CONTRIBUTING.md` — the authoring workflow and local dev loop.
1. The target skill's `SKILL.md`.

## The skill contract (self-check before running the validator)

- A skill is a folder `skills/<name>/` containing a `SKILL.md`.
- **Folder name == frontmatter `name`**, kebab-case `^[a-z0-9-]+$`, ≤ 64 chars, no
  leading/trailing/consecutive hyphen, and not `anthropic`/`claude`.
- Frontmatter is a top-of-file YAML block fenced by `---` … `---`. Allowed keys **only**: `name`,
  `description`, `license`, `allowed-tools`, `metadata`, `compatibility`. `name` and `description`
  are required.
- `description`: non-empty, ≤ 1024 chars, third person, no angle brackets. It is the trigger surface
  — say what the skill does **and** when to use it.
- `SKILL.md` body ≤ 500 lines (budget). Push depth into `references/`.
- Relative links in `SKILL.md` must resolve.

## Authoring discipline

- Each skill is **self-contained** under `skills/<name>/`: `scripts/` (executable logic),
  `references/` (depth loaded on demand), `assets/` (templates/files the skill emits), `tests/`
  (pytest, with a `conftest.py` that injects `scripts/` onto `sys.path`).
- Prefer the standard library; declare any extra test deps in the skill's `requirements-dev.txt` (CI
  always installs `pytest`).
- **Progressive disclosure**: keep `SKILL.md` lean; depth goes in `references/`.
- **Don't hand-format `SKILL.md` line shape.** `pre-commit` runs `mdformat --wrap 100` over every
  `SKILL.md`, so write prose in whatever line shape and let the hook reflow it (it leaves tables,
  code blocks, and long URLs intact). Run `pre-commit run --all-files` and commit the result; CI
  checks the same fixed point.

## Point to skills; never copy from them

A `SKILL.md` is the source of truth for what it owns. Referencing or linking a skill is good.
Copying one skill's mechanics into `README.md`, `AGENTS.md`, or another skill is wrong — it
duplicates, drifts, and goes stale. A skill may expose a CI-safe check command (the model is
`decisions.py check` from `decision-records`); CI runs it. **Never hand-edit a skill's generated
artifacts** (e.g. a generated `INDEX.md`) — regenerate via that skill's own tool.

## Definition of done (before opening a PR)

- `python scripts/validate_skills.py` passes for **all** skills.
- The touched skill's `python -m pytest -q` passes.
- New or changed behavior has a test.
- `pre-commit run --all-files` is clean, and the README catalog is updated if a skill was added or
  its description changed.
- Commits are [Conventional Commits](https://www.conventionalcommits.org) (`type(scope): summary`),
  subject and body wrapped at 72 — enforced by `gitlint` (commit-msg hook + CI). Write commit bodies
  at 72 columns.
