# One target per table and figure in the paper. `make all` regenerates results/, the paper's tables and figures,
# checks every number, and builds the PDF. `make demo` is the quick smoke test (about a minute).
# Analysis runs in an isolated environment pinned by requirements-analysis.txt; training and the post-hoc replays
# use the project environment pinned by uv.lock (they import ppo.py and intrinsic.py).
AN  := uv run --isolated --no-project --with-requirements requirements-analysis.txt python
PY  := uv run --locked python
TABLES  := table1 table2 table3 table4 table5 table6 table7 table8 table9 table10 table11
FIGURES := figure1 figure2 figure3 figure4 figure5

.PHONY: all demo results tables-tex $(TABLES) $(FIGURES) numbers check paper arxiv posthoc extract train clean

all: results check paper

demo: tables-tex numbers check

results: $(TABLES) $(FIGURES) numbers

# --- tables: generated LaTeX (paper/tables/) plus the matching results/tableN_*.csv
tables-tex:
	$(AN) scripts/make_tables.py
$(TABLES): tables-tex
	$(AN) scripts/export_results.py $@

# --- figures: vector PDF/SVG in paper/figs/ plus the plotted data in results/figureN_*.csv
figure1: ; $(AN) scripts/fig_solve_tamper.py && $(AN) scripts/export_results.py figure1
figure2: ; $(AN) scripts/fig_entropy.py && $(AN) scripts/export_results.py figure2
figure3: ; $(AN) scripts/fig_cost_sweep.py && $(AN) scripts/export_results.py figure3
figure4: ; $(AN) scripts/fig_explore_vs_novelty.py && $(AN) scripts/export_results.py figure4
figure5: ; $(AN) scripts/fig_farming_growth.py && $(AN) scripts/export_results.py figure5

# --- every number quoted in the prose (paper/numbers.tex and results/numbers.json)
numbers: tables-tex
	$(AN) scripts/make_numbers.py && $(AN) scripts/export_results.py numbers

# --- regenerate and compare every number, table and hash; flag stray literals in the text
check:
	$(AN) scripts/check_numbers.py

paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

arxiv: paper
	sh scripts/make_arxiv.sh

# --- post-hoc analyses (Section 4, Table 2). Slow: bound check ~4 min; replay ~15 min on 12 cores.
posthoc:
	$(PY) scripts/bound_check.py data/bound-check.json 200
	$(PY) scripts/farming_policy_returns.py data/farming-policy-returns.json
	$(PY) scripts/bound_summary.py
	for k in B1 B2 B3 B4; do $(PY) scripts/tamper_policy_returns.py run $$k 40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59 data/replay_$$k.json & done; wait
	$(PY) scripts/tamper_policy_returns.py merge data/tamper-policy-returns.json data/replay_B1.json data/replay_B2.json data/replay_B3.json data/replay_B4.json

# --- re-extract the log series and the independent cross-check values from the raw records
extract:
	$(AN) scripts/extract_run_series.py data/scored-results data/run-series.json
	$(AN) scripts/extract_claims.py data/scored-results data/claims.json

# --- retrain one configuration: make train RUN=b1-tamper-on-growth-1-160-norm-on__bb00e7e5
# 20 seeds x 2M steps; about 17-20 min wall-clock on a 12-core Apple M4 Pro (one process per seed).
train:
	@test -n "$(RUN)" || (echo "usage: make train RUN=<config name in configs/>"; exit 1)
	cp configs/$(RUN).toml config.toml && ./run.sh

clean:
	cd paper && latexmk -C main.tex
