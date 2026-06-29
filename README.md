# skills

A collection of reusable **agent skills** (Agent Skills format). Each skill is a self-contained
folder under `skills/<name>/` with a `SKILL.md` plus its own `scripts/`, `tests/`, and
`references/`.

## What is a skill

A skill is a `SKILL.md` whose YAML frontmatter declares a `name` and a `description` (the trigger
surface an agent matches against), and whose body progressively discloses supporting `scripts/`,
`references/`, and `assets/`. An agent loads the lean body first and pulls in depth only when
needed. See the
[Agent Skills documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).

## Catalog

| Skill              | What it does                                                                                                                                            | Docs                                         |
| :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------- |
| `decision-records` | Draft, promote, archive, and supersede ADR-style decision records; keeps `INDEX.md` and cross-links generated and validated via `scripts/decisions.py`. | [SKILL.md](skills/decision-records/SKILL.md) |

*Adding a skill? Add a row here — this catalog is maintained by hand.*

## Using a skill

Two steps: install the skill into your agent, then (for `decision-records`) adopt it in a repo.

### 1. Install it

Use the [`skills` CLI](https://github.com/vercel-labs/skills) — no clone needed. Choose
project-local or global, and pass each agent you use with `-a`:

```sh
# project-local (committed with the repo)
npx skills add skymavis/skills@decision-records -a claude-code -a codex

# global — available across all your projects
npx skills add skymavis/skills@decision-records -g -a claude-code
```

This drops the skill into each agent's skills directory — `.claude/skills/` for Claude Code,
`.agents/skills/` for Codex (`~/…` with `-g`). See the
[supported-agents table](https://github.com/vercel-labs/skills#supported-agents) for the exact path
per agent, then reload skills in your agent to pick it up.

> No CLI? Point an agent harness straight at `skills/<name>/`, or copy that folder into a project's
> `.claude/skills/`.

### 2. Adopt it in a repo

`decision-records` tracks decisions inside whatever repo you point it at. The easiest way: **ask
your agent to "set up decision records in this repo"** — it knows where its own skill scripts live.
Or run the bundled tool by hand from the repo you want to track:

```sh
python <skills-dir>/decision-records/scripts/decisions.py install   # <skills-dir> = your agent's, e.g. .claude/skills
```

It scaffolds `docs/decisions/`, generates the index, adds a pre-commit check, and drops a human
`README.md` + an agent-facing `AGENTS.md` so the repo (and its agents) know the convention.

## Layout

```
skills/                           # repo root
├── README.md                     # this file — orientation + catalog
├── AGENTS.md                     # rules for agents authoring/maintaining skills here
├── CONTRIBUTING.md               # the skill-authoring guide + dev loop
├── scripts/validate_skills.py    # the SKILL.md contract validator (source of truth)
├── template/skill-name/          # copy this to start a new skill
├── .github/workflows/ci.yml      # validate all skills + per-skill pytest matrix
└── skills/
    └── decision-records/         # a skill: SKILL.md + scripts/ + references/ + templates/ + tests/
```

## Develop locally

Skills target Python 3.12+ and prefer the standard library. To author a skill and run the dev loop
(set up, validate → test → lint), see [CONTRIBUTING.md](CONTRIBUTING.md); for the rules, see
[AGENTS.md](AGENTS.md).

This README is orientation only — it does not restate any skill's mechanics. Each `SKILL.md` is the
source of truth for its own skill.
