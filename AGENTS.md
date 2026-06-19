# Soseki — AGENTS.md

## Project structure

- `ssk/` — the distributable library. This is where core work lives.
- `app/` — example/blanco app (NOT part of the sdist). Build step copies it into `ssk/blanco_app/`.
- `tests/unittests/` and `tests/integration/` — separate conftest.py files, identical fixtures.

## Key commands

| Action | Command |
|---|---|
| Run all tests | `pytest` |
| Run with coverage | `pytest --cov=ssk` |
| Run single test file | `pytest tests/unittests/test_forms.py` |
| Build package | `python -m build` |
| Check dist | `twine check dist/*` |
| Init new app | `soseki init [app_name]` (or `python -m ssk.cli init`) |

## Config gotchas

- **YAML format** uses typed values: `KEY:\n  type: value` (types: string, int, bool, float, json).
- Config is loaded from `app/cfg/{FLASK_ENV}.yaml` or `SSK_CONFIG` env var.
- `FLASK_ENV` sets the profile (e.g. `lite`, `tst`). Not `FLASK_APP`.
- `TIME_TRAVEL` config fakes `datetime.now()` across the app (datetime string `"%Y-%m-%d %H:%M:%S"`).
- Env vars (`SSK_CONFIG`, `FLASK_ENV`) override config file values.

## Testing quirks

- Both conftest files create a fresh DB per test function (`db_clean` → `db_create`). Tests are isolated but somewhat slow.
- Tests need a config YAML accessible at runtime (works via `FLASK_ENV` default or explicit path).
- `app/cfg/tst.yaml` is the test profile — it disables CSRF and mail sending.
- If a test needs a config override, set `FLASK_ENV` before `pytest`.

## Architecture notes

- **Two DBs**: main app DB (`SQLALCHEMY_DATABASE_URI`) + log DB (`LOG_DB_CONNSTR`) via SQLAlchemy binds.
- App startup: `init_ssk()` (registry, config, blueprints, error handlers) → `start_ssk()` (scheduler, API gate, settings).
- Blueprints are registered in `ssk/__init__.py` (home, api, cmd, admin).
- `app/` has its own `create_app()` factory that wraps `init_ssk`/`start_ssk`.
- `AppLogic` / `BusLogic` classes: apps subclass `BusLogic` and pass to `init_ssk(..., BusLogic, DbUpgrader, ...)`.
- **bcrypt 72-byte limit**: monkey-patched in `ssk/__init__.py`. Password truncation via `truncate_password()`.
- **Scheduler**: APScheduler `BackgroundScheduler` runs health/page-stats/db-stats jobs. Skips when `a_testing=True`.
- `SSK_MODEL_VERSION` in `ssk/ssk_consts.py` = 8. Bump it + add an upgrade function in `ssk_upgrader.py` when schema changes.

## Build / CI

- CI runs on PR, push to `develop`/`main`/`release` on 3.10/3.11/3.12.
- TestPyPI upload on `main` push. PyPI upload on `release` push.
- Build step (`setup.py:CustomBuildPy`) syncs `app/` → `ssk/blanco_app/`, `bin/` → `ssk/blanco_bin/`, `jup/` → `ssk/blanco_jup/`.
- These sync dirs are gitignored; they must be regenerated before `python -m build`.
