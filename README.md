# NSW NEM Price Volatility Analysis

Analysis of 5-minute electricity price spikes and volatility in NSW (Australia's National Electricity Market). This project investigates when and why price spikes occur, and quantifies the relationship between renewable energy penetration and price volatility.

## Project Summary

- **Region**: NSW1 (New South Wales)
- **Time Resolution**: 5-minute dispatch intervals
- **Key Questions**:
  1. When do price spikes concentrate (hour/season)?
  2. What patterns appear in the 30 minutes before spikes?
  3. Does higher renewable share increase or decrease price volatility?

## Repository Structure

```
nem_price_volatility_analysis/
├── data/
│   ├── raw/              # Raw AEMO CSV files
│   └── processed/        # Cleaned parquet files
├── notebooks/
│   ├── 01_data_ingest.ipynb    # Data loading and preprocessing
│   ├── 02_eda.ipynb            # Exploratory data analysis
│   ├── 03_spike_events.ipynb   # Spike detection and drivers
│   ├── 04_volatility.ipynb     # Volatility vs renewables
│   └── 05_case_studies.ipynb   # Detailed event analysis
├── src/
│   ├── config.py         # Configuration settings
│   ├── io.py             # Data I/O functions
│   ├── features.py       # Feature engineering
│   ├── models.py         # Statistical analysis
│   └── plots.py          # Visualization functions
├── reports/
│   └── figures/          # Generated graphs
├── requirements.txt
└── README.md
```

## Key Outputs

### 8 Analysis Graphs

1. **NSW RRP Time Series** - Full price history overview
2. **RRP Distribution** - Histogram with log scale and percentile markers
3. **Weekday-Hour Heatmap** - Average price patterns
4. **Monthly Spike Count** - Seasonal spike frequency
5. **Pre-Spike Profile** - Average demand/renewable changes before spikes
6. **Spike vs Non-Spike Comparison** - Feature distribution boxplots
7. **Volatility vs Renewable Share** - Scatter plot with trend
8. **Case Studies** - Detailed multi-panel plots for top 3 events

### Analysis Features

- **Spike Detection**: Absolute (>$300/MWh) and percentile (top 1%) thresholds
- **Event Merging**: Consecutive 5-min intervals merged into single events
- **Pre-Spike Features**: Demand/solar/wind change rates, price slope, volatility
- **Volatility Metrics**: 1h/6h rolling std, daily max/mean ratio
- **Classification Models**: Logistic regression and decision tree for driver identification

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/nem_price_volatility_analysis.git
cd nem_price_volatility_analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Data Requirements

Download data from [AEMO NEMWeb](https://aemo.com.au/energy-systems/electricity/national-electricity-market-nem/data-nem/market-data-nemweb):

1. **DISPATCHPRICE** - 5-minute dispatch prices and demand
2. **DISPATCH_UNIT_SCADA** - Unit-level generation (optional, for solar/wind)

Place CSV files in `data/raw/`.

Alternative: Use [OpenNEM API](https://opennem.org.au/) for aggregated renewable data.

## Usage

Run notebooks in order:

```bash
# Start Jupyter
jupyter notebook

# Or use JupyterLab
jupyter lab
```

1. **01_data_ingest.ipynb** - Load and preprocess raw data
2. **02_eda.ipynb** - Generate overview graphs (1-3)
3. **03_spike_events.ipynb** - Spike analysis and graphs (4-6)
4. **04_volatility.ipynb** - Volatility analysis and graph (7)
5. **05_case_studies.ipynb** - Case study plots (8)

## Configuration

Edit `src/config.py` to adjust:

```python
SPIKE_ABSOLUTE_THRESHOLD = 300.0  # $/MWh
SPIKE_PERCENTILE = 99.0           # Top 1%
PRE_SPIKE_WINDOW_MINUTES = 30     # Lookback window
```

## Interview Talking Points

1. **Problem**: Price spikes in NSW create operational risk and cost uncertainty
2. **Approach**:
   - Analyzed AEMO 5-min data filtered to NSW
   - Defined spikes as events (merged consecutive intervals)
   - Extracted pre-spike features (demand/renewable changes)
   - Quantified volatility-renewable relationship
3. **Results**: [Fill with your findings]
4. **Limitations**:
   - Transmission constraints not fully captured
   - Generator bidding strategies unknown
   - Generation mix aggregation approximations
5. **Extensions**:
   - FCAS market integration
   - Spike risk scoring model
   - Cross-region analysis

## Dependencies

- pandas >= 1.5.0
- numpy >= 1.23.0
- matplotlib >= 3.6.0
- seaborn >= 0.12.0
- scipy >= 1.9.0
- scikit-learn >= 1.1.0
- pyarrow >= 10.0.0 (for parquet)
- pytz >= 2022.1

## License

MIT License

## Author

[Your Name]
