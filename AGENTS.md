# Soseki — AGENTS.md

## Project structure

- `ssk/` — the distributable library. Core work lives here.
- `app/` — example/blanco app (not in sdist). Build step copies it into `ssk/blanco_app/`.
- `tests/unittests/` and `tests/integration/` — separate identical `conftest.py` files.

## Key commands

| Action | Command |
|---|---|
| Run all tests | `pytest` |
| Run with coverage | `pytest --cov=ssk` |
| Run single test file | `pytest tests/unittests/test_forms.py` |
| Run single test | `pytest tests/unittests/test_forms.py::test_name` |
| Build package | `python -m build` |
| Check dist | `twine check dist/*` |
| Init new app | `soseki init [app_name]` (or `python -m ssk.cli init`) |

No Makefile or pre-commit. CI (`.github/workflows/tests.yml`) runs pytest on Python 3.10/3.11/3.12 for PRs and pushes to `develop`/`main`/`release`; `semgrep.yml` scans `develop`. PRs target `develop`.

## Config gotchas

- **YAML format** uses typed values: `KEY:\n  type: value` (types: string, int, bool, float, json).
- Config loaded from `app/cfg/{FLASK_ENV}.yaml` or `SSK_CONFIG` env var.
- `FLASK_ENV` sets the profile (e.g. `lite`, `tst`). Not `FLASK_APP`.
- `TIME_TRAVEL` config fakes `datetime.now()` across the app (datetime string `"%Y-%m-%d %H:%M:%S"`).
- Any env var named like a config key (e.g. `SECRET_KEY`) overrides that key's file value (`set_const` in `ssk/utils.py`).
- `API_ACTIVE_NOW`, `SCHED_ON` and the seeded users are copied into the DB when it's created; after that the DB value wins.

## Testing quirks

- Both conftest files create a fresh DB per test (`db_clean` → `db_create`). Tests are isolated but somewhat slow.
- Run pytest from the repo root: testing mode forces the `tst` profile and loads `app/cfg/tst.yaml` by relative path.
- `app/cfg/tst.yaml` is the test profile — disables CSRF and mail sending.
- If a test needs a config override, set `FLASK_ENV` before `pytest`.

## Architecture notes

- **Two DBs**: main app DB (`SQLALCHEMY_DATABASE_URI`) + log DB (`LOG_DB_CONNSTR`) via SQLAlchemy binds.
- App startup: `init_ssk()` (registry, config, blueprints, error handlers) → `start_ssk()` (scheduler, API gate, settings).
- Blueprints registered in `ssk/__init__.py`: home, api, cmd, admin.
- `app/` has its own `create_app()` factory wrapping `init_ssk`/`start_ssk`. It creates symlinks: `app/templates` → `ssk/templates`, `app/static` → `ssk/static`. Local overrides come from `app/html/local/` and `app/assets/local/`.
- Apps subclass `BusLogic` (from `ssk.logic.bus_logic`) and pass to `init_ssk(..., BusLogic, DbUpgrader, ...)`.
- **Auth** lives in `ssk/auth/` (Flask-Login + bcrypt + itsdangerous; replaced Flask-User and passlib). It keeps Flask-User's USER_* settings, `/user/...` URLs, `user.*` endpoints and `ssk/templates/flask_user/` templates. Protect views with `ssk.auth.roles_required` / `login_required`.
- **Scheduler**: APScheduler `BackgroundScheduler` runs health/page-stats/db-stats jobs hourly and `DB_CLEANUP` jobs every 6 hours; jobs only do work while the `SCHED_ON` setting is on. The command worker threads are not started when `a_testing=True`.
- `SSK_MODEL_VERSION` in `ssk/ssk_consts.py` = 8. Bump it + add upgrade function in `ssk/ssk_upgrader.py` when schema changes.

## Build

- Build step (`setup.py` custom commands) syncs `app/` → `ssk/blanco_app/` (excluding `templates/` and `static/`), `bin/` → `ssk/blanco_bin/`, `jup/` → `ssk/blanco_jup/`.
- These sync dirs are gitignored; regenerate before `python -m build`.
- Publishing is done by CI: pushes to `main` upload to TestPyPI, pushes to `release` upload to PyPI.
