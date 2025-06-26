#!/bin/bash
# Quick context for immediate session handoffs
# Run from project root or docs/context directory

# Detect if we're in the context directory and adjust paths
if [[ $(basename "$PWD") == "context" ]]; then
    PROJECT_ROOT="../.."
    cd "$PROJECT_ROOT"
fi

echo "=== QUICK CONTEXT - Resume Automation System ==="
echo "Working from: $(pwd)"
echo ""

# Current status
echo "📊 CURRENT STATUS:"
if [ -f "docs/context/CURRENT_STATE.md" ]; then
    echo "$(head -10 docs/context/CURRENT_STATE.md | grep -E "(Last Updated|System Status|Test Status)")"
else
    echo "❌ docs/context/CURRENT_STATE.md not found"
fi
echo ""

# Quick test
echo "🧪 QUICK HEALTH CHECK:"
if python test-scripts/test_resume_generation.py 2>&1 | grep -q "All tests passed"; then
    echo "✅ Main tests: PASSING"
else
    echo "❌ Main tests: FAILING - run full test for details"
fi

# Git status
echo ""
echo "📝 GIT STATUS:"
echo "Branch: $(git branch --show-current)"
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working directory: CLEAN"
else
    echo "⚠️  Working directory: HAS CHANGES"
    git status --porcelain | head -5
fi

# Last changes
echo ""
echo "🔄 RECENT ACTIVITY:"
git log --oneline -3

# Environment
echo ""
echo "🔧 ENVIRONMENT:"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API key configured"
else
    echo "❌ OpenAI API key missing"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ Anthropic API key configured"
else
    echo "❌ Anthropic API key missing"
fi

# Services
echo ""
echo "⚙️  SERVICES:"
if docker-compose ps 2>/dev/null | grep -q "Up"; then
    echo "✅ Docker services running"
else
    echo "⚠️  Docker services not running"
fi

echo ""
echo "=== NEXT SESSION STARTER ==="
echo "Copy this for context transfer:"
echo ""
echo "---"
echo "Hi! Continuing work on resume automation system."
echo ""
echo "**Current Status**: $(if [ -f "docs/context/CURRENT_STATE.md" ]; then grep -m1 "System Status" docs/context/CURRENT_STATE.md | cut -d':' -f2; else echo "Unknown - check docs/context/CURRENT_STATE.md"; fi)"
echo "**Last Working**: [UPDATE WITH CURRENT TASK]"
echo "**All Tests**: $(if python test-scripts/test_resume_generation.py 2>&1 | grep -q "All tests passed"; then echo "✅ 4/4 passing"; else echo "❌ Some failing"; fi)"
echo "**Git Status**: $(if [ -z "$(git status --porcelain)" ]; then echo "Clean"; else echo "Has changes"; fi)"
echo "**Next Step**: [UPDATE WITH NEXT PRIORITY]"
echo ""
echo "Please run: \`python test-scripts/test_resume_generation.py\` to verify state."
echo "---"
echo ""
echo "🚀 START COMMANDS:"
echo "python test-scripts/test_resume_generation.py    # Verify health"
echo "cat docs/context/CURRENT_STATE.md                # Check status"
echo "git status                                        # See changes"