### chase - Process Chase Bank transaction files

#### Usage
    chase [--no-color] [--no-exclude-chart-categories] [--totals-only]
          [--averages-only] [--monthly] [--category CATEGORY] [--barchart]
          [--piechart] [--detail] [--moving-average] [-s START_DATE]
          [-e END_DATE] [--use-datafiles] [-h] [-v] [-V] [--config FILE]
          [--print-config] [--print-url] [--completion [SHELL]]
          [files ...]
    
Process Chase Bank transaction files.

#### Positional Arguments
    files               CSV files to process.

#### Options
    --no-color          Do not print in color (default: `False`).
    --no-exclude-chart-categories
                        Do not exclude select categories for charts (default:
                        `False`).
    --totals-only       Print totals only (default: `False`).
    --averages-only     Print averages only (implies `--monthly`)
                        (`--(bar|pie)chart` may also be given) (default:
                        `False`).
    --monthly           Generate a monthly report (default: `False`).
    --category CATEGORY
                        Limit transactions to `CATEGORY`.
    --barchart          Display a barchart of category totals (default:
                        `False`).
    --piechart          Display a piechart of category totals (default:
                        `False`).
    --detail            Include transaction details in the report (default:
                        `False`).
    --moving-average    Plot a moving average on the chart (default: `False`).
    -s START_DATE, --start START_DATE
                        Print transactions at or after `start_date`
                        (inclusive) (YYYY-MM-DD). Defaults to the epoch. Use
                        `foy` to specify the first of this year.
    -e END_DATE, --end END_DATE
                        Print transactions prior to `end_date` (exclusive)
                        (YYYY-MM-DD). Defaults to the end of time. Use `fom`
                        to specify the first of this month.
    --use-datafiles     Process the CSV files defined in the config file
                        (default: `False`).

#### General options
    -h, --help          Show this help message and exit.
    -v, --verbose       `-v` for detailed output and `-vv` for more detailed.
    -V, --version       Print version number and exit.
    --config FILE       Use config `FILE` (default: `~/.chase.toml`).
    --print-config      Print effective config and exit.
    --print-url         Print project url and exit.
    --completion [SHELL]
                        Print completion scripts for `SHELL` and exit
                        (default: `bash`).

For example,

Print each Category, in descending order of the total spent on each category,
and within each category, print each Merchant, in descending order of the
total spent with each Merchant.

    python -m chase file...
