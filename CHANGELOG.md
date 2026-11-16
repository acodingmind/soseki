# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.10.0] - 2026-11-16

**Upgrading from 0.9.x:** import `roles_required` / `login_required` from `ssk.auth` instead of `flask_user`.
No database migration is needed; existing passwords keep working, but everyone has to sign in again.

### Security
- Task routes (`/ssk/tasks_action`, `/ssk/task_log_download/<tid>`, `/ssk/progress/<tid>`) now require a signed-in
  user who owns the job or is an admin. Before, anyone with a task id could stop or delete a job or download its log.
- Revoked API keys and closing the API now take effect immediately. Before, a key kept working as long as it was
  used within `API_ACTIVE_NOW` seconds.
- Post-login redirects (`next=`) are limited to local paths. Flask-User's `make_safe_url` allowed redirects such
  as `/////evil.com` (CVE-2021-23401, never fixed upstream); `ssk.auth` does not.

### Changed
- **Replaced Flask-User and passlib with `ssk.auth`**, built on Flask-Login, bcrypt and itsdangerous. Flask-User was
  unmaintained since 2019 and passlib since 2020, and passlib no longer fully supports bcrypt 5.
  - Unchanged for apps: USER_* settings, `/user/...` URLs, `user.*` endpoint names, the templates under
    `flask_user/`, `current_app.user_manager` (`hash_password`, `verify_password`, `password_validator`, ...).
  - Existing password hashes keep working; no database migration is needed.
  - Import decorators from `ssk.auth` (`roles_required`, `login_required`, `roles_accepted`) instead of `flask_user`.
  - Changing a password now signs out the user's other sessions and remember-me cookies.
  - Password-reset links stop working once used; email-confirmation links are tied to the address they were sent to.
  - A failed sign-in for an unknown account takes as long as one with a wrong password.
  - Users signed in before the upgrade need to sign in again.
  - Removed the unused multiple-email, Auth0 and combined login/register templates.
- Removed unused Bootstrap files: the vendored Bootstrap 4.5.3 bundle (never loaded) and a Bootstrap 3.1.1 layout
  for the Flask-User pages (not used). The site's own `global.css` / `global.js` provide the layout and tabs.
- Updated dependencies: SQLAlchemy 2.0.57, SQLAlchemy-Utils 0.43.0, PyMySQL 1.2.4, APScheduler 3.11.3,
  email-validator 2.4.0, textile 4.0.5, MarkupSafe 3.0.4; dev: pytest 9.2.0, pytest-mock 3.17.0, coverage 7.16.2.
- Minimum versions for indirect dependencies with security fixes: Werkzeug 3.1.9, urllib3 2.8.0, certifi 2026.10.18.
- CI uses `actions/checkout@v7` and `actions/setup-python@v7`.
- The error page uses `FONTAWESOME_KIT_ID` (or the free CDN) instead of a hardcoded kit, and the layout no
  longer loads Internet Explorer shims from the defunct `oss.maxcdn.com`.
- `/ssk/task_log_download/<tid>` returns not-found instead of failing with a server error when the log is missing.

### Fixed
- The `DB_CLEANUP` job deleted nothing since the move to SQLAlchemy 2.0; it now removes old rows from both
  databases, rejects table names that don't exist, and records failures in the audit log.
- Framework upgrades 2–4 failed on SQLAlchemy 2.0 and are now ported; each skips a missing table or an
  existing column.
- Framework upgrade 8 crashed on databases created before it, leaving them at version 7 without the pro user
  or subscriptions. It now creates them the same way a new database does, and is safe to run more than once.
- New databases no longer get a duplicate `SCHED_ON` setting.
- The admin terminal's `mail` command works by name, not only as `m`.
- The template configs no longer point `ROOT_URL` at codingminds.io, which made every new app request that
  site hourly. The health check request now has a 10-second timeout.

### Documentation
- Rewrote the quickstart, installation and configuration guides; the configuration guide now lists every setting.

## [0.9.3] - 2026-06-22

### Added
- IP blacklist configuration (`IP_BLACKLIST`) to block requests from specific IPs

## [0.9.0] - 2025-11-20

### Changed
- making it ready for Open Source
  - cleanup
  - documentation

## Earlier Versions

Previous versions were internal development releases.
