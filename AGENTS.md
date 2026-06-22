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
| Build package | `python -m build` |
| Check dist | `twine check dist/*` |
| Init new app | `soseki init [app_name]` (or `python -m ssk.cli init`) |

No Makefile, pre-commit, or CI workflow files exist.

## Config gotchas

- **YAML format** uses typed values: `KEY:\n  type: value` (types: string, int, bool, float, json).
- Config loaded from `app/cfg/{FLASK_ENV}.yaml` or `SSK_CONFIG` env var.
- `FLASK_ENV` sets the profile (e.g. `lite`, `tst`). Not `FLASK_APP`.
- `TIME_TRAVEL` config fakes `datetime.now()` across the app (datetime string `"%Y-%m-%d %H:%M:%S"`).
- Env vars (`SSK_CONFIG`, `FLASK_ENV`) override config file values.

## Testing quirks

- Both conftest files create a fresh DB per test (`db_clean` → `db_create`). Tests are isolated but somewhat slow.
- Tests need a config YAML accessible at runtime (works via `FLASK_ENV` default or explicit path).
- `app/cfg/tst.yaml` is the test profile — disables CSRF and mail sending.
- If a test needs a config override, set `FLASK_ENV` before `pytest`.

## Architecture notes

- **Two DBs**: main app DB (`SQLALCHEMY_DATABASE_URI`) + log DB (`LOG_DB_CONNSTR`) via SQLAlchemy binds.
- App startup: `init_ssk()` (registry, config, blueprints, error handlers) → `start_ssk()` (scheduler, API gate, settings).
- Blueprints registered in `ssk/__init__.py`: home, api, cmd, admin.
- `app/` has its own `create_app()` factory wrapping `init_ssk`/`start_ssk`. It creates symlinks: `app/templates` → `ssk/templates`, `app/static` → `ssk/static`. Local overrides come from `app/html/local/` and `app/assets/local/`.
- Apps subclass `BusLogic` (from `ssk.logic.bus_logic`) and pass to `init_ssk(..., BusLogic, DbUpgrader, ...)`.
- **bcrypt 72-byte limit**: monkey-patched in `ssk/__init__.py`. Password truncation via `truncate_password()`.
- **Scheduler**: APScheduler `BackgroundScheduler` runs health/page-stats/db-stats jobs. Skips when `a_testing=True`.
- `SSK_MODEL_VERSION` in `ssk/ssk_consts.py` = 8. Bump it + add upgrade function in `ssk/ssk_upgrader.py` when schema changes.

## Build

- Build step (`setup.py` custom commands) syncs `app/` → `ssk/blanco_app/` (excluding `templates/` and `static/`), `bin/` → `ssk/blanco_bin/`, `jup/` → `ssk/blanco_jup/`.
- These sync dirs are gitignored; regenerate before `python -m build`.
- `publish.sh` handles cleanup, build, twine check, and upload (PyPI or TestPyPI with `--test`).
