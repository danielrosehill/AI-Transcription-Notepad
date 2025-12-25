# v1.9.4 - Inferred Format Detection + Unified Database Backend

## New Features

### Experimental: Inferred Format Detection
- Added "Infer Format" checkbox in Prompt Stack UI
- AI automatically detects intended output format (email, to-do, meeting notes, etc.) from recording content
- Disabled by default - enable to test and provide feedback

## Backend Improvements

### Unified Mongita Database
- **Settings storage** migrated from JSON files to Mongita database
- All app data now in single database: transcripts, prompts, and settings
- **Automatic migration** from existing JSON config (backed up as `config.json.migrated`)

**Benefits:**
- More reliable: atomic writes prevent corruption on crash
- Cleaner architecture: single data layer for all persistent storage
- Consistent backup/restore process

## Technical Changes

- `config.py`: Format inference prompt element + database-backed settings
- `database_mongo.py`: Settings collection with full CRUD operations
- `stack_builder.py`: UI for format inference toggle

## Upgrade Notes

Settings will be automatically migrated on first launch. No user action required.

## Files Changed
- pyproject.toml (version bump)
- config.py
- database_mongo.py
- stack_builder.py
