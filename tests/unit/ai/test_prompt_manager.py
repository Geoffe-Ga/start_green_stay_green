"""Unit tests for prompt template manager."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from start_green_stay_green.ai.prompts.manager import PromptManager
from start_green_stay_green.ai.prompts.manager import PromptTemplateError


class TestPromptManagerInitialization:
    """Test PromptManager initialization."""

    def test_init_with_default_directory(self) -> None:
        """Test PromptManager initializes with default template directory."""
        manager = PromptManager()
        assert manager.template_dir.exists()
        assert manager.template_dir.name == "templates"

    def test_init_with_custom_directory(self, tmp_path: Path) -> None:
        """Test PromptManager accepts custom template directory."""
        # Create templates directory
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        manager = PromptManager(template_dir=templates_dir)
        assert manager.template_dir == templates_dir

    def test_init_with_nonexistent_directory_raises_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Test PromptManager raises error for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(
            PromptTemplateError,
            match="Prompt template directory not found",
        ):
            PromptManager(template_dir=nonexistent)

    def test_init_creates_jinja2_environment(self) -> None:
        """Test PromptManager initializes Jinja2 environment."""
        manager = PromptManager()
        assert manager._env is not None
        assert manager._env.loader is not None

    def test_init_creates_empty_template_cache(self) -> None:
        """Test PromptManager initializes empty template cache."""
        manager = PromptManager()
        assert manager._template_cache == {}
        assert isinstance(manager._template_cache, dict)

    def test_init_supported_languages_constant(self) -> None:
        """Test SUPPORTED_LANGUAGES constant is properly defined."""
        assert PromptManager.SUPPORTED_LANGUAGES == {
            "python",
            "typescript",
            "go",
            "rust",
            "swift",
            "java",
        }

    def test_init_supported_template_types_constant(self) -> None:
        """Test SUPPORTED_TEMPLATE_TYPES constant is properly defined."""
        assert PromptManager.SUPPORTED_TEMPLATE_TYPES == {
            "ci_cd",
            "precommit",
            "quality_scripts",
            "claude_md",
            "project_scaffolding",
        }


class TestPromptManagerRender:
    """Test PromptManager render functionality."""

    def test_render_basic_template(self, tmp_path: Path) -> None:
        """Test rendering a basic template with context."""
        # Create template directory and file
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "test.jinja2"
        template_file.write_text("Hello {{ name }}")

        manager = PromptManager(template_dir=templates_dir)
        result = manager.render("test", {"name": "World"})

        assert result == "Hello World"

    def test_render_with_multiple_variables(self, tmp_path: Path) -> None:
        """Test rendering template with multiple variables."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "greeting.jinja2"
        template_file.write_text("{{ greeting }}, {{ name }}!")

        manager = PromptManager(template_dir=templates_dir)
        result = manager.render(
            "greeting",
            {"greeting": "Hello", "name": "Alice"},
        )

        assert result == "Hello, Alice!"

    def test_render_with_language_variant(self, tmp_path: Path) -> None:
        """Test rendering template with language variant."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create language-specific template
        template_file = templates_dir / "config.python.jinja2"
        template_file.write_text("Python config: {{ setting }}")

        manager = PromptManager(template_dir=templates_dir)
        result = manager.render(
            "config",
            {"setting": "debug"},
            language="python",
        )

        assert result == "Python config: debug"

    def test_render_nonexistent_template_raises_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Test rendering nonexistent template raises error."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        manager = PromptManager(template_dir=templates_dir)

        with pytest.raises(
            PromptTemplateError,
            match="Prompt template not found",
        ):
            manager.render("nonexistent", {})

    def test_render_unsupported_language_raises_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Test rendering with unsupported language raises error."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "config.jinja2"
        template_file.write_text("Config")

        manager = PromptManager(template_dir=templates_dir)

        with pytest.raises(
            ValueError,
            match="Unsupported language",
        ):
            manager.render("config", {}, language="cobol")

    def test_render_empty_result_raises_error(self, tmp_path: Path) -> None:
        """Test rendering to empty content raises error."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create template that renders to empty string
        template_file = templates_dir / "empty.jinja2"
        template_file.write_text("{% if false %}content{% endif %}")

        manager = PromptManager(template_dir=templates_dir)

        with pytest.raises(
            PromptTemplateError,
            match="rendered to empty content",
        ):
            manager.render("empty", {})

    def test_render_caches_templates(self, tmp_path: Path) -> None:
        """Test templates are cached after first render."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "cached.jinja2"
        template_file.write_text("Content: {{ value }}")

        manager = PromptManager(template_dir=templates_dir)

        # First render
        manager.render("cached", {"value": "first"})
        assert "cached.jinja2" in manager._template_cache

        # Modify template file (shouldn't affect next render due to cache)
        template_file.write_text("Modified: {{ value }}")

        # Second render should use cached version
        result = manager.render("cached", {"value": "second"})
        assert result == "Content: second"

    def test_render_with_conditional_logic(self, tmp_path: Path) -> None:
        """Test rendering template with conditional logic."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "conditional.jinja2"
        template_file.write_text(
            "{% if debug %}Debug: {{ msg }}{% else %}Release{% endif %}"
        )

        manager = PromptManager(template_dir=templates_dir)

        # Test with debug=true
        result = manager.render("conditional", {"debug": True, "msg": "Testing"})
        assert result == "Debug: Testing"

        # Test with debug=false
        result = manager.render("conditional", {"debug": False})
        assert result == "Release"

    def test_render_with_loops(self, tmp_path: Path) -> None:
        """Test rendering template with loops."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "loop.jinja2"
        template_file.write_text(
            "{% for item in items %}{{ item }}\n{% endfor %}"
        )

        manager = PromptManager(template_dir=templates_dir)
        result = manager.render("loop", {"items": ["a", "b", "c"]})

        assert "a" in result
        assert "b" in result
        assert "c" in result


class TestPromptManagerTemplateDiscovery:
    """Test template discovery and listing."""

    def test_get_available_templates(self, tmp_path: Path) -> None:
        """Test getting list of available templates."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create multiple templates
        (templates_dir / "ci_cd.jinja2").write_text("CI/CD")
        (templates_dir / "precommit.jinja2").write_text("Pre-commit")
        (templates_dir / "quality_scripts.jinja2").write_text("Scripts")

        manager = PromptManager(template_dir=templates_dir)
        available = manager.get_available_templates()

        assert len(available) == 3
        assert "ci_cd" in available
        assert "precommit" in available
        assert "quality_scripts" in available

    def test_get_available_templates_excludes_language_variants(
        self,
        tmp_path: Path,
    ) -> None:
        """Test language variants are deduplicated in listing."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create base and language-specific versions
        (templates_dir / "config.jinja2").write_text("Default")
        (templates_dir / "config.python.jinja2").write_text("Python")
        (templates_dir / "config.typescript.jinja2").write_text("TypeScript")

        manager = PromptManager(template_dir=templates_dir)
        available = manager.get_available_templates()

        # Should only list "config" once, not three times
        assert available.count("config") == 1

    def test_get_available_templates_empty_directory(
        self,
        tmp_path: Path,
    ) -> None:
        """Test empty template directory returns empty list."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        manager = PromptManager(template_dir=templates_dir)
        available = manager.get_available_templates()

        assert available == []

    def test_validate_template_existing(self, tmp_path: Path) -> None:
        """Test validate_template returns True for existing template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "valid.jinja2"
        template_file.write_text("Valid template")

        manager = PromptManager(template_dir=templates_dir)
        assert manager.validate_template("valid") is True

    def test_validate_template_nonexistent(self, tmp_path: Path) -> None:
        """Test validate_template returns False for nonexistent template."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        manager = PromptManager(template_dir=templates_dir)
        assert manager.validate_template("nonexistent") is False


class TestPromptManagerCacheManagement:
    """Test template cache management."""

    def test_clear_cache(self, tmp_path: Path) -> None:
        """Test clearing template cache."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "test.jinja2"
        template_file.write_text("Test")

        manager = PromptManager(template_dir=templates_dir)

        # Render to populate cache
        manager.render("test", {})
        assert len(manager._template_cache) > 0

        # Clear cache
        manager.clear_cache()
        assert manager._template_cache == {}

    def test_cache_prevents_repeated_loading(self, tmp_path: Path) -> None:
        """Test cache prevents repeated template loading."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "cached.jinja2"
        template_file.write_text("{{ value }}")

        manager = PromptManager(template_dir=templates_dir)

        # Render twice
        manager.render("cached", {"value": "v1"})
        manager.render("cached", {"value": "v2"})

        # Cache should have only one entry
        cache_entries = [k for k in manager._template_cache.keys() if "cached" in k]
        assert len(cache_entries) == 1


class TestPromptManagerErrorHandling:
    """Test error handling and edge cases."""

    def test_render_with_syntax_error_raises_prompt_template_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Test template with syntax error raises PromptTemplateError."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "syntax_error.jinja2"
        # Invalid Jinja2 syntax
        template_file.write_text("{% if unterminated")

        manager = PromptManager(template_dir=templates_dir)

        with pytest.raises(PromptTemplateError):
            manager.render("syntax_error", {})

    def test_render_with_undefined_variable_raises_error(
        self,
        tmp_path: Path,
    ) -> None:
        """Test template with undefined variable raises error."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "undefined.jinja2"
        template_file.write_text("{{ undefined_var }}")

        manager = PromptManager(template_dir=templates_dir)

        with pytest.raises(PromptTemplateError):
            manager.render("undefined", {})

    def test_init_nonexistent_directory_error_message(
        self,
        tmp_path: Path,
    ) -> None:
        """Test error message is clear for nonexistent directory."""
        nonexistent = tmp_path / "nonexistent" / "path"

        with pytest.raises(PromptTemplateError) as exc_info:
            PromptManager(template_dir=nonexistent)

        error_msg = str(exc_info.value)
        assert "nonexistent" in error_msg
        assert "not found" in error_msg

    def test_render_language_validation_message(self, tmp_path: Path) -> None:
        """Test language validation provides helpful error message."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "test.jinja2"
        template_file.write_text("Test")

        manager = PromptManager(template_dir=templates_dir)

        with pytest.raises(ValueError) as exc_info:
            manager.render("test", {}, language="invalid_lang")

        error_msg = str(exc_info.value)
        assert "invalid_lang" in error_msg
        assert "Supported" in error_msg


class TestPromptManagerRealTemplates:
    """Test with actual template files."""

    def test_actual_ci_cd_template_exists(self) -> None:
        """Test actual CI/CD template file exists."""
        manager = PromptManager()
        assert manager.validate_template("ci_cd")

    def test_actual_precommit_template_exists(self) -> None:
        """Test actual pre-commit template file exists."""
        manager = PromptManager()
        assert manager.validate_template("precommit")

    def test_actual_quality_scripts_template_exists(self) -> None:
        """Test actual quality scripts template file exists."""
        manager = PromptManager()
        assert manager.validate_template("quality_scripts")

    def test_actual_claude_md_template_exists(self) -> None:
        """Test actual CLAUDE.md template file exists."""
        manager = PromptManager()
        assert manager.validate_template("claude_md")

    def test_actual_project_scaffolding_template_exists(self) -> None:
        """Test actual project scaffolding template file exists."""
        manager = PromptManager()
        assert manager.validate_template("project_scaffolding")

    def test_render_ci_cd_template_basic(self) -> None:
        """Test rendering CI/CD template with basic context."""
        manager = PromptManager()
        result = manager.render(
            "ci_cd",
            {
                "project_name": "Test Project",
                "language": "python",
                "purpose": "Testing",
                "python_version": "3.11",
                "package_manager": "pip",
            },
        )

        assert "Test Project" in result
        assert "python" in result
        assert len(result) > 100

    def test_render_precommit_template_basic(self) -> None:
        """Test rendering pre-commit template with basic context."""
        manager = PromptManager()
        result = manager.render(
            "precommit",
            {
                "project_name": "Test Project",
                "language": "python",
                "purpose": "Testing",
                "project_type": "library",
            },
        )

        assert "Test Project" in result
        assert "python" in result
        assert len(result) > 100

    def test_render_quality_scripts_template_basic(self) -> None:
        """Test rendering quality scripts template with basic context."""
        manager = PromptManager()
        result = manager.render(
            "quality_scripts",
            {
                "project_name": "Test Project",
                "language": "python",
                "purpose": "Testing",
                "test_framework": "pytest",
                "src_dir": "src",
            },
        )

        assert "Test Project" in result
        assert "python" in result
        assert len(result) > 100

    def test_render_claude_md_template_basic(self) -> None:
        """Test rendering CLAUDE.md template with basic context."""
        manager = PromptManager()
        result = manager.render(
            "claude_md",
            {
                "project_name": "Test Project",
                "language": "python",
                "purpose": "Testing",
                "repo_url": "https://github.com/test/project",
                "package_name": "test_project",
            },
        )

        assert "Test Project" in result
        assert "python" in result
        assert len(result) > 100

    def test_render_project_scaffolding_template_basic(self) -> None:
        """Test rendering project scaffolding template with basic context."""
        manager = PromptManager()
        result = manager.render(
            "project_scaffolding",
            {
                "project_name": "Test Project",
                "language": "python",
                "purpose": "Testing",
                "project_type": "library",
                "use_case": "General",
                "package_name": "test_project",
                "license": "MIT",
            },
        )

        assert "Test Project" in result
        assert "python" in result
        assert len(result) > 100


class TestPromptTemplateError:
    """Test PromptTemplateError exception."""

    def test_prompt_template_error_is_exception(self) -> None:
        """Test PromptTemplateError is an Exception."""
        error = PromptTemplateError("Test error")
        assert isinstance(error, Exception)

    def test_prompt_template_error_message(self) -> None:
        """Test PromptTemplateError stores message."""
        msg = "Template not found: test.jinja2"
        error = PromptTemplateError(msg)
        assert str(error) == msg

    def test_prompt_template_error_with_cause(self) -> None:
        """Test PromptTemplateError can have underlying cause."""
        cause = FileNotFoundError("File not found")
        error = PromptTemplateError("Failed to load", )
        # Standard exception chaining
        error.__cause__ = cause
        assert error.__cause__ is cause


class TestPromptManagerLanguageVariants:
    """Test language variant template selection."""

    def test_render_language_variant_preferred_over_base(
        self,
        tmp_path: Path,
    ) -> None:
        """Test language variant is preferred when available."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create both base and language-specific versions
        (templates_dir / "config.jinja2").write_text("Default config")
        (templates_dir / "config.python.jinja2").write_text(
            "Python-specific config"
        )

        manager = PromptManager(template_dir=templates_dir)

        # Render with language variant
        result = manager.render("config", {}, language="python")
        assert result == "Python-specific config"

    def test_render_falls_back_to_base_if_variant_not_found(
        self,
        tmp_path: Path,
    ) -> None:
        """Test falls back to base template if variant not found."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        # Create only base template
        (templates_dir / "config.jinja2").write_text("Default config")

        manager = PromptManager(template_dir=templates_dir)

        # Request variant that doesn't exist
        # This should raise because config.python.jinja2 doesn't exist
        with pytest.raises(PromptTemplateError):
            manager.render("config", {}, language="python")

    def test_all_supported_languages_are_valid(self) -> None:
        """Test all supported languages are in the constant."""
        expected = {"python", "typescript", "go", "rust", "swift", "java"}
        assert PromptManager.SUPPORTED_LANGUAGES == expected

    def test_render_with_each_supported_language(self, tmp_path: Path) -> None:
        """Test rendering with each supported language (base template)."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "test.jinja2"
        template_file.write_text("Test template")

        manager = PromptManager(template_dir=templates_dir)

        # All supported languages should work with base template
        for lang in PromptManager.SUPPORTED_LANGUAGES:
            # Create language-specific template for this test
            lang_template = templates_dir / f"test.{lang}.jinja2"
            lang_template.write_text(f"Test for {lang}")

            result = manager.render("test", {}, language=lang)
            assert f"Test for {lang}" in result
