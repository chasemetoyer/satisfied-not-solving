# Satisfied, Not Solving: Wireheading of Bounded Homeostatic Rewards in Reinforcement Learning

Code, data and every result file for the paper by Chase J. Metoyer (Northeastern University).

- **Paper:** `paper/main.pdf` (LaTeX source in `paper/`). The arXiv link will be added here once it is announced.
- **Archived snapshot:** release materials on Zenodo, [doi:10.5281/zenodo.23708845](https://doi.org/10.5281/zenodo.23708845).
- **Versions:** the paper's file links point to tag `v1.0`; tag `v1.0.1` is the repository snapshot archived on
  Zenodo. `main` holds the current paper.

**What the paper finds.** We give PPO agents a bounded "satiation" reward (needs that build up over time, where
relieving them is rewarding) and a cheap action that resets the needs. With that action, agents solved MiniGrid
DoorKey-8x8 in 2 of 80 seeds, against 71 of 80 without it. In KeyCorridorS3R1 they solved 0 of 20, against 20 of 20.
This happens although a telescoping argument shows solving still beats any policy that abandons the task. All
predictions were pre-registered, and the paper reports each one that failed.

## Reproduce

Requirements:
- [uv](https://docs.astral.sh/uv/), which installs Python 3.12 and the pinned packages itself;
- a TeX distribution with `latexmk` and `pdflatex`, needed only for `make paper`.

```sh
git clone https://github.com/chasemetoyer/satisfied-not-solving && cd satisfied-not-solving
make demo   # smoke test, ~5 s: regenerate every table and number, then check them
make all    # regenerate results/, check every number, build paper/main.pdf (~1 min)
```

`make all` rebuilds everything in `results/` from the committed data in `data/`, without retraining.

`make check` does the following:
- regenerates the paper's number macros (`paper/numbers.tex`) and tables, and fails on any difference;
- verifies every source snapshot against its SHA-256 sum;
- cross-checks 110 headline values against an independently extracted copy (`data/claims.json`);
- fails on any literal number in the text that is neither generated nor a declared design constant.

Measured on one Apple M4 Pro (12 CPU cores, 24 GB, no GPU):

| Command | What it does | Time |
|---|---|---|
| `make demo` | regenerate tables and numbers, run all checks | ~5 s |
| `make all` | the above, plus all figures, all result files and the PDF | ~1 min |
| `make extract` | re-extract the log series and the cross-check values from the raw run records | ~1 min |
| `make posthoc` | rerun the post-hoc analyses (bound check, learned-farmer returns, tamper-policy replay) from the checkpoints | ~10 min |
| `make train RUN=<config>` | retrain one configuration: 20 seeds x 2M environment steps | ~17-20 min |

## Paper artifact to command and result file

Every result file is plain text (CSV or JSON). Each one is named after the table or figure it backs, and each
table and figure caption in the paper links to its file.

| Paper | Command | Result file(s) |
|---|---|---|
| Table 1, post-hoc check (a): solving returns vs the cap | `make table1` | `results/table1_bound_check.csv` |
| Table 2, post-hoc replay of the tamper-on policies | `make table2` | `results/table2_replay.csv`, `results/table2_replay_per_seed.csv` |
| Table 3, tamper-cost sweep | `make table3` | `results/table3_cost_sweep.csv` |
| Table 4, cycle-farming counts | `make table4` | `results/table4_farming.csv` |
| Table 5, hypothesis-level accounting | `make table5` | `results/table5_hypotheses.csv` |
| Table 6, every pre-registered prediction (94 rows) | `make table6` | `results/table6_predictions.csv` |
| Table 7, round-4 per-seed "done" share | `make table7` | `results/table7_seeds_round4_tamper.csv`, `results/table7_9_partd_per_seed.csv` |
| Table 8, round-5 per-seed presses per step | `make table8` | `results/table8_seeds_round5_cost.csv`, `results/table8_seeds_round5_cost_per_seed.csv` |
| Table 9, Part D per seed | `make table9` | `results/table9_seeds_partd.csv`, `results/table7_9_partd_per_seed.csv` |
| Table 10, hyperparameters | `make table10` | `results/table10_hyperparameters.csv` |
| Table 11, label-to-run-ID map | `make table11` | `results/table11_runs.csv` |
| Figure 1, solve rates with and without the tamper action | `make figure1` | `results/figure1_solve_rates.csv` |
| Figure 2, policy entropy over training | `make figure2` | `results/figure2_entropy.csv` |
| Figure 3, tamper-cost sweep | `make figure3` | `results/figure3_cost_sweep.csv`, `results/figure3_threshold.csv` |
| Figure 4, explore-only satiation vs episodic novelty | `make figure4` | `results/figure4_explore_vs_novelty.csv` |
| Figure 5, farming against need growth | `make figure5` | `results/figure5a_farming_doorkey.csv`, `results/figure5b_keycorridor_pickups.csv` |
| Every number quoted in the text | `make numbers` | `results/numbers.json` |

**Tracing a number.** `results/numbers.json` lists every value quoted in the paper's prose (about 650). Each entry
has the printed text and the file and field it comes from. To find where a number in the paper comes from, search
that file for it.

**How the table files are made.** The `tableN_*.csv` files are the paper's tables exactly as printed. The
`*_per_seed.csv` files hold the unrounded per-seed values behind them.

## Layout

```
README.md, LICENSE, CITATION.cff
Makefile                  one target per table and figure; see above
pyproject.toml, uv.lock   pinned training environment (Python 3.12, PyTorch 2.14.1, Gymnasium 1.4.0, MiniGrid 3.2.0)
requirements.txt          the same pins, exported for pip
requirements-analysis.txt pinned analysis environment (NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2)
ppo.py                    PPO learner, network and MiniGrid wrappers
intrinsic.py              satiation reward (Homeostatic), event detector, tamper action, controls
run_seeds.py, run.sh      run every seed of config.toml in parallel
config.toml               the configuration run.sh trains (copied from configs/ by `make train`)
configs/                  the exact configuration of every run, named <experiment>__<run id>
data/
  sources/                byte-for-byte snapshots of the scored results the paper reads (+ SHA256SUMS)
  scored-results/         the full scored-results folder for rounds 2-5: scoring scripts, reports, replays
  preregistration/        pre-registration files, amendments and hash records (rounds 3-5)
  raw/run-records/        every run: command, console log, config, per-seed metrics.jsonl and summary.json
  raw/checkpoints/        final policy checkpoints (used by the post-hoc replays)
  raw/run-list.txt        run ID, experiment, commit and recorded wall-clock time of every run
  *.json                  post-hoc and extracted data (bound check, replays, log series, numbers)
scripts/                  everything that turns data into results: tables, figures, numbers, checks, post-hoc analyses
results/                  committed outputs, one file per table and figure (see above)
paper/                    LaTeX source, generated tables and figures, and the compiled PDF
```

## What is pinned

- **Seeds:** listed in every run's config under `[run] seeds`: 40-59 for DoorKey in rounds 4-5, 60-79 for
  KeyCorridor, and as stated in the paper for earlier rounds.
- **Environments:** `MiniGrid-DoorKey-8x8-v0` and `MiniGrid-KeyCorridorS3R1-v0` from MiniGrid 3.2.0.
- **Dependencies:** `uv.lock` for training; `requirements-analysis.txt` for the analysis scripts.
- **Python:** the runs used CPython 3.12.12, recorded in each run log. On that Python, `uv.lock` selects
  NumPy 2.5.4.
- **Hyperparameters:** in each `configs/*.toml`, summarized in Table 10.
- **Post-hoc analyses:** these use fixed seeds and layouts (environment seeds 10000-10199) and sampled actions with
  seeded generators.

## Notes

- **Code version.** The training code at the root is the version used in round 5. Earlier rounds ran earlier
  versions, identified by the commit in `data/raw/run-list.txt`. The round-4 and round-5 pre-registrations each
  record a regression check: with the new options off, training was bit-identical to the previous round.
- **Detector implementation.** The paper's Setup and Limitations describe two properties of the archived reward
  implementation, and the code here is left exactly as it was run:
  - the event detector's door cache is empty during the first episode of each training environment;
  - grasp and open events are not detected on the step that ends an episode. The code comment saying
    terminal-step pick-ups cannot happen is inaccurate.
- **Pre-registration lock times are self-reported.** Each hash record shows that a file is unchanged since it was
  hashed, not when it was written. See Appendix G of the paper.
- **KeyCorridor naming.** The paper names the KeyCorridor runs K1-K6. The files here call them C1-C6, and Table 11
  maps the names.
- **Paths.** In run commands and logs, the home directory is replaced by `~`.

## License and citation

- **Code:** MIT (see `LICENSE`).
- **Data and result files:** also released under CC BY 4.0, matching the Zenodo archive.
- **Citation:** please cite the paper; `CITATION.cff` has the details.
