import os
import pandas as pd
import matplotlib.pyplot as plt

RANDOM_SEED = 42
import numpy as np
np.random.seed(RANDOM_SEED)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
DATA_DIR = BASE_DIR
FIGURES_DIR = os.path.join(BASE_DIR, "outputs", "figures")
TABLES_DIR = os.path.join(BASE_DIR, "outputs", "tables")

os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

COMPETENCY_GROUP = {
    "Q1": "Number Sense", "Q2": "Place Value", "Q3": "Number Sense", "Q4": "Number Sense",
    "Q5": "Addition", "Q6": "Addition",
    "Q7": "Subtraction", "Q8": "Subtraction",
    "Q9": "Multiplication", "Q10": "Multiplication", "Q11": "Multiplication",
    "Q12": "Division", "Q13": "Division", "Q14": "Division",
    "Q15": "Fraction",
    "Q16": "Measurement", "Q17": "Measurement", "Q18": "Measurement",
    "Q19": "Shapes", "Q20": "Shapes",
}


def load_primary_data():
    print("[1/5] Loading and combining primary dataset...")
    files = {
        4: "GPContest_Grade_4_2022-23.xlsx",
        5: "GPContest_Grade_5_2022-23.xlsx",
        6: "GPContest_Grade_6_2022-23.xlsx",
    }
    frames = []
    for grade, fname in files.items():
        path = os.path.join(DATA_DIR, fname)
        d = pd.read_excel(path, sheet_name="Assessment Data")
        d["Grade"] = grade
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    print(f"    Combined shape: {df.shape}")
    return df


def compute_competency_scores(df):
    print("[2/5] Computing competency group scores...")
    group_scores = {}
    for group in set(COMPETENCY_GROUP.values()):
        cols = [q for q, g in COMPETENCY_GROUP.items() if g == group]
        group_scores[group] = df[cols].mean(axis=1) * 100
    group_df = pd.DataFrame(group_scores)
    group_df["District"] = df["District"]

    district_avg = group_df.groupby("District").mean(numeric_only=True)
    district_avg["weakest_group"] = district_avg.idxmin(axis=1)
    district_avg["weakest_score"] = district_avg.drop(columns=["weakest_group"]).min(axis=1)
    district_avg["strongest_score"] = district_avg.drop(
        columns=["weakest_group", "weakest_score"]).max(axis=1)
    district_avg["severity_gap"] = district_avg["strongest_score"] - district_avg["weakest_score"]

    severity_ranked = district_avg[
        ["weakest_group", "weakest_score", "strongest_score", "severity_gap"]
    ].sort_values("severity_gap", ascending=False)

    out_path = os.path.join(TABLES_DIR, "district_severity_ranked.csv")
    severity_ranked.to_csv(out_path)
    print(f"    Saved {out_path}")

    statewide_avg = {}
    for group in set(COMPETENCY_GROUP.values()):
        cols = [q for q, g in COMPETENCY_GROUP.items() if g == group]
        statewide_avg[group] = df[cols].mean().mean() * 100
    statewide_series = pd.Series(statewide_avg).sort_values()

    return district_avg, severity_ranked, statewide_series


def join_nfhs(severity_ranked):
    print("[3/5] Joining with NFHS-5 district data...")
    nfhs_path = os.path.join(DATA_DIR, "NFHS-5-KA-Karnataka.csv")
    nfhs = pd.read_csv(nfhs_path)
    nfhs["District"] = nfhs["District"].str.strip().str.lower()
    nfhs_wide = nfhs.pivot_table(index="District", columns="Indicator", values="NFHS-5", aggfunc="first")
    nfhs_wide.columns = [str(c).strip() for c in nfhs_wide.columns]

    indicators = {
        "female_literacy_pct": "14. Women who are literate4 (%)",
        "female_school_attendance_pct": "1. Female population age 6 years and above who ever attended school (%)",
    }
    nfhs_selected = pd.DataFrame(index=nfhs_wide.index)
    for new_name, exact_text in indicators.items():
        if exact_text in nfhs_wide.columns:
            nfhs_selected[new_name] = nfhs_wide[exact_text]

    district_name_map = {
        "belagavi chikkodi": "belgaum", "tumakuru madhugiri": "tumkur",
        "uttara kannada sirsi": "uttara kannada", "ballari": "bellary",
        "belagavi": "belgaum", "bengaluru rural": "bangalore rural",
        "chamarajanagara": "chamarajanagar", "kalaburgi": "gulbarga",
        "mysuru": "mysore", "tumakuru": "tumkur", "vijayapura": "bijapur",
        "yadagiri": "yadgir", "vijayanagar": "bellary",
    }
    severity_mapped = severity_ranked.copy()
    severity_mapped.index = severity_mapped.index.str.lower()
    severity_mapped = severity_mapped.rename(index=district_name_map)
    severity_mapped = severity_mapped.groupby(severity_mapped.index).mean(numeric_only=True)

    joined = severity_mapped.join(nfhs_selected, how="left")
    out_path = os.path.join(TABLES_DIR, "district_competency_with_nfhs.csv")
    joined.to_csv(out_path)
    print(f"    Saved {out_path}")
    return joined


def build_charts(statewide_series, severity_ranked):
    print("[4/5] Building charts...")

    # Chart 1: statewide competency bar chart
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#c0392b" if i < 3 else "#7f8c8d" for i in range(len(statewide_series))]
    bars = ax.barh(statewide_series.index, statewide_series.values, color=colors)
    ax.set_xlabel("Average Accuracy (%)")
    ax.set_title("Statewide Accuracy by Competency Group")
    ax.set_xlim(0, 100)
    for bar, value in zip(bars, statewide_series.values):
        ax.text(value + 1, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", va="center", fontsize=9)
    plt.tight_layout()
    path1 = os.path.join(FIGURES_DIR, "chart_competency_group_overall.png")
    plt.savefig(path1, dpi=150)
    plt.close()
    print(f"    Saved {path1}")

    # Chart 2: district severity clustered
    fig, ax = plt.subplots(figsize=(10, 7))
    groups_present = severity_ranked["weakest_group"].unique()
    palette = plt.cm.Set2(range(len(groups_present)))
    color_map = dict(zip(groups_present, palette))
    y_pos = range(len(severity_ranked))
    bar_colors = [color_map[g] for g in severity_ranked["weakest_group"]]
    ax.barh(y_pos, severity_ranked["severity_gap"], color=bar_colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(severity_ranked.index, fontsize=8)
    ax.set_xlabel("Severity Gap (Strongest % - Weakest %)")
    ax.set_title("District Competency Imbalance by Weakest Group")
    handles = [plt.Rectangle((0, 0), 1, 1, color=color_map[g]) for g in groups_present]
    ax.legend(handles, groups_present, title="Weakest group", loc="lower right", fontsize=8)
    plt.tight_layout()
    path2 = os.path.join(FIGURES_DIR, "chart_district_severity_clustered.png")
    plt.savefig(path2, dpi=150)
    plt.close()
    print(f"    Saved {path2}")


def main():
    print("=== Datathon 2026 — run_all.py ===")
    df = load_primary_data()
    district_avg, severity_ranked, statewide_series = compute_competency_scores(df)
    join_nfhs(severity_ranked)
    build_charts(statewide_series, severity_ranked)
    print("[5/5] Done. All outputs written to outputs/tables and outputs/figures.")


if __name__ == "__main__":
    main()