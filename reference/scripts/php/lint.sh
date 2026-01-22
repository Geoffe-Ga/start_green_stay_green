#!/usr/bin/env bash
# PHP linting script - runs all configured linters
set -euo pipefail

echo "=== Running PHP Linters ==="

# PHP-CS-Fixer - Code formatter check
echo "Running PHP-CS-Fixer..."
vendor/bin/php-cs-fixer fix --dry-run --diff

# PHPStan - Static analysis
echo "Running PHPStan..."
vendor/bin/phpstan analyse

# Psalm - Static analysis
echo "Running Psalm..."
vendor/bin/psalm

# PHPMD - Mess detector
echo "Running PHPMD..."
vendor/bin/phpmd src/ text cleancode,codesize,design,naming,unusedcode

echo "✓ All linters passed!"
