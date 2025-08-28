## End-of-Session Checklist

Complete these updates in order before ending session:

### 1. Version & Code Quality ✅
- [ ] Update version number in `src\version.py` (if not done)
- [ ] Run Ruff syntax check: `ruff check . --fix`
- [ ] Verify git commits are complete
- [ ] Check test status (if tests were modified/run)

### 2. Documentation Updates

#### DEVELOPMENT_HISTORY.md ✅
- [ ] Add new version entry with technical details
- [ ] Document problem solved, root cause, solution
- [ ] Include development process insights
- [ ] Note any agent usage or special techniques

#### todo.md
- [ ] Mark completed tasks as ✅
- [ ] Add any new issues discovered during session
- [ ] Update priority status for remaining tasks
- [ ] Remove obsolete items
- [ ] Move completed items to docs\DEVELOPMENT_HISTORY.md

#### CLAUDE.md
- [ ] Update "Current Status" section with latest version
- [ ] Add any new working principles learned
- [ ] Document new technical solutions or patterns
- [ ] Update testing notes if applicable
- [ ] Move older content to DEVELOPMENT_HISTORY.md to keep claude.md from growing

#### docs\codebase_analysis.md
- [ ] Update architecture changes
- [ ] Note new technical insights
- [ ] Document structural modifications

### 3. Session Summary
- [ ] Ensure all major changes are documented
- [ ] Verify development history is complete
- [ ] Confirm next steps are clear in todo.md