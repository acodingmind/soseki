# Installation

## Requirements

- Python 3.10, 3.11 or 3.12 (the versions tested in CI)
- pip

## Install from PyPI

```bash
pip install soseki
```

This installs the `soseki` command. Continue with the [Quickstart](quickstart.md) to create an app.

## Install from source

```bash
git clone https://github.com/acodingmind/soseki.git
cd soseki
pip install -e .
```

## Development installation

```bash
git clone https://github.com/acodingmind/soseki.git
cd soseki
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

Run the tests from the repository root:

```bash
pytest
```

To run the bundled blanco app from the repository, use `FLASK_ENV=lite flask run`.
`bin/run_app.sh` activates `./venv`, not `./.venv`.

### Building the package

```bash
python -m build
twine check dist/*
```

The build copies `app/` to `ssk/blanco_app/`, `bin/` to `ssk/blanco_bin/` and `jup/` to `ssk/blanco_jup/`;
these are the templates that `soseki init` uses. The copies are generated and git-ignored, so edit the source
folders instead.
