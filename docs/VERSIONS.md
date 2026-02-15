# Version Tracking -- AI Vectra Bank

## Git Workflow

```
main                  <-- stable, tested code only (via PR)
  |
  +-- dev/feature-x   <-- feature branches for active work
```

- **main**: protected, only receives merges via pull request
- **dev/***:  feature branches created for each piece of work
- Commits follow conventional format: `type(scope): description`

## Active Branches

| Branch | Goal | Status | Created | Last Updated |
|--------|------|--------|---------|--------------|
| main   | Stable production code | Active | 2026-02-15 | 2026-02-15 |

## Merged Branches

| Branch | Goal | Merged To | Date | PR |
|--------|------|-----------|------|----|
| (none yet) | | | | |

## Commit Convention

```
feat(scope): add new feature
fix(scope): fix a bug
docs(scope): documentation only
refactor(scope): code change that neither fixes nor adds
test(scope): add or update tests
chore(scope): maintenance (deps, config, etc.)
```

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2026-02-15 | Initial implementation -- 6 agents, orchestration, 21/21 tests |
