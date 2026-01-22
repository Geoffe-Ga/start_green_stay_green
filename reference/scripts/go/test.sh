#!/usr/bin/env bash
# Go testing script - runs test suite with coverage
set -euo pipefail

echo "=== Running Go Tests ==="

# Run go test with coverage
go test -v -race -coverprofile=coverage.out -covermode=atomic ./...

# Check coverage threshold (90%)
go tool cover -func=coverage.out | tail -1 | awk '{print $3}' | sed 's/%//' | awk '{if ($1 < 90) {print "Coverage below 90%: " $1 "%"; exit 1} else {print "Coverage: " $1 "%"}}'

echo "✓ Tests passed with required coverage!"
