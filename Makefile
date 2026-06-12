.PHONY: install regressions-nl regressions-ndbi plots tables all clean

install:
	pip install -r requirements.txt

# Night-lights outcome
regressions-nl:
	python src/regression/run_nl_ols_pooled.py
	python src/regression/run_nl_ols_by_state.py

# NDBI (built-up) outcome
regressions-ndbi:
	python src/regression/run_ndbi_pooled.py
	python src/regression/run_ndbi_by_state.py
	python src/regression/run_ndbi_ols_pooled.py
	python src/regression/run_ndbi_ols_by_state.py

# All regressions
regressions: regressions-nl regressions-ndbi

# Figures
plots:
	python src/visualization/generate_ols_plots.py
	python src/visualization/plot_coefficients.py
	python src/visualization/plot_state_trends.py

# Paper-ready tables
tables:
	python scripts/build_paper_table.py
	python scripts/build_paper_table_ndbi.py
	python scripts/build_paper_table_nl_ols.py
	python scripts/build_paper_table_ndbi_ols.py

# Full pipeline
all: regressions plots tables

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -name "*.pyc" -delete
