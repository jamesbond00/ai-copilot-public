# Repository Guidelines

## Project Structure & Module Organization
- `src/api/main.py`: FastAPI entrypoint serving dashboards and external agents.
- `src/data/`: fetchers and connectors; keep new data clients colocated here.
- `src/llm/`: prompt tooling, analyzers, and incident templates used across surfaces.
- `src/ui/`: Streamlit dashboard and future workspace-facing views.
- `tests/`: canonical unit and integration suites; retire legacy root-level `test_*.py` files when touched.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate`: set up an isolated interpreter.
- `pip install -r requirements.txt`: install runtime packages for the copilot services.
- `pip install -e ".[dev]"`: add Black, Pytest, and lint tooling for local development.
- `uvicorn src.api.main:app --reload`: run the API with hot reload.
- `streamlit run src/ui/dashboard.py`: launch the dashboard; pair with the API for end-to-end checks.

## Coding Style & Naming Conventions
- Target Python 3.11+, annotate public surfaces, and prefer dataclasses for structured payloads.
- Format with Black (`black .`); it enforces 88-character lines and normalized imports.
- Keep functions and modules in snake_case, classes in PascalCase, and constants in UPPER_CASE.
- Run `flake8` before review to catch unused imports and complexity spikes.

## Testing Guidelines
- Use Pytest; files follow `test_*.py`, classes `Test*`, and functions `test_*` per `pyproject.toml`.
- `pytest` runs the entire suite; scope to `pytest tests/test_dashboard_ui.py -k smoke` when iterating UI logic.
- Add fixtures or mocks in `tests/mock_api_server.py` when backend contracts shift.
- Expect green tests and comparable coverage with every pull request.

## Commit & Pull Request Guidelines
- Write imperative, one-line commit subjects (e.g., `Implement log fetcher module`); include detail in the body when needed.
- Group refactors and functional changes separately to simplify review.
- PRs must summarize intent, link issues or incidents, and attach screenshots/GIFs for UI updates.
- Confirm local `pytest` output and call out configuration changes or follow-up tasks in the description.

## Security & Configuration Tips
- Review `SECURITY.md` and `security-check.sh` before exposing new endpoints or dependencies.
- Never commit secrets; document new environment variables in `.env.example` instead.
- Use the `requirements-secure.txt` profile when validating hardened deployments.
