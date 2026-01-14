# Start Green Stay Green

> A meta-tool for generating quality-controlled, AI-ready repositories

## Status

🚧 **Under Development** - Repository initialization in progress (Issue 1.1)

## What is Start Green Stay Green?

Start Green Stay Green is a CLI tool that scaffolds new software projects with enterprise-grade quality controls pre-configured. Unlike traditional scaffolding tools, Start Green Stay Green generates **AI-orchestrated quality infrastructure** including:

- CI/CD pipelines
- Quality control scripts
- AI subagent profiles
- Architecture enforcement rules
- Comprehensive testing infrastructure

## Quick Start

_Coming soon - See Issue 4.2 for CLI implementation_

## Development

This project follows the [Maximum Quality Engineering Framework](plan/MAXIMUM_QUALITY_ENGINEERING.md).

### Quality Workflow

We enforce the **Stay Green** workflow with 4 sequential quality gates:

1. **Local Pre-Commit**: Run `./scripts/check-all.sh` - all checks must pass
2. **CI Pipeline**: Push to branch - all CI jobs must show ✅
3. **Mutation Testing**: Score must be ≥ 80%
4. **Code Review**: Address all feedback - only merge with LGTM

**Never request review with failing checks. Never merge without LGTM.**

See [Stay Green Workflow](/reference/workflows/stay-green.md) for complete documentation.

### Project Structure

```
start_green_stay_green/
├── start_green_stay_green/    # Main package
│   ├── ai/                    # AI orchestration
│   ├── config/                # Configuration management
│   ├── generators/            # Component generators
│   ├── github/                # GitHub integration
│   └── utils/                 # Utilities
├── templates/                 # Jinja2 templates per language
├── reference/                 # Reference implementations
├── tests/                     # Test suite
└── plan/                      # Project planning documents
```

### Current Phase

**Phase 1: Foundation** - Setting up core infrastructure

- [x] Issue 1.1: Repository Initialization
- [ ] Issue 1.2: Python Project Configuration
- [ ] Issue 1.3: Pre-commit Configuration
- [ ] Issue 1.4: Scripts Directory
- [ ] Issue 1.5: CI Pipeline
- [ ] Issue 1.6: CLAUDE.md Configuration

See [SPEC.md](plan/SPEC.md) for complete project specification.

## License

_To be determined_

## Contributing

_Contributing guidelines coming in Phase 6_
