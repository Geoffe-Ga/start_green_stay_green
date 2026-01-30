# Generator Guide

Complete guide to Start Green Stay Green generators - both built-in generators and custom development.

## Generator Architecture

### BaseGenerator

All generators inherit from `BaseGenerator`, which defines the common interface:

```python
from pathlib import Path
from start_green_stay_green.generators.base import BaseGenerator

class MyGenerator(BaseGenerator):
    """Custom generator example."""

    def __init__(self, output_dir: Path):
        """Initialize the generator.

        Args:
            output_dir: Directory where generated files are written.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, config: dict) -> str | dict:
        """Generate content from configuration.

        Args:
            config: Configuration dictionary.

        Returns:
            Generated content as string or dict.

        Raises:
            ValueError: If configuration is invalid.
        """
        # Implementation
        return "content"
```

### Generator Lifecycle

1. **Initialization**: Create generator with configuration
2. **Validation**: Validate input configuration
3. **Generation**: Generate content from templates or AI
4. **Output**: Write or return generated content
5. **Cleanup**: Optional cleanup of temporary files

## Built-in Generators

### PreCommitGenerator

Generates `.pre-commit-config.yaml` configuration for pre-commit hooks.

**Purpose**: Configure 32 quality hooks including formatting, linting, type checking, security scanning, and tests.

**Example**:
```python
from start_green_stay_green.generators.precommit import (
    PreCommitGenerator,
    GenerationConfig
)

# Create generator
generator = PreCommitGenerator(orchestrator=None)

# Configure
config = GenerationConfig(
    project_name="my-project",
    language="python",
    language_config={}
)

# Generate YAML content
yaml_content = generator.generate(config)

# Write to file
output_path = Path(".pre-commit-config.yaml")
output_path.write_text(yaml_content)
```

**Configuration Options**:
- `project_name`: Name of the project
- `language`: python, typescript, go, or rust
- `language_config`: Language-specific settings (dict)

**Output**: `.pre-commit-config.yaml` with hooks for:
- Code formatting (black, prettier, rustfmt)
- Import sorting (isort)
- Linting (pylint, eslint, clippy)
- Type checking (mypy)
- Security (bandit, safety)
- Testing (pytest)
- Docstring coverage (interrogate)
- Complexity analysis (radon)

### ScriptsGenerator

Generates quality control scripts in `./scripts/` directory.

**Purpose**: Provide convenient shell scripts for developers to run quality checks locally.

**Example**:
```python
from start_green_stay_green.generators.scripts import (
    ScriptsGenerator,
    ScriptConfig
)

# Configure
config = ScriptConfig(
    language="python",
    package_name="my_app"
)

# Create generator
generator = ScriptsGenerator(
    output_dir=Path("./scripts"),
    config=config
)

# Generate all scripts
scripts = generator.generate()

# Returns dict of script names to content
# {'check-all.sh': '...', 'test.sh': '...', ...}
```

**Generated Scripts**:
- `check-all.sh` - Run all quality checks
- `test.sh` - Run tests with coverage (target: ≥90%)
- `lint.sh` - Linting and type checking
- `format.sh` - Auto-format code
- `security.sh` - Security scanning
- `mutation.sh` - Mutation testing (target: ≥80%)
- `complexity.sh` - Code complexity analysis

**Configuration Options**:
- `language`: python, typescript, go, rust
- `package_name`: Python package name (snake_case)

### CIGenerator (AI-powered)

Generates GitHub Actions CI/CD workflow for the project.

**Purpose**: Create language-specific CI/CD pipelines with quality gates.

**Requirements**: `AIOrchestrator` with valid API key

**Example**:
```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.ci import CIGenerator

# Initialize orchestrator
orchestrator = AIOrchestrator(api_key="sk-ant-...")

# Create generator
generator = CIGenerator(orchestrator, language="python")

# Generate workflow
workflow = generator.generate_workflow()

# Write to file
workflows_dir = Path(".github/workflows")
workflows_dir.mkdir(parents=True, exist_ok=True)
(workflows_dir / "ci.yml").write_text(workflow.content)
```

**Output**: `.github/workflows/ci.yml` with:
- Matrix testing (multiple Python versions)
- Linting and type checking
- Code coverage analysis
- Security scanning
- Mutation testing
- Documentation validation

**Configuration Options**:
- `language`: python, typescript, go, rust

### SkillsGenerator

Copies reference Claude Code skills to project.

**Purpose**: Provide reusable AI skills for the project.

**Example**:
```python
from pathlib import Path
from start_green_stay_green.generators.skills import REQUIRED_SKILLS
from start_green_stay_green.generators.skills import REFERENCE_SKILLS_DIR

# Create target directory
skills_dir = Path(".claude/skills")
skills_dir.mkdir(parents=True, exist_ok=True)

# Copy each required skill
for skill_name in REQUIRED_SKILLS:
    source = REFERENCE_SKILLS_DIR / skill_name
    target = skills_dir / skill_name
    target.write_text(source.read_text())
```

**Available Skills**:
- `stay-green.md` - Stay Green workflow
- `mutation-testing.md` - Mutation testing
- `comprehensive-pr-review.md` - PR review checklist

**Reference Directory**: `reference/skills/` in package

### SubagentsGenerator (AI-powered)

Generates Claude Code subagent profiles customized for the project.

**Purpose**: Create specialized AI agents for different development tasks.

**Requirements**: `AIOrchestrator` with valid API key

**Example**:
```python
from pathlib import Path
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.utils.async_bridge import run_async

# Initialize orchestrator
orchestrator = AIOrchestrator(api_key="sk-ant-...")

# Create generator
agents_dir = Path(".claude/agents")
generator = SubagentsGenerator(
    orchestrator,
    reference_dir=agents_dir
)

# Generate all agents
project_config = (
    "Project: my-app, "
    "Language: python, "
    "Type: web-application"
)

results = run_async(
    generator.generate_all_agents(project_config)
)

# Write results
agents_dir.mkdir(parents=True, exist_ok=True)
for agent_name, result in results.items():
    (agents_dir / f"{agent_name}.md").write_text(result.content)
```

**Generated Agents**:
- test-engineer
- implementation-engineer
- architecture-design
- security-review
- code-review
- documentation-engineer
- performance-specialist
- (and more)

**Configuration Options**:
- `project_config`: Project description string
- `reference_dir`: Directory with reference profiles

### ClaudeMdGenerator (AI-powered)

Generates CLAUDE.md - the project context document for AI assistance.

**Purpose**: Provide AI assistants with comprehensive project context.

**Requirements**: `AIOrchestrator` with valid API key

**Example**:
```python
from pathlib import Path
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.claude_md import ClaudeMdGenerator

# Initialize orchestrator
orchestrator = AIOrchestrator(api_key="sk-ant-...")

# Create generator
generator = ClaudeMdGenerator(orchestrator)

# Configure project
project_config = {
    "project_name": "my-app",
    "language": "python",
    "scripts": [
        "check-all.sh",
        "test.sh",
        "lint.sh",
        "format.sh",
        "security.sh",
        "mutation.sh"
    ],
    "skills": [
        "stay-green.md",
        "mutation-testing.md",
        "comprehensive-pr-review.md"
    ]
}

# Generate
result = generator.generate(project_config)

# Write file
(Path("CLAUDE.md")).write_text(result.content)
```

**Output**: `CLAUDE.md` containing:
- Project overview
- Technology stack
- Quality standards
- AI assistant instructions
- Development workflow
- Available skills and scripts

**Configuration Options**:
- `project_name`: Name of the project
- `language`: Programming language
- `scripts`: Available quality scripts
- `skills`: Available AI skills

### ArchitectureEnforcementGenerator (AI-powered)

Generates architecture rules for dependency validation.

**Purpose**: Enforce layer separation and prevent circular dependencies.

**Requirements**: `AIOrchestrator` with valid API key

**Example**:
```python
from pathlib import Path
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator
)

# Initialize orchestrator
orchestrator = AIOrchestrator(api_key="sk-ant-...")

# Create generator
arch_dir = Path("plans/architecture")
generator = ArchitectureEnforcementGenerator(
    orchestrator,
    output_dir=arch_dir
)

# Generate architecture rules
generator.generate(language="python", project_name="my-app")

# Creates:
# - plans/architecture/layers.md (architecture layers)
# - plans/architecture/constraints.md (rules)
```

**Output**: Architecture rules for:
- Layer definitions
- Dependency constraints
- Import restrictions
- Circular dependency prevention
- Domain boundaries

**Tools Used**:
- Python: import-linter
- TypeScript: dependency-cruiser
- Go: gorevive
- Rust: cargo-deny

### GitHubActionsReviewGenerator (AI-powered)

Generates GitHub Actions workflow for AI-powered code review.

**Purpose**: Automate code review using Claude AI.

**Requirements**: `AIOrchestrator` with valid API key

**Example**:
```python
from pathlib import Path
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.github_actions import (
    GitHubActionsReviewGenerator
)

# Initialize orchestrator
orchestrator = AIOrchestrator(api_key="sk-ant-...")

# Create generator
generator = GitHubActionsReviewGenerator(orchestrator)

# Generate workflow
result = generator.generate()

# Write workflow
workflows_dir = Path(".github/workflows")
workflows_dir.mkdir(parents=True, exist_ok=True)
(workflows_dir / "code-review.yml").write_text(result.workflow_content)
```

**Output**: `.github/workflows/code-review.yml` with:
- PR analysis
- Code review comments
- Architecture validation
- Test coverage checks
- Security scanning

### MetricsGenerator

Generates quality metrics and dashboards.

**Purpose**: Create visualization and reporting of quality metrics.

**Example**:
```python
from pathlib import Path
from start_green_stay_green.generators.metrics import MetricsGenerator

# Create generator
generator = MetricsGenerator(output_dir=Path("./metrics"))

# Generate metrics dashboard
metrics = generator.generate(config={
    "coverage_threshold": 0.90,
    "mutation_threshold": 0.80,
    "complexity_threshold": 10
})

# Returns metrics data
print(f"Coverage: {metrics['coverage']}%")
print(f"Mutation: {metrics['mutation']}%")
```

**Output**: Quality dashboards and reports

## Custom Generator Development

### Creating a Custom Generator

```python
from pathlib import Path
from typing import Any
from start_green_stay_green.generators.base import BaseGenerator

class MyCustomGenerator(BaseGenerator):
    """Custom generator for specific needs."""

    def __init__(self, output_dir: Path):
        """Initialize generator.

        Args:
            output_dir: Where to write generated files.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, config: dict[str, Any]) -> str:
        """Generate custom content.

        Args:
            config: Configuration dictionary.

        Returns:
            Generated content as string.

        Raises:
            ValueError: If configuration is invalid.
        """
        # Validate configuration
        if "name" not in config:
            raise ValueError("Configuration must include 'name'")

        # Generate content
        name = config["name"]
        content = f"# {name}\n\nCustom content here."

        return content
```

### Integrating with AI

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator

class AICustomGenerator(BaseGenerator):
    """Generator using AI for content creation."""

    def __init__(self, orchestrator: AIOrchestrator, output_dir: Path):
        """Initialize with orchestrator.

        Args:
            orchestrator: AI orchestrator for generation.
            output_dir: Where to write generated files.
        """
        self.orchestrator = orchestrator
        self.output_dir = output_dir

    def generate(self, config: dict) -> str:
        """Generate using AI.

        Args:
            config: Configuration including prompt details.

        Returns:
            AI-generated content.
        """
        prompt = f"Generate {config['type']} for {config['name']}"
        result = self.orchestrator.generate(prompt)
        return result.content
```

### Testing Custom Generators

```python
import pytest
from pathlib import Path
from my_generators import MyCustomGenerator

def test_custom_generator():
    """Test custom generator."""
    # Setup
    output_dir = Path("/tmp/test_output")
    output_dir.mkdir(exist_ok=True)

    generator = MyCustomGenerator(output_dir)

    # Test valid config
    config = {"name": "TestProject"}
    content = generator.generate(config)
    assert "TestProject" in content
    assert len(content) > 0

    # Test invalid config
    with pytest.raises(ValueError):
        generator.generate({})

    # Cleanup
    import shutil
    shutil.rmtree(output_dir)
```

### Using Custom Generators

```python
from pathlib import Path
from my_generators import MyCustomGenerator

# Create generator
generator = MyCustomGenerator(output_dir=Path("./custom"))

# Generate content
config = {"name": "MyProject"}
content = generator.generate(config)

# Write output
(Path("./custom/output.md")).write_text(content)
```

## Generator Composition

### Combining Multiple Generators

```python
from pathlib import Path
from start_green_stay_green.generators.scripts import ScriptsGenerator, ScriptConfig
from start_green_stay_green.generators.precommit import (
    PreCommitGenerator,
    GenerationConfig as PreCommitConfig
)

# Setup
project_path = Path("./my-project")
project_path.mkdir(exist_ok=True)

# Generate scripts
scripts_config = ScriptConfig(language="python", package_name="my_app")
scripts_gen = ScriptsGenerator(
    output_dir=project_path / "scripts",
    config=scripts_config
)
scripts_gen.generate()

# Generate pre-commit config
precommit_config = PreCommitConfig(
    project_name="my-project",
    language="python",
    language_config={}
)
precommit_gen = PreCommitGenerator(orchestrator=None)
precommit_yaml = precommit_gen.generate(precommit_config)
(project_path / ".pre-commit-config.yaml").write_text(precommit_yaml)

# Both are now in place
```

## Error Handling

### Common Issues

**Generator Fails to Initialize**:
```python
try:
    generator = MyGenerator(output_dir)
except FileNotFoundError as e:
    print(f"Cannot create output directory: {e}")
except PermissionError as e:
    print(f"No permission to write to output directory: {e}")
```

**Configuration Validation Fails**:
```python
try:
    content = generator.generate(config)
except ValueError as e:
    print(f"Invalid configuration: {e}")
except TypeError as e:
    print(f"Wrong configuration type: {e}")
```

**AI Generation Fails**:
```python
from start_green_stay_green.generators.base import GenerationError

try:
    result = ai_generator.generate(config)
except GenerationError as e:
    print(f"Generation failed: {e}")
```

## Best Practices

### Configuration Management

1. **Validate Early**: Check configuration in `__init__` or at start of `generate()`
2. **Provide Defaults**: Use sensible defaults for optional config
3. **Document Requirements**: Clearly state required config keys
4. **Use Type Hints**: Enable IDE completion and type checking

### File Writing

1. **Create Parent Directories**: Use `mkdir(parents=True, exist_ok=True)`
2. **Avoid Overwriting**: Check file existence before writing
3. **Use Atomic Operations**: Write to temp file, then move
4. **Handle Permissions**: Catch `PermissionError` and `OSError`

### Testing

1. **Use Temporary Directories**: Use `pytest` fixtures or `tempfile`
2. **Test Valid and Invalid Inputs**: Cover both success and failure paths
3. **Verify Output**: Check generated content, not just file existence
4. **Clean Up**: Remove temporary files after tests

## Related Documentation

- [Tutorials](TUTORIALS.md) - How to use generators
- [CLI Reference](CLI_REFERENCE.md) - Command-line interface documentation
- [AI Orchestration](AI_ORCHESTRATION.md) - Using AI in generators
