# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Soseki is a Flask framework for internal tools and admin panels. The `ssk/` package is published to PyPI as `soseki` (version in `SSK_VER`, `ssk/ssk_consts.py`, parsed by `setup.py`). `app/` is the "blanco" template app that `soseki init` / `python3 -m ssk.cli init` scaffolds into new projects. Supported Python: 3.10–3.12.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .

# Tests (run from repo root — config is found via the relative path app/cfg/tst.yaml)
pytest
pytest --cov=ssk --cov-report=term-missing
pytest tests/unittests/test_cmd_user.py
pytest tests/unittests/test_cmd_user.py::test_name

# Run the blanco app (bin/run_app.sh activates ./venv, not ./.venv, and sets FLASK_ENV=lite)
FLASK_ENV=lite flask run

# Flask CLI commands registered by init_ssk
flask clean-db | flask create-db | flask setup-db

# Build package
python -m build && twine check dist/*
```

No linter is configured. CI (`.github/workflows/tests.yml`) runs pytest on 3.10/3.11/3.12 for PRs and pushes to `develop`/`main`/`release`; `main` publishes to TestPyPI, `release` to PyPI; `develop` also gets a Semgrep scan. PRs target `develop`.

## Architecture

### Framework lifecycle (`ssk/__init__.py`)
- `init_ssk(app, bus_logic_cls, db_upgrader_cls, testing)` loads YAML config, sets up logging, the two DBs, Flask-User auth, error handlers, CLI commands, and registers the `home` (`/ssk`), `api`, `cmd`, `admin` blueprints.
- `start_ssk(app, testing)` boots runtime services: `CmdProcessor` worker threads, `ApiGate`, app settings, and APScheduler jobs (health check, page stats, DB stats, DB cleanup).
- The host app passes in its own business-logic class and DB upgrader. `ssk.lg.get_logic()` returns a per-request instance of `current_app.bus_logic` (stored on `g`). The logic class provides `get_job_mgr()` and `get_root_cmd()`, which is how an app plugs its own commands into the framework.

### Configuration
- Config file comes from `SSK_CONFIG`, else `app/cfg/{profile}.yaml` or `cfg/{profile}.yaml`, where profile = `FLASK_ENV` (forced to `tst` when `testing=True`).
- YAML values under the top-level `ssk:` key are typed: each key maps to `{string|bool|int|json: value}`, converted by `set_const` in `ssk/utils.py`. New config keys must follow this shape.
- Two databases: main SQLAlchemy DB plus a log DB bound as `logdb` (`LOG_DB_CONNSTR` → `SQLALCHEMY_BINDS`).

### Request handling
Blueprints in `ssk/blueprints/*.py` are thin route modules that delegate to a matching `*_handler.py` class. Most pages check `WebGate.is_closed()` first; API access goes through `ApiGate` (API keys / rate limiting). Process-wide singletons live in `ssk/globals/` (cmd processor, job manager, api/web gates, settings, email, contacts).

### Command tree and jobs
- The in-browser terminal (`cmd` blueprint) executes a tree of commands built from `ssk/logic/cmd/abstract_cmd.py`: each command registers sub-commands with `reg_cmd([aliases], instance)`, enforces access in `has_access()`, and implements `action()`/`help()`. `RootCmd` dispatches and writes an `Audit` row for every executed command.
- Long-running work is a `BaseJob` subclass (`ssk/logic/jobs/`), queued via `CmdProcessor.submit_cmd()` and tracked by `JobMgr`. App-specific commands/jobs go in `app/logic/cmd/` and `app/logic/jobs/`.

### DB versioning
No Alembic. Schema upgrades are ordered static methods returned by `get_upgrade_functions()`: framework upgrades in `ssk/ssk_upgrader.py`, app upgrades in the app's `DbUpgrader` (`app/db_upgrader.py`). Each step checks `get_version()` and calls `set_version(n)`. See `docs/how-to-database-upgrade.md`.

### Auth
Flask-User with bcrypt. `ssk/__init__.py` monkey-patches bcrypt/passlib at import time to handle the 72-byte password limit — keep that patch ahead of any passlib/Flask-User initialization.

### Blanco app and build
- `app/__init__.py:create_app()` symlinks `app/templates` → `ssk/templates` and `app/static` → `ssk/static`, and copies `app/html/local` and `app/assets/local` into them. App-specific templates/assets belong in `app/html/local` and `app/assets/local`.
- `setup.py` custom `build_py`/`sdist` copy `app/` → `ssk/blanco_app/`, `bin/` → `ssk/blanco_bin/`, `jup/` → `ssk/blanco_jup/`. Those generated dirs are gitignored — edit the sources, never the copies.

## Testing notes
- `tests/unittests/conftest.py` and `tests/integration/conftest.py` are identical: they build the app with `init_ssk(Flask(...), BusLogic, DbUpgrader, True)`, run `db_clean()`/`db_create()`, then `start_ssk`, and clean the DB on teardown. Tests run against SQLite files defined in `app/cfg/tst.yaml`.
- No `pytest.ini`/`pyproject.toml`; pytest uses defaults.
