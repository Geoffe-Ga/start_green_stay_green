#!/usr/bin/env python3
"""Regenerate docs/dashboard.html from the MetricsGenerator template.

This script keeps docs/dashboard.html in sync with the template defined
in start_green_stay_green/generators/metrics.py. It is called by the
metrics CI workflow before deploying to GitHub Pages.

Usage:
    python scripts/regenerate_dashboard.py
    python scripts/regenerate_dashboard.py --output-dir docs
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from start_green_stay_green.generators.metrics import MetricsGenerationConfig
from start_green_stay_green.generators.metrics import MetricsGenerator


def main() -> int:
    """Regenerate dashboard.html from the template."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs"),
        help="Output directory for dashboard.html (default: docs)",
    )
    parser.add_argument(
        "--project-name",
        default="start-green-stay-green",
        help="Project name for the dashboard (default: start-green-stay-green)",
    )
    args = parser.parse_args()

    config = MetricsGenerationConfig(
        language="python",
        project_name=args.project_name,
    )
    generator = MetricsGenerator(None, config)
    result = generator.write_dashboard(args.output_dir)

    if result is None:
        print("Error: Dashboard generation is disabled in config", file=sys.stderr)
        return 1

    print(f"Regenerated {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
