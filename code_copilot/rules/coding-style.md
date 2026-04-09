# Coding Style

- Keep boundary code thin and business logic explicit.
- Prefer small functions with clear ownership.
- Wrap or annotate errors when they cross boundaries.
- Add tests for changed behavior, not only happy paths.
- Keep naming aligned across API, storage, and client layers.
- Prefer reversible changes over wide untracked edits.
