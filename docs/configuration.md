# Configuration

Soseki reads its settings from a YAML file. Every key under the top-level `ssk:` key becomes a Flask config
value (`app.config[...]`), so standard Flask, Flask-SQLAlchemy, Flask-Login, Flask-Mail and Flask-WTF options
can be set the same way.

## Configuration file location

The file is looked up in this order:

1. The path in the `SSK_CONFIG` environment variable
2. `app/cfg/{profile}.yaml`
3. `cfg/{profile}.yaml`

`{profile}` is the value of `FLASK_ENV` (for example `lite`), or `tst` when the app is created in testing mode.
Paths 2 and 3 are relative to the current directory, so start the app from the project folder. If no file is
found, startup fails with `FileNotFoundError`.

For production, point `SSK_CONFIG` at a file kept outside the code:

```bash
export SSK_CONFIG=/etc/myapp/prod.yaml
```

## File format

Each value is wrapped in its type:

```yaml
ssk:
  USER_APP_NAME:
    string: 'MyApp'
  MAX_COLLECTORS:
    int: 3
  WEBSITE_OPEN:
    bool: True
  DB_CLEANUP:
    json: {"job": 1, "audit": 21}
```

Supported types: `string`, `int`, `float`, `bool`, `json`.

## Environment variable overrides

An environment variable with the same name as a key replaces the value from the file, and Soseki prints
`<KEY> env var overwrites config file value` at startup. The value is parsed with the key's type from the file.
This is handy for secrets:

```bash
export SECRET_KEY='...'
export ADMIN_PASS='...'
```

Watch out for unrelated variables that happen to share a name with a key, such as `PROFILE` or `LOG_LEVEL`.

## Values stored in the database

Some values are copied into the settings table when the database is created. After that the database copy is
the one in use, so editing the file has no effect. Change them in the admin terminal with `admin conf set` instead:

- `API_ACTIVE_NOW`, `SCHED_ON`
- The `admin`, free and pro users (`ADMIN_*`, `USER_FREE_*`, `USER_PRO_*`) and the subscriptions
  (`FREE_SUB`, `PRO_SUB`)

`WEBSITE_OPEN` is the exception: it is copied from the file to the database on every start.

## Settings

Keys without a default are required; startup fails if one is missing. The template profiles in `app/cfg/`
contain all of them.

### Application

| Key | Type | Description |
|---|---|---|
| `PROFILE` | string | Profile name shown on the about page and in the terminal |
| `USER_APP_NAME` | string | Application name (shown in pages and account emails) |
| `USER_APP_VERSION` | string | Application version |
| `SECRET_KEY` | string | Flask secret key that signs sessions. **Set a long random value.** Anyone who knows it can forge logins. |
| `WTF_CSRF_ENABLED` | bool | CSRF protection for Flask-WTF forms. Keep `True` outside tests. |
| `COPYRIGHT`, `COPYRIGHT_YEAR` | string | Footer text |
| `FONTAWESOME_KIT_ID` | string | Font Awesome kit ID; empty uses the free CDN |
| `ROOT_URL` | string | Public URL of the app. The hourly health check requests it to measure response time; empty disables that check. |
| `DATA_FOLDER` | string | Folder for app data; created at startup |
| `TIME_TRAVEL` | string | Fakes the current time for Soseki's `now()` (`"%Y-%m-%d %H:%M:%S"`); empty uses the real time |

### Database

| Key | Type | Description |
|---|---|---|
| `SQLALCHEMY_DATABASE_URI` | string | Main database URL |
| `LOG_DB_CONNSTR` | string | Log database URL (the `logdb` SQLAlchemy bind) |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | bool | Flask-SQLAlchemy option; keep `False` |
| `DB_HOST` | string | Label used in log messages only |
| `DB_MODEL_VERSION` | int | Schema version of your app. Upgrades up to this version run at startup; see [How to Perform Database Upgrades](how-to-database-upgrade.md). |
| `DB_CLEANUP` | json | Retention per table in days, e.g. `{"audit": 21, "logdb.access": 21}`. Prefix log-database tables with `logdb.`. |

Both databases are created automatically on the first start.

### Logging

| Key | Type | Description |
|---|---|---|
| `LOG_DIR` | string | Folder for log files; created at startup |
| `LOG_FILE_NAME` | string | Log file name; rotated at 5 MB, 10 files kept |
| `LOG_LEVEL` | string | `DEBUG`, `INFO`, `WARN`, `ERROR`, `FATAL` or `CRITICAL`. Any other value, including `WARNING`, falls back to `DEBUG`. |
| `LOG_ALL_REQUESTS` | bool | Store requests in the log database's `access` table |
| `LOG_SLOWER_THAN` | int | With `LOG_ALL_REQUESTS`, store only requests slower than this many milliseconds, plus every failed request |

### Users

| Key | Type | Description |
|---|---|---|
| `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASS` | string | Admin account created with the database. `ADMIN_NAME` defaults to `admin`. **Replace the template password before the first start.** |
| `USER_FREE_NAME`, `USER_FREE_EMAIL`, `USER_FREE_PASS` | string | Sample free-tier user created with the database |
| `USER_PRO_NAME`, `USER_PRO_EMAIL`, `USER_PRO_PASS` | string | Sample pro-tier user created with the database |
| `FREE_SUB`, `PRO_SUB` | string | Names of the two subscriptions |
| `USER_ENABLE_REGISTER` | bool | Allow sign-up |
| `USER_REQUIRE_INVITATION` | bool | Sign-up only with an invitation link |
| `USER_ENABLE_FORGOT_PASSWORD` | bool | Password reset by email |

The admin account belongs to the `root` group, which unlocks the admin pages and the terminal.

More account settings, with their defaults, are listed in `ssk/auth/settings.py`. The ones you're most likely to
change: `USER_ENABLE_CONFIRM_EMAIL` (`True`: new users must confirm their address before signing in),
`USER_ENABLE_INVITE_USER` (`False`: lets signed-in users send invitations from `/user/invite`),
`USER_ENABLE_REMEMBER_ME` (`True`), `USER_USER_SESSION_EXPIRATION` (`3600`: seconds of inactivity before a session
ends) and `USER_BCRYPT_ROUNDS` (`12`). The names and defaults match Flask-User 1.0, which Soseki used before.

### Site and API

| Key | Type | Description |
|---|---|---|
| `WEBSITE_OPEN` | bool | When `False`, every user except the admin is signed out (maintenance mode) |
| `SCHED_ON` | bool | Run the background jobs started by the scheduler |
| `MAX_COLLECTORS` | int | Number of worker threads for terminal commands and jobs |
| `MAX_ACTIVE_KEYS` | int | Maximum number of API keys that can be active at the same time |
| `API_ACTIVE_NOW` | int | Seconds a key stays active after its last call |

The API starts closed after every restart. Open it from the admin terminal with `admin api open`.

### Email

| Key | Type | Description |
|---|---|---|
| `MAIL_SERVER`, `MAIL_PORT` | string, int | SMTP server |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | string | SMTP credentials |
| `MAIL_USE_TLS`, `MAIL_USE_SSL` | bool | Connection security |
| `MAIL_DEFAULT_SENDER` | string | Default `From` header, e.g. `'"My App" <noreply@example.com>'` |
| `USER_EMAIL_SENDER_EMAIL` | string | Sender address for account emails (confirmation, password reset, ...) |
| `MAIL_SUPPRESS_SEND` | bool | Don't actually send emails (useful in tests) |

### Security

| Key | Type | Default | Description |
|---|---|---|---|
| `IP_BLACKLIST` | json | `[]` | IP addresses to block, e.g. `["203.0.113.7"]`. Their requests are rejected before any processing. Behind a reverse proxy this needs the real client IP (for example through Werkzeug's `ProxyFix`). |
| `SESSION_COOKIE_HTTPONLY` | bool | `True` | Hide the session cookie from JavaScript |
| `SESSION_COOKIE_SAMESITE` | string | `Lax` | SameSite policy for the session cookie |
| `SESSION_COOKIE_SECURE` | bool | not set | Set to `True` when serving over HTTPS |

## Example configuration

See `app/cfg/lite.yaml` (development) and `app/cfg/tst.yaml` (tests) for complete files.
