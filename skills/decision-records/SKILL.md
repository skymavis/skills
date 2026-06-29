---
name: decision-records
description: >-
  Draft, promote, archive, and supersede ADR-style decision records (types are open: architecture,
  product, security, policy, legal, …) and keep INDEX.md and cross-links generated, via the bundled
  scripts/decisions.py tool. Use when creating or promoting decision drafts, superseding or
  archiving a decision, fixing a promotion breach, or running build, check, promote,
  rename-draft-id, or install.
---

# Decision records

This skill owns the registry tool `decisions.py`, symlinked into the repo at `scripts/decisions.py`
(run `decisions.py install` to set up the symlink + a CI check). The tool finds the repo's `docs/`
by walking up from the CWD, so run it from anywhere in the repo:

```
python scripts/decisions.py build [--relink]            # regenerate INDEX.md (+ refresh links)
python scripts/decisions.py check                       # validate (CI-safe; exit 1 if stale)
python scripts/decisions.py promote <name…> [--deref] [--allow-replace]   # draft(s) -> decisions/
python scripts/decisions.py rename-draft-id <name> <NEW>                  # re-id a draft
python scripts/decisions.py install [repo]              # adopt in a repo: symlink + pre-commit
```

## Layout

```
docs/
  INDEX.md            # GENERATED registry over decisions/ + archived/
  decisions/<type>/   # ACCEPTED numbered records; <type> = any lowercase slug you define
  archived/           # RETIRED records (superseded | deprecated) — flat
  drafts/             # WIP candidates — flat, 4-UPPERCASE-letter ids, NOT in INDEX
```

| Stage           | Dir                 | Id                                     | Status                      |
| :-------------- | :------------------ | :------------------------------------- | :-------------------------- |
| candidate (WIP) | `drafts/`           | 4 UPPERCASE letters, mnemonic (`CONF`) | `draft`                     |
| decision        | `decisions/<type>/` | global counter (`0001`…)               | `accepted`                  |
| retired         | `archived/`         | (keeps its counter)                    | `superseded` / `deprecated` |

**Types are open** — `<type>` is any lowercase slug, and your `decisions/<type>/` subdirs are the
set (software: `architecture`, `product`, `security`; governance: `policy`, `legal`, `finance`,
`people`, `compliance`, `operations`). A new type's directory is created on promotion. The tool
enforces that a decision sits in the subdir matching its `type` — not a fixed list.

There is no `proposed` status — "proposing" is the act of opening a PR that promotes a draft. Mint a
draft id yourself (a mnemonic of the topic); `check` enforces format + uniqueness. Cross-reference
by writing the bare id as inline code — `` `0006` `` (decision) or `` `CONF` `` (draft); never
hand-author a path — `build --relink` generates and self-heals every link across every `docs/*.md`
(records, drafts, and other docs like `threat-model.md`).

## Promoting drafts

**Promotion requires explicit human sign-off.** Promoting is a finalizing, semi-irreversible act
(accepted records are immutable — supersede, don't edit). Author, edit, and validate drafts freely;
but never run `promote` — or its downstream steps (replacing naming placeholders, resolving threads,
regenerating `INDEX.md`) — without the user's explicit go-ahead in the current turn. Don't infer
approval from an adjacent choice (a scope answer, a cleared checklist); when unsure, ask.

**An accepted decision may never reference a draft.** `promote` enforces this: it refuses a set that
would breach and prints exactly how to fix it (co-promote, `--deref`, or `--allow-replace`) with a
copy-paste prompt. Before any promotion the tool refuses — or any supersession — read
**[references/promotion.md](references/promotion.md)** for the mechanics.

## Adopting this in a repo

Run `python .claude/skills/decision-records/scripts/decisions.py install [repo]` (`repo` defaults to
the current dir; install sets up *there* — it does not search upward). It symlinks
`<repo>/scripts/decisions.py` to this skill's copy, scaffolds the `docs/` skeleton (`decisions/`,
`archived/`, `drafts/`, and the two templates), **generates** `INDEX.md` (it's a build artifact, not
a starter), and in a git repo adds a `pre-commit` hook running `decisions.py check`. Idempotent —
the skeleton is filled in only where missing; INDEX is (re)generated. For CI, run
`python scripts/decisions.py check` on every push.
