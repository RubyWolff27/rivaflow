#!/bin/bash
set -e
echo "Setting up RivaFlow development environment..."

# Python venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r rivaflow/requirements.txt
pip install pytest black ruff

# Frontend
cd web && npm install && cd ..

# Database
python -c "from rivaflow.db.database import init_db; init_db()"

echo "Setup complete! Run: source .venv/bin/activate"
