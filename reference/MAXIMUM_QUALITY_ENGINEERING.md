# Maximum Quality Engineering Framework for AI-Driven Development

> *"Zero is a hard number. If that by itself leads you to discount the attempt to reduce your project's number, since we won't reach zero anyway, there is something wrong with your philosophy of software development."*
> — Bjarke Hammersholt Roune, former TPUv3 Software Lead at Google

## Preamble: The AI Developer Advantage

Unlike human developers, Claude Code does not experience fatigue, impatience, or the psychological resistance to "tedious" quality work. Claude can write comprehensive tests in seconds, implement full linting suites without complaint, and enforce architectural boundaries without cutting corners. This framework is designed to leverage that advantage: **maximum rigor without compromise**.

**Core Principles:**
- **ABAT**: Always Be Adding Tests
- **ABP**: Always Be Profiling
- **ATTAM**: Always Try To Acquire (quality) Measures
- **No shortcuts. No exceptions. No "we'll add that later."**

---

## Part 1: Project Initialization Checklist

When starting any new project, Claude Code MUST implement ALL of the following before writing any business logic. This is non-negotiable.

### 1.1 Repository Structure Enforcement

```
project-root/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                    # Continuous Integration
│   │   ├── cd.yml                    # Continuous Deployment
│   │   ├── security.yml              # Security scanning
│   │   ├── dependency-review.yml     # Dependency audits
│   │   └── codeql.yml               # Static analysis
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── CODEOWNERS
├── .husky/
│   ├── pre-commit
│   ├── pre-push
│   ├── commit-msg
│   └── prepare-commit-msg
├── .vscode/
│   └── settings.json                 # Enforced editor settings
├── config/
│   ├── eslint/
│   ├── prettier/
│   ├── jest/
│   └── typescript/
├── scripts/
│   ├── quality/
│   │   ├── check-all.sh
│   │   ├── fix-all.sh
│   │   └── audit-dependencies.sh
│   └── hooks/
├── src/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   ├── property/
│   ├── mutation/
│   ├── snapshot/
│   ├── performance/
│   └── fixtures/
├── docs/
│   ├── architecture/
│   │   ├── ADR/                      # Architecture Decision Records
│   │   └── diagrams/
│   ├── api/
│   └── contributing/
└── quality-gates/
    ├── coverage-thresholds.json
    ├── complexity-limits.json
    └── architecture-rules.json
```

### 1.2 First Commit Requirements

The **very first commit** of any project MUST include:

1. Pre-configured linting (language-appropriate)
2. Pre-configured formatting (language-appropriate)
3. Git hooks (pre-commit, pre-push, commit-msg)
4. CI/CD pipeline skeleton
5. README with setup instructions
6. License file
7. Contributing guidelines
8. Code of conduct
9. Security policy
10. Basic test infrastructure with at least one example test

**DO NOT proceed to feature development until all 10 items are complete.**

---

## Part 2: Language-Specific Quality Configurations

### 2.1 Python Projects

#### Required Tools (Install ALL)

```bash
# Core Quality Stack
pip install --break-system-packages \
    ruff \
    mypy \
    black \
    isort \
    bandit \
    safety \
    vulture \
    radon \
    xenon \
    pylint \
    prospector \
    pytest \
    pytest-cov \
    pytest-xdist \
    pytest-timeout \
    pytest-randomly \
    pytest-benchmark \
    hypothesis \
    mutmut \
    pre-commit \
    commitizen \
    interrogate \
    pydocstyle \
    darglint \
    tryceratops \
    refurb \
    pyupgrade \
    autoflake \
    dead \
    importlib-metadata
```

#### pyproject.toml (MANDATORY Configuration)

```toml
[project]
name = "your-project"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "ALL"  # Enable ALL rules - no exceptions
]
ignore = []  # Start with NO ignores - add only with documented justification

[tool.ruff.per-file-ignores]
"tests/**/*.py" = ["S101", "PLR2004"]  # Allow assert and magic values in tests

[tool.ruff.isort]
force-single-line = true
force-sort-within-sections = true
known-first-party = ["your_project"]

[tool.ruff.mccabe]
max-complexity = 10  # Cyclomatic complexity ceiling

[tool.ruff.pylint]
max-args = 5
max-branches = 12
max-returns = 6
max-statements = 50

[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
check_untyped_defs = true
show_error_codes = true
show_column_numbers = true
pretty = true
plugins = []

[tool.pytest.ini_options]
minversion = "7.0"
addopts = [
    "-ra",
    "-q",
    "--strict-markers",
    "--strict-config",
    "-p", "no:cacheprovider",
    "--tb=short",
    "--cov=src",
    "--cov-branch",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=90",
    "--hypothesis-seed=0",
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
]
filterwarnings = [
    "error",  # Turn all warnings into errors
]

[tool.coverage.run]
branch = true
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 90
show_missing = true
precision = 2

[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = []  # No skips - fix the security issues

[tool.interrogate]
ignore-init-method = false
ignore-init-module = true
ignore-magic = false
ignore-semiprivate = false
ignore-private = false
ignore-property-decorators = false
ignore-module = false
ignore-nested-functions = false
ignore-nested-classes = false
ignore-setters = false
fail-under = 95
exclude = ["setup.py", "docs", "build"]
verbose = 2

[tool.pydocstyle]
convention = "google"
add-ignore = []

[tool.vulture]
min_confidence = 80
paths = ["src"]

[tool.xenon]
max_absolute = "B"
max_modules = "A"
max_average = "A"

[tool.commitizen]
name = "cz_conventional_commits"
version = "0.1.0"
tag_format = "v$version"
version_files = [
    "pyproject.toml:version"
]
```

#### .pre-commit-config.yaml (Python)

```yaml
default_language_version:
  python: python3.11

repos:
  # Git checks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=500']
      - id: check-case-conflict
      - id: check-merge-conflict
      - id: check-symlinks
      - id: check-toml
      - id: check-yaml
        args: ['--unsafe']
      - id: check-json
      - id: detect-private-key
      - id: end-of-file-fixer
      - id: fix-byte-order-marker
      - id: mixed-line-ending
        args: ['--fix=lf']
      - id: no-commit-to-branch
        args: ['--branch', 'main', '--branch', 'master']
      - id: trailing-whitespace
      - id: check-ast
      - id: debug-statements
      - id: check-docstring-first

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
        additional_dependencies: ['bandit[toml]']

  # Secrets detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Code formatting
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  # Comprehensive linting
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: ['--fix']
      - id: ruff-format

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: []  # Add your type stubs here
        args: ['--strict']

  # Docstring coverage
  - repo: https://github.com/econchick/interrogate
    rev: 1.5.0
    hooks:
      - id: interrogate
        args: ['-vv', '--fail-under=95']

  # Dead code detection
  - repo: https://github.com/jendrikseipp/vulture
    rev: v2.10
    hooks:
      - id: vulture
        args: ['src/', '--min-confidence', '80']

  # Upgrade syntax
  - repo: https://github.com/asottile/pyupgrade
    rev: v3.15.0
    hooks:
      - id: pyupgrade
        args: ['--py311-plus']

  # Remove unused imports/variables
  - repo: https://github.com/PyCQA/autoflake
    rev: v2.2.1
    hooks:
      - id: autoflake
        args: [
          '--in-place',
          '--remove-all-unused-imports',
          '--remove-unused-variables',
          '--remove-duplicate-keys',
          '--ignore-init-module-imports'
        ]

  # Exception handling best practices
  - repo: https://github.com/guilatrova/tryceratops
    rev: v2.3.2
    hooks:
      - id: tryceratops

  # Modern Python suggestions
  - repo: https://github.com/dosisod/refurb
    rev: v1.26.0
    hooks:
      - id: refurb

  # Commit message validation
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.13.0
    hooks:
      - id: commitizen
        stages: [commit-msg]

ci:
  autofix_commit_msg: 'style: auto-fix by pre-commit hooks'
  autoupdate_commit_msg: 'chore: update pre-commit hooks'
  skip: []  # Don't skip anything in CI
```

### 2.2 TypeScript/JavaScript Projects

#### Required Tools (Install ALL)

```bash
# Core Quality Stack
npm install --save-dev \
    typescript \
    eslint \
    @typescript-eslint/parser \
    @typescript-eslint/eslint-plugin \
    eslint-plugin-import \
    eslint-plugin-unicorn \
    eslint-plugin-sonarjs \
    eslint-plugin-promise \
    eslint-plugin-security \
    eslint-plugin-no-secrets \
    eslint-plugin-deprecation \
    eslint-plugin-jsdoc \
    eslint-plugin-prettier \
    eslint-config-prettier \
    prettier \
    jest \
    ts-jest \
    @types/jest \
    jest-extended \
    fast-check \
    stryker-cli \
    @stryker-mutator/core \
    @stryker-mutator/jest-runner \
    @stryker-mutator/typescript-checker \
    husky \
    lint-staged \
    commitlint \
    @commitlint/cli \
    @commitlint/config-conventional \
    depcheck \
    npm-check-updates \
    madge \
    dependency-cruiser \
    knip \
    publint
```

#### eslint.config.mjs (ESLint v9 Flat Config - MANDATORY)

```javascript
import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import unicornPlugin from 'eslint-plugin-unicorn';
import sonarjsPlugin from 'eslint-plugin-sonarjs';
import promisePlugin from 'eslint-plugin-promise';
import securityPlugin from 'eslint-plugin-security';
import importPlugin from 'eslint-plugin-import';
import jsdocPlugin from 'eslint-plugin-jsdoc';

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        project: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      unicorn: unicornPlugin,
      sonarjs: sonarjsPlugin,
      promise: promisePlugin,
      security: securityPlugin,
      import: importPlugin,
      jsdoc: jsdocPlugin,
    },
    rules: {
      // TypeScript Strict
      '@typescript-eslint/explicit-function-return-type': 'error',
      '@typescript-eslint/explicit-module-boundary-types': 'error',
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/strict-boolean-expressions': 'error',
      '@typescript-eslint/no-floating-promises': 'error',
      '@typescript-eslint/no-misused-promises': 'error',
      '@typescript-eslint/await-thenable': 'error',
      '@typescript-eslint/no-unnecessary-condition': 'error',
      '@typescript-eslint/prefer-nullish-coalescing': 'error',
      '@typescript-eslint/prefer-optional-chain': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
      '@typescript-eslint/consistent-type-definitions': ['error', 'interface'],
      '@typescript-eslint/naming-convention': [
        'error',
        { selector: 'interface', format: ['PascalCase'] },
        { selector: 'typeAlias', format: ['PascalCase'] },
        { selector: 'enum', format: ['PascalCase'] },
        { selector: 'enumMember', format: ['UPPER_CASE'] },
        { selector: 'variable', format: ['camelCase', 'UPPER_CASE'] },
        { selector: 'function', format: ['camelCase'] },
        { selector: 'parameter', format: ['camelCase'] },
        { selector: 'method', format: ['camelCase'] },
        { selector: 'property', format: ['camelCase'] },
        { selector: 'class', format: ['PascalCase'] },
      ],

      // Unicorn (Modern JS/TS)
      'unicorn/prevent-abbreviations': 'error',
      'unicorn/filename-case': ['error', { case: 'kebabCase' }],
      'unicorn/no-null': 'error',
      'unicorn/prefer-module': 'error',
      'unicorn/prefer-node-protocol': 'error',
      'unicorn/prefer-top-level-await': 'error',
      'unicorn/no-array-reduce': 'error',
      'unicorn/no-for-loop': 'error',
      'unicorn/prefer-spread': 'error',
      'unicorn/prefer-string-slice': 'error',
      'unicorn/prefer-ternary': 'error',
      'unicorn/prefer-array-find': 'error',
      'unicorn/prefer-array-flat': 'error',
      'unicorn/prefer-array-flat-map': 'error',
      'unicorn/prefer-array-index-of': 'error',
      'unicorn/prefer-array-some': 'error',
      'unicorn/prefer-at': 'error',
      'unicorn/prefer-includes': 'error',
      'unicorn/prefer-set-has': 'error',
      'unicorn/prefer-string-replace-all': 'error',
      'unicorn/prefer-switch': 'error',
      'unicorn/switch-case-braces': 'error',
      'unicorn/throw-new-error': 'error',
      'unicorn/no-useless-undefined': 'error',
      'unicorn/no-useless-spread': 'error',
      'unicorn/consistent-destructuring': 'error',
      'unicorn/explicit-length-check': 'error',
      'unicorn/new-for-builtins': 'error',
      'unicorn/no-lonely-if': 'error',
      'unicorn/prefer-negative-index': 'error',
      'unicorn/prefer-object-from-entries': 'error',
      'unicorn/prefer-prototype-methods': 'error',
      'unicorn/prefer-regexp-test': 'error',
      'unicorn/prefer-type-error': 'error',

      // SonarJS (Code Quality)
      'sonarjs/cognitive-complexity': ['error', 15],
      'sonarjs/no-duplicate-string': 'error',
      'sonarjs/no-identical-functions': 'error',
      'sonarjs/no-collapsible-if': 'error',
      'sonarjs/no-collection-size-mischeck': 'error',
      'sonarjs/no-duplicated-branches': 'error',
      'sonarjs/no-element-overwrite': 'error',
      'sonarjs/no-extra-arguments': 'error',
      'sonarjs/no-identical-conditions': 'error',
      'sonarjs/no-identical-expressions': 'error',
      'sonarjs/no-ignored-return': 'error',
      'sonarjs/no-inverted-boolean-check': 'error',
      'sonarjs/no-nested-switch': 'error',
      'sonarjs/no-nested-template-literals': 'error',
      'sonarjs/no-one-iteration-loop': 'error',
      'sonarjs/no-redundant-boolean': 'error',
      'sonarjs/no-redundant-jump': 'error',
      'sonarjs/no-same-line-conditional': 'error',
      'sonarjs/no-small-switch': 'error',
      'sonarjs/no-unused-collection': 'error',
      'sonarjs/no-use-of-empty-return-value': 'error',
      'sonarjs/no-useless-catch': 'error',
      'sonarjs/prefer-immediate-return': 'error',
      'sonarjs/prefer-object-literal': 'error',
      'sonarjs/prefer-single-boolean-return': 'error',
      'sonarjs/prefer-while': 'error',

      // Promise best practices
      'promise/always-return': 'error',
      'promise/no-return-wrap': 'error',
      'promise/param-names': 'error',
      'promise/catch-or-return': 'error',
      'promise/no-native': 'off',
      'promise/no-nesting': 'error',
      'promise/no-promise-in-callback': 'error',
      'promise/no-callback-in-promise': 'error',
      'promise/avoid-new': 'off',
      'promise/no-new-statics': 'error',
      'promise/no-return-in-finally': 'error',
      'promise/valid-params': 'error',
      'promise/prefer-await-to-then': 'error',
      'promise/prefer-await-to-callbacks': 'error',

      // Security
      'security/detect-object-injection': 'error',
      'security/detect-non-literal-regexp': 'error',
      'security/detect-unsafe-regex': 'error',
      'security/detect-buffer-noassert': 'error',
      'security/detect-child-process': 'error',
      'security/detect-disable-mustache-escape': 'error',
      'security/detect-eval-with-expression': 'error',
      'security/detect-new-buffer': 'error',
      'security/detect-no-csrf-before-method-override': 'error',
      'security/detect-possible-timing-attacks': 'error',
      'security/detect-pseudoRandomBytes': 'error',

      // Import organization
      'import/order': [
        'error',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            'parent',
            'sibling',
            'index',
            'object',
            'type',
          ],
          'newlines-between': 'always',
          alphabetize: { order: 'asc', caseInsensitive: true },
        },
      ],
      'import/no-duplicates': 'error',
      'import/no-cycle': 'error',
      'import/no-self-import': 'error',
      'import/no-useless-path-segments': 'error',
      'import/newline-after-import': 'error',
      'import/first': 'error',
      'import/exports-last': 'error',
      'import/no-mutable-exports': 'error',
      'import/no-default-export': 'error',

      // JSDoc requirements
      'jsdoc/require-jsdoc': [
        'error',
        {
          require: {
            FunctionDeclaration: true,
            MethodDefinition: true,
            ClassDeclaration: true,
            ArrowFunctionExpression: true,
            FunctionExpression: true,
          },
        },
      ],
      'jsdoc/require-description': 'error',
      'jsdoc/require-param': 'error',
      'jsdoc/require-param-description': 'error',
      'jsdoc/require-param-type': 'off', // TypeScript handles types
      'jsdoc/require-returns': 'error',
      'jsdoc/require-returns-description': 'error',
      'jsdoc/require-returns-type': 'off', // TypeScript handles types
      'jsdoc/check-alignment': 'error',
      'jsdoc/check-param-names': 'error',

      // General code quality
      'no-console': 'error',
      'no-debugger': 'error',
      'no-alert': 'error',
      'no-var': 'error',
      'prefer-const': 'error',
      'prefer-template': 'error',
      'prefer-arrow-callback': 'error',
      'prefer-destructuring': 'error',
      'prefer-rest-params': 'error',
      'prefer-spread': 'error',
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-new-func': 'error',
      'no-param-reassign': 'error',
      'no-return-assign': 'error',
      'no-sequences': 'error',
      'no-throw-literal': 'error',
      'no-unmodified-loop-condition': 'error',
      'no-unused-expressions': 'error',
      'no-useless-call': 'error',
      'no-useless-concat': 'error',
      'no-useless-return': 'error',
      'no-void': 'error',
      'no-with': 'error',
      'radix': 'error',
      'require-await': 'error',
      'yoda': 'error',
      'eqeqeq': ['error', 'always'],
      'curly': ['error', 'all'],
      'max-depth': ['error', 4],
      'max-lines': ['error', { max: 300, skipBlankLines: true, skipComments: true }],
      'max-lines-per-function': ['error', { max: 50, skipBlankLines: true, skipComments: true }],
      'max-nested-callbacks': ['error', 3],
      'max-params': ['error', 4],
      'max-statements': ['error', 20],
      'complexity': ['error', 10],
    },
  },
  {
    files: ['**/*.test.ts', '**/*.spec.ts', 'tests/**/*.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'max-lines-per-function': 'off',
      'max-statements': 'off',
    },
  }
);
```

#### tsconfig.json (MANDATORY - Maximum Strictness)

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "./dist",
    "rootDir": "./src",

    "strict": true,
    "alwaysStrict": true,
    "noImplicitAny": true,
    "noImplicitReturns": true,
    "noImplicitThis": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "strictBindCallApply": true,
    "strictFunctionTypes": true,
    "strictNullChecks": true,
    "strictPropertyInitialization": true,
    "useUnknownInCatchVariables": true,
    "allowUnusedLabels": false,
    "allowUnreachableCode": false,

    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "verbatimModuleSyntax": true,

    "allowSyntheticDefaultImports": true,
    "incremental": true,
    "composite": true,
    "tsBuildInfoFile": "./.tsbuildinfo"
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "coverage"]
}
```

### 2.3 Swift Projects

#### Required Tools

```bash
# SwiftLint
brew install swiftlint

# SwiftFormat
brew install swiftformat

# Periphery (dead code detection)
brew install periphery

# xcbeautify (CI log formatting)
brew install xcbeautify

# swift-sh (for scripts)
brew install swift-sh
```

#### .swiftlint.yml (MANDATORY)

```yaml
# SwiftLint Configuration - Maximum Strictness

disabled_rules: []  # NO rules disabled

opt_in_rules:
  - all  # Enable ALL optional rules

included:
  - Sources
  - Tests

excluded:
  - Pods
  - .build
  - DerivedData

# Rule configurations
line_length:
  warning: 120
  error: 150
  ignores_comments: true
  ignores_urls: true

type_body_length:
  warning: 200
  error: 300

file_length:
  warning: 400
  error: 500

function_body_length:
  warning: 40
  error: 60

function_parameter_count:
  warning: 5
  error: 7

cyclomatic_complexity:
  warning: 10
  error: 15

nesting:
  type_level: 2
  function_level: 3

identifier_name:
  min_length:
    warning: 2
    error: 1
  max_length:
    warning: 50
    error: 60
  excluded:
    - id
    - x
    - y
    - z
    - i
    - j

type_name:
  min_length: 3
  max_length: 50

large_tuple:
  warning: 3
  error: 4

reporter: 'xcode'

custom_rules:
  force_unwrapping_limited:
    name: "Limit Force Unwrapping"
    regex: "\\!(?!\\=)"
    message: "Avoid force unwrapping. Use guard let or if let."
    severity: warning
```

#### .swiftformat

```
--swiftversion 5.9
--indent 4
--indentcase false
--trimwhitespace always
--voidtype void
--nospaceoperators ..<, ...
--ifdef noindent
--stripunusedargs closure-only
--maxwidth 120
--wraparguments before-first
--wrapparameters before-first
--wrapcollections before-first
--closingparen same-line
--funcattributes prev-line
--typeattributes prev-line
--varattributes prev-line
--modifierorder [override, required, convenience, public, internal, fileprivate, private, static, final, lazy]
--enable isEmpty
--enable sortedImports
--enable wrapMultilineStatementBraces
--enable redundantBreak
--enable blankLinesBetweenScopes
--enable redundantPattern
--enable redundantReturn
```

---

## Part 3: CI/CD Pipeline Requirements

### 3.1 GitHub Actions Workflow (Python)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * *'  # Daily security scan

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHON_VERSION: '3.11'
  COVERAGE_THRESHOLD: 90

jobs:
  # Job 1: Code Quality
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run Ruff (linting)
        run: ruff check . --output-format=github

      - name: Run Ruff (formatting)
        run: ruff format --check .

      - name: Run Black
        run: black --check .

      - name: Run isort
        run: isort --check-only --diff .

      - name: Run MyPy
        run: mypy src/

      - name: Run Pylint
        run: pylint src/ --fail-under=9.0

      - name: Run Bandit (security)
        run: bandit -r src/ -c pyproject.toml

      - name: Run Safety (dependency security)
        run: safety check

      - name: Run Vulture (dead code)
        run: vulture src/ --min-confidence 80

      - name: Check complexity (Radon)
        run: |
          radon cc src/ -a -nb
          radon mi src/ -nb

      - name: Check complexity (Xenon)
        run: xenon --max-absolute B --max-modules A --max-average A src/

      - name: Check docstring coverage
        run: interrogate -v src/ --fail-under=95

      - name: Check for type annotation coverage
        run: |
          pip install mypy-coverage
          mypy-coverage src/

  # Job 2: Tests
  test:
    name: Tests
    runs-on: ubuntu-latest
    needs: quality
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-dev.txt

      - name: Run unit tests with coverage
        run: |
          pytest tests/unit/ \
            --cov=src \
            --cov-branch \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=${{ env.COVERAGE_THRESHOLD }} \
            --junitxml=junit.xml \
            -n auto

      - name: Run integration tests
        run: pytest tests/integration/ -v --tb=short

      - name: Run property-based tests
        run: pytest tests/property/ -v --hypothesis-seed=0

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          fail_ci_if_error: true
          verbose: true

      - name: Upload test results
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.python-version }}
          path: |
            junit.xml
            htmlcov/

  # Job 3: Mutation Testing
  mutation:
    name: Mutation Testing
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
          pip install mutmut

      - name: Run mutation tests
        run: |
          mutmut run --paths-to-mutate=src/ || true
          mutmut results
          mutmut junitxml > mutmut.xml

      - name: Check mutation score
        run: |
          SCORE=$(mutmut results | grep -oP 'Mutation score: \K[\d.]+')
          if (( $(echo "$SCORE < 80" | bc -l) )); then
            echo "Mutation score $SCORE is below 80%"
            exit 1
          fi

  # Job 4: Security Scanning
  security:
    name: Security Scanning
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: >-
            p/python
            p/security-audit
            p/secrets
            p/owasp-top-ten

  # Job 5: Dependency Review
  dependency-review:
    name: Dependency Review
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Dependency Review
        uses: actions/dependency-review-action@v3
        with:
          fail-on-severity: moderate
          deny-licenses: GPL-3.0, AGPL-3.0

  # Job 6: Architecture Validation
  architecture:
    name: Architecture Validation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: pip install import-linter pydeps

      - name: Check import rules
        run: lint-imports

      - name: Check for circular dependencies
        run: pydeps src/ --no-output --only-cycles

  # Job 7: Documentation
  documentation:
    name: Documentation
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check README exists and is valid
        run: |
          test -f README.md
          npx markdown-lint README.md

      - name: Check CHANGELOG exists
        run: test -f CHANGELOG.md

      - name: Check API documentation generation
        run: |
          pip install pdoc
          pdoc src/ --html --output-dir docs/api/
```

### 3.2 GitHub Actions Workflow (TypeScript)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '20'
  COVERAGE_THRESHOLD: 90

jobs:
  quality:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Check formatting (Prettier)
        run: npx prettier --check .

      - name: Lint (ESLint)
        run: npx eslint . --max-warnings 0

      - name: Type check
        run: npx tsc --noEmit

      - name: Check for unused dependencies
        run: npx depcheck

      - name: Check for unused exports
        run: npx knip

      - name: Check for circular dependencies
        run: npx madge --circular --extensions ts src/

      - name: Validate package.json
        run: npx publint

  test:
    name: Tests
    runs-on: ubuntu-latest
    needs: quality
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm test -- --coverage --coverageThreshold='{"global":{"branches":90,"functions":90,"lines":90,"statements":90}}'

      - name: Run integration tests
        run: npm run test:integration

  mutation:
    name: Mutation Testing
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run Stryker mutation testing
        run: npx stryker run
        env:
          STRYKER_DASHBOARD_API_KEY: ${{ secrets.STRYKER_DASHBOARD_API_KEY }}

  security:
    name: Security
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run npm audit
        run: npm audit --audit-level=moderate

      - name: Run Snyk security scan
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

---

## Part 4: Architecture Enforcement

### 4.1 Import Rules (Python - import-linter)

```ini
# .importlinter
[importlinter]
root_package = your_project

[importlinter:contract:1]
name = Domain layer independence
type = independence
modules =
    your_project.domain
    your_project.infrastructure
    your_project.application

[importlinter:contract:2]
name = Layers contract
type = layers
layers =
    your_project.presentation
    your_project.application
    your_project.domain
    your_project.infrastructure

[importlinter:contract:3]
name = No circular dependencies in domain
type = forbidden
source_modules =
    your_project.domain
forbidden_modules =
    your_project.domain
ignore_imports =
    your_project.domain.models -> your_project.domain.exceptions
```

### 4.2 Dependency Cruiser (TypeScript)

```javascript
// .dependency-cruiser.js
module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependencies are forbidden',
      from: {},
      to: {
        circular: true,
      },
    },
    {
      name: 'no-orphans',
      severity: 'error',
      comment: 'No orphan modules allowed',
      from: {
        orphan: true,
        pathNot: ['\\.(test|spec)\\.ts$', '__tests__/', '__mocks__/'],
      },
      to: {},
    },
    {
      name: 'domain-independence',
      severity: 'error',
      comment: 'Domain layer must not depend on infrastructure',
      from: {
        path: '^src/domain',
      },
      to: {
        path: '^src/(infrastructure|application|presentation)',
      },
    },
    {
      name: 'application-layer-rules',
      severity: 'error',
      comment: 'Application layer must not depend on presentation',
      from: {
        path: '^src/application',
      },
      to: {
        path: '^src/presentation',
      },
    },
    {
      name: 'no-deprecated-packages',
      severity: 'error',
      from: {},
      to: {
        dependencyTypes: ['deprecated'],
      },
    },
    {
      name: 'no-dev-deps-in-production',
      severity: 'error',
      from: {
        pathNot: '\\.(test|spec)\\.ts$',
      },
      to: {
        dependencyTypes: ['npm-dev'],
      },
    },
  ],
  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    tsConfig: {
      fileName: 'tsconfig.json',
    },
    enhancedResolveOptions: {
      exportsFields: ['exports'],
      conditionNames: ['import', 'require', 'node', 'default'],
    },
    reporterOptions: {
      dot: {
        collapsePattern: 'node_modules/[^/]+',
      },
      archi: {
        collapsePattern: '^(packages|src|lib)/[^/]+|node_modules/[^/]+',
      },
    },
  },
};
```

---

## Part 5: Testing Requirements

### 5.1 Test Categories (All MANDATORY)

Every project MUST have tests in ALL of these categories:

| Category | Purpose | Tool (Python) | Tool (TypeScript) |
|----------|---------|---------------|-------------------|
| Unit | Test individual functions/classes | pytest | jest |
| Integration | Test component interactions | pytest | jest |
| E2E | Test complete workflows | pytest + selenium | playwright |
| Property | Test invariants with generated data | hypothesis | fast-check |
| Mutation | Verify test quality | mutmut | stryker |
| Snapshot | Detect unintended changes | pytest-snapshot | jest |
| Performance | Detect performance regressions | pytest-benchmark | benchmark.js |
| Contract | API contract validation | pact-python | pact-js |
| Fuzz | Find edge cases | atheris | jsfuzz |

### 5.2 Test Quality Rules

```python
# tests/conftest.py - MANDATORY test configuration

import pytest
from hypothesis import settings, Verbosity

# Global Hypothesis settings
settings.register_profile(
    "ci",
    max_examples=1000,
    verbosity=Verbosity.verbose,
    deadline=None,
)
settings.register_profile(
    "dev",
    max_examples=100,
    verbosity=Verbosity.normal,
)
settings.register_profile(
    "debug",
    max_examples=10,
    verbosity=Verbosity.verbose,
)


@pytest.fixture(scope="session")
def enforce_test_naming():
    """Ensure all test functions follow naming conventions."""
    # test_<unit>_<scenario>_<expected_outcome>
    pass


@pytest.fixture(autouse=True)
def no_external_calls(monkeypatch):
    """Prevent accidental external API calls in unit tests."""
    import socket

    def guard(*args, **kwargs):
        raise RuntimeError("Unit tests must not make external calls")

    monkeypatch.setattr(socket, "socket", guard)
```

### 5.3 Coverage Requirements

```json
// coverage-thresholds.json
{
  "global": {
    "branches": 90,
    "functions": 95,
    "lines": 90,
    "statements": 90
  },
  "per-file": {
    "src/domain/**/*.{ts,py}": {
      "branches": 95,
      "functions": 100,
      "lines": 95
    },
    "src/application/**/*.{ts,py}": {
      "branches": 90,
      "functions": 95,
      "lines": 90
    }
  },
  "mutation-score-minimum": 80
}
```

---

## Part 6: Documentation Requirements

### 6.1 Code Documentation (MANDATORY)

Every public function, class, and module MUST have documentation that includes:

**Python (Google-style docstrings):**
```python
def calculate_risk_score(
    user_data: UserData,
    market_conditions: MarketConditions,
    *,
    include_historical: bool = True,
) -> RiskScore:
    """Calculate comprehensive risk score for a user.

    This function analyzes user data against current market conditions
    to produce a risk assessment. It considers credit history, income
    stability, and market volatility.

    Args:
        user_data: Complete user profile including financial history.
        market_conditions: Current market state and volatility metrics.
        include_historical: Whether to include historical trend analysis.
            Defaults to True.

    Returns:
        A RiskScore object containing:
            - score: Numeric risk value (0-100)
            - confidence: Confidence interval
            - factors: List of contributing factors

    Raises:
        ValidationError: If user_data is incomplete or malformed.
        MarketDataError: If market conditions cannot be fetched.

    Examples:
        >>> user = UserData(credit_score=750, income=100000)
        >>> market = MarketConditions(volatility=0.15)
        >>> score = calculate_risk_score(user, market)
        >>> assert 0 <= score.score <= 100

    Note:
        This function caches results for 15 minutes. Use
        `clear_risk_cache()` to force recalculation.

    See Also:
        - `UserData`: User profile structure
        - `calculate_portfolio_risk`: For portfolio-level analysis
    """
```

**TypeScript (JSDoc):**
```typescript
/**
 * Calculates comprehensive risk score for a user.
 *
 * This function analyzes user data against current market conditions
 * to produce a risk assessment.
 *
 * @param userData - Complete user profile including financial history
 * @param marketConditions - Current market state and volatility metrics
 * @param options - Configuration options
 * @param options.includeHistorical - Whether to include historical analysis
 * @returns A RiskScore object with score, confidence, and factors
 * @throws {ValidationError} If user data is incomplete
 * @throws {MarketDataError} If market conditions unavailable
 *
 * @example
 * ```typescript
 * const user = new UserData({ creditScore: 750, income: 100000 });
 * const market = new MarketConditions({ volatility: 0.15 });
 * const score = calculateRiskScore(user, market);
 * console.log(score.value); // 0-100
 * ```
 *
 * @see {@link UserData} for user profile structure
 * @see {@link calculatePortfolioRisk} for portfolio analysis
 */
export function calculateRiskScore(
  userData: UserData,
  marketConditions: MarketConditions,
  options: RiskOptions = { includeHistorical: true }
): RiskScore {
```

### 6.2 Architecture Decision Records (ADRs)

Every significant architectural decision MUST be documented:

```markdown
# ADR-001: Use Event Sourcing for Order Management

## Status
Accepted

## Context
We need to track all changes to orders for audit compliance and
enable temporal queries for analytics.

## Decision
We will implement Event Sourcing for the Order aggregate with
CQRS for read optimization.

## Consequences

### Positive
- Complete audit trail
- Temporal queries enabled
- Easy debugging via event replay

### Negative
- Increased complexity
- Learning curve for team
- Additional infrastructure (event store)

### Neutral
- Different testing patterns required

## Alternatives Considered
1. **Audit table approach**: Simpler but loses event semantics
2. **CDC with Debezium**: External dependency, eventual consistency

## References
- Martin Fowler: Event Sourcing
- Team RFC-2024-03
```

---

## Part 7: Git Workflow Enforcement

### 7.1 Commit Message Format (Conventional Commits - MANDATORY)

```
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

**Types (REQUIRED):**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting (no code change)
- `refactor`: Code change that neither fixes nor adds
- `perf`: Performance improvement
- `test`: Adding tests
- `build`: Build system changes
- `ci`: CI configuration
- `chore`: Maintenance tasks
- `revert`: Revert a commit

**commitlint.config.js:**
```javascript
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'build', 'ci', 'chore', 'revert'],
    ],
    'scope-case': [2, 'always', 'kebab-case'],
    'subject-case': [2, 'never', ['sentence-case', 'start-case', 'pascal-case', 'upper-case']],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'type-case': [2, 'always', 'lower-case'],
    'type-empty': [2, 'never'],
    'body-leading-blank': [2, 'always'],
    'body-max-line-length': [2, 'always', 100],
    'footer-leading-blank': [2, 'always'],
    'footer-max-line-length': [2, 'always', 100],
    'header-max-length': [2, 'always', 72],
  },
};
```

### 7.2 Branch Protection Rules

Configure in repository settings:

- ✅ Require pull request reviews (minimum 1)
- ✅ Dismiss stale reviews when new commits pushed
- ✅ Require review from CODEOWNERS
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Require signed commits
- ✅ Require linear history
- ✅ Include administrators
- ❌ Allow force pushes
- ❌ Allow deletions

---

## Part 8: Subagent Profiles for Claude Code

### 8.1 Quality Reviewer Agent

```markdown
# Quality Reviewer Agent Profile

## Role
You are a ruthless code quality enforcer. Your job is to find problems,
not to approve code. Assume every submission has issues until proven otherwise.

## Review Checklist (Check ALL)

### Code Quality
- [ ] All functions under 50 lines
- [ ] Cyclomatic complexity under 10
- [ ] No magic numbers (use named constants)
- [ ] No commented-out code
- [ ] No TODO/FIXME without linked issue
- [ ] No print/console.log statements
- [ ] Error handling is explicit and complete
- [ ] No bare except/catch clauses

### Testing
- [ ] Unit tests cover the change
- [ ] Edge cases tested
- [ ] Error paths tested
- [ ] Test names describe behavior
- [ ] No test interdependencies
- [ ] Assertions are specific (not assertTrue)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] SQL injection prevented
- [ ] XSS prevented
- [ ] CSRF protected
- [ ] Rate limiting considered

### Architecture
- [ ] Single Responsibility followed
- [ ] Dependencies flow inward
- [ ] No circular imports
- [ ] Interface segregation maintained
- [ ] Liskov substitution valid

### Documentation
- [ ] Public APIs documented
- [ ] Complex logic explained
- [ ] Examples provided
- [ ] Breaking changes noted

## Response Format
Always respond with specific line numbers and code suggestions.
Never say "looks good" without explaining what makes it good.
```

### 8.2 Test Generator Agent

```markdown
# Test Generator Agent Profile

## Role
You generate comprehensive tests that would make a mutation testing
framework cry. Your tests must be so thorough that any code change
that doesn't update tests must be a no-op.

## Test Generation Rules

1. **Start with failure modes**
   - What could go wrong?
   - What are the boundary conditions?
   - What invalid inputs are possible?

2. **Test behavior, not implementation**
   - Test public interfaces
   - Don't test private methods directly
   - Focus on outcomes, not internals

3. **Use property-based testing for**
   - Numeric operations
   - String manipulation
   - Collection operations
   - Serialization/deserialization
   - Any idempotent operations

4. **Test naming convention**
   ```
   test_<unit>_<scenario>_<expected_outcome>

   Examples:
   test_calculator_divide_by_zero_raises_error
   test_user_create_valid_input_returns_user
   test_cache_expired_entry_returns_none
   ```

5. **Mandatory test categories per feature**
   - Happy path
   - Error handling
   - Boundary conditions
   - Concurrent access (if applicable)
   - Performance baseline
```

### 8.3 Security Auditor Agent

```markdown
# Security Auditor Agent Profile

## Role
You assume every line of code is a potential vulnerability.
Your job is to prevent security incidents before they happen.

## Audit Checklist

### Authentication & Authorization
- [ ] Authentication required for protected resources
- [ ] Authorization checks at every layer
- [ ] Session management secure
- [ ] Password requirements enforced
- [ ] MFA considered

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit
- [ ] PII handling compliant
- [ ] Data retention policies followed
- [ ] Secure deletion implemented

### Input Validation
- [ ] All inputs validated
- [ ] Validation whitelist-based
- [ ] File uploads restricted
- [ ] Path traversal prevented
- [ ] Command injection prevented

### Dependencies
- [ ] Dependencies from trusted sources
- [ ] Versions pinned
- [ ] Known vulnerabilities checked
- [ ] Minimal dependency principle

### Error Handling
- [ ] Errors don't leak information
- [ ] Stack traces not exposed
- [ ] Error messages generic externally
- [ ] Logging doesn't include secrets

## Common Vulnerabilities to Check
- OWASP Top 10
- CWE Top 25
- Language-specific issues
```

---

## Part 9: Metrics & Monitoring

### 9.1 Required Quality Metrics

Track and enforce these metrics:

| Metric | Threshold | Tool |
|--------|-----------|------|
| Code Coverage | ≥90% | pytest-cov / jest |
| Branch Coverage | ≥85% | pytest-cov / jest |
| Mutation Score | ≥80% | mutmut / stryker |
| Cyclomatic Complexity | ≤10 | radon / eslint |
| Cognitive Complexity | ≤15 | sonarqube |
| Maintainability Index | ≥20 | radon |
| Technical Debt Ratio | ≤5% | sonarqube |
| Documentation Coverage | ≥95% | interrogate |
| Dependency Freshness | ≤30 days | npm-check-updates |
| Security Vulnerabilities | 0 critical/high | safety / npm audit |

### 9.2 Quality Dashboard Configuration

```yaml
# sonar-project.properties
sonar.projectKey=your-project
sonar.projectName=Your Project
sonar.sources=src
sonar.tests=tests
sonar.coverage.exclusions=**/tests/**,**/__mocks__/**
sonar.cpd.exclusions=**/tests/**

# Quality Gate
sonar.qualitygate.wait=true

# Custom thresholds
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.pylint.reportPath=pylint-report.txt

# Fail on
sonar.issue.ignore.multicriteria=e1
sonar.issue.ignore.multicriteria.e1.resourceKey=**/*
sonar.issue.ignore.multicriteria.e1.ruleKey=python:S125
```

---

## Part 10: Template Generation Instructions

When asked to templatize this framework for a new project:

### 10.1 Required Information

1. **Language(s)**: Python / TypeScript / Swift / Go / Rust / Java / etc.
2. **Project Type**: Library / CLI / API / Web App / Mobile App
3. **Team Size**: Solo / Small (2-5) / Medium (6-15) / Large (15+)
4. **Deployment**: Self-hosted / Cloud / Serverless / Edge
5. **Compliance**: None / SOC2 / HIPAA / GDPR / PCI-DSS

### 10.2 Generation Process

```bash
# For each new project, Claude Code MUST:

1. Create repository structure (Part 1)
2. Generate language-specific configs (Part 2)
3. Set up CI/CD pipelines (Part 3)
4. Configure architecture rules (Part 4)
5. Create test infrastructure (Part 5)
6. Set up documentation templates (Part 6)
7. Configure git hooks (Part 7)
8. Create subagent profiles (Part 8)
9. Configure metrics (Part 9)

# NEVER skip any step
# NEVER "simplify" configurations
# NEVER leave placeholders unfilled
```

### 10.3 Validation Checklist

Before declaring a project "initialized", verify:

- [ ] All linters run without errors
- [ ] All formatters run without changes
- [ ] At least one passing test exists
- [ ] Pre-commit hooks work
- [ ] CI pipeline runs successfully
- [ ] Documentation builds
- [ ] Coverage reports generate
- [ ] Architecture rules validate

---

## Part 11: Principles from Classic Software Engineering

### From "Extreme Programming" (Kent Beck)

- **Test-First Development**: Write tests BEFORE implementation
- **Continuous Integration**: Integrate multiple times daily
- **Refactoring**: Improve code without changing behavior
- **Simple Design**: Do the simplest thing that could work
- **Pair Programming**: Two minds on every problem (AI can be the pair)

### From "The Pragmatic Programmer" (Hunt & Thomas)

- **DRY**: Don't Repeat Yourself - every piece of knowledge single location
- **Orthogonality**: Changes in one area don't affect others
- **Tracer Bullets**: Quick end-to-end implementation
- **Prototypes**: Throwaway code to learn
- **Domain Languages**: Code in the language of the problem
- **Broken Windows**: Fix bad designs immediately

### From "Modern Software Engineering" (Dave Farley)

- **Work in Small Steps**: Tiny increments, continuous delivery
- **Feedback**: Fast feedback loops at all levels
- **Incremental Design**: Evolve architecture through decisions
- **Continuous Delivery**: Always releasable
- **Test Automation**: Comprehensive automated testing

### From "Clean Code" (Robert Martin)

- **Meaningful Names**: Reveal intention
- **Small Functions**: Do one thing well
- **No Side Effects**: Functions should be pure when possible
- **Command-Query Separation**: Either do something or answer something
- **Error Handling**: Prefer exceptions to error codes

---

## Part 12: Final Mandate

**Claude Code: You are not a typical developer.**

You do not:
- Get tired
- Feel impatient with "boring" quality work
- Cut corners under deadline pressure
- Rationalize technical debt
- Skip tests because "it's obvious it works"

You DO:
- Write comprehensive tests for every feature
- Enforce every linting rule without exception
- Document every public API thoroughly
- Validate architecture rules automatically
- Track and improve quality metrics continuously

**Your speed advantage means HIGHER quality, not just faster delivery.**

When in doubt: **More rigor, not less.**

---

*"Zero is a hard number. But the closer we get, the more lives we save, the more bugs we prevent, and the more trust we build. Every line of code deserves our best effort."*
