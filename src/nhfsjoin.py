import pandas as pd

nfhs = pd.read_csv("NFHS-5-KA-Karnataka.csv")  # <-- update filename/sheet
print("NFHS-5 raw shape:", nfhs.shape)
print(nfhs.head())

nfhs["District"] = nfhs["District"].str.strip().str.lower()

nfhs_wide = nfhs.pivot_table(
    index="District", columns="Indicator", values="NFHS-5", aggfunc="first"
)
nfhs_wide.columns = [str(c).strip() for c in nfhs_wide.columns]
print("\nNFHS-5 wide shape:", nfhs_wide.shape)
print("Sample indicators available:\n", nfhs_wide.columns.tolist()[:10])

indicators_of_interest = {
    "female_literacy_pct": "14. Women who are literate4 (%)",
    "female_school_attendance_pct": "1. Female population age 6 years and above who ever attended school (%)",
    "pre_primary_attendance_pct": "13. Children age 5 years who attended pre-primary school during the school year 2019-20 (%)",
}

nfhs_selected = pd.DataFrame(index=nfhs_wide.index)
for new_name, exact_indicator_text in indicators_of_interest.items():
    if exact_indicator_text in nfhs_wide.columns:
        nfhs_selected[new_name] = nfhs_wide[exact_indicator_text]
    else:
        print(f"WARNING: indicator not found — check exact text: '{exact_indicator_text}'")

print("\nSelected NFHS-5 indicators:")
print(nfhs_selected)

severity = pd.read_csv("district_severity_ranked.csv")
severity["District"] = severity["District"].str.strip().str.lower()
severity = severity.set_index("District")

assessment_districts = set(severity.index)
nfhs_districts = set(nfhs_selected.index)

only_in_assessment = assessment_districts - nfhs_districts
only_in_nfhs = nfhs_districts - assessment_districts

print(f"\n{len(only_in_assessment)} district names in your assessment data "
      f"with NO exact match in NFHS-5:")
print(sorted(only_in_assessment))
print(f"\n{len(only_in_nfhs)} district names in NFHS-5 with no match in your data:")
print(sorted(only_in_nfhs))

manual_district_map = {
    "belagavi chikkodi": "belgaum",
    "tumakuru madhugiri": "tumkur",
    "uttara kannada sirsi": "uttara kannada",
    "ballari": "bellary",
    "belagavi": "belgaum",
    "bengaluru rural": "bangalore rural",
    "chamarajanagara": "chamarajanagar",
    "kalaburgi": "gulbarga",
    "mysuru": "mysore",
    "tumakuru": "tumkur",
    "vijayapura": "bijapur",
    "yadagiri": "yadgir",
    "vijayanagar": "bellary",
}
severity_mapped = severity.rename(index=manual_district_map)
joined = severity_mapped.join(nfhs_selected, how="left")
print("\n=== Joined table (district competency severity + NFHS-5 indicators) ===")
print(joined.round(1))

missing_after_join = joined[nfhs_selected.columns].isna().any(axis=1)
if missing_after_join.any():
    print("\nWARNING — these districts still have no NFHS-5 match after mapping:")
    print(joined[missing_after_join].index.tolist())

joined.to_csv("district_competency_with_nfhs.csv")
print("\nSaved district_competency_with_nfhs.csv")

print("\n=== Correlation: severity_gap vs NFHS-5 indicators ===")
for col in nfhs_selected.columns:
    if col in joined.columns:
        corr = joined["severity_gap"].corr(joined[col])
        print(f"severity_gap vs {col}: r = {corr:.2f}")

print("\n=== Correlation: weakest_score vs NFHS-5 indicators ===")
for col in nfhs_selected.columns:
    if col in joined.columns:
        corr = joined["weakest_score"].corr(joined[col])
        print(f"weakest_score vs {col}: r = {corr:.2f}")