# Session End - Update Context Files

Please help me update the context preservation files before I switch to a different LLM. This ensures seamless handoff and no loss of progress.

## Tasks to Complete

### 1. Update Current State
**File**: `docs/context/CURRENT_STATE.md`

**What to update**:
- Change "Last Updated" date to today
- Update "System Status" if anything changed
- Update "Test Status" based on current test results
- In "Recent Major Fixes" section, add any significant work done this session
- Update "Next Development Priorities" if priorities changed

**Current session work summary**:
[DESCRIBE WHAT WAS ACCOMPLISHED THIS SESSION]

### 2. Log Recent Changes  
**File**: `docs/context/RECENT_CHANGES.md`

**Add new entry** for today's session using this format:
```markdown
### X. [Change Title] ✅
**Problem**: [What was the issue or need]
**Solution**: [How it was addressed]
**Files**: `file1.py`, `file2.py`
**Changes**:
- [Specific change 1]
- [Specific change 2]
**Impact**: [What this enables or fixes]
**Test Result**: [How to verify it works]
```

**Session changes to document**:
[LIST THE MAIN CHANGES MADE THIS SESSION]

### 3. Update Architecture Decisions (if applicable)
**File**: `docs/context/ARCHITECTURE_DECISIONS.md`

**Only if we made significant design decisions**, add new entry:
```markdown
### Decision: [Title]
**Date**: [Today's date]
**Context**: [Why this decision was needed]
**Decision**: [What was chosen]
**Reasoning**: [Key reasons]
**Implementation**: [How it was implemented]
**Trade-offs**: [What we gave up and gained]
```

**New decisions made** (if any):
[DESCRIBE ANY ARCHITECTURE DECISIONS]

### 4. Update Troubleshooting (if applicable)
**File**: `docs/context/TROUBLESHOOTING.md`

**Only if we encountered and solved new issues**, add to appropriate section:
- Common issues and solutions
- Environment-specific problems  
- Prevention checklist updates

**New issues/solutions** (if any):
[DESCRIBE ANY NEW PROBLEMS AND SOLUTIONS]

### 5. Generate Handoff Context
After updating the files, run:
```bash
docs/context/quick-context.sh
```

And provide me with:
- The generated "NEXT SESSION STARTER" template
- Current test status (✅ or ❌)
- Any warnings or issues I should know about

## Current Session Summary

**What I worked on**:
[FILL IN: Main tasks/features/fixes worked on]

**Current status**:
[FILL IN: What's working, what's broken, what's in progress]

**Files modified**:
[FILL IN: List of files that were changed]

**Test results**:
[FILL IN: Current state of test suite]

**Next priority**:
[FILL IN: What should be worked on next]

**Any blockers/issues**:
[FILL IN: Problems encountered or things to watch out for]

---

Please update the appropriate context files based on this session's work, then run the quick-context script to generate the handoff template for the next LLM.