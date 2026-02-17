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
| main   | Stable production code | Active | 2026-02-15 | 2026-02-16 |
| dev    | Current development | Active | 2026-02-16 | 2026-02-17 |

## Merged Branches

| Branch | Goal | Merged To | Date | PR |
|--------|------|-----------|------|----||
| dev/azure-embeddings-and-diagrams | Azure embedding function + architecture docs | main | 2026-02-16 | #1 |

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
| 0.2.0 | 2026-02-16 | Azure embedding integration, architecture diagrams, PR #1 merged |
| 0.3.0 | 2026-02-17 | Live Azure AI Foundry deployment -- gpt-4o + ada-002, 23/23 tests |
| 0.4.0 | 2026-02-17 | Azure SQL provisioned -- full data plane live, 23/23 tests with live DB |

## Commit Log

| Hash | Branch | Message |
|------|--------|---------|
| 485998d | main | chore: initial project setup with 6-agent banking RAG system |
| e701a85 | dev/azure-embeddings-and-diagrams | feat(rag): add Azure text-embedding-ada-002 integration and architecture diagrams |
| 53a2a3f | dev/azure-embeddings-and-diagrams | docs: add session 3 memory log |
| 70bdfdb | main | Merge pull request #1 (azure-embeddings-and-diagrams -> main) |
| 537586e | dev | docs: add enhanced multi-agent systems course notes for team reference |
| 54668d2 | dev | feat: integrate live Azure AI Foundry deployments (gpt-4o + ada-002) |
