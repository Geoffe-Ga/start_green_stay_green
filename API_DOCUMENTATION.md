# Start Green Stay Green - API Documentation

Complete API reference for all modules in Start Green Stay Green.

## Table of Contents

1. [AI Orchestration Module](#ai-orchestration-module)
2. [GitHub Integration Module](#github-integration-module)
3. [Common Patterns](#common-patterns)
4. [Error Handling](#error-handling)
5. [Examples](#examples)

---

## AI Orchestration Module

### Overview

The AI orchestration module (`start_green_stay_green.ai.orchestrator`) coordinates AI-powered content generation using the Claude API. It manages prompt construction, context injection, response handling, error handling, and retry logic with exponential backoff.

**Module Path**: `start_green_stay_green/ai/orchestrator.py`

### Constants

#### OutputFormat

Type alias for supported output formats.

```python
OutputFormat = Literal["yaml", "toml", "markdown", "bash"]
```

Supported formats:
- `yaml`: YAML configuration format
- `toml`: TOML configuration format
- `markdown`: Markdown documentation format
- `bash`: Bash script format

### Classes

#### ModelConfig

Claude model configuration constants.

```python
class ModelConfig:
    """Claude model configuration constants."""
    OPUS: str = "claude-opus-4-20250514"
    SONNET: str = "claude-sonnet-4-20250514"
```

#### GenerationError

Exception raised when AI generation fails.

```python
class GenerationError(Exception):
    """Raised when AI generation fails."""

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
    ) -> None:
        """Initialize GenerationError.

        Args:
            message: Error message describing the failure.
            cause: Optional underlying exception that caused this error.
        """
```

#### PromptTemplateError

Exception raised when prompt template is invalid or malformed.

```python
class PromptTemplateError(Exception):
    """Raised when prompt template is invalid or malformed."""
```

#### GenerationConfig

Configuration for AI generation request.

```python
@dataclass(frozen=True)
class GenerationConfig:
    """Configuration for AI generation request.

    Attributes:
        model: Claude model identifier to use. If None, uses orchestrator default.
        max_tokens: Maximum tokens in response.
        temperature: Sampling temperature (0.0-1.0).
    """

    model: str | None = None
    max_tokens: int = 4096
    temperature: float = 1.0
```

**Example**:
```python
config = GenerationConfig(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    temperature=0.7,
)
```

#### TokenUsage

Token usage information from API response.

```python
@dataclass(frozen=True)
class TokenUsage:
    """Token usage information from API response.

    Attributes:
        input_tokens: Number of tokens in the prompt.
        output_tokens: Number of tokens in the response.
    """

    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used.

        Returns:
            Sum of input and output tokens.
        """
```

#### GenerationResult

Result of an AI generation task.

```python
@dataclass(frozen=True)
class GenerationResult:
    """Result of an AI generation task.

    Attributes:
        content: Generated content from the AI.
        format: Output format of the generated content.
        token_usage: Token usage statistics.
        model: Model identifier used for generation.
        message_id: Unique message identifier from API.
    """

    content: str
    format: OutputFormat
    token_usage: TokenUsage
    model: str
    message_id: str
```

#### AIOrchestrator

Main orchestrator class for AI-powered generation.

```python
class AIOrchestrator:
    """Coordinates AI-powered generation tasks.

    Manages the complete lifecycle of AI-assisted content generation including
    prompt template processing, context injection, API communication, response
    parsing, error handling, and retry logic with exponential backoff.

    Attributes:
        api_key: Anthropic API key for authentication.
        default_model: Default Claude model to use for generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = ModelConfig.OPUS,
        *,
        max_retries: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ) -> None:
        """Initialize AIOrchestrator.

        Args:
            api_key: Anthropic API key. Cannot be empty or whitespace.
            model: Claude model identifier. Defaults to Opus.
            max_retries: Maximum number of retry attempts for failed requests.
                Defaults to 3.
            initial_retry_delay: Initial delay in seconds before first retry.
                Defaults to 1.0.
            max_retry_delay: Maximum delay in seconds between retries.
                Defaults to 60.0.

        Raises:
            ValueError: If api_key is empty or contains only whitespace.
        """
```

##### Methods

**generate()**

```python
async def generate(
    self,
    prompt_template: str,
    context: dict[str, str],
    output_format: OutputFormat,
    *,
    config: GenerationConfig | None = None,
) -> GenerationResult:
    """Generate content using AI with injected context.

    Constructs a prompt from the template and context, sends it to the
    Claude API, and returns the parsed result with metadata.

    Args:
        prompt_template: Prompt template with {variable} placeholders.
        context: Dictionary of variables to inject into template.
        output_format: Desired output format (yaml, toml, markdown, bash).
        config: Generation configuration (model, tokens, temperature).
            Defaults to orchestrator settings if not provided.

    Returns:
        GenerationResult containing generated content and metadata.

    Raises:
        PromptTemplateError: If template is empty or context variables missing.
        ValueError: If output_format is not a valid format.
        GenerationError: If generation fails after all retries.

    Examples:
        >>> result = await orchestrator.generate(
        ...     prompt_template="Write {doc_type} for {project}",
        ...     context={"doc_type": "README", "project": "MyApp"},
        ...     output_format="markdown",
        ... )
        >>> assert result.format == "markdown"
        >>> assert "MyApp" in result.content
    """
```

**tune()**

```python
async def tune(
    self,
    content: str,
    target_context: str,
    model: str = ModelConfig.SONNET,
    *,
    max_tokens: int = 4096,
) -> str:
    """Lightweight tuning pass to adapt content to specific repo.

    Takes existing content and adapts it to match the target repository's
    context, conventions, and requirements. Uses a lighter model by default
    for cost efficiency.

    Args:
        content: Original content to tune.
        target_context: Description of target repository context.
        model: Model to use for tuning. Defaults to Sonnet.
        max_tokens: Maximum tokens in response. Defaults to 4096.

    Returns:
        Tuned content adapted to target context.

    Raises:
        ValueError: If content or target_context is empty.
        GenerationError: If tuning fails after all retries.

    Examples:
        >>> tuned = await orchestrator.tune(
        ...     content="# Generic README\\n...",
        ...     target_context="Python project using pytest and black",
        ... )
        >>> assert "pytest" in tuned or "black" in tuned
    """
```

---

## GitHub Integration Module

### Overview

The GitHub integration module provides classes for managing GitHub repositories, issues, and workflows via the GitHub REST API. It supports token-based authentication and includes comprehensive error handling.

**Module Paths**:
- `start_green_stay_green/github/client.py` - Repository operations
- `start_green_stay_green/github/issues.py` - Issue and milestone management
- `start_green_stay_green/github/actions.py` - Workflow management

### GitHub Client Module (`client.py`)

#### GitHubError

Exception raised when GitHub API operation fails.

```python
class GitHubError(Exception):
    """Raised when GitHub API operation fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize GitHubError.

        Args:
            message: Error message describing the failure.
            status_code: Optional HTTP status code from API response.
            response_data: Optional response data from failed API call.
        """
```

#### RepositoryConfig

Configuration for repository creation.

```python
@dataclass
class RepositoryConfig:
    """Configuration for repository creation.

    Attributes:
        name: Repository name (required, alphanumeric and hyphens).
        description: Repository description (optional).
        is_private: Whether repository is private (default: False).
        include_wiki: Whether to include wiki (default: False).
        include_projects: Whether to include projects (default: False).
        include_discussions: Whether to include discussions (default: False).
    """

    name: str
    description: str | None = None
    is_private: bool = False
    include_wiki: bool = False
    include_projects: bool = False
    include_discussions: bool = False

    def __post_init__(self) -> None:
        """Validate repository configuration.

        Raises:
            ValueError: If name is empty or invalid.
        """
```

**Example**:
```python
config = RepositoryConfig(
    name="my-awesome-project",
    description="An awesome project",
    is_private=False,
    include_wiki=True,
)
```

#### GitHubClient

GitHub API client for repository operations.

```python
class GitHubClient:
    """GitHub API client for repository operations.

    Provides methods for authenticating with GitHub, creating and configuring
    repositories, and managing branch protection rules via the GitHub REST API.

    Attributes:
        token: GitHub personal access token for authentication.
        base_url: GitHub API base URL (default: https://api.github.com).
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.github.com",
    ) -> None:
        """Initialize GitHubClient.

        Args:
            token: GitHub personal access token. Cannot be empty.
            base_url: Base URL for GitHub API. Defaults to GitHub.com API.

        Raises:
            ValueError: If token is empty or contains only whitespace.
        """
```

##### Methods

**verify_token()**

```python
def verify_token(self) -> bool:
    """Verify that the GitHub token is valid.

    Attempts to authenticate with the GitHub API to verify that
    the provided token has valid credentials.

    Returns:
        True if token is valid, False otherwise.
    """
```

**get_authenticated_user()**

```python
def get_authenticated_user(self) -> dict[str, Any]:
    """Get information about the authenticated user.

    Retrieves user profile information for the authenticated account.

    Returns:
        Dictionary containing authenticated user information.

    Raises:
        GitHubError: If API request fails.
    """
```

**create_repository()**

```python
def create_repository(
    self,
    config: RepositoryConfig,
) -> dict[str, Any]:
    """Create a new GitHub repository.

    Creates a new repository with the specified configuration.
    Requires 'public_repo' or 'repo' scope in GitHub token.

    Args:
        config: Repository configuration.

    Returns:
        Dictionary containing created repository information.

    Raises:
        GitHubError: If repository creation fails.

    Examples:
        >>> client = GitHubClient(token="ghp_...")
        >>> config = RepositoryConfig(
        ...     name="my-repo",
        ...     description="My repository",
        ...     is_private=False,
        ... )
        >>> repo = client.create_repository(config)
        >>> print(repo["full_name"])
    """
```

**get_repository()**

```python
def get_repository(
    self,
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """Get information about a repository.

    Retrieves metadata and configuration for a specific repository.

    Args:
        owner: Repository owner (username or organization).
        repo: Repository name.

    Returns:
        Dictionary containing repository information.

    Raises:
        GitHubError: If repository cannot be found or access is denied.
    """
```

**set_branch_protection()**

```python
def set_branch_protection(
    self,
    owner: str,
    repo: str,
    branch: str,
    *,
    required_status_checks: dict[str, Any] | None = None,
    dismiss_stale_reviews: bool = False,
    require_code_owner_reviews: bool = False,
    required_approving_review_count: int = 0,
) -> dict[str, Any]:
    """Configure branch protection rules.

    Sets up branch protection rules including required status checks,
    review requirements, and other protection settings.

    Args:
        owner: Repository owner.
        repo: Repository name.
        branch: Branch name to protect (e.g., "main").
        required_status_checks: Status checks configuration dict with
            'strict' (bool) and 'contexts' (list) keys. Defaults to None.
        dismiss_stale_reviews: Whether to dismiss stale reviews.
            Defaults to False.
        require_code_owner_reviews: Whether to require code owner reviews.
            Defaults to False.
        required_approving_review_count: Number of required approvals.
            Defaults to 0.

    Returns:
        Dictionary containing branch protection configuration.

    Raises:
        GitHubError: If branch protection cannot be configured.

    Examples:
        >>> client = GitHubClient(token="ghp_...")
        >>> client.set_branch_protection(
        ...     owner="myorg",
        ...     repo="my-repo",
        ...     branch="main",
        ...     required_status_checks={
        ...         "strict": True,
        ...         "contexts": ["ci/build"],
        ...     },
        ...     require_code_owner_reviews=True,
        ...     required_approving_review_count=1,
        ... )
    """
```

### GitHub Issues Module (`issues.py`)

#### GitHubIssueError

Exception raised when GitHub Issues API operation fails.

```python
class GitHubIssueError(Exception):
    """Raised when GitHub Issues API operation fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        """Initialize GitHubIssueError."""
```

#### IssueConfig

Configuration for issue creation.

```python
@dataclass
class IssueConfig:
    """Configuration for issue creation.

    Attributes:
        title: Issue title (required).
        body: Issue description/body (required).
        labels: List of label names to apply (optional).
        milestone: Milestone number to associate (optional).
        assignees: List of usernames to assign (optional).
    """

    title: str
    body: str
    labels: list[str] | None = None
    milestone: int | None = None
    assignees: list[str] | None = None
```

#### MilestoneConfig

Configuration for milestone (epic) creation.

```python
@dataclass
class MilestoneConfig:
    """Configuration for milestone (epic) creation.

    Attributes:
        title: Milestone title (required).
        description: Milestone description (optional).
        due_date: Due date in YYYY-MM-DD format (optional).
    """

    title: str
    description: str | None = None
    due_date: str | None = None
```

#### GitHubIssueManager

GitHub issue and milestone manager.

```python
class GitHubIssueManager:
    """GitHub issue and milestone manager.

    Provides methods for managing GitHub issues, milestones (epics),
    and labels. Supports creating issues from specifications and
    bulk operations.

    Attributes:
        token: GitHub personal access token for authentication.
        base_url: GitHub API base URL (default: https://api.github.com).
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.github.com",
    ) -> None:
        """Initialize GitHubIssueManager."""
```

##### Methods

**create_issue()**

```python
def create_issue(
    self,
    owner: str,
    repo: str,
    issue: IssueConfig,
) -> dict[str, Any]:
    """Create a new GitHub issue.

    Creates a new issue in the specified repository with the
    provided configuration.

    Args:
        owner: Repository owner.
        repo: Repository name.
        issue: Issue configuration.

    Returns:
        Dictionary containing created issue information.

    Raises:
        GitHubIssueError: If issue creation fails.

    Examples:
        >>> manager = GitHubIssueManager(token="ghp_...")
        >>> issue = IssueConfig(
        ...     title="Bug: Login fails",
        ...     body="User cannot log in with email",
        ...     labels=["type: bug", "priority: high"],
        ... )
        >>> result = manager.create_issue("myorg", "my-repo", issue)
        >>> print(result["number"])
    """
```

**get_issue()**

```python
def get_issue(
    self,
    owner: str,
    repo: str,
    issue_number: int,
) -> dict[str, Any]:
    """Get information about a specific issue.

    Retrieves metadata for an issue including comments, labels,
    and assignees.

    Args:
        owner: Repository owner.
        repo: Repository name.
        issue_number: Issue number.

    Returns:
        Dictionary containing issue information.

    Raises:
        GitHubIssueError: If issue cannot be found.
    """
```

**list_issues()**

```python
def list_issues(
    self,
    owner: str,
    repo: str,
    *,
    state: str = "open",
    labels: list[str] | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """List issues in a repository.

    Retrieves issues from a repository with optional filtering
    by state and labels.

    Args:
        owner: Repository owner.
        repo: Repository name.
        state: Issue state (open, closed, all). Defaults to "open".
        labels: Optional list of label names to filter by.
        limit: Maximum number of issues to return. Defaults to 30.

    Returns:
        List of issue dictionaries.

    Raises:
        GitHubIssueError: If issues cannot be retrieved.
    """
```

**create_milestone()**

```python
def create_milestone(
    self,
    owner: str,
    repo: str,
    milestone: MilestoneConfig,
) -> dict[str, Any]:
    """Create a new milestone (epic).

    Creates a new milestone in the repository. Milestones are used
    to group related issues and track progress.

    Args:
        owner: Repository owner.
        repo: Repository name.
        milestone: Milestone configuration.

    Returns:
        Dictionary containing created milestone information.

    Raises:
        GitHubIssueError: If milestone creation fails.

    Examples:
        >>> manager = GitHubIssueManager(token="ghp_...")
        >>> milestone = MilestoneConfig(
        ...     title="Epic 1: Core Features",
        ...     description="Implement core features",
        ...     due_date="2024-06-30",
        ... )
        >>> result = manager.create_milestone("myorg", "my-repo", milestone)
        >>> print(result["number"])
    """
```

**get_milestone()**

```python
def get_milestone(
    self,
    owner: str,
    repo: str,
    milestone_number: int,
) -> dict[str, Any]:
    """Get information about a specific milestone.

    Retrieves metadata for a milestone including progress and due date.

    Args:
        owner: Repository owner.
        repo: Repository name.
        milestone_number: Milestone number.

    Returns:
        Dictionary containing milestone information.

    Raises:
        GitHubIssueError: If milestone cannot be found.
    """
```

**list_milestones()**

```python
def list_milestones(
    self,
    owner: str,
    repo: str,
    *,
    state: str = "open",
    limit: int = 30,
) -> list[dict[str, Any]]:
    """List milestones in a repository.

    Retrieves all milestones from a repository with optional
    state filtering.

    Args:
        owner: Repository owner.
        repo: Repository name.
        state: Milestone state (open, closed, all). Defaults to "open".
        limit: Maximum number of milestones to return. Defaults to 30.

    Returns:
        List of milestone dictionaries.

    Raises:
        GitHubIssueError: If milestones cannot be retrieved.
    """
```

**create_label()**

```python
def create_label(
    self,
    owner: str,
    repo: str,
    name: str,
    color: str,
    description: str | None = None,
) -> dict[str, Any]:
    """Create a new label.

    Creates a new label that can be applied to issues and pull requests.

    Args:
        owner: Repository owner.
        repo: Repository name.
        name: Label name.
        color: Label color (6-character hex code, no #).
        description: Optional label description.

    Returns:
        Dictionary containing created label information.

    Raises:
        GitHubIssueError: If label creation fails.

    Examples:
        >>> manager = GitHubIssueManager(token="ghp_...")
        >>> label = manager.create_label(
        ...     owner="myorg",
        ...     repo="my-repo",
        ...     name="type: feature",
        ...     color="0366d6",
        ...     description="Feature request",
        ... )
        >>> print(label["name"])
    """
```

**list_labels()**

```python
def list_labels(
    self,
    owner: str,
    repo: str,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    """List all labels in a repository.

    Retrieves all labels that can be applied to issues and
    pull requests in a repository.

    Args:
        owner: Repository owner.
        repo: Repository name.
        limit: Maximum number of labels to return. Defaults to 30.

    Returns:
        List of label dictionaries.

    Raises:
        GitHubIssueError: If labels cannot be retrieved.
    """
```

### GitHub Actions Module (`actions.py`)

#### GitHubActionsError

Exception raised when GitHub Actions API operation fails.

```python
class GitHubActionsError(Exception):
    """Raised when GitHub Actions API operation fails."""
```

#### WorkflowConfig

Configuration for workflow operations.

```python
@dataclass
class WorkflowConfig:
    """Configuration for workflow operations.

    Attributes:
        name: Workflow name (required).
        file_path: Path to workflow YAML file (e.g., .github/workflows/ci.yml).
        description: Workflow description (optional).
    """

    name: str
    file_path: str | None = None
    description: str | None = None
```

#### GitHubActionsManager

GitHub Actions workflow manager.

```python
class GitHubActionsManager:
    """GitHub Actions workflow manager.

    Provides methods for managing GitHub Actions workflows including
    triggering runs, listing workflows, and retrieving run status.

    Attributes:
        token: GitHub personal access token for authentication.
        base_url: GitHub API base URL (default: https://api.github.com).
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = "https://api.github.com",
    ) -> None:
        """Initialize GitHubActionsManager."""
```

##### Methods

**get_workflow()**

```python
def get_workflow(
    self,
    owner: str,
    repo: str,
    workflow_id: int | str,
) -> dict[str, Any]:
    """Get information about a workflow.

    Retrieves metadata for a specific workflow by ID or filename.

    Args:
        owner: Repository owner.
        repo: Repository name.
        workflow_id: Workflow ID or filename (e.g., "ci.yml").

    Returns:
        Dictionary containing workflow information.

    Raises:
        GitHubActionsError: If workflow cannot be found.
    """
```

**list_workflows()**

```python
def list_workflows(
    self,
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """List all workflows in a repository.

    Retrieves all workflows defined in a repository.

    Args:
        owner: Repository owner.
        repo: Repository name.

    Returns:
        Dictionary containing list of workflows.

    Raises:
        GitHubActionsError: If workflows cannot be retrieved.
    """
```

**trigger_workflow()**

```python
def trigger_workflow(
    self,
    owner: str,
    repo: str,
    workflow_id: int | str,
    ref: str,
    *,
    inputs: dict[str, Any] | None = None,
) -> bool:
    """Trigger a workflow run.

    Triggers a new run of the specified workflow on the given branch
    or tag, optionally passing input values.

    Args:
        owner: Repository owner.
        repo: Repository name.
        workflow_id: Workflow ID or filename.
        ref: Git reference (branch or tag name).
        inputs: Optional input values for the workflow.

    Returns:
        True if workflow was triggered successfully, False otherwise.

    Examples:
        >>> manager = GitHubActionsManager(token="ghp_...")
        >>> manager.trigger_workflow(
        ...     owner="myorg",
        ...     repo="my-repo",
        ...     workflow_id="ci.yml",
        ...     ref="main",
        ...     inputs={"debug": "true"},
        ... )
    """
```

**list_workflow_runs()**

```python
def list_workflow_runs(
    self,
    owner: str,
    repo: str,
    workflow_id: int | str,
    *,
    status: str | None = None,
    conclusion: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    """List workflow runs for a specific workflow.

    Retrieves runs for a workflow, optionally filtered by status or conclusion.

    Args:
        owner: Repository owner.
        repo: Repository name.
        workflow_id: Workflow ID or filename.
        status: Optional status filter (queued, in_progress, completed).
        conclusion: Optional conclusion filter (success, failure, etc.).
        limit: Maximum number of runs to return. Defaults to 30.

    Returns:
        Dictionary containing list of workflow runs.

    Raises:
        GitHubActionsError: If runs cannot be retrieved.
    """
```

**get_workflow_run()**

```python
def get_workflow_run(
    self,
    owner: str,
    repo: str,
    run_id: int,
) -> dict[str, Any]:
    """Get information about a specific workflow run.

    Retrieves detailed information about a workflow run including
    status, conclusion, and timestamps.

    Args:
        owner: Repository owner.
        repo: Repository name.
        run_id: Workflow run ID.

    Returns:
        Dictionary containing workflow run information.

    Raises:
        GitHubActionsError: If run cannot be found.
    """
```

---

## Common Patterns

### Initialization Pattern

All client classes follow a consistent initialization pattern:

```python
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.github.client import GitHubClient
from start_green_stay_green.github.issues import GitHubIssueManager

# Initialize AI orchestrator
orchestrator = AIOrchestrator(api_key="sk-...")

# Initialize GitHub client
github_client = GitHubClient(token="ghp_...")

# Initialize issue manager
issue_manager = GitHubIssueManager(token="ghp_...")
```

### Configuration Pattern

Configuration is handled through dataclasses with validation:

```python
from start_green_stay_green.github.client import RepositoryConfig
from start_green_stay_green.github.issues import IssueConfig

# Repository configuration
repo_config = RepositoryConfig(
    name="my-repo",
    description="My awesome repository",
    is_private=False,
)

# Issue configuration
issue_config = IssueConfig(
    title="Implement feature X",
    body="Description of feature X",
    labels=["type: feature"],
)
```

### Async/Await Pattern

AI orchestration uses async/await for non-blocking API calls:

```python
import asyncio

async def generate_documentation():
    orchestrator = AIOrchestrator(api_key="sk-...")

    result = await orchestrator.generate(
        prompt_template="Create documentation for {project}",
        context={"project": "MyProject"},
        output_format="markdown",
    )

    return result.content

# Run async function
content = asyncio.run(generate_documentation())
```

### Error Handling Pattern

All API calls should be wrapped in try-except blocks:

```python
from start_green_stay_green.github.client import GitHubClient, GitHubError

client = GitHubClient(token="ghp_...")

try:
    user = client.get_authenticated_user()
except GitHubError as e:
    print(f"GitHub API error: {e}")
    if e.status_code == 401:
        print("Invalid or expired token")
```

---

## Error Handling

### Exception Hierarchy

```
Exception
├── GenerationError (AI orchestration)
├── PromptTemplateError (AI orchestration)
├── GitHubError (Repository operations)
├── GitHubIssueError (Issue/milestone operations)
└── GitHubActionsError (Workflow operations)
```

### Error Context

All GitHub exceptions include status codes and response data for debugging:

```python
try:
    repo = client.create_repository(config)
except GitHubError as e:
    print(f"Status: {e.status_code}")
    print(f"Message: {e}")
    if e.response_data:
        print(f"Details: {e.response_data}")
```

---

## Examples

### Complete AI Generation Workflow

```python
import asyncio
from start_green_stay_green.ai.orchestrator import (
    AIOrchestrator,
    GenerationConfig,
    ModelConfig,
)

async def generate_readme():
    """Generate a README for a Python project."""

    # Initialize orchestrator
    orchestrator = AIOrchestrator(
        api_key="sk-ant-...",
        model=ModelConfig.OPUS,
        max_retries=3,
    )

    # Generate README
    result = await orchestrator.generate(
        prompt_template=(
            "Create a comprehensive README for a {language} "
            "project called {project_name}. "
            "The project is about {description}."
        ),
        context={
            "language": "Python",
            "project_name": "DataAnalyzer",
            "description": "analyzing and visualizing data",
        },
        output_format="markdown",
        config=GenerationConfig(
            model=ModelConfig.OPUS,
            max_tokens=4096,
            temperature=1.0,
        ),
    )

    print(f"Generated {result.format} content")
    print(f"Tokens used: {result.token_usage.total_tokens}")
    return result.content

# Run the workflow
readme_content = asyncio.run(generate_readme())
print(readme_content)
```

### Complete GitHub Repository Setup

```python
from start_green_stay_green.github.client import GitHubClient, RepositoryConfig
from start_green_stay_green.github.issues import GitHubIssueManager, IssueConfig

def setup_repository():
    """Set up a new GitHub repository with issues and labels."""

    # Initialize clients
    github_client = GitHubClient(token="ghp_...")
    issue_manager = GitHubIssueManager(token="ghp_...")

    # Create repository
    repo_config = RepositoryConfig(
        name="my-new-project",
        description="My new project",
        is_private=False,
    )
    repo = github_client.create_repository(repo_config)
    owner = repo["owner"]["login"]
    repo_name = repo["name"]

    # Create labels
    issue_manager.create_label(
        owner=owner,
        repo=repo_name,
        name="type: bug",
        color="d73a4a",
        description="Something isn't working",
    )

    issue_manager.create_label(
        owner=owner,
        repo=repo_name,
        name="type: feature",
        color="a2eeef",
        description="New feature",
    )

    # Create initial issue
    issue_config = IssueConfig(
        title="Initial setup",
        body="Set up the repository structure",
        labels=["type: feature"],
    )
    issue = issue_manager.create_issue(owner, repo_name, issue_config)

    return repo, issue

repo_info, issue_info = setup_repository()
print(f"Created {repo_info['full_name']}")
print(f"Initial issue #{issue_info['number']}")
```

### Combined Workflow: Generate and Deploy

```python
import asyncio
from start_green_stay_green.ai.orchestrator import AIOrchestrator
from start_green_stay_green.github.client import GitHubClient, RepositoryConfig

async def generate_and_deploy():
    """Generate documentation and deploy to GitHub."""

    # Generate documentation
    orchestrator = AIOrchestrator(api_key="sk-...")
    result = await orchestrator.generate(
        prompt_template="Create comprehensive API docs for {project}",
        context={"project": "MyLibrary"},
        output_format="markdown",
    )

    # Create repository
    github_client = GitHubClient(token="ghp_...")
    repo_config = RepositoryConfig(
        name="my-library-docs",
        description="API Documentation",
    )
    repo = github_client.create_repository(repo_config)

    # Configure branch protection
    github_client.set_branch_protection(
        owner=repo["owner"]["login"],
        repo=repo["name"],
        branch="main",
        required_status_checks={
            "strict": True,
            "contexts": ["ci/build"],
        },
        require_code_owner_reviews=True,
        required_approving_review_count=1,
    )

    return result.content

content = asyncio.run(generate_and_deploy())
```

---

## Type Hints and Validation

All APIs use strict type hints and validation:

- All public functions have complete type hints (no `Any` unless documented)
- Configuration dataclasses validate input on instantiation
- Errors are specific and informative
- Documentation examples are executable

---

## Best Practices

1. **Always handle exceptions** - Every API call can fail
2. **Validate tokens before use** - Use `verify_token()` for GitHub clients
3. **Use configuration objects** - Leverage dataclasses for safety
4. **Respect rate limits** - Implement appropriate delays for batch operations
5. **Log important operations** - All clients log via Python logging module

---

**Last Updated**: 2026-01-12
**API Version**: 1.0
