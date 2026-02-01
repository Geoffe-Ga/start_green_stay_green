#!/bin/bash
# Script to create backlog issues for language template support
# Related to issue #170: Generated projects missing core structure

set -e

echo "Creating backlog issues for language templates..."

# TypeScript Templates
echo "Creating TypeScript templates issue..."
gh issue create \
  --title "feat(templates): Add TypeScript project templates" \
  --body "## Feature Request

Add TypeScript project templates to enable \`sgsg init\` for TypeScript projects.

### Context

Issue #170 identified that generated projects are missing core structure. The fix implements Python templates first, but SGSG supports multiple languages. This issue tracks TypeScript template creation.

### What's Needed

Create \`templates/typescript/\` with:

- ✅ Source code directory structure (\`src/\`)
- ✅ \`package.json\` and \`tsconfig.json\`
- ✅ Hello World starter code (\`src/index.ts\`)
- ✅ Tests directory with example test (\`tests/\`, \`__tests__/\`, or \`*.test.ts\`)
- ✅ Development dependencies (\`package.json\` devDependencies)
- ✅ \`README.md\` template
- ✅ TypeScript-specific scripts (build, typecheck, etc.)

### Generator Functions

Implement or extend:
- \`_generate_project_structure_step()\` - TypeScript source layout
- \`_generate_starter_code_step()\` - TypeScript Hello World + test
- \`_generate_dependencies_step()\` - package.json generation
- \`_generate_readme_step()\` - TypeScript-specific README
- \`ScriptsGenerator\` updates - TypeScript build/check scripts

### Acceptance Criteria

- [ ] Templates exist in \`templates/typescript/\`
- [ ] \`sgsg init --language typescript\` generates functional project
- [ ] Generated project passes \`check-all.sh\`
- [ ] E2E integration test validates generated TypeScript projects
- [ ] All 3 gates pass (local pre-commit, CI, code review)

### Related

- Parent: #170 (Generated projects missing core structure)
- Implements: Phase 1 for TypeScript language support

### Priority

**MEDIUM** - Blocks TypeScript users from using SGSG effectively." \
  --label "enhancement,backlog,templates,typescript"

# Go Templates
echo "Creating Go templates issue..."
gh issue create \
  --title "feat(templates): Add Go project templates" \
  --body "## Feature Request

Add Go project templates to enable \`sgsg init\` for Go projects.

### Context

Issue #170 identified that generated projects are missing core structure. The fix implements Python templates first, but SGSG supports multiple languages. This issue tracks Go template creation.

### What's Needed

Create \`templates/go/\` with:

- ✅ Source code directory structure (standard Go layout)
- ✅ \`go.mod\` and \`go.sum\` templates
- ✅ Hello World starter code (\`main.go\`)
- ✅ Tests directory with example test (\`*_test.go\`)
- ✅ \`README.md\` template
- ✅ Go-specific scripts (build, test, fmt, vet, etc.)

### Generator Functions

Implement or extend:
- \`_generate_project_structure_step()\` - Go source layout
- \`_generate_starter_code_step()\` - Go Hello World + test
- \`_generate_dependencies_step()\` - go.mod generation
- \`_generate_readme_step()\` - Go-specific README
- \`ScriptsGenerator\` updates - Go build/check scripts

### Acceptance Criteria

- [ ] Templates exist in \`templates/go/\`
- [ ] \`sgsg init --language go\` generates functional project
- [ ] Generated project passes \`check-all.sh\`
- [ ] E2E integration test validates generated Go projects
- [ ] All 3 gates pass (local pre-commit, CI, code review)

### Related

- Parent: #170 (Generated projects missing core structure)
- Implements: Phase 1 for Go language support

### Priority

**MEDIUM** - Blocks Go users from using SGSG effectively." \
  --label "enhancement,backlog,templates,go"

# Rust Templates
echo "Creating Rust templates issue..."
gh issue create \
  --title "feat(templates): Add Rust project templates" \
  --body "## Feature Request

Add Rust project templates to enable \`sgsg init\` for Rust projects.

### Context

Issue #170 identified that generated projects are missing core structure. The fix implements Python templates first, but SGSG supports multiple languages. This issue tracks Rust template creation.

### What's Needed

Create \`templates/rust/\` with:

- ✅ Source code directory structure (Cargo package layout)
- ✅ \`Cargo.toml\` and \`Cargo.lock\` templates
- ✅ Hello World starter code (\`src/main.rs\` or \`src/lib.rs\`)
- ✅ Tests directory with example test (\`tests/\` or inline tests)
- ✅ \`README.md\` template
- ✅ Rust-specific scripts (build, test, clippy, fmt, etc.)

### Generator Functions

Implement or extend:
- \`_generate_project_structure_step()\` - Rust source layout
- \`_generate_starter_code_step()\` - Rust Hello World + test
- \`_generate_dependencies_step()\` - Cargo.toml generation
- \`_generate_readme_step()\` - Rust-specific README
- \`ScriptsGenerator\` updates - Rust build/check scripts

### Acceptance Criteria

- [ ] Templates exist in \`templates/rust/\`
- [ ] \`sgsg init --language rust\` generates functional project
- [ ] Generated project passes \`check-all.sh\`
- [ ] E2E integration test validates generated Rust projects
- [ ] All 3 gates pass (local pre-commit, CI, code review)

### Related

- Parent: #170 (Generated projects missing core structure)
- Implements: Phase 1 for Rust language support

### Priority

**MEDIUM** - Blocks Rust users from using SGSG effectively." \
  --label "enhancement,backlog,templates,rust"

# Swift Templates
echo "Creating Swift templates issue..."
gh issue create \
  --title "feat(templates): Add Swift project templates" \
  --body "## Feature Request

Add Swift project templates to enable \`sgsg init\` for Swift projects.

### Context

Issue #170 identified that generated projects are missing core structure. The fix implements Python templates first, but SGSG supports multiple languages. This issue tracks Swift template creation.

### What's Needed

Create \`templates/swift/\` with:

- ✅ Source code directory structure (Swift Package Manager layout)
- ✅ \`Package.swift\` template
- ✅ Hello World starter code (\`Sources/Main/main.swift\`)
- ✅ Tests directory with example test (\`Tests/\`)
- ✅ \`README.md\` template
- ✅ Swift-specific scripts (build, test, etc.)

### Generator Functions

Implement or extend:
- \`_generate_project_structure_step()\` - Swift source layout
- \`_generate_starter_code_step()\` - Swift Hello World + test
- \`_generate_dependencies_step()\` - Package.swift generation
- \`_generate_readme_step()\` - Swift-specific README
- \`ScriptsGenerator\` updates - Swift build/check scripts

### Acceptance Criteria

- [ ] Templates exist in \`templates/swift/\`
- [ ] \`sgsg init --language swift\` generates functional project
- [ ] Generated project passes \`check-all.sh\`
- [ ] E2E integration test validates generated Swift projects
- [ ] All 3 gates pass (local pre-commit, CI, code review)

### Related

- Parent: #170 (Generated projects missing core structure)
- Implements: Phase 1 for Swift language support

### Priority

**MEDIUM** - Blocks Swift users from using SGSG effectively." \
  --label "enhancement,backlog,templates,swift"

echo ""
echo "✅ Successfully created 4 backlog issues for language templates"
echo "   - TypeScript templates"
echo "   - Go templates"
echo "   - Rust templates"
echo "   - Swift templates"
