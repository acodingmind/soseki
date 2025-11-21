# Soseki

A lightweight, batteries-included Flask framework designed for rapidly building internal tools, admin panels, and data-driven web applications.

Soseki takes care of the repetitive infrastructure—authentication, database management, background jobs, API controls, and logging—so you can focus on building the features that matter. Perfect for prototypes, internal dashboards, and production-ready utilities that need to ship fast without sacrificing structure.

## Features

- 🔐 **User Management** - Complete authentication system with Flask-User
- 📊 **Database Management** - SQLAlchemy integration with dual database support (app + logs)
- ⏰ **Job Scheduling** - Background job execution with APScheduler
- 📧 **Email Support** - Built-in email functionality with Flask-Mail
- 🔌 **API Gateway** - API key management and rate limiting
- 📝 **Request Logging** - Comprehensive request/response logging
- 🛠️ **Database Versioning** - Built-in database migration support
- 🛠️ **CLI** - interactive command line for quick feature development and testing
- 🎨 **Customizable** - YAML-based configuration system

## Requirements

- Python 3.10 or higher
- Flask 3.0+
- SQLAlchemy 2.0+

## Installation

### From PyPI (coming soon)

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
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Quick Start

1. Initialize a new soseki like application:

```bash
# Create a project folder 
mkdir soseki_app
cd soseki_app

# Install soseki
python3 -m venv venv
source venv/bin/activate
pip install soseki

# Initialize basic soseki app
python3 -m ssk.cli init
```

2. Update configuration file (`cfg/lite.yaml`):

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
```

3. Run your application:

```bash
# run the app
./bin/run_app.sh
```

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

```bash
pytest
```

With coverage:

```bash
pytest --cov=ssk
```

## License

MIT License - see [LICENCE](https://github.com/acodingmind/soseki/blob/release/LICENSE) file for details.

## Author

Michał Świtała - [CodingMinds.io](https://codingminds.io)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

- [How Contribute](https://github.com/acodingmind/soseki/blob/release/CONTRIBUTING.md)

## Support

For issues and questions, please use the [GitHub issue tracker](https://github.com/acodingmind/soseki/issues).
