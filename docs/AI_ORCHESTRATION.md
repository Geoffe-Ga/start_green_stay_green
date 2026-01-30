# AI Orchestration Guide

Guide to using AI-powered features in Start Green Stay Green with the AIOrchestrator.

## Overview

AIOrchestrator provides a unified interface for AI-powered content generation using Claude API. It handles:
- API key management and validation
- Credential storage in OS keyring
- Generation request handling
- Error handling and retries
- Token management

## Getting Started with AIOrchestrator

### Basic Usage

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator

# Initialize with API key
orchestrator = AIOrchestrator(api_key="sk-ant-abc123def456")

# Use in generators
from start_green_stay_green.generators.ci import CIGenerator

generator = CIGenerator(orchestrator, language="python")
workflow = generator.generate_workflow()

print(workflow.content)  # Generated CI/CD workflow
```

### API Key Validation

The orchestrator validates API keys before use:

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator

try:
    orchestrator = AIOrchestrator(api_key="sk-ant-invalid")
except ValueError as e:
    print(f"Invalid API key: {e}")
```

**API Key Format**:
- Starts with `sk-ant-`
- Minimum 20 characters
- Alphanumeric and hyphens only

### Obtaining an API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign in with your account
3. Navigate to "API keys" section
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Store securely (never commit to version control)

## Credential Management

### Using OS Keyring

Store API keys securely in your operating system's credential store:

```python
from start_green_stay_green.utils.credentials import (
    store_api_key_in_keyring,
    get_api_key_from_keyring,
)

# Store API key
api_key = "sk-ant-abc123def456"  # pragma: allowlist secret
if store_api_key_in_keyring(api_key):
    print("API key stored in keyring")
else:
    print("Failed to store in keyring")

# Retrieve API key
stored_key = get_api_key_from_keyring()
if stored_key:
    orchestrator = AIOrchestrator(api_key=stored_key)
```

### Credential Priority

The CLI uses this priority order for finding credentials:

1. **Command Line Argument** (`--api-key`)
   ```bash
   start-green-stay-green init --api-key sk-ant-...
   ```

2. **Environment Variable** (`ANTHROPIC_API_KEY`)
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   start-green-stay-green init
   ```

3. **OS Keyring** (saved previously)
   ```bash
   # Stored from previous interactive run
   start-green-stay-green init  # Retrieves from keyring
   ```

4. **Interactive Prompt**
   ```bash
   start-green-stay-green init
   # Prompts: "Would you like to enter your API key now?"
   ```

### Managing Credentials

#### macOS (Keychain)

```bash
# Store API key
security add-generic-password -s "anthropic_api_key" \
  -a "$USER" -w "sk-ant-abc123def456"

# Retrieve API key
security find-generic-password -s "anthropic_api_key" \
  -a "$USER" -w

# Delete API key
security delete-generic-password -s "anthropic_api_key" \
  -a "$USER"

# Update API key
security delete-generic-password -s "anthropic_api_key" -a "$USER"
security add-generic-password -s "anthropic_api_key" \
  -a "$USER" -w "sk-ant-new-key"
```

#### Linux (pass/seahorse)

```bash
# Using pass password manager
pass insert anthropic/api-key
# Prompts for key

# Using python-keyring
python3 -c "import keyring; \
  keyring.set_password('anthropic', 'api_key', 'sk-ant-...')"
```

#### Windows (Credential Manager)

```bash
# Using Windows Credential Manager (via python-keyring)
python3 -c "import keyring; \
  keyring.set_password('anthropic', 'api_key', 'sk-ant-...')"

# Or manually in Credential Manager:
# 1. Open Settings -> Credential Manager
# 2. Click "Windows Credentials" or "Generic Credentials"
# 3. Add a new credential for 'anthropic_api_key'
```

## Using with Generators

### AI-Powered Generators

Several generators require AIOrchestrator:

#### CIGenerator

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.ci import CIGenerator

orchestrator = AIOrchestrator(api_key="sk-ant-...")
generator = CIGenerator(orchestrator, language="python")

# Generates language-specific CI/CD workflow
workflow = generator.generate_workflow()
print(f"Generated workflow: {len(workflow.content)} characters")
```

#### SubagentsGenerator

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.subagents import SubagentsGenerator
from start_green_stay_green.utils.async_bridge import run_async
from pathlib import Path

orchestrator = AIOrchestrator(api_key="sk-ant-...")
generator = SubagentsGenerator(
    orchestrator,
    reference_dir=Path(".claude/agents")
)

# Generate multiple agents
project_config = "Project: my-app, Language: python, Type: web-app"
results = run_async(
    generator.generate_all_agents(project_config)
)

for agent_name, result in results.items():
    print(f"Generated agent: {agent_name}")
```

#### ClaudeMdGenerator

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.claude_md import ClaudeMdGenerator

orchestrator = AIOrchestrator(api_key="sk-ant-...")
generator = ClaudeMdGenerator(orchestrator)

config = {
    "project_name": "my-app",
    "language": "python",
    "scripts": ["check-all.sh", "test.sh", "lint.sh"],
    "skills": ["stay-green.md", "mutation-testing.md"]
}

result = generator.generate(config)
print(f"Generated CLAUDE.md: {len(result.content)} characters")
```

#### ArchitectureEnforcementGenerator

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.generators.architecture import (
    ArchitectureEnforcementGenerator
)
from pathlib import Path

orchestrator = AIOrchestrator(api_key="sk-ant-...")
generator = ArchitectureEnforcementGenerator(
    orchestrator,
    output_dir=Path("plans/architecture")
)

# Generate architecture rules
generator.generate(language="python", project_name="my-app")
```

## Error Handling

### API Errors

```python
from start_green_stay_green.ai.orchestrator import (
    AIOrchestrator,
    GenerationError
)

try:
    orchestrator = AIOrchestrator(api_key="sk-ant-...")
    result = orchestrator.generate("Create a CI workflow")
except GenerationError as e:
    print(f"Generation failed: {e}")
    # Handle generation error (rate limit, timeout, etc.)
except ValueError as e:
    print(f"Invalid API key or configuration: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Common Errors

#### Invalid API Key

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator

try:
    orchestrator = AIOrchestrator(api_key="invalid-key")
except ValueError as e:
    # Error: "Invalid API key format"
    print(f"API key validation failed: {e}")
```

**Solution**: Verify API key format starts with `sk-ant-` and is at least 20 characters.

#### Rate Limiting

```python
from start_green_stay_green.ai.orchestrator import GenerationError

try:
    result = orchestrator.generate(prompt)
except GenerationError as e:
    if "rate" in str(e).lower():
        print("Rate limited. Please wait before retrying.")
        # Implement exponential backoff
```

**Solution**: Wait before retrying (exponential backoff recommended).

#### Network Errors

```python
try:
    result = orchestrator.generate(prompt)
except GenerationError as e:
    if "connection" in str(e).lower():
        print("Network error. Check internet connection.")
        # Implement retry logic
```

**Solution**: Check internet connection, retry with backoff.

#### Generation Timeouts

```python
try:
    result = orchestrator.generate(prompt, max_tokens=1000, timeout=30)
except GenerationError as e:
    if "timeout" in str(e).lower():
        print("Generation timed out. Try shorter prompt or fewer tokens.")
```

**Solution**: Reduce `max_tokens`, simplify prompt, or increase `timeout`.

## Async Usage

### Running Async Generators

Many generators use async operations internally. Use the async bridge:

```python
from start_green_stay_green.utils.async_bridge import run_async
from start_green_stay_green.generators.subagents import SubagentsGenerator

async def generate_all():
    """Generate all agents asynchronously."""
    generator = SubagentsGenerator(orchestrator)
    return await generator.generate_all_agents(config)

# Run sync
results = run_async(generate_all())
```

### Manual Async Handling

```python
import asyncio

async def main():
    """Main async function."""
    # Create generators
    generator = SubagentsGenerator(orchestrator)

    # Generate agents
    results = await generator.generate_all_agents(config)

    # Process results
    for name, result in results.items():
        print(f"Generated: {name}")

# Run with asyncio
asyncio.run(main())
```

### Concurrent Generation

```python
import asyncio
from start_green_stay_green.utils.async_bridge import run_async

async def generate_all():
    """Generate multiple items concurrently."""
    tasks = [
        generate_ci_workflow(),
        generate_all_agents(),
        generate_claude_md()
    ]
    return await asyncio.gather(*tasks)

results = run_async(generate_all())
```

## Best Practices

### API Key Security

1. **Never Commit API Keys**: Add to `.gitignore`
   ```gitignore
   # API Keys
   .env
   .env.local
   *.key
   ```

2. **Use Environment Variables**: In CI/CD
   ```yaml
   - name: Generate project
     env:
       ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
     run: start-green-stay-green init
   ```

3. **Use OS Keyring**: For local development
   ```bash
   start-green-stay-green init
   # Prompts to save to keyring
   ```

4. **Rotate Keys Regularly**: Create new keys in console
   ```bash
   # Delete old key
   security delete-generic-password -s "anthropic_api_key" -a "$USER"

   # Add new key
   security add-generic-password -s "anthropic_api_key" \
     -a "$USER" -w "sk-ant-new-key"
   ```

### Generation Optimization

1. **Reuse Orchestrator Instance**:
   ```python
   # Good - reuse same instance
   orchestrator = AIOrchestrator(api_key=key)
   for config in configs:
       result = orchestrator.generate(prompt)

   # Bad - create new instance for each call
   for config in configs:
       orchestrator = AIOrchestrator(api_key=key)  # Wasteful
       result = orchestrator.generate(prompt)
   ```

2. **Batch Requests**: Generate multiple items at once
   ```python
   # Good - one API call for multiple agents
   results = run_async(
       generator.generate_all_agents(config)
   )

   # Bad - one API call per agent
   for agent_name in agent_names:
       result = orchestrator.generate(f"Generate {agent_name}")
   ```

3. **Cache Results**: Store generated content
   ```python
   from pathlib import Path
   import json

   cache_file = Path(".cache/generation_results.json")

   # Check cache
   if cache_file.exists():
       cached = json.loads(cache_file.read_text())
       return cached  # Skip API call

   # Generate and cache
   result = orchestrator.generate(prompt)
   cache_file.write_text(json.dumps(result))
   return result
   ```

### Error Recovery

1. **Implement Retries**: With exponential backoff
   ```python
   import time

   def generate_with_retry(prompt, max_retries=3):
       """Generate with exponential backoff retry."""
       for attempt in range(max_retries):
           try:
               return orchestrator.generate(prompt)
           except GenerationError as e:
               if attempt < max_retries - 1:
                   wait_time = 2 ** attempt  # 1, 2, 4 seconds
                   time.sleep(wait_time)
               else:
                   raise
   ```

2. **Validate Generated Content**:
   ```python
   import json

   result = orchestrator.generate(prompt)

   # Validate YAML
   import yaml
   try:
       yaml.safe_load(result.content)
   except yaml.YAMLError as e:
       print(f"Invalid YAML generated: {e}")
       # Regenerate or fallback
   ```

3. **Fallback to Templates**: If generation fails
   ```python
   try:
       result = orchestrator.generate(prompt)
   except GenerationError:
       # Use reference template
       template_path = Path("reference/templates/default.yaml")
       result.content = template_path.read_text()
   ```

## Configuration

### AIOrchestrator Parameters

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator

orchestrator = AIOrchestrator(
    api_key="sk-ant-abc123",           # Required  # pragma: allowlist secret
    model="claude-opus-4-5-20251101",  # Optional, defaults to latest
    max_tokens=4096,                   # Optional, defaults to 4096
    temperature=1.0,                   # Optional, defaults to 1.0
    timeout=60.0,                      # Optional, defaults to 60 seconds
)
```

**Parameters**:
- `api_key`: Anthropic API key (required)
- `model`: Claude model to use (defaults to latest)
- `max_tokens`: Maximum response length (1-8192)
- `temperature`: Response randomness (0.0-2.0)
- `timeout`: Request timeout in seconds

## Integration with CLI

### Command Line API Key Handling

```bash
# Method 1: Command line argument
start-green-stay-green init \
  --project-name my-app \
  --language python \
  --api-key sk-ant-abc123

# Method 2: Environment variable
export ANTHROPIC_API_KEY=sk-ant-abc123
start-green-stay-green init \
  --project-name my-app \
  --language python

# Method 3: OS keyring (interactive)
start-green-stay-green init
# Prompts for API key and offers to save to keyring

# Method 4: Configuration file
# In project.yaml:
# project_name: my-app
# language: python
# api_key: sk-ant-abc123  # NOT RECOMMENDED - security risk
start-green-stay-green init --config project.yaml
```

## Troubleshooting

### API Key Not Found

**Problem**: "No API key found" message

**Solution**:
1. Check environment variable: `echo $ANTHROPIC_API_KEY`
2. Check keyring (macOS): `security find-generic-password -s "anthropic_api_key"`
3. Provide via CLI: `--api-key sk-ant-...`
4. Run interactively: `start-green-stay-green init` (will prompt)

### Generation Fails Silently

**Problem**: No error, but no content generated

**Solution**:
1. Enable verbose mode: `--verbose`
2. Check API key validity: `security find-generic-password -s "anthropic_api_key" -w`
3. Test API key directly: Create a simple test script
4. Check network: `curl https://api.anthropic.com`

### Slow Generation

**Problem**: Generation takes too long

**Solution**:
1. Reduce `max_tokens` parameter
2. Simplify the prompt
3. Check network latency: `ping api.anthropic.com`
4. Increase `timeout` if needed

## Related Documentation

- [Tutorials](TUTORIALS.md) - Using AI features in projects
- [Generator Guide](GENERATOR_GUIDE.md) - AI-powered generators
- [CLI Reference](CLI_REFERENCE.md) - API key command line options
