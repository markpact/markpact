# Sync Workflow Example

Demonstrates `markpact sync` — keeping README.md in sync with source files.

## Quick Start

```bash
# Sync existing blocks with source files
markpact sync --source src README.md

# Preview changes without writing
markpact sync --source src --dry-run README.md

# Show unified diff for changed files
markpact sync --source src --diff README.md

# CI check — exit code 1 if out of sync
markpact sync --source src --check README.md
```

## Track New Files

```bash
# List untracked source files
markpact sync --missing --source src README.md

# Add ALL untracked files as new blocks
markpact sync --add --source src README.md

# Add specific files only
markpact sync --add config.yaml utils.py --source src README.md

# Preview what --add would do
markpact sync --add --dry-run --source src README.md
```

## Backup & Rollback

```bash
# List backups
markpact sync --backups README.md

# Rollback to latest backup
markpact sync --rollback README.md

# Rollback to specific backup
markpact sync --rollback-to .markpact/README.md.bak.20260101_120000 README.md
```

## Tracked Files

```python markpact:file path=app.py
from fastapi import FastAPI

app = FastAPI(title="Sync Demo")

@app.get("/")
def root():
    return {"status": "ok"}
```

```yaml markpact:file path=config.yaml
app:
  name: sync-demo
  port: 8000
  debug: false
```

```bash markpact:file path=run.sh
#!/bin/bash
uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
```

## Workflow

1. Edit files in `src/` directory
2. Run `markpact sync --source src README.md` to update README
3. Commit both source files and README together
4. In CI: `markpact sync --check --source src README.md` to verify sync

## Recursive Sync

For projects with sub-READMEs:

```bash
# Sync root and all included sub-READMEs
markpact sync --source src -R README.md
```

Use `<!-- markpact:include path=docs/API.md -->` directives to reference sub-READMEs.
