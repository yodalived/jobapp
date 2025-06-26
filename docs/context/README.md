# Context Preservation System

This directory contains all files needed for seamless handoffs between different LLM sessions.

## Quick Start for New Sessions

### 1. For Immediate Context
```bash
# Run from project root
docs/context/quick-context.sh
```

### 2. Copy Initial Prompt
```bash
cat docs/context/NEXT_LLM_PROMPT.md
```
Copy the entire content as your first message to a new LLM.

### 3. Verify System Health
```bash
python test-scripts/test_resume_generation.py
```
Should show "🎉 All tests passed!"

## Files in This Directory

### 📋 Documentation
- **`CURRENT_STATE.md`** - Real-time system status and functionality
- **`RECENT_CHANGES.md`** - Last 10 changes with context and reasoning  
- **`ARCHITECTURE_DECISIONS.md`** - Key design choices and rationale
- **`TROUBLESHOOTING.md`** - Common issues and solutions
- **`SESSION_HANDOFF_TEMPLATE.md`** - Template for detailed handoffs

### 🚀 Quick Start
- **`NEXT_LLM_PROMPT.md`** - Ready-to-use initial prompt for new LLM sessions
- **`SESSION_END_PROMPT.md`** - Detailed template for ending sessions
- **`QUICK_SESSION_END.md`** - Fast template for session handoffs
- **`README.md`** - This file

### 🔧 Helper Scripts  
- **`quick-context.sh`** - Fast context generation (30 seconds)
- **`generate-context.sh`** - Comprehensive system report (2 minutes)

## Usage Patterns

### Starting New LLM Session
1. Copy content from `NEXT_LLM_PROMPT.md` 
2. Paste as first message to new LLM
3. Run health check when prompted
4. Continue development

### Ending Current Session
**Option 1: Quick Update**
1. Copy content from `QUICK_SESSION_END.md`
2. Fill in the session summary
3. Give to current LLM to update context files
4. Get handoff template from LLM
5. Commit working state

**Option 2: Detailed Update**  
1. Copy content from `SESSION_END_PROMPT.md`
2. Fill in detailed session information
3. Give to current LLM to update all context files
4. Get comprehensive handoff template
5. Commit working state

### Troubleshooting
1. Check `TROUBLESHOOTING.md` for known issues
2. Run `docs/context/generate-context.sh` for detailed system report
3. Verify tests with `python test-scripts/test_resume_generation.py`

## Key Information

**System Status**: ✅ Fully functional resume automation system  
**Test Status**: 4/4 tests passing (Basic Gen, AI Custom, PDF compilation, API endpoints)  
**Tech Stack**: FastAPI + PostgreSQL + LaTeX + OpenAI/Anthropic + Redis  

**Next Priorities**: Frontend development, LinkedIn scraper, additional LLM providers

---

**Quick Command**: `docs/context/quick-context.sh` for immediate context recovery