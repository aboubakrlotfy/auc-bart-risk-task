import pandas as pd
import statsmodels.formula.api as smf
from datetime import timedelta
from scipy.stats import ttest_rel
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
participants = pd.read_csv("../data/participants_raw.csv")
responses = pd.read_csv("../data/responses_raw.csv")

# Adjust time zone
participants["submission_time_egp"] = pd.to_datetime(participants["submission_time"], errors="coerce") + timedelta(hours=3)
participants["submission_hour"] = participants["submission_time_egp"].dt.hour
participants["is_stem"] = participants["major"].str.contains("STEM", case=False, na=False).astype(int)

# Filter completed
participants = participants[participants["completed"] == True]

# Merge data
df = responses.merge(participants, on="participant_id", how="inner")

# Compute risk-adjusted score
def compute_risk_adjusted_score(sub_df):
    non_popped = sub_df[sub_df["popped"] == False]
    return non_popped["num_pumps"].mean() if len(non_popped) > 0 else None

risk_df = df.groupby(["participant_id", "condition"]).apply(compute_risk_adjusted_score).reset_index()
risk_df.columns = ["participant_id", "condition", "risk_adjusted_score"]
risk_df = risk_df[risk_df["condition"].isin(["baseline", "pressure"])]
wide_df = risk_df.pivot(index="participant_id", columns="condition", values="risk_adjusted_score").dropna()
wide_df["delta_risk_score"] = wide_df["pressure"] - wide_df["baseline"]

# Merge with participants
analysis_df = wide_df.merge(participants, on="participant_id")

# Descriptive stats
summary_stats = analysis_df[["baseline", "pressure", "delta_risk_score"]].agg(["mean", "std", "median", "min", "max", "count"]).T
summary_stats["mode"] = analysis_df[["baseline", "pressure", "delta_risk_score"]].mode().iloc[0]
summary_stats = summary_stats.round(2)

# Paired t-test
t_stat, p_val = ttest_rel(analysis_df["baseline"], analysis_df["pressure"])

# Output text file
with open("results_statistics_output.txt", "w") as out:
    out.write("Descriptive Statistics (Table 1):\n")
    out.write(summary_stats.to_string())
    out.write("\n\nPaired t-test:\n")
    out.write("t = {:.2f}, p = {:.4f}\n".format(t_stat, p_val))

    # Moderators
    moderators = ["gender", "standing", "is_stem", "sleep_hours", "stress_level", "caffeine_today", "submission_hour"]
    out.write("\nModeration Analyses:\n")
    for var in moderators:
        out.write(f"\n--- Moderation by {var} ---\n")
        model = smf.ols(f"delta_risk_score ~ {var}", data=analysis_df).fit()
        out.write(str(model.summary()))
        out.write("\n")

# Colors
baseline_color = "#DFA320"  # orangey-yellow
pressure_color = "#DA713B"  # reddish-orange

# Boxplot: Baseline vs. Pressure
plt.figure(figsize=(8, 6))

# Melt actual lowercase columns
plot_data = pd.melt(analysis_df, id_vars=["participant_id"], value_vars=["baseline", "pressure"],
                    var_name="Condition", value_name="Risk-Adjusted Score")

# Rename for display purposes
plot_data["Condition"] = plot_data["Condition"].replace({
    "baseline": "Baseline",
    "pressure": "Time Pressure"
})


# Then set palette to match these display values
palette = {"Baseline": baseline_color, "Time Pressure": pressure_color}

# Create boxplot
sns.boxplot(
    data=plot_data,
    x="Condition",
    y="Risk-Adjusted Score",
    hue="Condition",
    palette=palette,
    legend=False
)

plt.title("Risk-Adjusted Scores Under Baseline and Time Pressure Conditions")
plt.grid(axis='y', linestyle='-', color='gray', linewidth=0.5, alpha=0.3)
plt.savefig("boxplot_risk_scores.png", dpi=300)
plt.close()

# Histogram of Δ Risk Score
plt.figure(figsize=(8, 6))
sns.histplot(
    analysis_df["delta_risk_score"],
    kde=True,
    bins=10,
    color="#ffb347",
)
plt.axvline(0, color='red', linestyle='--', label='No Change (Δ = 0)')
plt.legend(loc='upper right')  
plt.xlabel("Change in Risk-Adjusted Score")
plt.ylabel("Number of Participants")
plt.title("Distribution of Change in Risk-Adjusted Score (Time Pressure - Baseline)")
plt.grid(axis='y', linestyle='-', color='gray', linewidth=0.5, alpha=0.3)
plt.savefig("histogram_delta_scores.png", dpi=300)
plt.close()


# Export Cleaned Participant-Level Data for Appendix A 

# Select and organize data columns for Appendix A
columns_to_export = {
    "participant_id": "Participant ID",
    "gender": "Gender",
    "major": "Major",
    "standing": "Academic Standing",
    "caffeine_today": "Caffeine Today",
    "sleep_hours": "Sleep Hours",
    "stress_level": "Stress Level",
    "submission_hour": "Submission Hour",
    "baseline": "Baseline Risk-Adjusted Score",
    "pressure": "Time Pressure Risk-Adjusted Score",
    "delta_risk_score": "Δ Risk-Adjusted Score"
}

# Select, rename, sort, and round
appendix_export = (
    analysis_df[list(columns_to_export.keys())]
    .rename(columns=columns_to_export)
    .sort_values("Participant ID")
    .round(2)
)
# Save cleaned dataset
appendix_export.to_csv("appendix_a_cleaned_data.csv", index=False)