# Mutation Testing Skill

**Purpose**: Efficient mutation testing analysis without wasting tokens on large log files.

---

## Critical Rule: NEVER Read Mutation Files Directly

**ALWAYS use the `analyze_mutations.py` script or direct SQL queries.**

**NEVER read these files directly:**
- ❌ `.mutmut-cache` (binary SQLite database)
- ❌ `mutation_*.log` files (extremely verbose, 200K+ lines)
- ❌ `mutmut` command output logs
- ❌ Any mutation-related log files

**Why**: These files contain thousands of lines of repetitive mutation diffs that consume massive amounts of tokens (10K-50K+ tokens per file) with little useful information.

---

## Correct Approach: Use Analyze Script

### Always Use This
```bash
# Analyze all mutations
python scripts/analyze_mutations.py

# Analyze specific file (PREFERRED)
python scripts/analyze_mutations.py cli.py

# Analyze with custom cache
python scripts/analyze_mutations.py --cache .mutmut-cache

# Show more files
python scripts/analyze_mutations.py --top 50
```

**What you get:**
- Mutation score (killed/survived/total)
- Status breakdown
- Files with most survivors
- Sample of surviving mutant IDs and line numbers
- All in <500 tokens

### Direct SQL Queries (Alternative)

If `analyze_mutations.py` doesn't provide needed information, use direct SQL:

```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('.mutmut-cache')
cursor = conn.cursor()

# Get status counts
cursor.execute('SELECT status, COUNT(*) FROM Mutant GROUP BY status')
for status, count in cursor.fetchall():
    print(f"{status}: {count}")

# Get files with survivors
cursor.execute('''
    SELECT sf.filename, COUNT(*) as count
    FROM Mutant m, Line l, SourceFile sf
    WHERE m.line = l.id AND l.sourcefile = sf.id
      AND m.status = "bad_survived"
    GROUP BY sf.filename
    ORDER BY count DESC
''')
for filename, count in cursor.fetchall():
    print(f"{filename}: {count} survivors")

conn.close()
EOF
```

---

## Workflow

### Checking Mutation Test Progress

1. **Start mutation test** (in background if long-running):
   ```bash
   ./scripts/mutation.sh --paths-to-mutate start_green_stay_green/cli.py
   ```

2. **Check progress** (anytime):
   ```bash
   python scripts/analyze_mutations.py cli.py
   ```

3. **Wait for completion** - Don't check logs, use analyze script

4. **Analyze results**:
   ```bash
   python scripts/analyze_mutations.py cli.py
   ```

### Investigating Specific Mutants

If you need to see what a specific mutant changed:

```bash
# View one specific mutant (limited output)
mutmut show 42
```

**Only view individual mutants when absolutely necessary** - the analyze script usually provides sufficient context.

---

## Common Mistakes to Avoid

### ❌ WRONG
```bash
# Reading entire log file
cat mutation_cli.log

# Grepping through log
grep "survived" mutation_cli.log

# Reading cache directly
cat .mutmut-cache

# Tailing large log files
tail -1000 mutation_cli.log
```

**Impact**: 10,000-50,000+ tokens wasted per file read

### ✅ CORRECT
```bash
# Use analyze script
python scripts/analyze_mutations.py cli.py

# Or direct SQL for specific queries
python3 -c "import sqlite3; conn=sqlite3.connect('.mutmut-cache'); ..."
```

**Impact**: <500 tokens

---

## Summary

**Golden Rule**: Before reading ANY mutation-related file, ask yourself:

> "Can I get this information from `analyze_mutations.py` or a SQL query?"

**The answer is almost always YES.**

Only use `mutmut show <id>` for inspecting individual mutants when the analyze script has identified specific problematic mutants you need to investigate.

---

**Token Savings**: Following this skill saves 10,000-50,000 tokens per mutation testing session.
