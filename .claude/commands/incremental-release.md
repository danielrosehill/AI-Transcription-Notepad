# Incremental Release

Run this after every feature update to bump the version, push to GitHub, build locally, and update the local Debian installation.

## Steps

Follow these steps in order:

### 1. Commit any uncommitted changes

Check `git status`. If there are uncommitted changes, stage and commit them with an appropriate message describing what was changed. Ask the user for a commit message if the changes are unclear.

### 2. Bump the patch version

Run the release script in deb-only mode (this bumps the version in `pyproject.toml` and `app/src/about_widget.py`, then builds the .deb):

```bash
./build.sh --release-deb
```

This will:
- Increment the patch version (e.g., 1.14.7 -> 1.14.8)
- Build the Debian package to `dist/`

### 3. Commit the version bump

Stage and commit the version bump files:
- `pyproject.toml`
- `app/src/about_widget.py`

Use the commit message format: `chore: bump version to X.Y.Z`

### 4. Push to GitHub

```bash
git push origin main
```

### 5. Install the new .deb locally

```bash
./build.sh --install
```

This installs/upgrades the local Debian package using `sudo dpkg -i`.

### 6. Report completion

Tell the user:
- The old and new version numbers
- That the package was pushed to GitHub
- That the local installation was updated
- Remind them to restart the app if it's currently running

## Notes

- This is a **patch release** (third version number). For minor/major bumps, the user should specify explicitly.
- The build uses `--deb-only` mode since this is for personal local use, not a full public release with AppImage/tarball.
- If the build or install fails, stop and report the error rather than continuing.

$ARGUMENTS
