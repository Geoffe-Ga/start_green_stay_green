#!/usr/bin/env bash
# Go linting script - runs all configured linters
set -euo pipefail

echo "=== Running Go Linters ==="

# go vet - Built-in Go linter
echo "Running go vet..."
go vet ./...

# golangci-lint - Comprehensive linter
echo "Running golangci-lint..."
golangci-lint run

# staticcheck - Advanced static analysis
echo "Running staticcheck..."
staticcheck ./...

echo "✓ All linters passed!"
