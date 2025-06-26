#!/bin/bash
# Generate context summary for session handoff
# Run from project root or docs/context directory

# Detect if we're in the context directory and adjust paths
if [[ $(basename "$PWD") == "context" ]]; then
    PROJECT_ROOT="../.."
    cd "$PROJECT_ROOT"
fi

echo "=== Resume Automation System - Context Report ==="
echo "Generated: $(date)"
echo "Working from: $(pwd)"
echo ""

# System status
echo "=== SYSTEM STATUS ==="
if command -v python &> /dev/null; then
    echo "Python: $(python --version)"
else
    echo "Python: Not found"
fi

if command -v poetry &> /dev/null; then
    echo "Poetry: $(poetry --version)"
else
    echo "Poetry: Not found"
fi

if command -v docker &> /dev/null; then
    echo "Docker: $(docker --version)"
else
    echo "Docker: Not found"
fi

if command -v pdflatex &> /dev/null; then
    echo "pdflatex: $(pdflatex --version | head -1)"
else
    echo "pdflatex: Not installed"
fi

echo ""

# Git status
echo "=== GIT STATUS ==="
echo "Branch: $(git branch --show-current)"
echo "Last 5 commits:"
git log --oneline -5
echo ""
echo "Working directory status:"
git status --porcelain
if [ $? -eq 0 ] && [ -z "$(git status --porcelain)" ]; then
    echo "✅ Working directory clean"
else
    echo "⚠️  Uncommitted changes present"
fi
echo ""

# Service status
echo "=== SERVICES STATUS ==="
if command -v docker-compose &> /dev/null; then
    echo "Docker services:"
    docker-compose ps 2>/dev/null || echo "Docker compose not running or not available"
else
    echo "docker-compose not available"
fi
echo ""

# Environment check (without secrets)
echo "=== ENVIRONMENT CHECK ==="
echo "Current directory: $(pwd)"
echo "Environment variables (masked):"
env | grep -E "(DATABASE|REDIS|API_KEY|LLM)" | sed 's/=.*/=***/' | sort
echo ""

# Test results
echo "=== TEST RESULTS ==="
echo "Running main test suite..."
if python test-scripts/test_resume_generation.py > /tmp/test_output.txt 2>&1; then
    echo "✅ Main tests: PASSED"
    # Extract summary
    grep -E "(Results|tests passed)" /tmp/test_output.txt | tail -2
else
    echo "❌ Main tests: FAILED"
    echo "Error output:"
    tail -10 /tmp/test_output.txt
fi
echo ""

echo "Running API endpoint tests..."
if python test-scripts/test_all_endpoints.py > /tmp/api_test_output.txt 2>&1; then
    echo "✅ API tests: PASSED"
else
    echo "❌ API tests: FAILED"
    echo "Error output:"
    tail -5 /tmp/api_test_output.txt
fi
echo ""

echo "Running LaTeX escaping tests..."
if python test-scripts/test_latex_escaping.py > /tmp/latex_test_output.txt 2>&1; then
    echo "✅ LaTeX tests: PASSED"
else
    echo "❌ LaTeX tests: FAILED"
    echo "Error output:"
    tail -5 /tmp/latex_test_output.txt
fi
echo ""

# File structure
echo "=== KEY FILES STATUS ==="
echo "Documentation files:"
for file in CLAUDE.md docs/context/CURRENT_STATE.md docs/context/RECENT_CHANGES.md docs/context/ARCHITECTURE_DECISIONS.md docs/context/TROUBLESHOOTING.md; do
    if [ -f "$file" ]; then
        echo "✅ $file ($(wc -l < $file) lines)"
    else
        echo "❌ $file missing"
    fi
done
echo ""

echo "Test scripts:"
for file in test-scripts/test_resume_generation.py test-scripts/test_all_endpoints.py test-scripts/test_latex_escaping.py; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file missing"
    fi
done
echo ""

echo "Core source files:"
for file in src/api/main.py src/generator/resume_generator.py src/generator/llm_interface.py; do
    if [ -f "$file" ]; then
        echo "✅ $file ($(wc -l < $file) lines)"
    else
        echo "❌ $file missing"
    fi
done
echo ""

# Output files
echo "=== OUTPUT FILES ==="
if [ -d "resume_outputs" ]; then
    echo "Resume outputs directory:"
    ls -la resume_outputs/ | head -10
    file_count=$(ls -1 resume_outputs/ | wc -l)
    echo "Total files: $file_count"
else
    echo "❌ resume_outputs directory missing"
fi
echo ""

# System health summary
echo "=== HEALTH SUMMARY ==="
health_score=0
total_checks=8

# Check git status
if [ -z "$(git status --porcelain)" ]; then
    health_score=$((health_score + 1))
    echo "✅ Git working directory clean"
else
    echo "⚠️  Git has uncommitted changes"
fi

# Check test files exist
if [ -f "test-scripts/test_resume_generation.py" ]; then
    health_score=$((health_score + 1))
    echo "✅ Test scripts present"
else
    echo "❌ Test scripts missing"
fi

# Check documentation
if [ -f "CLAUDE.md" ] && [ -f "docs/context/CURRENT_STATE.md" ]; then
    health_score=$((health_score + 1))
    echo "✅ Documentation present"
else
    echo "❌ Documentation incomplete"
fi

# Check source files
if [ -f "src/api/main.py" ] && [ -f "src/generator/resume_generator.py" ]; then
    health_score=$((health_score + 1))
    echo "✅ Core source files present"
else
    echo "❌ Core source files missing"
fi

# Check Python environment
if command -v python &> /dev/null && command -v poetry &> /dev/null; then
    health_score=$((health_score + 1))
    echo "✅ Python environment ready"
else
    echo "❌ Python environment issues"
fi

# Check output directory
if [ -d "resume_outputs" ]; then
    health_score=$((health_score + 1))
    echo "✅ Output directory exists"
else
    echo "❌ Output directory missing"
fi

# Check if tests pass (simplified check)
if [ -f "/tmp/test_output.txt" ] && grep -q "tests passed" /tmp/test_output.txt; then
    health_score=$((health_score + 1))
    echo "✅ Main tests passing"
else
    echo "❌ Main tests failing"
fi

# Check pdflatex
if command -v pdflatex &> /dev/null; then
    health_score=$((health_score + 1))
    echo "✅ PDF generation available"
else
    echo "❌ pdflatex not installed"
fi

echo ""
echo "System Health: $health_score/$total_checks checks passed"
if [ $health_score -ge 6 ]; then
    echo "🎉 System appears healthy"
elif [ $health_score -ge 4 ]; then
    echo "⚠️  System has some issues but may be functional"
else
    echo "❌ System has significant issues"
fi

echo ""
echo "=== QUICK COMMANDS FOR NEXT SESSION ==="
echo "# Verify system health:"
echo "python test-scripts/test_resume_generation.py"
echo ""
echo "# Check current status:"
echo "cat docs/context/CURRENT_STATE.md"
echo ""
echo "# See recent changes:"
echo "cat docs/context/RECENT_CHANGES.md"
echo ""
echo "# Start API server:"
echo "poetry run uvicorn src.api.main:app --reload"
echo ""
echo "=== END CONTEXT REPORT ==="

# Cleanup temp files
rm -f /tmp/test_output.txt /tmp/api_test_output.txt /tmp/latex_test_output.txt