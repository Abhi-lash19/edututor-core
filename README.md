# Edututor

## Development Setup

1. `git clone <(https://github.com/Abhi-lash19/edututor-core.git)>`
2. `cd edututor`
3. `python -m venv .venv`
4. `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows)
5. `pip install -e ".[dev]"` (This installs the package in editable mode with dev dependencies)
6. `cp env.example .env`
7. Edit `.env` with your actual values.
8. `pre-commit install`

## Running the App

`python -m edututor.app`
