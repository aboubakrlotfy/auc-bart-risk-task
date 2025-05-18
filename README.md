# 🎈 Time Pressure and Risk-Taking: A BART-Based Experiment

This repository contains the materials, executable, raw data, and analysis code for a psychology experiment conducted at the American University in Cairo (AUC). The experiment investigates how **time pressure affects risk-taking in decision-making** using the **Balloon Analogue Risk Task (BART)**.

## Repository Structure
<pre>
  data
  ├── participants_raw.csv # Raw participant demographics and contextual data
  └── responses_raw.csv # Raw BART task responses per trial data_analysis
  data_analysis
  ├── data_analysis.py # Full analysis script (stats + plots)
  ├── results_statistics_output.txt # Text report: stats, t-test, regression 
  ├── appendix_a_cleaned_data.csv # Appendix A: participant-level scores & variables 
  ├── boxplot_risk_scores.png # Risk scores by condition (boxplot) 
  └── histogram_delta_scores.png # Δ risk score distribution (histogram)
  bart_15.py # Source code for building the experiment 
  bart_15_new.exe # Standalone Windows executable used by participants   
</pre>

## Experiment Summary

Participants completed two versions of the BART, with randomly assigned order per gender. There was a 5 min break between conditions:
- **Baseline Condition** — No time pressure  
- **Time-Pressure Condition** — 15-second limit per round  

The **risk-adjusted score** was used to quantify risk-taking, calculated as the average number of pumps on balloons that did not explode.

## Key Outputs

All statistical analyses and visualizations are located in the `/data_analysis/` folder. These include:

- Descriptive statistics and **paired t-test**
- Regression models testing **moderating variables**:
  - Gender  
  - Academic standing  
  - Caffeine intake  
  - Stress level  
  - Sleep  
  - Submission time  
- **Appendix A** (`appendix_a_cleaned_data.csv`) contains cleaned, participant-level results for transparency and reference.

## 📎 Citation & Use

This repository is provided for academic and educational use only. All data has been anonymized. If you use any part of this project or build on it, please cite appropriately and credit the original author.

For questions, please contact:  
**Aboubakr Lotfy**  
[https://github.com/aboubakrlotfy](https://github.com/aboubakrlotfy)
