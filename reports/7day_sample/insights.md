# 7-Day Sample Analysis Insights

**Period**: 2026-02-14 ~ 2026-02-21 (7 days)
**Region**: NSW1
**Intervals**: 2,016 (5-min resolution)

---

## Key Statistics

| Metric | Value |
|--------|-------|
| Mean RRP | $53.90 |
| Median RRP | $57.06 |
| Min RRP | -$65.53 |
| Max RRP | $147.51 |
| Std Dev | $30.92 |
| 95th Percentile | $104.48 |
| Spike Events | 23 (95th pct threshold) |

---

## Graph Insights

### 1. RRP Time Series (`01_rrp_timeseries.png`)
- Price oscillates between -$65 and $147
- Negative prices indicate oversupply (renewables flooding the grid)
- Daily cycling pattern visible

### 2. RRP Distribution (`02_rrp_distribution.png`)
- Most prices cluster around $40-80
- Right-skewed distribution (positive skew)
- Log scale reveals the "fat tail" characteristic of electricity markets

### 3. Weekday-Hour Heatmap (`03_weekday_hour_heatmap.png`)
- **Peak hours**: 5-8 PM (evening demand + solar ramp-down)
- **Low hours**: 2-5 AM (minimum demand)
- Weekend slightly lower than weekdays

### 4. Daily Spike Count (`04_daily_spike_count.png`)
- 1-5 spike events per day
- Limited data prevents seasonal pattern identification

### 5. Pre-Spike Profile (`05_pre_spike_profile.png`)
- Price shows gradual increase before spike
- Suggests predictability - spikes don't occur without warning

### 6. Spike by Hour (`06_spike_by_hour.png`)
- Spikes concentrate at 5-7 PM
- Matches "evening ramp" - solar decline + demand surge
- Critical period for grid operators

### 7. Volatility Time Series (`07_volatility_timeseries.png`)
- 1-hour rolling volatility: mean $8.10
- 6-hour rolling volatility: mean $16.25
- Volatility increases during evening hours

### 8. Case Study (`08_case_study_1.png`)
- Highest price event: Feb 19, 17:45 ($147.51)
- Occurred during evening peak
- Duration: ~15 minutes

---

## Limitations of 7-Day Sample

| Can Do | Cannot Do |
|--------|-----------|
| Validate pipeline | Seasonal patterns |
| Daily patterns | True spikes ($300+) |
| Method demonstration | Statistical significance |
| Code verification | Renewable impact analysis |

---

## Next Steps

1. Download 90+ days for robust analysis
2. Add demand data for correlation analysis
3. Include renewable generation (solar/wind) data
4. Capture actual price spikes ($300+, $1000+)
5. Seasonal comparison (summer vs winter)

---

*This is a methodology demonstration using limited data. Full analysis requires 3-6 months of data.*
