# Metrics Dashboard - Production Workflow

This document explains how the metrics dashboard works in production SGSG projects.

## Architecture

```
┌─────────────────┐
│  GitHub Actions │  ← CI runs quality checks
│    Workflow     │
└────────┬────────┘
         │
         ├── pytest --cov → coverage.json
         ├── radon cc → complexity
         ├── interrogate → docs coverage
         └── bandit → security scan
         │
         ▼
┌─────────────────┐
│  Generate       │  ← Python script aggregates results
│  metrics.json   │
└────────┬────────┘
         │
         ├── Option 1: Upload as GitHub Actions Artifact
         ├── Option 2: Deploy to GitHub Pages
         └── Option 3: Commit to gh-pages branch
         │
         ▼
┌─────────────────┐
│  Dashboard      │  ← Fetches metrics.json via HTTP
│  (HTML+JS)      │
└─────────────────┘
```

## Files in This Example

- **`dashboard-production.html`** - Fully functional dashboard with data fetching
- **`metrics.json`** - Example metrics data (generated from actual project)
- **`metrics-workflow.yml`** - GitHub Actions workflow example
- **`README-METRICS-DASHBOARD.md`** - This file

## How It Works

### 1. CI Pipeline (GitHub Actions)

The CI workflow runs quality checks and generates `metrics.json`:

```yaml
- name: Run tests with coverage
  run: pytest --cov=. --cov-report=json

- name: Generate metrics.json
  run: python scripts/generate_metrics.py  # Aggregates all reports
```

### 2. Metrics Data Format

```json
{
  "timestamp": "2026-01-28T15:46:43.063681",
  "project": "start-green-stay-green",
  "thresholds": {
    "coverage": 90,
    "branch_coverage": 85,
    "mutation_score": 80,
    "complexity": 10,
    "docs_coverage": 95,
    "security_issues": 0
  },
  "metrics": {
    "coverage": 92.62,
    "coverage_status": "pass",
    "branch_coverage": 90.26,
    "branch_coverage_status": "pass",
    "mutation_score": 85.0,
    "mutation_status": "pass",
    "complexity_avg": 4.8,
    "security_issues": 0,
    "security_status": "pass"
  }
}
```

### 3. Deployment Options

#### Option A: GitHub Pages (Recommended)

```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: .
```

Dashboard URL: `https://username.github.io/repo/dashboard.html`

#### Option B: GitHub Actions Artifacts

```yaml
- name: Upload metrics artifact
  uses: actions/upload-artifact@v4
  with:
    name: quality-metrics
    path: metrics.json
```

Fetch via: `https://api.github.com/repos/owner/repo/actions/artifacts`

#### Option C: Commit to gh-pages Branch

```bash
git checkout gh-pages
cp metrics.json dashboard.html .
git commit -m "Update metrics"
git push
```

### 4. Dashboard Data Fetching

The dashboard JavaScript fetches data automatically:

```javascript
async function loadMetrics() {
    const response = await fetch('metrics.json');
    const data = await response.json();
    updateDashboard(data);
}
```

## Viewing the Example

### Local Viewing

1. Open `dashboard-production.html` in your browser
2. It will load `metrics.json` from the same directory
3. See real metrics from start-green-stay-green project

```bash
# From this directory:
open dashboard-production.html  # macOS
# or
firefox dashboard-production.html  # Linux
# or
start dashboard-production.html  # Windows
```

### Production Setup

1. Add workflow to `.github/workflows/metrics.yml`
2. Enable GitHub Pages in repository settings
3. Dashboard auto-updates on every push to main

## SGSG Integration

When you run `sgsg init`, it generates:

1. **Metrics Generator** (`generators/metrics.py`)
   - Creates dashboard template
   - Generates metrics.yml config
   - Creates CI integration snippets

2. **GitHub Actions Workflow** (`.github/workflows/ci.yml`)
   - Runs all quality checks
   - Generates metrics.json
   - Deploys to GitHub Pages

3. **Dashboard** (`docs/dashboard.html`)
   - Responsive dark theme
   - Real-time data updates
   - Status indicators (PASS/FAIL)

## Real Project Example

See the **start-green-stay-green** project itself:

- **CI Workflow**: `.github/workflows/ci.yml`
- **Scripts**: `./scripts/coverage.sh`, `./scripts/complexity.sh`
- **Pre-commit**: `.pre-commit-config.yaml` (runs checks locally)

## Thresholds

All thresholds are configurable during `sgsg init`:

| Metric | Default | Adjustable |
|--------|---------|------------|
| Code Coverage | 90% | ✅ |
| Branch Coverage | 85% | ✅ |
| Mutation Score | 80% | ✅ |
| Complexity | ≤10 | ✅ |
| Docs Coverage | 95% | ✅ |
| Security Issues | 0 | ✅ |

## Benefits

1. **Visual Progress Tracking** - See quality trends over time
2. **Stakeholder Communication** - Share dashboard URL with team
3. **CI Integration** - Auto-updates on every merge
4. **Zero Maintenance** - Fully automated in CI pipeline
5. **Customizable** - Modify thresholds per project needs

## Next Steps

To implement in your SGSG project:

```bash
# 1. Generate metrics infrastructure
sgsg init --enable-metrics-dashboard

# 2. Commit generated files
git add .github/workflows/metrics.yml docs/dashboard.html
git commit -m "feat: add metrics dashboard"

# 3. Enable GitHub Pages (Settings → Pages)
# Source: gh-pages branch or /docs folder

# 4. Push and view
git push
# Dashboard: https://username.github.io/repo/dashboard.html
```

## Questions?

See:
- **Full SGSG Docs**: https://github.com/Geoffe-Ga/start_green_stay_green
- **Metrics Generator**: `start_green_stay_green/generators/metrics.py`
- **Example Workflows**: `.github/workflows/`
