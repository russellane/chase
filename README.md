### chase - Process Chase Bank transaction files

#### Usage
    chase [--totals-only] [--detail] [--monthly] [--averages-only]
          [--barchart | --piechart] [--moving-average]
          [--no-exclude-chart-categories] [-s START_DATE] [-e END_DATE]
          [--category CATEGORY] [--no-color] [--use-datafiles]
          [--print-sample-config] [-h] [-v] [-V] [--config FILE]
          [--print-config] [--print-url] [--completion [SHELL]]
          [FILES ...]
    
Process downloaded Chase Bank transaction files.

#### Category/Merchant Report
  By default, `chase` prints the Category/Merchant Report:
  
  List each Category, in descending order of the amount spent on each
  category.  Within each Category, list each Merchant, in descending
  order of the amount spent on each Merchant.

    --totals-only       List Categories and Totals only (suppress Merchants)
                        (default: `False`).
    --detail            List Transactions under Merchants, in chronological
                        order (default: `False`).

#### Category Monthly Report
  List each Category, in descending order of the amount spent on each
  category.  Within each Category, list each Month, and the amount
  spent on the category that month.

    --monthly           Print Category Monthly Report (default: `False`).
    --averages-only     List averages only (implies `--monthly`) `--barchart`
                        or `--piechart` may also be given) (default: `False`).

#### Charting options
    --barchart          Display a barchart of the report (default: `False`).
    --piechart          Display a piechart of the report (default: `False`).
    --moving-average    Plot a moving average on a barchart (default:
                        `False`).
    --no-exclude-chart-categories
                        Do not exclude select categories for charts. The
                        categories are listed under `chart_exclude_categories`
                        in the config file (default: `False`).

#### Filtering options
    -s, --start START_DATE
                        Print transactions at or after `START_DATE`
                        (inclusive) (YYYY-MM-DD). Defaults to the epoch. Use
                        `foy` to specify the first of this year.
    -e, --end END_DATE  Print transactions prior to `END_DATE` (exclusive)
                        (YYYY-MM-DD). Defaults to the end of time. Use `fom`
                        to specify the first of this month.
    --category CATEGORY
                        Limit transactions to `CATEGORY`. If `--barchart` or
                        `--piechart` are also given, then `--monthly` is
                        implied.

#### Misc options
    --no-color          Do not print report in color (default: `False`).

#### Datafile options
    --use-datafiles     Process the `CSV` files defined under `datafiles` in
                        the config file (default: `False`).
    FILES               The `CSV` file(s) to process.

#### Category Totals Chart
  Plot the Total amount spent on each category across the date-range,
  in descending order of the amount spent on each category.  This is a
  visualization of the Category/Merchant Report with `--totals-only`.
  Use `--barchart` or `--piechart` to display this chart.

#### Monthly Averages Chart
  Plot the Average amount spent on each category per month, in
  descending order of the amount spent on each category.  This is a
  visualization of the Category Monthly Report with `--averages-only`.
  Use `--barchart` or `--piechart`, along with `--monthly` or
  `--averages-only`, to display this chart.

#### Monthly Category Chart
  Plot the Amount spent each month on a given category.  Use
  `--barchart` or `--piechart`, along with `--category CATEGORY`,
  to display this chart.

#### Configuration File
  The configuration file defines these elements:
  
      `datafiles` (str):  Points to the `CSV` files to process. May
                          begin with `~`, and may contain wildcards.
  
      `chart_exclude_categories` (list[str]): List of categories
                          to not plot on charts.
  
      `startswith_aliases` (mapping table): Map merchants that start
                          with the left-string to the right-string.
  
      `in_aliases` (mapping table): Map merchants that contain
                          the left-string to the right-string.
  
      `categories_by_merchant` (mapping table): Re-categorize the merchants
                          on the left to the Categories on the right.

    --print-sample-config
                        Print a sample configuration file.

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
