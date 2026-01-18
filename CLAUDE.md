# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python CLI tool that processes downloaded Chase Bank transaction CSV files and generates financial reports with charting capabilities. Published to PyPI as `rlane-chase`.

## Build Commands

```bash
make build          # Full pipeline: install deps, lint, test (100% coverage), build
make lint           # Run black, isort, flake8, mypy (strict mode)
make test           # Run pytest with 100% coverage requirement
make pytest_debug   # Run tests with --capture=no for debugging
make install        # Install via pipx after building
```

## Running the Application

```bash
# Run from source (use -m to run as module)
python -m chase -s foy -e fom --use-datafiles

# Makefile shortcuts for manual testing
make report         # Year-to-date category/merchant report
make monthly        # Monthly breakdown
make charts         # Generate bar and pie charts
```

## Architecture

Three-module structure in `chase/`:

- **cli.py** - `ChaseCLI(BaseCLI)` handles argument parsing and orchestration. Entry point: `chase.cli:main()`
- **chase.py** - `Chase` class processes CSV files, normalizes merchants via alias tables, categorizes transactions, aggregates data
- **chart.py** - `Chart` class renders matplotlib bar/pie charts

Data flow: CLI parses args → Chase reads CSVs → normalizes merchants (startswith_aliases → in_aliases) → applies category overrides → aggregates by category/merchant/month → outputs text reports or charts.

## Configuration

User config at `~/.chase.toml` defines:
- `datafiles` - glob pattern for CSV files (supports `~` expansion)
- `startswith_aliases` / `in_aliases` - merchant name normalization
- `categories_by_merchant` - category overrides
- `chart_exclude_categories` - categories to hide from charts

## Code Style

- Line length: 97 characters
- Type checking: mypy strict mode
- Docstrings: Google convention
- Test coverage: 100% minimum (enforced via `COV_FAIL_UNDER=100`)

## Dependencies

Uses `rlane-libcli` as base CLI framework. Main deps: pandas (CSV/data), matplotlib/numpy (charts).
