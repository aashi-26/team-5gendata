import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("combined_with_scores.csv")
print("Loaded:", df.shape)


#SAMPLE SIZE CHECK
counts = df["District"].value_counts()
print("\n=== Students per District ===")
print(counts.sort_values())

THIN_THRESHOLD = 300  
thin_districts = counts[counts < THIN_THRESHOLD]
if len(thin_districts):
    print(f"\nWARNING — districts with fewer than {THIN_THRESHOLD} students "
          f"(treat their 'weakest group' with caution):")
    print(thin_districts)
else:
    print(f"\nAll districts have at least {THIN_THRESHOLD} students. Good.")

competency_group = {
    "Q1": "Number Sense", "Q2": "Place Value", "Q3": "Number Sense", "Q4": "Number Sense",
    "Q5": "Addition", "Q6": "Addition",
    "Q7": "Subtraction", "Q8": "Subtraction",
    "Q9": "Multiplication", "Q10": "Multiplication", "Q11": "Multiplication",
    "Q12": "Division", "Q13": "Division", "Q14": "Division",
    "Q15": "Fraction",
    "Q16": "Measurement", "Q17": "Measurement", "Q18": "Measurement",
    "Q19": "Shapes", "Q20": "Shapes",
}
group_scores = {}
for group in set(competency_group.values()):
    cols_in_group = [q for q, g in competency_group.items() if g == group]
    group_scores[group] = df[cols_in_group].mean(axis=1) * 100
group_df = pd.DataFrame(group_scores)
group_df["District"] = df["District"]

district_group_avg = group_df.groupby("District").mean(numeric_only=True)

district_group_avg["weakest_group"] = district_group_avg.idxmin(axis=1)
district_group_avg["weakest_score"] = district_group_avg.drop(columns=["weakest_group"]).min(axis=1)
district_group_avg["strongest_score"] = district_group_avg.drop(
    columns=["weakest_group", "weakest_score"]).max(axis=1)
district_group_avg["severity_gap"] = (
    district_group_avg["strongest_score"] - district_group_avg["weakest_score"]
)

severity_ranked = district_group_avg[
    ["weakest_group", "weakest_score", "strongest_score", "severity_gap"]
].sort_values("severity_gap", ascending=False)

print("\n=== Districts ranked by severity gap (biggest imbalance first) ===")
print(severity_ranked.round(1))

severity_ranked.to_csv("district_severity_ranked.csv")
print("\nSaved district_severity_ranked.csv")

fig, ax = plt.subplots(figsize=(10, 7))
groups_present = severity_ranked["weakest_group"].unique()
colors = plt.cm.Set2(range(len(groups_present)))
color_map = dict(zip(groups_present, colors))

y_pos = range(len(severity_ranked))
bar_colors = [color_map[g] for g in severity_ranked["weakest_group"]]
ax.barh(y_pos, severity_ranked["severity_gap"], color=bar_colors)
ax.set_yticks(y_pos)
ax.set_yticklabels(severity_ranked.index, fontsize=8)
ax.set_xlabel("Severity Gap (Strongest group % - Weakest group %)")
ax.set_title("District Competency Imbalance, Colored by Weakest Competency Group")

# legend
handles = [plt.Rectangle((0, 0), 1, 1, color=color_map[g]) for g in groups_present]
ax.legend(handles, groups_present, title="Weakest group", loc="lower right", fontsize=8)

plt.tight_layout()
plt.savefig("chart_district_severity_clustered.png", dpi=150)
plt.close()
print("Saved chart_district_severity_clustered.png")

print("\n=== Count of districts by weakest competency group ===")
print(severity_ranked["weakest_group"].value_counts())