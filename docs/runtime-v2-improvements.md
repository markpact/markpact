# Markpact Runtime v2 - Improvements Summary

This document summarizes the improvements made to markpact runtime based on feedback from the TODO file.

## ✅ Implemented Features

### 1. Pydantic Validation (Schema Validation)

**Before:** Manual dict parsing with no validation
```python
step = {
    "id": "deploy",
    "action": "docker",
    "timeout": "not-a-number"  # No validation!
}
```

**After:** Pydantic models with validation
```python
from markpact.runtime.models import Step

step = Step(
    id="deploy",
    action="docker",
    timeout=300,  # Must be int >= 1
    risk="low"    # Must be low/medium/high
)
# ValidationError if invalid
```

**Files:**
- `src/markpact/runtime/models.py` - Pydantic models with validation
- `src/markpact/runtime/state.py` - Condition checking

---

### 2. Idempotency + State Persistence

**Before:** Steps always executed
```bash
$ python runtime.py migration.md
# All steps execute, even if already done
```

**After:** State tracking with `.deploy-state.json`
```bash
$ python -m markpact.runtime.cli migration.md
# Steps already completed are skipped

$ python -m markpact.runtime.cli migration.md --show-state
State file: .deploy-state.json
Steps completed: 3
  ✓ install_docker
  ✓ rsync_code
  ✓ docker_build

$ python -m markpact.runtime.cli migration.md --reset-state
# Fresh start - clears state
```

**Features:**
- Automatic state persistence to `.deploy-state.json`
- Resume after failure
- Skip already completed steps
- State inspection with `--show-state`

**Files:**
- `src/markpact/runtime/state.py` - StateManager class

---

### 3. Persistent SSH Sessions

**Before:** New SSH connection per step
```python
# Step 1
ssh pi@192.168.188.108 "command1"  # Connect → Execute → Close
# Step 2  
ssh pi@192.168.188.108 "command2"  # Connect → Execute → Close
# Slow and unreliable!
```

**After:** Single persistent SSH session
```python
from markpact.runtime import SSHSessionManager

ssh = SSHSessionManager("192.168.188.108", "pi")
ssh.connect()

# Step 1
ssh.exec_command("command1")  # Reuses session
# Step 2
ssh.exec_command("command2")  # Reuses session

ssh.close()
```

**Files:**
- `src/markpact/runtime/ssh_manager.py` - SSHSessionManager

---

### 4. Retry with Exponential Backoff

**Before:** Single attempt, hard failure
```yaml
extra_steps:
  - id: deploy
    action: docker
    # One attempt only
```

**After:** Configurable retry with exponential backoff
```yaml
extra_steps:
  - id: deploy
    action: docker
    retry: 3           # 4 attempts total (initial + 3 retries)
    timeout: 300
    # Delays: 1s, 2s, 4s between retries
```

**CLI:**
```bash
# Default retry for all steps
python -m markpact.runtime.cli migration.md --retry 3

# Override per step in YAML
retry: 5  # More retries for critical step
```

**Files:**
- `src/markpact/runtime/core_v2.py` - `_execute_step_with_retry()`

---

### 5. Automatic Rollback

**Before:** No rollback on failure
```python
try:
    deploy()
except:
    print("Failed!")  # Leftover state on host
```

**After:** Automatic rollback on failure
```markdown
```markpact:steps yaml
extra_steps:
  - id: docker_up
    action: docker
    command: "docker compose up"
    rollback_cmd: "docker compose down"  # Per-step rollback
```

```markpact:rollback yaml
steps:
  - id: cleanup
    action: shell
    command: "rm -rf /tmp/deploy"
  - id: docker_down
    action: shell
    command: "docker compose down"
```

# On failure:
# 1. Execute failed step's rollback_cmd
# 2. Execute rollback steps in reverse order
```

**Files:**
- `src/markpact/runtime/core_v2.py` - `_rollback()` method

---

### 6. Conditional Step Execution (when/skip_if)

**Before:** No conditions
```yaml
extra_steps:
  - id: install_docker
    action: ssh_cmd
    command: "install docker"  # Runs always
```

**After:** Idempotent conditions
```yaml
extra_steps:
  - id: install_docker
    action: ssh_cmd
    command: "curl -fsSL get.docker.com | sh"
    when: "docker_not_running"  # Only if docker not installed
    
  - id: rsync_code
    action: rsync
    src: ./code/
    dst: remote:/code/
    skip_if: "step_completed:rsync_code"  # Skip if already done
```

**Supported Conditions:**
- `docker_not_running` / `docker_running`
- `file_not_exists:path` / `file_exists:path`
- `dir_not_exists:path` / `dir_exists:path`
- `container_not_running:name` / `container_running:name`
- `step_completed:id` / `step_not_completed:id`
- `always`

**Files:**
- `src/markpact/runtime/state.py` - ConditionChecker class

---

### 7. Enhanced CLI

**New Options:**

```bash
# Reset state for fresh deployment
python -m markpact.runtime.cli migration.md --reset-state

# Show current state
python -m markpact.runtime.cli migration.md --show-state

# Custom state file
python -m markpact.runtime.cli migration.md --state-file ./my-state.json

# Default retry for all steps
python -m markpact.runtime.cli migration.md --retry 3

# List steps with completion status
python -m markpact.runtime.cli migration.md --list-steps
# Shows: [DONE] for completed steps
```

**Files:**
- `src/markpact/runtime/cli.py` - Updated CLI

---

## Example Migration File (v2)

```markdown
# c2004 RPi5 Deployment v1.0.22

## Configuration

```markpact:config yaml
name: "c2004 rpi5 deploy"
version: "1.0.22"
target:
  host: pi@192.168.188.108
  remote_dir: ~/c2004
```

## Deployment Steps

```markpact:steps yaml
extra_steps:
  - id: install_docker
    action: ssh_cmd
    description: "Install Docker if not present"
    command: "curl -fsSL get.docker.com | sh"
    when: "docker_not_running"  # Idempotent
    retry: 2
    risk: medium
    
  - id: rsync_code
    action: rsync
    description: "Sync code to RPi5"
    src: /home/tom/c2004/
    dst: pi@192.168.188.108:~/c2004/
    excludes: [".git", ".venv"]
    skip_if: "step_completed:rsync_code"  # Skip if done
    timeout: 300
    
  - id: docker_deploy
    action: docker
    description: "Deploy with Docker"
    docker_action: compose_up
    host: pi@192.168.188.108
    build: true
    wait_healthy: true
    retry: 3
    rollback_cmd: "docker compose down"  # Rollback on failure
    risk: low
    timeout: 600
```

## Rollback Plan

```markpact:rollback yaml
steps:
  - id: docker_down
    action: ssh_cmd
    command: "cd ~/c2004 && docker compose down"
  - id: cleanup
    action: ssh_cmd
    command: "rm -rf ~/c2004/tmp/*"
```

## Usage

```bash
# First run
python -m markpact.runtime.cli migration.md
# → Executes all steps

# Resume after failure
python -m markpact.runtime.cli migration.md
# → Skips completed steps, resumes from failed step

# Dry run
python -m markpact.runtime.cli migration.md --dry-run

# Fresh start
python -m markpact.runtime.cli migration.md --reset-state
```

---

## Files Changed

### New Files:
1. `src/markpact/runtime/core_v2.py` - Production runtime
2. `src/markpact/runtime/models.py` - Pydantic models
3. `src/markpact/runtime/state.py` - State & condition management
4. `src/markpact/runtime/ssh_manager.py` - Persistent SSH

### Updated Files:
1. `src/markpact/runtime/__init__.py` - New exports
2. `src/markpact/runtime/cli.py` - New CLI options
3. `src/markpact/runtime/executors.py` - SSH persistence
4. `src/markpact/runtime/parser.py` - Rollback block support

---

## Testing

```bash
# 1. Dry run
cd /home/tom/github/wronai/markpact
python -m markpact.runtime.cli examples/md/01-rpi5-deploy/migration.md --dry-run

# 2. List steps with state
python -m markpact.runtime.cli examples/md/01-rpi5-deploy/migration.md --list-steps

# 3. Show state
python -m markpact.runtime.cli examples/md/01-rpi5-deploy/migration.md --show-state

# 4. Reset and execute
python -m markpact.runtime.cli examples/md/01-rpi5-deploy/migration.md --reset-state

# 5. Resume (automatically skips completed)
python -m markpact.runtime.cli examples/md/01-rpi5-deploy/migration.md
```

---

## Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| **Validation** | ❌ None | ✅ Pydantic |
| **Idempotency** | ❌ Always run | ✅ State tracking |
| **SSH** | ❌ Per-step connect | ✅ Persistent session |
| **Retry** | ❌ Single attempt | ✅ Exponential backoff |
| **Rollback** | ❌ Manual cleanup | ✅ Automatic |
| **Conditions** | ❌ N/A | ✅ when/skip_if |
| **Resume** | ❌ Start over | ✅ Continue after failure |
