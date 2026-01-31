#!/bin/bash

# AI Copilot Security Check Script
# This script runs security checks on the project dependencies

echo "🔒 AI Copilot Security Check"
echo "=============================="

# Check if virtual environment exists
if [ ! -d "ai-copilot-secure" ]; then
    echo "❌ Secure virtual environment not found. Please run the security setup first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating secure virtual environment..."
source ai-copilot-secure/bin/activate

# Run safety check
echo "🔍 Running security vulnerability scan..."
safety check

# Check for outdated packages
echo ""
echo "📊 Checking for outdated packages..."
pip list --outdated

# Check for known security issues in requirements
echo ""
echo "🔍 Checking requirements files for known issues..."
if [ -f "requirements.txt" ]; then
    echo "Checking requirements.txt..."
    safety check -r requirements.txt
fi

if [ -f "requirements-test.txt" ]; then
    echo "Checking requirements-test.txt..."
    safety check -r requirements-test.txt
fi

echo ""
echo "✅ Security check completed!"
echo ""
echo "💡 Tips:"
echo "  - Run this script regularly: ./security-check.sh"
echo "  - Update packages when vulnerabilities are found"
echo "  - Use the secure virtual environment: source ai-copilot-secure/bin/activate"
echo "  - Check for updates: pip list --outdated"


