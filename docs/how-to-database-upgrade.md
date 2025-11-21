# How to Perform Database Upgrades

This guide explains how to add new database tables or modify existing ones in Soseki's dual database system.

## Overview

Soseki uses a versioned database migration system that:

1. Tracks database schema versions via `SSK_MODEL_VERSION` in `ssk/ssk_consts.py`
2. Defines migration functions in `ssk/ssk_upgrader.py`
3. Automatically applies migrations on application startup
4. Supports both the main app database and the separate log database

### Key Concepts

- **Version Number**: Sequential integer in `SSK_MODEL_VERSION` (current: 8)
- **Dual Databases**: Main app database (`appdb`) + Log database (`logdb`)
- **Automatic Migration**: Runs via `SSKUpgrader` class during `start_ssk()`
- **Skip List**: Prevents re-running migrations when initializing from scratch

## Database Architecture

Soseki maintains two separate SQLAlchemy databases:

1. **App Database** (`appdb`): User data, settings, application models
2. **Log Database** (`logdb`): Request/response logs, access records

Each database can be upgraded independently.

## Step-by-Step: Adding a New Database Table

### Step 1: Create the Model

Create your new SQLAlchemy model in `ssk/models/`.

**Example:** Adding a new `Task` model

**File:** `ssk/models/task.py`

```python
#
# Copyright (c) 2025 Your Name
# SPDX-License-Identifier: MIT
#

from datetime import datetime
from ssk.db import db

class Task(db.Model):
    """Model for user tasks/to-dos."""
    
    __tablename__ = 'tasks'
    __bind_key__ = 'appdb'  # or 'logdb' for log database
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref='tasks')
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
```

**Key Points:**
- Use `__bind_key__` to specify which database (`appdb` or `logdb`)
- Define primary keys, foreign keys, and relationships
- Add default values where appropriate
- Include docstrings and copyright headers

### Step 2: Import the Model

Import your new model in `ssk/db.py` so it's registered with SQLAlchemy.

**File:** `ssk/db.py`

```python
# Add to imports section
from ssk.models.task import Task  # Add this line
from ssk.models.user import User, Role, Subs, UserSubs, Transaction
from ssk.models.setting import Setting
from ssk.models.notes import Notes
# ... other imports
```

This ensures the model is loaded when the database initializes.

### Step 3: Increment the Model Version

Update the model version number in `ssk/ssk_consts.py`.

**File:** `ssk/ssk_consts.py`

```python
SSK_VER = '0.8.6'
SSK_NAME = 'soseki'
SSK_MODEL_VERSION = 9  # Increment from 8 to 9

SSK_ADMIN_GROUP = 'root'
```

This indicates the database schema has changed.

### Step 4: Create Migration Function

Add a new migration function to `ssk/ssk_upgrader.py`.

**File:** `ssk/ssk_upgrader.py`

```python
@staticmethod
def ver9():
    my_version = 9
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        # Import the new model
        from ssk.models.task import Task
        
        # Create the new table
        get_db().create_all()
        
        current_app.logger.info("Created tasks table")
    
    set_ssk_version(my_version)
```

**For log database tables**, use the log database engine:

```python
@staticmethod
def ver9():
    my_version = 9
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        from ssk.models.log_model import LogModel
        
        # For log database, use the logdb engine
        my_engine = create_engine(current_app.config['SQLALCHEMY_BINDS']['logdb'])
        get_db().create_all(bind_key='logdb')
        
        current_app.logger.info("Created log_model table in log database")
    
    set_ssk_version(my_version)
```

### Step 5: Register Migration Function

Add your new migration function to the list in `get_upgrade_functions()`.

**File:** `ssk/ssk_upgrader.py`

```python
@staticmethod
def get_upgrade_functions():
    my_retval = [
        SSKUpgrader.ver1, 
        SSKUpgrader.ver2, 
        SSKUpgrader.ver3, 
        SSKUpgrader.ver4, 
        SSKUpgrader.ver5,
        SSKUpgrader.ver6, 
        SSKUpgrader.ver7, 
        SSKUpgrader.ver8,
        SSKUpgrader.ver9  # Add your new version here
    ]
    
    return my_retval
```

**IMPORTANT**: The order must match the version numbers sequentially.

### Step 6: Test the Migration

#### Option A: Test with Fresh Database

```bash
# Activate virtual environment
source venv/bin/activate

# Set test environment
export FLASK_ENV='test'

# Clean existing database
flask clean-db

# Create fresh database (will run all migrations)
flask setup-db

# Verify tables created
flask shell
>>> from ssk.models.task import Task
>>> Task.query.all()
[]
>>> exit()
```

#### Option B: Test with Existing Database

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment
export FLASK_ENV='lite'  # or your test environment

# Start the app (migrations run automatically)
flask run
```

Check the logs for migration messages:

```
INFO in ssk_upgrader [ssk/ssk_upgrader.py:105]:
upgrading to 9
INFO in ssk_upgrader [ssk/ssk_upgrader.py:115]:
Created tasks table
```

### Step 7: Verify the Migration

Connect to the database and verify the table was created:

```bash
# For SQLite databases
sqlite3 soseki_lite.sqlite

# View tables
.tables

# Describe the new table
.schema tasks

# Exit
.quit
```

Or use Flask shell:

```bash
flask shell
>>> from ssk.db import get_db
>>> from sqlalchemy import inspect
>>> inspector = inspect(get_db().engine)
>>> inspector.get_table_names()
['tasks', 'user', 'setting', 'notes', ...]
>>> inspector.get_columns('tasks')
[{'name': 'id', 'type': INTEGER(), ...}, ...]
>>> exit()
```

## Step-by-Step: Modifying an Existing Table

### Adding a Column to Existing Table

**Example:** Adding `priority` column to existing `tasks` table

#### Step 1: Increment Model Version

```python
# ssk/ssk_consts.py
SSK_MODEL_VERSION = 10  # Increment
```

#### Step 2: Update the Model

```python
# ssk/models/task.py
class Task(db.Model):
    # ... existing fields ...
    priority = db.Column(db.String(10), default='medium')  # Add new field
```

#### Step 3: Create Migration with ALTER TABLE

```python
# ssk/ssk_upgrader.py

@staticmethod
def ver10():
    my_version = 10
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        # Add column to existing table
        get_db().engine.execute(
            "ALTER TABLE tasks ADD COLUMN priority VARCHAR(10) DEFAULT 'medium'"
        )
        
        current_app.logger.info("Added priority column to tasks table")
    
    set_ssk_version(my_version)
```

**For PostgreSQL compatibility**, use text() wrapper:

```python
from sqlalchemy import text

get_db().engine.execute(
    text("ALTER TABLE tasks ADD COLUMN priority VARCHAR(10) DEFAULT 'medium'")
)
```

#### Step 4: Register and Test

Follow steps 5-7 from "Adding a New Table" section.

## Migration Patterns

### Pattern 1: Simple Table Creation

Use `create_all()` for new tables:

```python
@staticmethod
def ver9():
    my_version = 9
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        from ssk.models.new_model import NewModel
        get_db().create_all()
    
    set_ssk_version(my_version)
```

### Pattern 2: Adding Columns with ALTER TABLE

Use raw SQL for column additions:

```python
@staticmethod
def ver10():
    my_version = 10
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        get_db().engine.execute('ALTER TABLE notes ADD COLUMN category VARCHAR(100)')
    
    set_ssk_version(my_version)
```

### Pattern 3: Data Migration

Migrate or populate data during upgrade:

```python
@staticmethod
def ver11():
    my_version = 11
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        # Create default settings for all users
        from ssk.models.user import User
        from ssk.models.setting import Setting
        
        users = User.query.all()
        for user in users:
            default_setting = Setting()
            default_setting.key = "THEME"
            default_setting.value = "light"
            user.user_settings.append(default_setting)
        
        get_db().session.commit()
        current_app.logger.info("Added default theme settings for all users")
    
    set_ssk_version(my_version)
```

### Pattern 4: Log Database Modifications

Modify the separate log database:

```python
@staticmethod
def ver12():
    my_version = 12
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        # Get log database engine
        my_engine = create_engine(current_app.config['SQLALCHEMY_BINDS']['logdb'])
        
        # Alter log database table
        my_engine.execute('ALTER TABLE access ADD COLUMN response_time INTEGER')
        
        current_app.logger.info("Added response_time to access log table")
    
    set_ssk_version(my_version)
```

## The Skip List

When creating a brand new database with `ver1()`, the skip list prevents running migrations that are already included in the initial schema.

```python
@staticmethod
def ver1():
    my_version = 1
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    # These migrations are already in the initial schema
    SSKUpgrader._to_skip.append(2)
    SSKUpgrader._to_skip.append(3)
    # ...
    
    set_ssk_version(my_version)
```

**When to update the skip list:**
- When creating a new database from scratch should skip intermediate migrations
- Typically only modified during major version bumps
- Most incremental changes don't need skip list updates

## Testing Your Migration

### Unit Test Example

Create tests in `tests/test_migrations.py`:

```python
import pytest
from ssk import create_app, db
from ssk.models.task import Task

def test_task_table_exists(app):
    """Test that tasks table exists after migration."""
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        assert 'tasks' in inspector.get_table_names()

def test_task_columns(app):
    """Test that tasks table has expected columns."""
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = {col['name'] for col in inspector.get_columns('tasks')}
        
        assert 'id' in columns
        assert 'title' in columns
        assert 'status' in columns
        assert 'created_at' in columns

def test_create_task(app):
    """Test that we can create a task."""
    with app.app_context():
        task = Task()
        task.title = "Test Task"
        task.description = "Test description"
        
        db.session.add(task)
        db.session.commit()
        
        assert task.id is not None
        assert task.status == 'pending'
```

Run tests:

```bash
source venv/bin/activate
pytest tests/test_migrations.py
```

### Manual Testing Checklist

- [ ] Fresh database creation works (`flask setup-db`)
- [ ] Existing database upgrades cleanly
- [ ] New table appears in schema
- [ ] Can insert/query data
- [ ] Foreign keys work correctly
- [ ] Default values are set
- [ ] Rollback doesn't break (if implemented)
- [ ] Logs show migration messages

## Troubleshooting

### Migration Doesn't Run

**Symptoms:** Table not created, no log messages

**Causes:**
1. Database version already higher than migration version
2. Migration in skip list
3. Model not imported

**Solutions:**
```bash
# Check current database version
flask shell
>>> from ssk.db import get_version
>>> get_version().ssk_version
8

# If version is already 9+, migration won't run
# Reset database or manually set version lower
```

### Table Already Exists Error

**Symptoms:** SQLAlchemy raises "table already exists" error

**Cause:** Running `create_all()` when table exists

**Solution:** Check if table exists before creating:

```python
from sqlalchemy import inspect

inspector = inspect(get_db().engine)
if 'tasks' not in inspector.get_table_names():
    get_db().create_all()
```

### Foreign Key Constraint Failed

**Symptoms:** Cannot insert data, foreign key errors

**Cause:** Referenced table/column doesn't exist

**Solutions:**
- Ensure referenced tables exist first
- Check foreign key column names match
- Verify `__bind_key__` matches for related tables

### Column Type Mismatch

**Symptoms:** Data truncation, type errors

**Cause:** Model definition doesn't match database column

**Solution:** Use ALTER TABLE to modify column type:

```python
# SQLite doesn't support ALTER COLUMN, need to recreate table
# PostgreSQL/MySQL support ALTER COLUMN
get_db().engine.execute(
    'ALTER TABLE tasks ALTER COLUMN priority TYPE VARCHAR(20)'
)
```

## Best Practices

### Version Management

✅ **Do:**
- Increment version by 1 for each migration
- Never reuse version numbers
- Keep migrations small and focused
- Add descriptive log messages

❌ **Don't:**
- Skip version numbers
- Combine unrelated changes in one migration
- Modify existing migrations after release

### Migration Safety

✅ **Do:**
- Backup database before testing migrations
- Test on non-production data first
- Use transactions where possible
- Log all migration steps

❌ **Don't:**
- Run destructive migrations without backups
- Assume data exists (check first)
- Delete columns without deprecation period

### Code Organization

✅ **Do:**
- Keep one model per file
- Group related models in same directory
- Import models in `db.py`
- Document complex migrations

❌ **Don't:**
- Put multiple unrelated models in one file
- Import models only in migration functions
- Skip docstrings and comments

### Testing

✅ **Do:**
- Test fresh database creation
- Test upgrade from previous version
- Verify data integrity after migration
- Check foreign key constraints

❌ **Don't:**
- Test only on your local setup
- Skip edge cases
- Forget to test rollback scenarios

## Production Deployment

### Pre-Deployment Checklist

1. **Backup Production Database**
   ```bash
   # SQLite
   cp production.sqlite production.sqlite.backup
   
   # PostgreSQL
   pg_dump mydb > mydb_backup.sql
   ```

2. **Test Migration Locally**
   - Copy production database to local
   - Run migration on copy
   - Verify data integrity

3. **Document Rollback Plan**
   - How to restore from backup
   - Manual SQL to undo changes if needed

4. **Schedule Downtime** (if needed)
   - Notify users
   - Plan maintenance window

### Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Activate environment
source venv/bin/activate

# 3. Backup database
cp soseki.sqlite soseki.sqlite.$(date +%Y%m%d_%H%M%S)

# 4. Stop application
sudo systemctl stop soseki

# 5. Start application (migrations run automatically)
sudo systemctl start soseki

# 6. Verify migration in logs
tail -f log/web.log | grep "upgrading to"

# 7. Test application
curl http://localhost:5000/health
```

### Rollback Procedure

If migration fails:

```bash
# 1. Stop application
sudo systemctl stop soseki

# 2. Restore backup
cp soseki.sqlite.backup soseki.sqlite

# 3. Revert code
git checkout previous-version

# 4. Restart application
sudo systemctl start soseki

# 5. Investigate issue
tail -f log/web.log
```

## Example: Complete Migration Workflow

Let's walk through a complete example of adding a `Category` table for organizing notes.

### 1. Create Model

**File:** `ssk/models/category.py`

```python
#
# Copyright (c) 2025 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from ssk.db import db

class Category(db.Model):
    """Model for note categories."""
    
    __tablename__ = 'categories'
    __bind_key__ = 'appdb'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    color = db.Column(db.String(7), default='#3498db')  # Hex color
    
    # Relationship to notes
    notes = db.relationship('Notes', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>'
```

### 2. Update Notes Model

**File:** `ssk/models/notes.py`

```python
# Add to existing Notes model
class Notes(db.Model):
    # ... existing fields ...
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    # ... rest of model ...
```

### 3. Import Model

**File:** `ssk/db.py`

```python
from ssk.models.category import Category
```

### 4. Increment Version

**File:** `ssk/ssk_consts.py`

```python
SSK_MODEL_VERSION = 9
```

### 5. Create Migration

**File:** `ssk/ssk_upgrader.py`

```python
@staticmethod
def ver9():
    my_version = 9
    current_app.logger.info(SSKUpgrader.UPGRADING_MESG.format(my_version))
    
    my_db_version = get_version()
    
    if my_db_version.ssk_version < my_version and my_version not in SSKUpgrader._to_skip:
        # Create categories table
        from ssk.models.category import Category
        get_db().create_all()
        
        # Add category_id column to notes
        get_db().engine.execute(
            'ALTER TABLE notes ADD COLUMN category_id INTEGER REFERENCES categories(id)'
        )
        
        # Create default categories
        default_categories = [
            Category(name='Technical', description='Technical articles', color='#3498db'),
            Category(name='Tutorial', description='How-to guides', color='#2ecc71'),
            Category(name='Opinion', description='Opinion pieces', color='#e74c3c')
        ]
        
        for cat in default_categories:
            get_db().session.add(cat)
        
        get_db().session.commit()
        
        current_app.logger.info("Created categories table and default categories")
    
    set_ssk_version(my_version)

@staticmethod
def get_upgrade_functions():
    return [
        SSKUpgrader.ver1, SSKUpgrader.ver2, SSKUpgrader.ver3, 
        SSKUpgrader.ver4, SSKUpgrader.ver5, SSKUpgrader.ver6, 
        SSKUpgrader.ver7, SSKUpgrader.ver8, SSKUpgrader.ver9
    ]
```

### 6. Test Migration

```bash
# Activate venv
source venv/bin/activate

# Clean database
flask clean-db

# Create fresh database
flask setup-db

# Verify
flask shell
>>> from ssk.models.category import Category
>>> Category.query.all()
[<Category Technical>, <Category Tutorial>, <Category Opinion>]
>>> exit()
```

### 7. Update Application Code

Now you can use categories in your application:

```python
# In routes/blueprints
from ssk.models.category import Category

@app.route('/notes/by-category/<int:category_id>')
def notes_by_category(category_id):
    category = Category.query.get_or_404(category_id)
    notes = category.notes.all()
    return render_template('notes_list.html', notes=notes, category=category)
```

## References

- **Main upgrader code**: `ssk/ssk_upgrader.py`
- **Database management**: `ssk/db.py`
- **Version constants**: `ssk/ssk_consts.py`
- **Model examples**: `ssk/models/`
- **Flask-SQLAlchemy docs**: https://flask-sqlalchemy.palletsprojects.com/
- **SQLAlchemy migrations**: https://alembic.sqlalchemy.org/

## Support

For issues or questions:
- Check logs: `log/web.log`
- Review database: `flask shell` → `from ssk.db import get_version`
- GitHub Issues: https://github.com/codingminds/soseki/issues
- Author: Michał Świtała (michal@codingminds.io)
