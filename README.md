# Soseki

A lightweight, batteries-included Flask framework designed for rapidly building internal tools, admin panels, and data-driven web applications.

Soseki takes care of the repetitive infrastructure—authentication, database management, background jobs, API controls, and logging—so you can focus on building the features that matter. Perfect for prototypes, internal dashboards, and production-ready utilities that need to ship fast without sacrificing structure.

## Features

- 🔐 **User Management** - Sign-in, registration (optionally invite-only), email confirmation, password reset and roles
- 📊 **Database Management** - SQLAlchemy integration with dual database support (app + logs)
- ⏰ **Job Scheduling** - Background job execution with APScheduler
- 📧 **Email Support** - Built-in email functionality with Flask-Mail
- 🔌 **API Gateway** - API key management with a cap on concurrently active keys
- 📝 **Request Logging** - Logs slow and failed requests to a separate log database
- 🛠️ **Database Versioning** - Built-in database migration support
- 💻 **Admin Terminal** - in-browser command line for managing users, jobs, settings and API keys
- 🎨 **Customizable** - YAML-based configuration system

## Requirements

- Python 3.10 or higher
- Flask 3.0+
- SQLAlchemy 2.0+

## Installation

### From PyPI

```bash
pip install soseki
```

### From source

```bash
git clone https://github.com/acodingmind/soseki
cd soseki
pip install -e .
```

### Development Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

## Quick Start

1. Create a project and initialize a Soseki app in it:

```bash
# Create a project folder 
mkdir soseki_app
cd soseki_app

# Install soseki
python3 -m venv venv
source venv/bin/activate
pip install soseki

# Initialize basic soseki app (creates app/, bin/ and jup/)
soseki init
```

2. Edit the configuration file `app/cfg/lite.yaml`. **Do this before the first start**: the first start creates
   the database and the `admin`, free and pro users from these values, and changing the passwords in the file
   later has no effect.

```yaml
ssk:
  USER_APP_NAME:
    string: 'MyApp'
  SECRET_KEY:
    string: 'your-secret-key-here'
  SQLALCHEMY_DATABASE_URI:
    string: 'sqlite:///myapp.sqlite'
  LOG_DB_CONNSTR:
    string: 'sqlite:///myapp_log.sqlite'
  ADMIN_PASS:
    string: 'a-strong-admin-password'
```

   Also replace the `USER_FREE_PASS` and `USER_PRO_PASS` placeholders. See [Configuration](https://github.com/acodingmind/soseki/blob/release/docs/configuration.md) for every setting.

3. Run your application:

```bash
./bin/run_app.sh
```

   It serves on port 5000. Sign in at `/user/sign-in` as `admin`; the admin terminal is at `/cmd/terminal`.

## Documentation

- [Installation Guide](https://github.com/acodingmind/soseki/blob/release/docs/installation.md)
- [Quick Start](https://github.com/acodingmind/soseki/blob/release/docs/quickstart.md)
- [Configuration](https://github.com/acodingmind/soseki/blob/release/docs/configuration.md)

## How To

- [How To Add Notes](https://github.com/acodingmind/soseki/blob/release/docs/how-to-add-notes.md)
- [How To Upgrade Database](https://github.com/acodingmind/soseki/blob/release/docs/how-to-database-upgrade.md)

## Blanco App

Check the `app/` directory for a complete working example application.

The standard folder structure (created by init command):
- `assets/local` - Static files (CSS, JS)
- `blueprints/` - Flask blueprints
- `cfg/` - Configuration files
- `html/local` - Templates
- `logic/cmd` - Custom commands
- `logic/jobs` - Background jobs
- `models/` - Database models

## Project Structure

```
soseki/
├── ssk/              # Core framework package
├── app/              # Blanco application
├── bin/              # Utility scripts
├── tests/            # Test suite
├── docs/             # Documentation
└── requirements.txt  # Core dependencies
```

## Running Tests

Run from the repository root (the tests load `app/cfg/tst.yaml` by relative path):

```bash
pytest
pytest --cov=ssk --cov-report=term-missing
pytest tests/unittests/test_home_blueprint.py
```

## Security Notes

- Set a random `SECRET_KEY` and replace every `changeme` value in the config before the first start.
- Serve over HTTPS in production and enable `SESSION_COOKIE_SECURE`.
- Accounts are handled by `ssk.auth` (Flask-Login, bcrypt, itsdangerous). Changing a password signs out the
  user's other sessions, password-reset links work once, and post-login redirects (`next=`) stay on the site.

## License

MIT License - see the [LICENSE](https://github.com/acodingmind/soseki/blob/release/LICENSE) file for details.

## Author

Michał Świtała - [CodingMinds.io](https://codingminds.io)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

- [How to Contribute](https://github.com/acodingmind/soseki/blob/release/CONTRIBUTING.md)

## Support

For issues and questions, please use the [GitHub issue tracker](https://github.com/acodingmind/soseki/issues).
