# skills

A collection of reusable **agent skills** (Agent Skills format). Each skill is a
self-contained folder under `skills/<name>/` with a `SKILL.md` plus its own
`scripts/`, `tests/`, and `references/`.

## What is a skill
A skill is a `SKILL.md` whose YAML frontmatter declares a `name` and a
`description` (the trigger surface an agent matches against), and whose body
progressively discloses supporting `scripts/`, `references/`, and `assets/`. An
agent loads the lean body first and pulls in depth only when needed. See the
[Agent Skills documentation](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).

## Catalog
| Skill | What it does | Docs |
|:------|:-------------|:-----|

*Adding a skill? Add a row here — this catalog is maintained by hand.*

## Using a skill
- Point an agent harness at `skills/<name>/`, or copy that folder into a project's
  `.claude/skills/`.

## Layout
```
skills/                           # repo root
├── README.md                     # this file — orientation + catalog
├── AGENTS.md                     # rules for agents authoring/maintaining skills here
├── CONTRIBUTING.md               # the skill-authoring guide + dev loop
├── scripts/validate_skills.py    # the SKILL.md contract validator (source of truth)
├── template/skill-name/          # copy this to start a new skill
├── .github/workflows/ci.yml      # validate all skills + per-skill pytest matrix
└── skills/                       # skills live here — one self-contained folder each
```

## Develop locally
```
python -m pip install pre-commit ruff pytest && pre-commit install
python scripts/validate_skills.py            # validate every skill (and the template)
cd skills/<name> && python -m pytest -q       # run one skill's test suite
pre-commit run --all-files
```
Skills target Python 3.12+ and prefer the standard library. To author a new skill,
start from `template/` and read **CONTRIBUTING.md** and **AGENTS.md**.

This README is orientation only — it does not restate any skill's mechanics. Each
`SKILL.md` is the source of truth for its own skill.
