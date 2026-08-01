import os
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.join(BASE_DIR, "outputs", "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

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


def compute_group_scores(df):
    group_scores = {}
    for group in set(COMPETENCY_GROUP.values()):
        cols = [q for q, g in COMPETENCY_GROUP.items() if g == group]
        group_scores[group] = df[cols].mean(axis=1) * 100
    group_df = pd.DataFrame(group_scores)
    group_df["District"] = df["District"]

    statewide = group_df.drop(columns=["District"]).mean().sort_values()
    district_group_avg = group_df.groupby("District").mean(numeric_only=True)
    return statewide, district_group_avg


def chart_competency_bar(statewide_series, save=True):
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#c0392b" if i < 3 else "#7f8c8d" for i in range(len(statewide_series))]
    bars = ax.barh(statewide_series.index, statewide_series.values, color=colors)
    ax.set_xlabel("Average Accuracy (%)")
    ax.set_title("Statewide Accuracy by Competency Group")
    ax.set_xlim(0, 100)
    for bar, value in zip(bars, statewide_series.values):
        ax.text(value + 1, bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", va="center", fontsize=9)
    plt.tight_layout()
    if save:
        path = os.path.join(FIGURES_DIR, "chart_competency_group_overall.png")
        plt.savefig(path, dpi=150)
        print(f"Saved {path}")
    return fig


def chart_district_heatmap(district_group_avg, save=True):
    fig, ax = plt.subplots(figsize=(10, 12))
    data = district_group_avg.sort_index()
    im = ax.imshow(data.values, cmap="RdYlGn", aspect="auto", vmin=30, vmax=90)

    ax.set_xticks(range(len(data.columns)))
    ax.set_xticklabels(data.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(data.index)))
    ax.set_yticklabels(data.index, fontsize=8)

    for i in range(len(data.index)):
        for j in range(len(data.columns)):
            val = data.values[i, j]
            ax.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=6,
                     color="black" if 40 < val < 75 else "white")

    ax.set_title("District x Competency Group Accuracy Heatmap")
    fig.colorbar(im, ax=ax, label="Accuracy (%)", shrink=0.6)
    plt.tight_layout()
    if save:
        path = os.path.join(FIGURES_DIR, "chart_district_competency_heatmap.png")
        plt.savefig(path, dpi=150)
        print(f"Saved {path}")
    return fig


def chart_severity_clustered(severity_ranked, save=True):
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
    if save:
        path = os.path.join(FIGURES_DIR, "chart_district_severity_clustered.png")
        plt.savefig(path, dpi=150)
        print(f"Saved {path}")
    return fig


def build_all_charts(df, severity_ranked):
    statewide, district_group_avg = compute_group_scores(df)
    chart_competency_bar(statewide)
    chart_district_heatmap(district_group_avg)
    chart_severity_clustered(severity_ranked)


if __name__ == "__main__":
    df = pd.read_csv(os.path.join(BASE_DIR, "combined_with_scores.csv"))
    severity_ranked = pd.read_csv(
        os.path.join(BASE_DIR,"district_severity_ranked.csv"),
        index_col=0,
    )
    build_all_charts(df, severity_ranked)
    print("All charts generated.")