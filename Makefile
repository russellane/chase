PROJECT = chase
include Python.mk
lint:: mypy
doc :: README.md

test:: cov_fail_under_100
cov_fail_under_100:
	python -m pytest --cov-fail-under 100 --cov=chase tests

# The following is for manual testing.
CHASE	:= python -m chase -s foy -e fom --use-datafiles

report:
	$(CHASE)

report_detail:
	$(CHASE) --detail

monthly:
	$(CHASE) --monthly

monthly_detail:
	$(CHASE) --monthly --detail

monthly_averages_only:
	$(CHASE) --monthly --averages-only

cashflow:
	@$(CHASE) --monthly | grep 'Average' | python -c 'import sys; print(f"Cashflow = {sum([(float(line.split()[1])) for line in sys.stdin]):.2f}")'

reports:	report report_detail monthly monthly_detail monthly_averages_only cashflow

baseline:
	$(MAKE) reports >baseline-`date +%Y-%m-%dT%H:%M:%S` 2>&1

charts:
	$(CHASE) --barchart
	$(CHASE) --piechart
	$(CHASE) --barchart --monthly
	$(CHASE) --piechart --monthly
	$(CHASE) --barchart --category Groceries --moving-average
	$(CHASE) --piechart --category Groceries
