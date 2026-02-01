# CLI Reference

Complete reference documentation for the Start Green Stay Green command-line interface.

## Overview

Start Green Stay Green provides a simple command-line interface for generating quality-controlled projects:

```bash
start-green-stay-green [OPTIONS] COMMAND [ARGS]
```

All commands are interactive by default. Use `--no-interactive` for automation.

## Global Options

### `--verbose` / `-v`

Enable verbose output with detailed information about what's happening.

**Example**:
```bash
start-green-stay-green --verbose init --project-name my-app --language python
```

**Output**:
```
[dim]Loading project configuration...[/dim]
[dim]Validating project name: my-app[/dim]
[dim]Language: python[/dim]
[green]✓[/green] Project generated successfully at: /path/to/my-app
```

### `--quiet` / `-q`

Suppress non-essential output, showing only important messages.

**Example**:
```bash
start-green-stay-green --quiet init --project-name my-app --language python
```

**Note**: `--verbose` and `--quiet` are mutually exclusive.

### `--config` / `--config-file PATH`

Load configuration from a YAML or TOML file.

**Example**:
```bash
start-green-stay-green --config project.yaml init
```

**Configuration File Format (YAML)**:
```yaml
project_name: my-awesome-project
language: python
output_dir: ~/projects
api_key: sk-ant-...  # Optional, only if storing in config
```

**Configuration File Format (TOML)**:
```toml
project_name = "my-awesome-project"
language = "python"
output_dir = "~/projects"
```

### `--help`

Show help message and exit.

**Example**:
```bash
start-green-stay-green --help
start-green-stay-green init --help
```

## Commands

### `init`

Initialize a new project with quality controls.

**Syntax**:
```bash
start-green-stay-green init [OPTIONS]
```

#### Options

##### `--project-name` / `-n TEXT` (Optional)

Name of the project to generate.

**Constraints**:
- Alphanumeric characters, hyphens, underscores only
- Maximum 100 characters
- Cannot start with hyphen or underscore
- Cannot be a Windows reserved name (CON, PRN, AUX, etc.)

**Examples**:
```bash
# Valid
--project-name my-app
--project-name MyApp
--project-name my_app
--project-name my123app

# Invalid
--project-name "my app"          # spaces not allowed
--project-name "my.app"          # dots not allowed
--project-name "-my-app"         # cannot start with hyphen
--project-name "con"             # Windows reserved name
```

**Interactive Fallback**:
If not provided in non-interactive mode, will prompt:
```
Project name:
```

##### `--language` / `-l TEXT` (Optional)

Primary programming language for the project.

**Supported Languages**:
- `python` - Python 3.11+
- `typescript` - TypeScript with Node.js
- `go` - Go 1.21+
- `rust` - Rust 1.70+

**Examples**:
```bash
--language python
--language typescript
--language go
--language rust
```

**Interactive Fallback**:
If not provided, will prompt with options:
```
Primary language: [python/typescript/go/rust]
```

##### `--output-dir` / `-o PATH` (Optional)

Output directory for the generated project.

**Default**: Current working directory

**Examples**:
```bash
--output-dir /home/user/projects
--output-dir ~/projects
--output-dir ./generated

# With relative paths
--output-dir ../projects
--output-dir .  # Current directory
```

**Path Safety**:
- Paths are normalized and resolved to absolute paths
- Path traversal attempts (using `..`) are detected and rejected
- Project path must stay within output directory

##### `--dry-run` (Optional)

Preview what would be generated without creating files.

**Example**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --dry-run
```

**Output**:
```
Dry Run Mode - Preview only

Project: my-app
Language: python
Output: /path/to/my-app

Would generate:
  - CI/CD pipeline
  - Pre-commit hooks
  - Quality scripts
  - Skills
  - Subagent profiles
  - CLAUDE.md
  - GitHub Actions (AI review)
  - Architecture enforcement
```

**Note**: Does not prompt for missing options even in interactive mode.

##### `--no-interactive` (Optional)

Run in non-interactive mode without prompts.

**Behavior**:
- All required options must be provided via CLI or config file
- Fails with exit code 1 if any required option is missing
- No interactive prompts even for missing values

**Examples**:
```bash
# Valid - all options provided
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --no-interactive

# Invalid - missing --language
start-green-stay-green init \
  --project-name my-app \
  --no-interactive
# Error: --language required in non-interactive mode.
```

##### `--api-key TEXT` (Optional)

Claude API key for AI-powered features.

**Behavior**:
- If not provided, checks environment variable `ANTHROPIC_API_KEY`
- If not found, checks OS keyring
- If still not found, prompts interactively (unless `--no-interactive`)
- If provided, enables AI-powered generation:
  - Custom CI/CD pipelines
  - Language-specific subagent profiles
  - Tailored CLAUDE.md
  - Custom architecture rules

**Examples**:
```bash
# Provide API key directly
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --api-key sk-ant-abc123def456

# Use environment variable
export ANTHROPIC_API_KEY=sk-ant-abc123def456
start-green-stay-green init --project-name my-app --language python

# Use OS keyring (saved previously)
start-green-stay-green init --project-name my-app --language python
```

**API Key Priority** (in order):
1. `--api-key` command line argument
2. `ANTHROPIC_API_KEY` environment variable
3. OS keyring (macOS/Linux/Windows)
4. Interactive prompt (unless `--no-interactive`)

**Security**:
- API key is never logged or displayed
- `--api-key` input is hidden from shell history
- Prompted input is masked in terminal
- Use OS keyring for storage: `echo $ANTHROPIC_API_KEY | security add-generic-password -s "anthropic_api_key" -a "$USER" -w -`

##### `--config PATH` (Optional)

Path to configuration file (YAML or TOML).

**File Detection**:
- Automatically detects format based on extension
- `.yaml` / `.yml` for YAML
- `.toml` for TOML

**Example Configuration (YAML)**:
```yaml
project_name: my-awesome-project
language: python
output_dir: ~/projects
api_key: sk-ant-...
```

**Example Configuration (TOML)**:
```toml
project_name = "my-awesome-project"
language = "python"
output_dir = "~/projects"
api_key = "sk-ant-..."  # pragma: allowlist secret
```

**Merge Behavior**:
1. Loads defaults
2. Merges config file values
3. Merges CLI argument values (highest priority)

#### Examples

**Interactive Mode**:
```bash
start-green-stay-green init

# Prompts for:
# Project name: my-app
# Primary language: python
```

**Non-Interactive Mode**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --output-dir ~/projects \
  --no-interactive
```

**With API Key**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --api-key sk-ant-abc123
```

**With Configuration File**:
```bash
start-green-stay-green init --config project.yaml
```

**Dry Run**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --dry-run
```

**Verbose Output**:
```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --verbose
```

#### Exit Codes

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success - project generated | ✓ Project created |
| 1 | Validation error | Invalid project name, missing option |
| 1 | Generation failed | File system error, permission denied |
| 1 | Invalid API key | API key validation failed |
| 2 | Missing required option | Non-interactive mode missing argument |

#### Validation

The `init` command validates:

**Project Name**:
- Alphanumeric, hyphens, underscores only
- 1-100 characters
- Does not start with hyphen or underscore
- Not a Windows reserved name

**Language**:
- Must be one of: python, typescript, go, rust
- Case-insensitive

**Output Directory**:
- Path must be safe from traversal attacks
- Parent directories are created if needed
- Project directory must not already exist (to avoid conflicts)

**API Key**:
- Must be a valid Anthropic API key format
- Validated before use

### `version`

Display version information.

**Syntax**:
```bash
start-green-stay-green version [OPTIONS]
```

#### Options

##### `--verbose` / `-v`

Show detailed version information.

**Example**:
```bash
start-green-stay-green version --verbose
```

**Output**:
```
Start Green Stay Green
Version: 2.0.0
Python: 3.11.6
Platform: darwin
```

#### Examples

**Simple Version**:
```bash
start-green-stay-green version

# Output: Start Green Stay Green v1.0.0
```

**Verbose Version**:
```bash
start-green-stay-green version --verbose

# Output:
# Start Green Stay Green
# Version: 1.0.0
# Python: 3.11.6
# Platform: darwin
```

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - version displayed |

## Environment Variables

### `ANTHROPIC_API_KEY`

Claude API key for AI-powered features.

**Usage**:
```bash
export ANTHROPIC_API_KEY=sk-ant-abc123def456
start-green-stay-green init --project-name my-app --language python
```

**Priority**: Lower than `--api-key` CLI argument, higher than OS keyring

### `PYTHONUNBUFFERED`

Disable Python output buffering for real-time logging.

**Usage**:
```bash
export PYTHONUNBUFFERED=1
start-green-stay-green init --verbose --project-name my-app --language python
```

**Benefit**: See log messages immediately instead of batched

## Configuration Files

### YAML Format

```yaml
# project.yaml
project_name: my-awesome-project
language: python
output_dir: ~/projects
api_key: sk-ant-...  # Optional
```

**Usage**:
```bash
start-green-stay-green init --config project.yaml
```

### TOML Format

```toml
# project.toml
project_name = "my-awesome-project"
language = "python"
output_dir = "~/projects"
api_key = "sk-ant-..."  # pragma: allowlist secret
```

**Usage**:
```bash
start-green-stay-green init --config project.toml
```

### Merge Priority

When using both config file and CLI arguments:

1. **Defaults** (lowest priority)
2. Config file values
3. **CLI arguments** (highest priority)

Example:
```yaml
# config.yaml
project_name: config-project
language: python
```

```bash
start-green-stay-green init \
  --config config.yaml \
  --project-name cli-project

# Result: Uses "cli-project" from CLI argument
```

## Error Handling

### Validation Errors

**Invalid Project Name**:
```
Error: Invalid project name: my app.
Only letters, numbers, hyphens, and underscores are allowed.
```

**Missing Required Option**:
```
Error: --project-name required in non-interactive mode.
```

**Invalid API Key**:
```
Error: Invalid API key
```

### File System Errors

**No Permission**:
```
Error: Generation failed: Permission denied creating directory
```

**Disk Full**:
```
Error: Generation failed: No space left on device
```

**Path Escape Attempt**:
```
Error: Output directory cannot contain '..' components
```

## Usage Patterns

### Creating a Single Project

```bash
start-green-stay-green init \
  --project-name my-service \
  --language python
```

### Batch Creating Projects

```bash
#!/bin/bash
for project in api-server web-client data-pipeline; do
  start-green-stay-green init \
    --project-name "$project" \
    --language python \
    --output-dir ~/projects \
    --no-interactive
done
```

### Using in CI/CD

```yaml
# .github/workflows/generate.yml
- name: Generate project
  run: |
    start-green-stay-green init \
      --project-name ${{ github.event.inputs.name }} \
      --language ${{ github.event.inputs.language }} \
      --api-key ${{ secrets.ANTHROPIC_API_KEY }} \
      --no-interactive
```

### Integration with Existing Scripts

```bash
# generate-project.sh
#!/bin/bash

PROJECT_NAME=${1:-my-app}
LANGUAGE=${2:-python}
OUTPUT_DIR=${3:-.}

start-green-stay-green init \
  --project-name "$PROJECT_NAME" \
  --language "$LANGUAGE" \
  --output-dir "$OUTPUT_DIR" \
  --api-key "$ANTHROPIC_API_KEY" \
  --no-interactive
```

## FAQ

**Q: Can I change the project name after creation?**
A: Yes, manually rename the directory and update references in configuration files.

**Q: What if I don't have an API key?**
A: The tool falls back to reference templates. AI features are optional.

**Q: Can I use the same API key for multiple projects?**
A: Yes, the API key is validated per-command but not stored by the CLI.

**Q: How do I update a project created by Start Green Stay Green?**
A: The generated infrastructure is yours to customize. Make changes directly to configuration files.

**Q: Can I integrate this into my existing CI/CD?**
A: Yes, use `--no-interactive` mode and pass configuration via environment variables or files.

## Related Documentation

- [Tutorials](TUTORIALS.md) - Step-by-step guides
- [Generator Guide](GENERATOR_GUIDE.md) - Detailed generator documentation
- [AI Orchestration](AI_ORCHESTRATION.md) - API key and credential management
- [API Documentation](API_DOCUMENTATION.md) - Complete API reference
