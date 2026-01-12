#!/bin/bash
cd /Users/geoffgallinger/Projects/start_green_stay_green/worktrees/issue-3-precommit

# Add the new and modified files
git add .secrets.baseline
git add .pre-commit-config.yaml
git add PRECOMMIT_CONFIG_SUMMARY.md

# Commit with the message
git commit -F .commit_message.txt

# Clean up the temporary files
rm -f .commit_message.txt

# Show the result
git log --oneline -1
