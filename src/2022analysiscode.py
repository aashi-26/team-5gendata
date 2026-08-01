import pandas as pd
import numpy as np

FILES = {
    (4, "2022-23"): "GPContest_Grade_4_2022-23.xlsx",
    (5, "2022-23"): "GPContest_Grade_5_2022-23.xlsx",
    (6, "2022-23"): "GPContest_Grade_6_2022-23.xlsx",
}

frames = []
for (grade, year), path in FILES.items():
    try:
        d = pd.read_excel(path, sheet_name="Assessment Data")
        d["Grade"] = grade
        d["Year"] = year
        frames.append(d)
    except FileNotFoundError:
        print(f"NOTE: {path} not found yet — skipping for now")

if frames:
    df = pd.concat(frames, ignore_index=True)
else:
    df = pd.read_excel("primary_dataset.xlsx", sheet_name="Assessment Data")

print("Combined shape:", df.shape)
print(df.head())


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
q_cols = list(competency_group.keys())


df["total_score"] = df[q_cols].sum(axis=1)
df["pct_score"] = df["total_score"] / len(q_cols) * 100

group_scores = {}
for group in set(competency_group.values()):
    cols_in_group = [q for q, g in competency_group.items() if g == group]
    group_scores[group] = df[cols_in_group].mean(axis=1) * 100
group_df = pd.DataFrame(group_scores)

print("\n=== Average accuracy by competency group (overall) ===")
print(group_df.mean().sort_values().round(1))

print("\n=== Average accuracy by competency group, by Gender ===")
group_df["Gender"] = df["Gender"]
print(group_df.groupby("Gender").mean().round(1).T)

if "Grade" in df.columns:
    group_df["Grade"] = df["Grade"]
    print("\n=== Average accuracy by competency group, by Grade ===")
    print(group_df.groupby("Grade").mean(numeric_only=True).round(1).T)

operation_order = ["Addition", "Subtraction", "Multiplication", "Division"]
print("\n=== Accuracy across the operation difficulty sequence ===")
print(group_df[operation_order].mean().round(1))

if "District" in df.columns:
    geo_group = pd.concat([df[["District"]], group_df.drop(columns=["Gender","Grade","Year"], errors="ignore")], axis=1)
    print("\n=== Weakest competency group per District ===")
    district_group_avg = geo_group.groupby("District").mean(numeric_only=True)
    print(district_group_avg.round(1))
    print("\nWeakest group per district(name only):")
    print(district_group_avg.idxmin(axis=1))
    print("\nLowest score value value per district:")
    print(district_group_avg.min(axis=1).round(1))



df.to_csv("combined_with_scores.csv", index=False)
print("\nSaved combined_with_scores.csv")