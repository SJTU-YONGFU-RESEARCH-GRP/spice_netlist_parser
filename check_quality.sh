#!/bin/bash

# SPICE Netlist Parser - Quality Check Script
# This script runs all quality checks before committing

echo "🔍 Running Quality Checks for SPICE Netlist Parser"
echo "===================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counter for failed checks
FAILED_CHECKS=0

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" -eq 0 ]; then
        echo -e "${GREEN}✅ $message${NC}"
    else
        echo -e "${RED}❌ $message${NC}"
        FAILED_CHECKS=$((FAILED_CHECKS + 1))
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo -e "\n${BLUE}1. Running pre-commit hooks...${NC}"
if command_exists pre-commit; then
    if pre-commit run --all-files; then
        print_status 0 "Pre-commit hooks passed"
    else
        print_status 1 "Pre-commit hooks failed"
        echo -e "${YELLOW}💡 Install pre-commit: pip install pre-commit${NC}"
        echo -e "${YELLOW}💡 Or run: pre-commit install${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  pre-commit not found. Install with: pip install pre-commit${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo -e "\n${BLUE}2. Running Ruff linting checks...${NC}"
if command_exists ruff; then
    if [ -d "tests" ] && [ "$(ls -A tests 2>/dev/null)" ]; then
        if ruff check src/ tests/; then
            print_status 0 "Ruff linting passed"
        else
            print_status 1 "Ruff linting failed"
            echo -e "${YELLOW}💡 Fix with: ruff check --fix src/ tests/${NC}"
        fi
    else
        if ruff check src/; then
            print_status 0 "Ruff linting passed"
        else
            print_status 1 "Ruff linting failed"
            echo -e "${YELLOW}💡 Fix with: ruff check --fix src/${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  ruff not found. Install with: pip install ruff${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo -e "\n${BLUE}3. Checking Ruff formatting...${NC}"
if command_exists ruff; then
    if [ -d "tests" ] && [ "$(ls -A tests 2>/dev/null)" ]; then
        if ruff format --check src/ tests/; then
            print_status 0 "Ruff formatting check passed"
        else
            echo -e "${YELLOW}⚠️  Ruff formatting issues found. Run 'ruff format src/ tests/' to fix.${NC}"
            print_status 1 "Ruff formatting check failed"
        fi
    else
        if ruff format --check src/; then
            print_status 0 "Ruff formatting check passed"
        else
            echo -e "${YELLOW}⚠️  Ruff formatting issues found. Run 'ruff format src/' to fix.${NC}"
            print_status 1 "Ruff formatting check failed"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  ruff not found (already noted above)${NC}"
fi

echo -e "\n${BLUE}4. Running type checking with MyPy...${NC}"
if python3 -m mypy --version >/dev/null 2>&1 || python -m mypy --version >/dev/null 2>&1; then
    if python3 -m mypy src/ --ignore-missing-imports 2>/dev/null || python -m mypy src/ --ignore-missing-imports; then
        print_status 0 "MyPy type checking passed"
    else
        print_status 1 "MyPy type checking failed"
    fi
else
    echo -e "${YELLOW}⚠️  mypy not found. Install with: pip install mypy${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo -e "\n${BLUE}5. Running security checks with Bandit...${NC}"
if python3 -m bandit --version >/dev/null 2>&1 || python -m bandit --version >/dev/null 2>&1; then
    # Use config file if it exists, otherwise run without it
    if [ -f "pyproject.toml" ]; then
        if python3 -m bandit -r src/ -c pyproject.toml --exit-zero 2>/dev/null || python -m bandit -r src/ -c pyproject.toml --exit-zero; then
            print_status 0 "Bandit security check completed"
        else
            print_status 1 "Bandit security check failed"
        fi
    else
        if python3 -m bandit -r src/ --exit-zero 2>/dev/null || python -m bandit -r src/ --exit-zero; then
            print_status 0 "Bandit security check completed"
        else
            print_status 1 "Bandit security check failed"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  bandit not found. Install with: pip install bandit[toml]${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo -e "\n${BLUE}6. Running tests with coverage...${NC}"
if python3 -m pytest --version >/dev/null 2>&1 || python -m pytest --version >/dev/null 2>&1; then
    # Check if tests directory exists
    if [ -d "tests" ] && [ "$(ls -A tests 2>/dev/null)" ]; then
        if python3 -m pytest --cov=spice_netlist_parser --cov-report=term-missing -q 2>/dev/null || python -m pytest --cov=spice_netlist_parser --cov-report=term-missing -q; then
            print_status 0 "Tests passed with coverage"
        else
            print_status 1 "Tests failed"
            echo -e "${YELLOW}💡 Run tests with: python3 -m pytest -v (or python -m pytest -v)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No tests directory found. Skipping test execution.${NC}"
        echo -e "${YELLOW}💡 Create tests in ./tests/ directory${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  pytest not found. Install with: pip install pytest pytest-cov${NC}"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
fi

echo ""
if [ $FAILED_CHECKS -eq 0 ]; then
    echo -e "${GREEN}🎉 All quality checks passed! Your code is ready for commit.${NC}"
    echo -e "${BLUE}💡 Tip: Run 'git add .' and 'git commit' when ready.${NC}"
else
    echo -e "${RED}❌ $FAILED_CHECKS check(s) failed. Please fix the issues above before committing.${NC}"
    echo -e "${BLUE}💡 Tip: Install missing tools with: pip install -e \".[dev]\"${NC}"
    exit 1
fi
