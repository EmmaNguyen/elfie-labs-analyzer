#!/bin/bash
# Run test_first_page.py with proper environment setup

cd /Users/emma/CascadeProjects/elfie-labs-analyzer

# Activate virtual environment
source backend/.venv/bin/activate

# Load environment variables from .env.local
if [ -f ".env.local" ]; then
    export $(grep -v '^#' .env.local | xargs)
    echo "✅ Loaded environment from .env.local"
else
    echo "❌ .env.local not found!"
    exit 1
fi

# Run the test
echo ""
python backend/test_first_page.py "$@"
