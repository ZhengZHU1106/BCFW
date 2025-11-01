# Repository Guidelines

## Project Structure & Module Organization
The monorepo splits by runtime: `backend/` holds the FastAPI API (`backend/main.py`), services (`backend/app/`), blockchain helpers (`backend/blockchain/`), and persistence assets (`backend/assets/`, `backend/database/`). `frontend/` contains the Vue 3 client (`src/` for views, components, axios clients, and utilities). Smart-contract sources and build artifacts live in `contracts/`, while orchestration scripts sit in `system.sh` and `scripts/`.

## Build, Test, and Development Commands
Launch the full stack with `./system.sh start`; use `./system.sh stop` for cleanup. For backend work, install deps via `pip install -r requirements.txt` and run `python3 -m uvicorn backend.main:app --reload --port 8000`. Frontend iterations rely on `npm install` then `npm run dev`; build production bundles with `npm run build`. Execute browser flows through Playwright using `npx playwright test` (start the dev server first or enable the commented `webServer` block).

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indentation; keep functions in `snake_case`, classes in `PascalCase`, and mirror existing patterns like `get_threat_model`. Format Python with `black backend`. Prefer explicit imports, dataclasses, and type hints when they clarify interfaces. Vue files use composition API with PascalCase SFC filenames and camelCase helpers; keep module-relative imports for readability.

## Testing Guidelines
Adopt `pytest` for backend suites placed under `backend/tests/` and named `test_<feature>.py`; leverage fixtures to spin up temporary SQLite files instead of reusing `security_platform.db`. For the frontend, extend Playwright coverage or add unit specs under `frontend/src/__tests__/` if Vitest joins the toolchain. Before sharing changes, run `pytest -q` and `npx playwright test`, and note any gaps or manual checks in the PR body.

## Commit & Pull Request Guidelines
Use the observed `type: summary` convention (`feat: 完成Phase 17 DevLeChain完整集成和功能增强`, `docs: 更新文档反映Phase 17 DevLeChain架构`). Optional scopes such as `feat(backend): ...` keep history searchable. Each PR should outline problem, approach, and verification; link issues, attach UI screenshots, and call out deployment or contract migration steps when relevant.

## Security & Configuration Tips
Keep DevLeChain paths consistent with `backend/config.py`; override locally via env vars instead of editing committed constants. Treat `backend/assets/model_package/` as read-only unless you regenerate the model and document provenance in `docs/`. Never commit keystore files, RPC credentials, or `.env` overrides—store them locally and ensure `.gitignore` remains intact.
