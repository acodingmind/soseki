# Quickstart

## 1. Create a project

```bash
mkdir myproject && cd myproject

# bin/run_app.sh expects the virtual environment in ./venv
python3 -m venv venv
source venv/bin/activate
pip install soseki

# create the app from the blanco template
soseki init            # or: python3 -m ssk.cli init
```

`soseki init [app_name]` creates the app folder (default name `app`) and, next to it, `bin/` and `jup/`.
It refuses to run if the app folder already exists.

```
myproject/
├── app/
│   ├── assets/local/      # Static assets (CSS, JS, images)
│   ├── blueprints/        # App blueprints (home at "/", api at "/lapi")
│   ├── cfg/               # Configuration profiles (lite.yaml, tst.yaml)
│   ├── html/local/        # HTML templates
│   ├── logic/
│   │   ├── app_logic.py   # Business logic class passed to init_ssk
│   │   ├── cmd/           # Custom terminal commands
│   │   └── jobs/          # Background jobs
│   ├── models/            # Database models
│   ├── db_upgrader.py     # App database upgrades
│   ├── __init__.py        # create_app()
│   └── requirements.txt
├── bin/                   # run_app.sh, render_jup.sh
└── jup/                   # Jupyter notebooks for notes/blog posts
```

## 2. Configure

Edit `app/cfg/lite.yaml`. The `lite` profile is selected by `FLASK_ENV=lite`, which `bin/run_app.sh` sets.

**Do this before the first start.** The first start creates the database and seeds the `admin`, free and pro
users from the config. Changing their passwords in the file afterwards has no effect.

```yaml
ssk:
  USER_APP_NAME:
    string: 'MyApp'
  SECRET_KEY:
    string: 'a-long-random-string'

  SQLALCHEMY_DATABASE_URI:
    string: 'sqlite:///myapp.sqlite'
  LOG_DB_CONNSTR:
    string: 'sqlite:///myapp_log.sqlite'

  ADMIN_PASS:
    string: 'a-strong-admin-password'
  USER_FREE_PASS:
    string: 'another-strong-password'
  USER_PRO_PASS:
    string: 'and-another-one'
```

Leave the other keys in place: most of them are required. See [Configuration](configuration.md) for the full list.

## 3. Run

```bash
./bin/run_app.sh
```

The app listens on port 5000.

- `/` – your app's home page
- `/user/sign-in` – sign in (the admin username is `ADMIN_NAME`, `admin` by default)
- `/cmd/terminal` – admin terminal; type `?` for the list of commands
- `/admin/` – system stats for admins

## 4. Customize

Add routes in `app/blueprints/`, templates in `app/html/local/`, static files in `app/assets/local/`,
terminal commands in `app/logic/cmd/` and jobs in `app/logic/jobs/`.

On every start `create_app()` copies `app/html/local` and `app/assets/local` into the symlinked
`app/templates/local` and `app/static/local`. Edit the source folders; edits made under `templates/` or
`static/` are overwritten.

For schema changes, see [How to Perform Database Upgrades](how-to-database-upgrade.md).

## Database commands

The database is created automatically on the first start, so these are only needed to reset it.
Run them from the project folder with the same profile:

```bash
export FLASK_ENV=lite
flask clean-db   # drop all tables
flask create-db  # create the tables
flask setup-db   # seed users, groups and settings from the config
```
