# Repository guidance

Maintain a small, versioned instruction system for ChatGPT Work. Python compiles and validates execution packets; it never executes a business workflow, installs a skill, or grants tool permissions.

- Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system boundaries and [PROTOCOL.md](docs/PROTOCOL.md) for loading semantics when changing either behavior.
- Run `python -m router validate`, `python -m router eval`, and `python -m unittest discover -s tests -v` before committing behavioral changes.
- After an intentional skill edit, run `python -m router lock --write`, review the diff, and rerun validation. CI uses `lock --check`; never regenerate a lock to conceal an unexpected change.
- Keep project IDs explicit. Never import another project's active state. Keep untrusted research material outside the instruction graph.
- Prefer instruction-only skills. Registering a skill in this repository does not install it in ChatGPT.
- Record static checks, agent probes, real Work tests, and human checks separately. Do not turn pending tests into a passing claim.
- Preserve existing user content. Use scoped commits and PRs for subsequent improvements. Channel updates require an immutable, validated source commit and a release record.
- Do not copy private chat transcripts or credentials into this public repository.
- Keep `catalog/skills` outside the instruction graph. Edit its YAML sources, regenerate the map with `python -m router.catalog render`, and run `python -m router.catalog check`; see `docs/SKILLS_MAP.md`. Do not convert discovery or source-reading records into host validation claims.
