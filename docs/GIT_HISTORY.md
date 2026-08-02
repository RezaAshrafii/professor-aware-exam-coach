# Git history for v0.4.0

This release was built with real branches and commits.

## Branches

- `chore/repository-foundation`
- `feat/example-cards`
- `main`

## Commits

```text
*   222ac78 (HEAD -> main) merge: add professor example cards
|\  
| * 20a6126 (feat/example-cards) docs: document v0.4.0 workflow and release gate
| * cf4ff4a feat(ui): add example card review workflow
| * 0fcaf5e feat(examples): add confirmed professor example cards
|/  
*   51b5744 merge: establish GitHub repository foundation
|\  
| * 441577b (chore/repository-foundation) ci: add GitHub quality workflow and repository standards
|/  
* 01b2361 chore: import validated v0.3.0 baseline
```

## Release policy

Future versions should start from `main`, use one short-lived branch per bounded change, pass CI and the version-specific manual gate, then merge through a Pull Request.
