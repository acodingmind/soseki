# How to Perform Database Upgrades

Soseki doesn't use Alembic. Each schema change is a small Python function, and the pending ones run
automatically when the app starts.

## How it works

The `version` table in the main database holds two counters:

| Counter | Owned by | Required version comes from | Upgrade functions |
|---|---|---|---|
| `db_version` | your app | `DB_MODEL_VERSION` in your config YAML | `DbUpgrader` in `app/db_upgrader.py` |
| `ssk_version` | the Soseki framework | `SSK_MODEL_VERSION` in `ssk/ssk_consts.py` | `SSKUpgrader` in `ssk/ssk_upgrader.py` |

If you build an app on Soseki, you only touch the first row. The second is for framework maintainers.
The log database has no counter of its own; its tables are part of the framework track.

On every start, `start_ssk()` calls `db_version_check()` (`ssk/db.py`), which:

1. Creates both databases if they don't exist, creates all tables of the models imported so far, and seeds
   users and settings. A new database starts at version 0 on both counters.
2. Runs the framework upgrades, then your app's upgrades, each from the stored version up to the required one.
3. Writes a `START` row to the `audit` table.

Things to know about the runner:

- **Functions are picked by position.** `get_upgrade_functions()` returns a list, and the function at index
  `N - 1` upgrades to version `N`. Never reorder or remove entries.
- **The current version's function runs again** on every upgrade pass, so every function must check the stored
  version before changing anything.
- **Failures don't stop startup.** An exception is logged as `IMP DB Upgrade failed ...` (app) or
  `SSK DB Upgrade failed ...` (framework), and the app keeps starting. If a later function succeeds, its
  version is recorded and the failed one is never retried. Check the log after every upgrade.
- **A database that is ahead stops the app.** If a stored version is higher than the required one, Soseki
  writes a `NOK` `START` audit row and exits. Running older code against an upgraded database therefore
  doesn't work; see [Rolling back](#rolling-back).
- **A fresh database runs every upgrade function** from version 1, after the tables have been created.
  Write functions so they also work when their table or column already exists.

## For app developers

### Adding a table

1. Create the model in `app/models/`:

   ```python
   # app/models/task.py
   from ssk.db import func_db


   class Task(func_db.Model):
       __tablename__ = 'task'

       id = func_db.Column(func_db.Integer, primary_key=True)
       title = func_db.Column(func_db.String(200), nullable=False)
       done = func_db.Column(func_db.Boolean, default=False)
       user_id = func_db.Column(func_db.Integer, func_db.ForeignKey('user.id', ondelete='CASCADE'))
       created = func_db.Column(func_db.DateTime(timezone=True),
                                server_default=func_db.func.current_timestamp())
   ```

   Tables in the main database don't need a `__bind_key__`. For a table in the log database, add
   `__bind_key__ = 'logdb'`.

2. Add the upgrade function to `app/db_upgrader.py` and append it to the list:

   ```python
   from flask import current_app
   from ssk.db import get_db, get_version, set_version


   class DbUpgrader:
       @staticmethod
       def ver1():
           ...

       @staticmethod
       def ver2():
           my_version = 2
           current_app.logger.info("upgrading to {}".format(my_version))

           if get_version().db_version < my_version:
               from app.models.task import Task  # noqa: F401  registers the model
               get_db().create_all()             # creates missing tables only

               set_version(my_version)

       @staticmethod
       def get_upgrade_functions():
           return [DbUpgrader.ver1, DbUpgrader.ver2]
   ```

   `create_all()` only creates tables that don't exist yet, so this is safe on both new and existing databases.

3. Raise the required version in every config profile (`app/cfg/lite.yaml`, `app/cfg/tst.yaml` and production):

   ```yaml
     DB_MODEL_VERSION:
       int: 2
   ```

4. Restart the app. The log shows `IMP DB 1 < 2 Upgrading` followed by `upgrading to 2`.

### Adding a column

Add the column to the model, then alter the table in the next `verN`. Check first whether the column is there:
on a new database `create_all()` already creates it from the model.

```python
@staticmethod
def ver3():
    my_version = 3
    current_app.logger.info("upgrading to {}".format(my_version))

    if get_version().db_version < my_version:
        from sqlalchemy import inspect, text

        my_engine = get_db().engine
        my_columns = [my_col["name"] for my_col in inspect(my_engine).get_columns("task")]
        if "priority" not in my_columns:
            with my_engine.begin() as my_conn:
                my_conn.execute(text("ALTER TABLE task ADD COLUMN priority INTEGER DEFAULT 0"))

        set_version(my_version)
```

- Use `engine.begin()` and `text()`. `engine.execute()` was removed in SQLAlchemy 2.0.
- For a table in the log database, use `get_db().engines['logdb']` instead of `get_db().engine`.
- SQLite can't change or drop columns with `ALTER TABLE`; you have to create a new table, copy the data over
  and rename it.

### Migrating data

Use the ORM session inside the same guard, and commit before calling `set_version`:

```python
if get_version().db_version < my_version:
    from app.models.task import Task

    for my_task in Task.query.filter(Task.title.is_(None)).all():
        my_task.title = "untitled"
    get_db().session.commit()

    set_version(my_version)
```

## For framework maintainers

Framework tables live in `ssk/models/` and use the `ssk_version` counter:

1. Add or change the model in `ssk/models/`.
2. Import it in both `db_clean()` and `db_create()` in `ssk/db.py`, so new databases get it straight from
   `create_all()`.
3. Add `verN` to `SSKUpgrader` in `ssk/ssk_upgrader.py`, guarded by `get_version().ssk_version < N`, ending
   with `set_ssk_version(N)`. Append it to `get_upgrade_functions()`.
4. Add `N` to the skip list in `ver1` when the change is already covered by `db_create()` / `db_init()` on a
   new database. `ver1` only runs on a new database (version 0) and appends to `SSKUpgrader._to_skip` the
   versions that would otherwise repeat work, for example an `ALTER TABLE ADD COLUMN` on a column `create_all()`
   just created. Every `verN` checks `N not in SSKUpgrader._to_skip`.
5. Bump `SSK_MODEL_VERSION` in `ssk/ssk_consts.py`.

## Testing an upgrade

### Against a fresh database

```bash
export FLASK_ENV=lite
flask clean-db   # drops the tables
flask run        # the next start recreates the tables, seeds data and runs every upgrade
```

Any `flask` command starts the app, so the database is rebuilt as soon as you run one. Don't run
`flask setup-db` on a database the app has already set up: it seeds the users again and fails on the
duplicate usernames.

### Against an existing database

Back up the database, start the app, and check the log (`log/web.log` with the default `LOG_DIR`):

```
INFO in db: IMP DB 1 < 2 Upgrading
INFO in db: Upgrading IMP DB to 2
INFO in db_upgrader: upgrading to 2
```

Then search the log for `Upgrade failed`.

Relative SQLite paths are resolved against the Flask instance folder. For the blanco app that is `ins/`,
so `sqlite:///soseki_lite.sqlite` ends up at `ins/soseki_lite.sqlite`:

```bash
sqlite3 ins/soseki_lite.sqlite '.schema task'
sqlite3 ins/soseki_lite.sqlite 'select * from version order by id desc limit 1'
```

### Unit test

The `app` fixture in `tests/unittests/conftest.py` builds a fresh database. Call your function directly
and inspect the result:

```python
from sqlalchemy import inspect
from ssk.db import get_db


def test_ver3_adds_priority(app):
    with app.app_context():
        from app.db_upgrader import DbUpgrader
        DbUpgrader.ver2()
        DbUpgrader.ver3()

        my_columns = [c["name"] for c in inspect(get_db().engine).get_columns("task")]
        assert "priority" in my_columns
```

## Troubleshooting

**The upgrade didn't run.**
- Check that `DB_MODEL_VERSION` was raised in the profile the app actually loads (`FLASK_ENV`, or `SSK_CONFIG`).
- Check that the function was appended to `get_upgrade_functions()` at the right position (index `N - 1`).
- Search the log for `Upgrade failed`.
- Check the stored versions: `select * from version order by id desc limit 1`.

**The app exits right after starting.**
The stored version is higher than the code's required version. Look for `DB Version is ahead of Required
Version` in the log and a `NOK` row in the `audit` table.

**`duplicate column name` or `table already exists`.**
The function doesn't check whether its change is already there. Add the check described in
[Adding a column](#adding-a-column).

## Deploying

1. Back up both databases.
2. Deploy the code and the config with the raised `DB_MODEL_VERSION`.
3. Restart the app. Upgrades run during startup.
4. Check the log for `Upgrade failed` and the `version` table for the new number.

### Rolling back

Because the app refuses to run against a database that's ahead of it, rolling back the code means rolling
back the database too:

1. Stop the app.
2. Restore the database backup taken before the upgrade.
3. Deploy the previous code and config.
4. Start the app.
