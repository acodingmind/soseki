# Quickstart

## Basic Setup

1. Create a basic soseki application

```bash
# Create virtual environment
python3 -m venv venv

# initialize basic soseki app structure
python3 -m ssk.cli init

# run the app
./bin/run_app.sh

```

This command creates a standard folder structure:

```
myapp/
├── assets/local/      # Static assets (CSS, JS, images)
├── blueprints/        # Flask blueprints for routes
├── cfg/               # Configuration files
├── html/local/        # HTML templates
├── logic/
│   ├── cmd/          # Custom commands
│   └── jobs/         # Background jobs
├── models/           # Database models
├── __init__.py       # Application initialization
└── requirements.txt  # Python dependencies
```

2. Update your application configuration file (e.g., `cfg/lite.yaml`):

```yaml
ssk:
  PROFILE:
    string: 'development'
  USER_APP_NAME:
    string: 'MyApp'
  USER_APP_VERSION:
    string: '1.0.0'
  SECRET_KEY:
    string: 'your-secret-key-here'
  
  # Database configuration
  SQLALCHEMY_DATABASE_URI:
    string: 'sqlite:///myapp.sqlite'
  LOG_DB_CONNSTR:
    string: 'sqlite:///myapp_log.sqlite'
```
2. Customize the app by modifing code in app folder

## Commands

### Soseki CLI Commands

These commands can be run from anywhere:

```bash
soseki init [app_name]  # Creates a new application (default: 'app')
```

### Flask Database Commands

These commands require your application context:

Initialize the database:

```bash
flask create-db  # Create database tables
flask setup-db   # Setup initial configuration
flask clean-db   # Remove all data and tables
```
