# AI Transcription Notepad v1.9.4 Release Notes

Release Date: December 25, 2024

## Overview

Version 1.9.4 introduces an experimental intelligent format detection feature and consolidates the application's backend storage to a unified Mongita database. This release improves both user experience and system reliability.

## New Features

### Experimental: Inferred Format Detection

AI Transcription Notepad can now automatically detect the intended output format from your spoken content.

**What it does:**
- Analyzes your recording content to determine the most appropriate format (email, to-do list, meeting notes, etc.)
- Eliminates the need to manually select format presets for obvious use cases
- Works by asking the AI model to infer format intent during transcription

**How to use:**
1. Enable the "Infer Format" checkbox in the Prompt Stack section (above the accordion)
2. Record your content naturally
3. The AI will automatically determine and apply the appropriate format

**Status:** Experimental feature, disabled by default. Please provide feedback on accuracy and usefulness.

**Technical details:**
- Added to prompt stack builder as an optional instruction layer
- Does not override explicit format preset selection
- Can be combined with other prompt stack elements

## Backend Improvements

### Unified Mongita Database

All persistent storage has been consolidated into a single Mongita (MongoDB-compatible) database backend.

**What changed:**
- Settings storage migrated from JSON files to Mongita database
- Settings now stored alongside transcripts and prompt stacks
- Single database location: `~/.config/voice-notepad-v3/mongita/`

**Benefits:**
- **Reliability**: Atomic writes prevent corruption on application crash
- **Consistency**: Single backup/restore process for all app data
- **Architecture**: Cleaner codebase with unified data layer
- **Performance**: Document-based storage better suited for flexible schemas

**Migration:**
- Existing JSON config is automatically migrated on first run
- Original config backed up as `config.json.migrated`
- No user action required

## Technical Changes

### Modified Files

**config.py:**
- Added "Infer Format" prompt stack element
- Migrated settings storage from JSON to Mongita
- Maintains backward compatibility with existing configuration

**database_mongo.py:**
- Added settings collection with full CRUD operations
- Implemented atomic save/load for settings documents
- Added migration logic from JSON to database

**stack_builder.py:**
- Added UI checkbox for "Infer Format" option
- Integrated format inference into prompt stack system

## Upgrade Notes

### From v1.9.3 to v1.9.4

- Settings will be automatically migrated from JSON to database
- No configuration changes required
- Your original `config.json` will be preserved as `config.json.migrated`
- All existing transcripts, prompts, and settings are retained

### Testing Recommendations

If you're upgrading from v1.9.3:
1. Back up `~/.config/voice-notepad-v3/` before upgrading (optional)
2. Launch v1.9.4 - migration happens automatically
3. Verify your settings in Settings → General, Behavior, Prompt
4. Test the new "Infer Format" feature (optional, experimental)

## Known Issues

- **Inferred Format**: Being experimental, format detection may not always match user intent
- **First Launch**: Initial migration from JSON to database may add ~1-2 seconds to first startup

## Future Roadmap

- Refine format inference based on user feedback
- Add format detection confidence scores
- Consider adding user-trainable format patterns

## Compatibility

- **Platform**: Linux (Ubuntu, Debian, and derivatives)
- **Python**: 3.10+
- **Desktop**: KDE Plasma (Wayland), GNOME, other Linux DEs

## Links

- **Repository**: https://github.com/danielrosehill/Voice-Notepad-V3
- **Issues**: https://github.com/danielrosehill/Voice-Notepad-V3/issues
- **Documentation**: See CLAUDE.md in repository

---

**Credits**: Daniel Rosehill
**License**: MIT
