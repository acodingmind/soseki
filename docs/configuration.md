# Configuration

Soseki uses YAML configuration files for application settings.

## Configuration File Location

The framework looks for configuration files in the following order:

1. Path specified by `SSK_CONFIG` environment variable (highest priority)
2. `app/cfg/{profile}.yaml`
3. `cfg/{profile}.yaml`

Where `{profile}` is determined by:
- `FLASK_ENV` environment variable
- `"tst"` if testing mode is enabled

### Recommended Approach

For production applications, always set the `SSK_CONFIG` environment variable:

```bash
export SSK_CONFIG=/path/to/your/config.yaml
```

For development, you can place your config in `cfg/{profile}.yaml` in your project root.

## Core Settings

### Application

- `USER_APP_NAME`: Your application name
- `USER_APP_VERSION`: Your application version
- `SECRET_KEY`: Flask secret key (must be changed in production!)
- `PROFILE`: Environment profile (dev, test, prod)

### Database

- `SQLALCHEMY_DATABASE_URI`: Main database connection string
- `LOG_DB_CONNSTR`: Logging database connection string
- `DB_MODEL_VERSION`: Database schema version

### Logging

- `LOG_DIR`: Directory for log files
- `LOG_FILE_NAME`: Log file name
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_ALL_REQUESTS`: Enable request logging
- `LOG_SLOWER_THAN`: Log requests slower than (ms)

### User Management

- `USER_ENABLE_REGISTER`: Allow user registration
- `USER_ENABLE_FORGOT_PASSWORD`: Enable password reset
- `USER_REQUIRE_INVITATION`: Require invitation to register

### Email

- `MAIL_SERVER`: SMTP server address
- `MAIL_PORT`: SMTP port
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password
- `MAIL_USE_TLS`: Use TLS
- `MAIL_DEFAULT_SENDER`: Default sender email

### Scheduling

- `SCHED_ON`: Enable background scheduler
- `DB_CLEANUP`: Database cleanup configuration

## Example Configuration

See `app/cfg/` for complete configuration examples.
