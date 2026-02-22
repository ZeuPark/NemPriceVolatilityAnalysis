# NSW NEM Price Volatility Analysis Report

**Analysis Period**: [Fill in date range]
**Author**: [Your Name]
**Date**: [Report date]

---

## Executive Summary

[2-3 sentence overview of key findings]

---

## 1. Introduction

### 1.1 Background
The National Electricity Market (NEM) in Australia operates on a 5-minute dispatch interval basis. NSW (New South Wales) is the largest region by demand. Price spikes create operational and financial risks for market participants.

### 1.2 Objectives
1. Identify when and where price spikes occur
2. Characterize pre-spike conditions
3. Quantify the relationship between renewable energy share and price volatility

### 1.3 Data Sources
- AEMO DISPATCHPRICE (5-minute RRP and demand)
- [Additional sources if used]

---

## 2. Data Overview

### 2.1 Dataset Summary
| Metric | Value |
|--------|-------|
| Total intervals | [n] |
| Date range | [start] to [end] |
| Missing data | [%] |

### 2.2 Price Statistics
| Statistic | RRP ($/MWh) |
|-----------|-------------|
| Mean | |
| Median | |
| Std Dev | |
| Min | |
| Max | |
| 99th percentile | |

---

## 3. Key Findings

### 3.1 Price Spike Timing

**Graph 1: RRP Time Series**
![RRP Time Series](figures/01_rrp_timeseries.png)

**Graph 3: Weekday-Hour Heatmap**
![Heatmap](figures/03_weekday_hour_heatmap.png)

**Key observations:**
- Peak hours: [fill in]
- Weekday vs weekend: [fill in]
- Seasonal patterns: [fill in]

### 3.2 Spike Event Analysis

**Graph 4: Monthly Spike Count**
![Monthly Spikes](figures/04_monthly_spike_count.png)

**Spike definition used:**
- Absolute threshold: $300/MWh
- Top 1% threshold: $[X]/MWh
- Total events identified: [n]

**Graph 5: Pre-Spike Profile**
![Pre-Spike Profile](figures/05_pre_spike_profile.png)

**Pre-spike patterns:**
- Demand change: [fill in]
- Solar change: [fill in]
- Wind change: [fill in]

### 3.3 Spike Drivers

**Graph 6: Feature Comparison**
![Feature Comparison](figures/06_spike_feature_comparison.png)

**Top drivers (from classification model):**
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

### 3.4 Volatility and Renewable Share

**Graph 7: Volatility vs Renewable Share**
![Volatility vs Renewable](figures/07_volatility_vs_renewable.png)

**Correlation analysis:**
| Metric | Pearson r | p-value |
|--------|-----------|---------|
| 1h volatility vs renewable share | | |
| 6h volatility vs renewable share | | |

**Interpretation:**
[Does higher renewable share correlate with higher or lower volatility?]

---

## 4. Case Studies

### Case Study 1: [Date/Time]
![Case Study 1](figures/08_case_study_1.png)

**Event details:**
- Max price: $[X]/MWh
- Duration: [X] minutes
- Time of day: [X]

**Analysis:**
[What happened? What were the likely causes?]

### Case Study 2: [Date/Time]
![Case Study 2](figures/08_case_study_2.png)

[Similar format]

### Case Study 3: [Date/Time]
![Case Study 3](figures/08_case_study_3.png)

[Similar format]

---

## 5. Conclusions

### 5.1 Key Insights
1. **Timing**: [When do spikes concentrate?]
2. **Pre-spike patterns**: [What typically happens before spikes?]
3. **Renewable impact**: [Does renewable share affect volatility?]

### 5.2 Limitations
1. **Data limitations**:
   - Transmission constraints not captured
   - Generator bidding strategies unknown

2. **Methodology limitations**:
   - [Any approximations made]

### 5.3 Recommendations
1. [Actionable recommendation 1]
2. [Actionable recommendation 2]

---

## 6. Next Steps

1. **FCAS Integration**: Incorporate frequency control markets
2. **Forecasting**: Develop spike probability model
3. **Cross-region**: Extend analysis to VIC, QLD, SA

---

## Appendix

### A. Full Graph List
1. NSW RRP Time Series
2. RRP Distribution Histogram
3. Weekday-Hour Heatmap
4. Monthly Spike Count
5. Pre-Spike Average Profile
6. Spike vs Non-Spike Feature Comparison
7. Volatility vs Renewable Share
8. Case Study Plots (x3)

### B. Technical Details
- Spike merging: Adjacent 5-min intervals combined
- Pre-spike window: 30 minutes
- Volatility: Rolling standard deviation (1h, 6h)

### C. Code Repository
[GitHub URL]
