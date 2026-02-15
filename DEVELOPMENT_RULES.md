# Development Rules - AI Vectra Bank Project
Last Updated: 2026-02-15

## CODE QUALITY
- NO EMOJIS in code, comments, commit messages, or documentation - causes encoding issues and looks unprofessional
- Use project virtual environment (.venv) - NEVER use global environment
- Follow PEP 8 for Python, consistent SQL capitalization
- Meaningful names: user_count not x, calculate_weighted_average() not calc()
- Type hints for Python functions, docstrings for all modules/functions/classes

## VERSION CONTROL
- NEVER commit directly to main - all changes through feature branches
- Branch naming: `<type>/<short-description>`
  - feat/ - New feature
  - fix/ - Bug fix
  - docs/ - Documentation
  - refactor/ - Code restructuring
  - test/ - Tests
  - chore/ - Maintenance
- Commit messages: Use conventional commits format: `<type>: <description>`
  - GOOD: `feat: add user authentication with JWT`
  - GOOD: `fix: resolve null pointer in data aggregation`
  - BAD: `updated stuff` or `fix bug`
- One branch = one logical unit of work - do not bundle unrelated changes
- Branch Workflow:
  1. `git pull origin main`
  2. `git checkout -b <type>/<description>`
  3. Make changes, commit incrementally
  4. `git push origin <branch-name>`
  5. Create Pull Request
  6. After merge: delete branch

## DOCUMENTATION
- Do NOT create new markdown files unless explicitly requested
- Use existing docs/ files to accommodate new content
- Update documentation as you code, not later - include in the same commit
- Update `docs/PROJECT_STATUS_REVIEW.md` after every significant change with:
  - Date and update number
  - What was evaluated/changed
  - Results and metrics
  - Reason for change
  - Files modified
- Track all branches in `docs/VERSIONS.md`:
  - Active Branches: branch name, goal, status, date created, last updated
  - Archived Branches: branch name, goal, final status (merged/abandoned), date closed, notes

## SCRIPT MANAGEMENT
- Track all scaffolding scripts - document purpose and delete after integration
- NO ORPHAN SCRIPTS - before deleting, verify:
  - Functionality integrated into main system
  - Tests pass without it
  - No dependencies on it
  - Documentation updated
- Production scripts require:
  - Error handling (not just print statements)
  - Logging
  - Docstrings (module, function, class level)
  - Argument parsing
  - Usage examples

## TESTING
- Run tests before merging: `pytest tests/`
- Unit tests for critical functions (data transformations, calculations, business logic)
- Integration tests for end-to-end pipelines
- Pre-merge checklist:
  - [ ] All tests pass
  - [ ] Code follows style guide
  - [ ] Documentation updated
  - [ ] No hardcoded credentials/paths
  - [ ] No debug print statements
  - [ ] Branch tracking updated

## SECURITY
- NEVER commit API keys, passwords, connection strings
- Use environment variables: `api_key = os.getenv("API_KEY")`
- Use .env files (add to .gitignore)
- Document required secrets in README/env.example without exposing values

## PROJECT PLANNING
- At the end of every status update, include BIG PICTURE PLAN:
  - Current Phase
  - Immediate Priorities (This Week)
  - Next Phase (Next 2 Weeks)
  - Long-term Goals (Next Month+)
- Purpose: Prevents tunnel vision on single tasks while losing sight of overall goals

## AI AGENT SPECIFIC
What You Should ALWAYS Do:
  - Explain reasoning before implementing
  - Show diffs for file changes
  - Ask for confirmation on destructive operations
  - Validate assumptions with user
  - Provide rollback instructions when making changes
What You Should NEVER Do:
  - Make breaking changes without explicit approval
  - Delete data or files without confirmation
  - Commit directly to main branch
  - Add dependencies without discussion
  - Assume requirements without asking

## DATA HANDLING
- Reproducibility: Set random seeds where applicable
- Validate input before processing (nulls, ranges, types)
- Log data quality metrics
- Clear notebook outputs before committing

## ENVIRONMENT SETUP
- Always activate .venv before running any Python command
- Use python-dotenv for environment variable management
- Validate all required env vars at startup
- env.example committed to repo (placeholder values only)
- .env NEVER committed (listed in .gitignore)

## QUICK CHECKLIST
Starting New Work:
  1. `git pull origin main`
  2. `git checkout -b <type>/<description>`
  3. Activate virtual environment
  4. Update `docs/VERSIONS.md` with new branch
During Development:
  1. Commit incrementally with conventional commits
  2. Update documentation as you go
  3. Track scaffolding scripts
  4. Run tests frequently
  5. No emojis in code/commits
Before Merging:
  1. All tests pass
  2. Documentation updated
  3. Scaffolding scripts deleted or justified
  4. Code reviewed
  5. `docs/VERSIONS.md` updated
  6. Big picture plan reviewed
After Merging:
  1. Delete feature branch
  2. Update `docs/VERSIONS.md` (move to Archived)
