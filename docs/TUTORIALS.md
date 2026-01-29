# Tutorials

Comprehensive step-by-step guides for using Start Green Stay Green to create quality-controlled projects.

## Getting Started

### Creating Your First Project

The simplest way to create a new project is using interactive mode:

```bash
start-green-stay-green init
```

This will prompt you for:
- **Project name**: Name of your new project (alphanumeric, hyphens, underscores)
- **Primary language**: python, typescript, go, or rust

Example session:
```bash
$ start-green-stay-green init
Project name: my-web-app
Primary language: python

✓ Project generated successfully at: /Users/you/my-web-app
```

#### What Gets Generated

Inside your new project directory:

```
my-web-app/
├── .github/
│   └── workflows/              # CI/CD pipelines
├── .claude/
│   ├── agents/                 # AI subagent profiles
│   └── skills/                 # Claude Code skills
├── scripts/
│   ├── check-all.sh           # Run all quality checks
│   ├── test.sh                # Run tests
│   ├── lint.sh                # Run linters
│   ├── format.sh              # Auto-format code
│   ├── security.sh            # Security scanning
│   └── mutation.sh            # Mutation testing
├── .pre-commit-config.yaml     # Pre-commit hooks
├── CLAUDE.md                   # AI assistant context
└── (language-specific files)
```

### Understanding the Generated Structure

#### Quality Control Scripts

All scripts are located in `./scripts/`:

```bash
# Run all quality checks (32 hooks)
./scripts/check-all.sh

# Run tests with coverage
./scripts/test.sh

# Run linters and type checkers
./scripts/lint.sh

# Auto-format code
./scripts/format.sh

# Security scanning
./scripts/security.sh

# Mutation testing
./scripts/mutation.sh
```

#### Pre-commit Hooks

The project uses 32 pre-commit hooks that run automatically before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run all hooks on current changes
pre-commit run

# Run all hooks on all files
pre-commit run --all-files
```

#### CI/CD Pipeline

GitHub Actions workflows run automatically on:
- Push to main/develop branches
- Pull requests
- Manual trigger via GitHub Actions tab

Workflows include:
- Linting and formatting
- Type checking
- Unit tests with coverage
- Security scanning
- Mutation testing
- Documentation building

### Your First Commit

```bash
cd my-web-app

# Make some changes
echo "# My Web App" > README.md

# Stage changes
git add README.md

# Pre-commit hooks run automatically
# They will format, lint, and test your code

# Commit your changes
git commit -m "docs: add initial README"

# Push to GitHub
git push origin main
```

The 3-gate workflow ensures quality:

1. **Gate 1**: Local pre-commit hooks pass (your machine)
2. **Gate 2**: CI pipeline passes (GitHub Actions)
3. **Gate 3**: Code review approval (team review)

## Common Workflows

### Using Configuration Files

Instead of interactive prompts, provide a configuration file:

```yaml
# project.yaml
project_name: my-analytics-platform
language: python
```

Then run:
```bash
start-green-stay-green init --config project.yaml
```

### Specifying Output Directory

Create the project in a specific location:

```bash
start-green-stay-green init \
  --project-name my-app \
  --language typescript \
  --output-dir ~/projects
```

This creates `~/projects/my-app/`.

### Non-Interactive Mode

Useful for scripts and CI/CD:

```bash
start-green-stay-green init \
  --project-name my-service \
  --language go \
  --output-dir ./generated \
  --no-interactive
```

Fails with exit code 1 if any required option is missing.

### Dry Run Preview

Preview what would be generated without creating files:

```bash
start-green-stay-green init \
  --project-name my-app \
  --language rust \
  --dry-run
```

Output:
```
Dry Run Mode - Preview only

Project: my-app
Language: rust
Output: /current/directory/my-app

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

### Working with AI Features

Enable AI-powered features by providing an API key:

```bash
# Via command line
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --api-key sk-ant-...

# Via environment variable
export ANTHROPIC_API_KEY=sk-ant-...
start-green-stay-green init \
  --project-name my-app \
  --language python

# Via OS keyring (saved for future use)
start-green-stay-green init --project-name my-app --language python
# Prompts: "Save to OS keyring for future use?" -> Yes
```

With AI features enabled, the generator creates:
- **Custom CI/CD**: Language-specific workflows
- **AI Subagents**: Tailored to your project
- **CLAUDE.md**: Detailed project context
- **Architecture Rules**: Customized for your project
- **GitHub Actions Review**: AI-powered code review

Without an API key, it uses reference templates.

## Advanced Patterns

### Creating Multi-Language Projects

While each project has a primary language, you can extend it:

```bash
# Create Python project
start-green-stay-green init --project-name my-app --language python

# Then add TypeScript support by modifying .pre-commit-config.yaml
# and adding TypeScript-specific tools
```

### Customizing Generated Files

After generation, you can customize:

1. **CI/CD Workflows** (`.github/workflows/`)
   - Add custom jobs
   - Modify triggers
   - Add additional checks

2. **Pre-commit Hooks** (`.pre-commit-config.yaml`)
   - Disable hooks you don't need
   - Add additional hooks
   - Adjust hook versions

3. **Quality Scripts** (`./scripts/`)
   - Modify thresholds
   - Add custom checks
   - Integrate with external tools

4. **CLAUDE.md**
   - Update project description
   - Adjust quality standards
   - Add domain-specific guidance

5. **Subagent Profiles** (`.claude/agents/`)
   - Customize for your workflow
   - Add domain expertise
   - Adjust responsibilities

### Integrating with Existing Projects

To add Start Green Stay Green infrastructure to an existing project:

1. Create a temporary directory:
   ```bash
   mkdir temp-sgsg
   cd temp-sgsg
   start-green-stay-green init --project-name temp --language python --no-interactive
   ```

2. Copy the components you want:
   ```bash
   # Copy CI/CD workflows
   cp -r temp/.github/workflows/ /path/to/your/project/.github/

   # Copy pre-commit configuration
   cp temp/.pre-commit-config.yaml /path/to/your/project/

   # Copy scripts
   cp -r temp/scripts/ /path/to/your/project/

   # Copy CLAUDE.md
   cp temp/CLAUDE.md /path/to/your/project/
   ```

3. Adjust for your existing structure:
   - Update script paths if needed
   - Merge with existing CI/CD
   - Adapt to your project layout

4. Run quality checks:
   ```bash
   cd /path/to/your/project
   pre-commit run --all-files
   ```

### Version Management

Check which version of Start Green Stay Green you have:

```bash
start-green-stay-green version

# Output: Start Green Stay Green v2.0.0
```

Verbose version information:

```bash
start-green-stay-green version --verbose

# Output:
# Start Green Stay Green
# Version: 2.0.0
# Python: 3.11.0
# Platform: darwin
```

## Troubleshooting

### Common Issues

#### Project Name Validation Fails

**Error**: `Invalid project name: my-app-123-test. Only letters, numbers, hyphens, and underscores are allowed.`

**Solution**: Use only alphanumeric characters, hyphens, and underscores.

```bash
# ✗ Invalid
start-green-stay-green init --project-name "my app"          # spaces not allowed
start-green-stay-green init --project-name "my.app"          # dots not allowed
start-green-stay-green init --project-name "my@app"          # @ not allowed

# ✓ Valid
start-green-stay-green init --project-name "my-app"          # hyphens OK
start-green-stay-green init --project-name "my_app"          # underscores OK
start-green-stay-green init --project-name "myapp"           # simple OK
```

#### API Key Issues

**Error**: `Error: Invalid API key`

**Solution**: Verify your API key:

```bash
# Check environment variable
echo $ANTHROPIC_API_KEY

# Check keyring (macOS)
security find-generic-password -s "anthropic_api_key" -a "$USER"

# Clear keyring and re-enter
security delete-generic-password -s "anthropic_api_key" -a "$USER"
```

#### Non-Interactive Mode Missing Options

**Error**: `Error: --project-name required in non-interactive mode.`

**Solution**: Provide all required options:

```bash
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --no-interactive
```

#### Pre-commit Hook Failures

**Error**: `Some hooks failed. Use --no-verify to skip hooks.`

**Solution**: Fix the issues or use configuration file:

```bash
# See what's failing
pre-commit run --all-files

# Many issues are auto-fixed
# Re-run after fixes
pre-commit run --all-files

# Only skip as a last resort
git commit --no-verify  # DON'T DO THIS in normal workflow!
```

### Getting Help

```bash
# Show help
start-green-stay-green --help

# Help for specific command
start-green-stay-green init --help

# Verbose mode shows detailed information
start-green-stay-green init --verbose --project-name my-app --language python
```

## Best Practices

### Project Naming

Use kebab-case (hyphens) for project names:

```bash
# ✓ Good
start-green-stay-green init --project-name my-awesome-project
start-green-stay-green init --project-name web-api
start-green-stay-green init --project-name data-pipeline

# ⚠ Works but less conventional
start-green-stay-green init --project-name my_awesome_project
start-green-stay-green init --project-name MyAwesomeProject
```

### Quality Control

Always run quality checks before committing:

```bash
# Run comprehensive checks
pre-commit run --all-files

# Or use the quality script
./scripts/check-all.sh

# For faster feedback during development
pre-commit run                # only changed files
pre-commit run --hook-stage push  # only pre-push hooks
```

### Documentation

Every generated project includes:
- `CLAUDE.md` - Context for AI assistance
- `README.md` - Project overview
- `.github/` - Workflow documentation
- `./scripts/` - Script help text

Update these as your project evolves.

### CI/CD Integration

The generated GitHub Actions workflows:
- Run on every push (develop/main branches)
- Run on every PR
- Can be triggered manually
- Support multiple test matrix configurations

Test locally before pushing:

```bash
# Run the same checks as CI
./scripts/check-all.sh

# Or manually
pre-commit run --all-files
pytest --cov=./src
pylint ./src
```

## Next Steps

Now that you understand the basics:

1. **Explore the Generated Structure**: Run `tree -L 2` to see the layout
2. **Read CLAUDE.md**: Your AI assistant's context document
3. **Review the Scripts**: See what each quality script does
4. **Check the Workflows**: Look at `.github/workflows/` for CI/CD details
5. **Start Developing**: Add your code and let the checks guide you

For detailed API documentation, see [API Documentation](API_DOCUMENTATION.md).
