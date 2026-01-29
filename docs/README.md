# Start Green Stay Green - Documentation

## 📊 Live Quality Metrics Dashboard

View our live quality metrics dashboard: **[dashboard.html](https://geoffe-ga.github.io/start_green_stay_green/dashboard.html)**

The dashboard displays real-time quality metrics updated automatically after every merge to main:

- **Code Coverage**: Current test coverage (target: ≥90%)
- **Branch Coverage**: Branch-level coverage (target: ≥85%)
- **Mutation Score**: Mutation testing effectiveness (target: ≥80%)
- **Cyclomatic Complexity**: Average code complexity (target: ≤10)
- **Documentation Coverage**: Docstring coverage (target: ≥95%)
- **Security Issues**: Critical/high security vulnerabilities (target: 0)

## How It Works

1. **Automated Collection**: On every push to `main`, our GitHub Actions workflow runs all quality checks
2. **Metrics Generation**: Results are aggregated into `metrics.json`
3. **Live Deployment**: Dashboard and metrics are deployed to GitHub Pages
4. **Auto-Update**: Dashboard fetches latest `metrics.json` and displays live data

## Local Development

To view the dashboard locally with current metrics:

```bash
# Generate current metrics
python -c "
from start_green_stay_green.generators.metrics import MetricsGenerationConfig, MetricsGenerator
from pathlib import Path

config = MetricsGenerationConfig(
    language='python',
    project_name='start-green-stay-green',
    coverage_threshold=90,
    enable_dashboard=True,
)

generator = MetricsGenerator(None, config)
generator.write_dashboard(Path('docs'))
"

# Open in browser
open docs/dashboard.html  # macOS
```

## Files

- **`dashboard.html`**: Interactive metrics dashboard (auto-generated)
- **`metrics.json`**: Live metrics data (updated by CI)
- **`API_DOCUMENTATION.md`**: API documentation
- **`METRICS_DASHBOARD.md`**: Complete metrics generator documentation

## GitHub Actions

See [`.github/workflows/metrics.yml`](../.github/workflows/metrics.yml) for the automated metrics collection workflow.

## Questions?

For more information about the metrics system, see:
- [METRICS_DASHBOARD.md](METRICS_DASHBOARD.md) - Complete documentation
- [examples/README-METRICS-DASHBOARD.md](../examples/README-METRICS-DASHBOARD.md) - Production workflow guide
