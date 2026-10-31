"""Write results/: one committed text file per table and figure in the paper, plus every quoted number.

Tables: each results/tableN_*.csv is the paper's table exactly as printed, converted from paper/tables/*.tex (run
make_tables.py first). Per-seed tables additionally get a per-seed CSV with unrounded values.
Figures: each results/figureN_*.csv holds the exact data the figure script plots.
Numbers: results/numbers.json lists every value quoted in the prose, with the file and field it comes from.

Usage (repo root): python scripts/export_results.py [name ...]   (no names: write everything)
"""
import csv, json, re, shutil, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from figdata import J, cp  # noqa: E402

ROOT = HERE.parent
TAB, RES, DATA = ROOT / "paper" / "tables", ROOT / "results", ROOT / "data"


def write_csv(name, header, rows):
    RES.mkdir(exist_ok=True)
    with open(RES / name, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


def clean(cell):
    s = cell.strip()
    s = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}\{(.*)\}", r"\1", s)
    s = re.sub(r"\$([0-9.]+)\\times10\^\{(-?\d+)\}\$", r"\1e\2", s)          # p-values
    s = re.sub(r"\\textsuperscript\{\$?\\dagger\$?\}", " (tamper-tested)", s)
    s = re.sub(r"\\textsuperscript\{([^}]*)\}", r" [\1]", s)
    s = re.sub(r"\\(textbf|emph|texttt)\{([^}]*)\}", r"\2", s)
    for a, b in (("$\\leq$", "<="), ("$\\geq$", ">="), ("$>$", ">"), ("$<$", "<"), ("$\\times$", "x"), ("\\%", "%"),
                 ("--", "-"), ("``", '"'), ("''", '"'), ("\\&", "&"), ("\\_", "_"), ("\\rightarrow", "->"), ("\\bar D", "mean D")):
        s = s.replace(a, b)
    for a, b in (("\\leq", "<="), ("\\geq", ">="), ("\\gamma", "gamma"), ("\\dagger", "(tamper-tested)")):
        s = s.replace(a, b)
    s = s.replace("$", "").replace("{", "").replace("}", "").replace("\\", "")
    return re.sub(r"\s+", " ", s).strip()


def tex_table(texname, csvname):
    """Every row of a generated LaTeX table, as printed (header rows included)."""
    t = (TAB / texname).read_text()
    t = t.split("\\endfoot", 1)[1] if "\\endfoot" in t else t      # longtable: body only (headers re-added below)
    rows = []
    for line in t.splitlines():
        line = line.strip()
        if not line.endswith("\\\\") or line.startswith(("\\caption", "%")):
            continue
        cells = [clean(c) for c in re.split(r"(?<!\\)&", line[:-2])]
        if any(cells):
            rows.append(cells)
    if "\\endfoot" in (TAB / texname).read_text():               # longtable header from its first-head block
        head = (TAB / texname).read_text().split("\\toprule", 1)[1].split("\\midrule", 1)[0]
        hdr = [[clean(c) for c in l.strip()[:-2].split(" & ")] for l in head.splitlines() if l.strip().endswith("\\\\")]
        rows = hdr + rows
    width = max(len(r) for r in rows)
    write_csv(csvname, [f"col{i + 1}" for i in range(width)], [r + [""] * (width - len(r)) for r in rows])


TABLES = {
    "table1": ("bound.tex", "table1_bound_check.csv"), "table2": ("replay.tex", "table2_replay.csv"),
    "table3": ("cost.tex", "table3_cost_sweep.csv"), "table4": ("farming.tex", "table4_farming.csv"),
    "table5": ("accounting.tex", "table5_hypotheses.csv"), "table6": ("predictions.tex", "table6_predictions.csv"),
    "table7": ("seeds_r4.tex", "table7_seeds_round4_tamper.csv"), "table8": ("seeds_r5b.tex", "table8_seeds_round5_cost.csv"),
    "table9": ("seeds_d.tex", "table9_seeds_partd.csv"), "table10": ("hyper.tex", "table10_hyperparameters.csv"),
    "table11": ("runs.tex", "table11_runs.csv"),
}


def per_seed_extras(name):
    """Unrounded per-seed values behind the per-seed and replay tables."""
    if name == "table2":
        tr = J("tamper-policy-returns.json", src=False)
        lab = {"B1": "growth 1/160, norm on", "B2": "growth 1/160, norm off", "B3": "growth 1/40, norm on", "B4": "growth 1/40, norm off"}
        rows = [[lab[k.split("/")[0]], k.split("/")[1], v["mean_disc_int"], v["mean_disc_total"], v["mean_mean_drive"],
                 v["mean_success"], v["mean_press_share"], v["train_press_share"]] for k, v in tr["policies"].items()]
        write_csv("table2_replay_per_seed.csv", ["setting", "seed", "disc_intrinsic_return", "disc_total_return",
                  "time_averaged_drive", "success_rate", "press_share_replay", "press_share_training_log"], rows)
    if name in ("table7", "table9"):
        pd = J("part-d-results.json")
        rows = []
        for run, seeds in pd["seeds"].items():
            for s, d in seeds.items():
                rows.append([run, s, d["first_goal_step"], d["cls"], d["peak_success"], d["final_success"], d["declined"],
                             d["entropy_final10"], d["done_frac_final10"], d["rise_step"], d["decline_step"], d["order"]])
        write_csv("table7_9_partd_per_seed.csv", ["run", "seed", "first_goal_step", "class", "peak_success", "final_success",
                  "declined", "entropy_final10", "done_share_final10", "rise_step", "decline_step", "order"], rows)
    if name == "table8":
        rs = J("run-series.json", src=False)["presses"]
        rows = [[k, s, v["presses_per_step"], v["presses_per_episode"], v["mean_len_final10"], v["category"]]
                for k in ("B1", "B9", "B10", "B11", "A1b") for s, v in rs[k].items()]
        write_csv("table8_seeds_round5_cost_per_seed.csv", ["run", "seed", "presses_per_step", "presses_per_episode",
                  "mean_episode_length_final10", "category"], rows)


def figure1():
    r4, r5 = J("round4-scores.json")["runs"], J("round5-scores.json")["runs"]
    spec = [("DoorKey growth 1/160 norm on", [("task-only", r5, "A1"), ("satiation (ours)", r4, "A1b"), ("satiation (ours) + tamper", r4, "B1")]),
            ("DoorKey growth 1/160 norm off", [("task-only", r5, "A2"), ("satiation (ours)", r4, "B7"), ("satiation (ours) + tamper", r4, "B2")]),
            ("DoorKey growth 1/40 norm on", [("satiation (ours)", r4, "B5"), ("satiation (ours) + tamper", r4, "B3")]),
            ("DoorKey growth 1/40 norm off", [("satiation (ours)", r4, "B6"), ("satiation (ours) + tamper", r4, "B4")]),
            ("KeyCorridorS3R1 growth 1/160 norm on", [("task-only", r5, "C6"), ("satiation (ours)", r5, "C1"), ("satiation (ours) + tamper", r5, "C5")])]
    rows = []
    for g, arms in spec:
        for lab, sc, k in arms:
            d = sc[k]; s, n = d["categories"]["solve"], d["n"]; lo, hi = cp(s, n)
            rows.append([g, lab, d["run"][:8], s, n, s / n, lo, hi])
    write_csv("figure1_solve_rates.csv", ["setting", "arm", "run_id", "solved", "seeds", "solve_rate", "ci95_lo", "ci95_hi"], rows)


def figure2():
    rs = J("run-series.json", src=False)["entropy"]
    lab = {"B1": "growth 1/160 norm on, tamper", "A1b": "growth 1/160 norm on, no tamper", "B2": "growth 1/160 norm off, tamper",
           "B7": "growth 1/160 norm off, no tamper", "B3": "growth 1/40 norm on, tamper", "B5": "growth 1/40 norm on, no tamper",
           "B4": "growth 1/40 norm off, tamper", "B6": "growth 1/40 norm off, no tamper"}
    rows = [[lab[k], s, st, e] for k, seeds in rs.items() for s, v in seeds.items() for st, e in zip(v["step"], v["entropy"])]
    write_csv("figure2_entropy.csv", ["setting", "seed", "env_step", "policy_entropy"], rows)


def figure3():
    r5, rs, s0 = J("round5-scores.json")["runs"], J("run-series.json", src=False)["presses"], J("step0-tamper-cost.json")
    rows = []
    for sk, pk, c in (("r4-B1", "B1", 0.0), ("B9", "B9", 0.01), ("B10", "B10", 0.1), ("B11", "B11", 1.0)):
        k, n = r5[sk]["categories"]["solve"], r5[sk]["n"]; lo, hi = cp(k, n)
        for s, v in rs[pk].items():
            rows.append([c, s, v["presses_per_step"], k, n, lo, hi])
    write_csv("figure3_cost_sweep.csv", ["tamper_cost", "seed", "presses_per_step", "solved", "seeds", "solve_ci95_lo", "solve_ci95_hi"], rows)
    write_csv("figure3_threshold.csv", ["growth", "largest_cost_still_tampering", "smallest_cost_no_tamper"],
              [[g, s0[g]["largest_c_still_tampers"], s0[g]["smallest_c_no_tamper"]] for g in ("1/160", "1/40")])


def figure4():
    r4 = J("round4-scores.json")["runs"]
    rows = [[k, s["seed"], g, s["curve"][g]] for k in ("A2a", "A2b", "A2c") for s in r4[k]["seeds"] for g in ("DoorKey-8x8", "DoorKey-16x16")]
    write_csv("figure4_explore_vs_novelty.csv", ["run", "seed", "eval_grid", "eval_curve_area"], rows)


def figure5():
    r3, r4, r5 = J("round3-scores.json"), J("round4-scores.json")["runs"], J("round5-scores.json")["runs"]
    ex = r3["exploratory_rescore"]
    cf = lambda d: d["counts"]["cycle-farm"] if "counts" in d else d["categories"]["cycle-farm"]
    pts = [("on", "pre-registered", 1/640, r4["A1a"]), ("on", "pre-registered", 1/160, r4["A1b"]), ("on", "pre-registered", 1/60, r3["round3"]["R1"]),
           ("on", "pre-registered", 1/40, r3["round3"]["R4"]), ("on", "pre-registered", 1/40, r4["B5"]), ("on", "pre-registered", 1/30, r3["round3"]["R2"]),
           ("on", "re-scored", 1/640, ex["Agent 3: homeostatic satiation, growth 1/640"]), ("on", "re-scored", 1/160, ex["Agent 3: homeostatic satiation, growth 1/160"]),
           ("on", "re-scored", 1/80, ex["N3: growth 1/80"]), ("on", "re-scored", 1/40, ex["Agent 3: homeostatic satiation, growth 1/40"]),
           ("on", "re-scored", 1/40, ex["N1: anchor replicate, growth 1/40, seeds 10-19"]), ("on", "re-scored", 1/20, ex["N6: growth 1/20"]),
           ("off", "pre-registered", 1/160, r4["B7"]), ("off", "pre-registered", 1/40, r3["round3"]["R7"]), ("off", "pre-registered", 1/40, r4["B6"])]
    rows = []
    for norm, scoring, g, d in pts:
        k, n = cf(d), d["n"]; lo, hi = cp(k, n)
        rows.append([norm, scoring, g, k, n, k / n, lo, hi])
    write_csv("figure5a_farming_doorkey.csv", ["normalization", "scoring", "growth", "cycle_farm_seeds", "seeds", "fraction", "ci95_lo", "ci95_hi"], rows)
    kc = J("run-series.json", src=False)["keycorridor_pickups"]
    g = {"C1": "1/160", "C2": "1/40", "C3": "1/20", "C4": "1/20 norm off", "C5": "1/160 + tamper", "C6": "task-only"}
    rows = [[f"K{k[1]}", g[k], s, v["peak_key_pickups"], v["final_key_pickups"], v["category"]] for k, seeds in kc.items() for s, v in seeds.items()]
    write_csv("figure5b_keycorridor_pickups.csv", ["run", "setting", "seed", "peak_key_pickups", "final_key_pickups", "category"], rows)


FIGS = {"figure1": figure1, "figure2": figure2, "figure3": figure3, "figure4": figure4, "figure5": figure5}


def main(names):
    names = names or [*TABLES, *FIGS, "numbers"]
    for n in names:
        if n in TABLES:
            tex_table(*TABLES[n]); per_seed_extras(n)
        elif n in FIGS:
            FIGS[n]()
        elif n == "numbers":
            RES.mkdir(exist_ok=True); shutil.copy(DATA / "numbers.json", RES / "numbers.json")
        else:
            sys.exit(f"unknown result {n!r}")
    print("wrote results/ for:", " ".join(names))


if __name__ == "__main__":
    main(sys.argv[1:])
