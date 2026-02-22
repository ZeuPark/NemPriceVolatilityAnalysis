"""
Configuration settings for NEM Price Volatility Analysis.
"""

from pathlib import Path
import pytz

# =============================================================================
# PATH CONFIGURATION
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# =============================================================================
# TIME CONFIGURATION
# =============================================================================
TIMEZONE = pytz.timezone("Australia/Sydney")
INTERVAL_MINUTES = 5

# =============================================================================
# REGION CONFIGURATION
# =============================================================================
REGION = "NSW1"

# =============================================================================
# SPIKE THRESHOLDS
# =============================================================================
# Absolute threshold ($/MWh)
SPIKE_ABSOLUTE_THRESHOLD = 300.0

# Percentile threshold (top X%)
SPIKE_PERCENTILE = 99.0

# Minimum consecutive intervals to merge into single event
SPIKE_MERGE_INTERVALS = 1  # Adjacent 5-min intervals merged

# =============================================================================
# FEATURE ENGINEERING
# =============================================================================
# Lookback window for pre-spike features (minutes)
PRE_SPIKE_WINDOW_MINUTES = 30

# =============================================================================
# VOLATILITY CONFIGURATION
# =============================================================================
# Rolling window sizes (in number of 5-min intervals)
VOLATILITY_WINDOWS = {
    "1h": 12,   # 12 * 5min = 1 hour
    "6h": 72,   # 72 * 5min = 6 hours
}

# =============================================================================
# PLOTTING CONFIGURATION
# =============================================================================
FIGURE_DPI = 150
FIGURE_SIZE_WIDE = (14, 6)
FIGURE_SIZE_SQUARE = (10, 8)
FIGURE_SIZE_TALL = (10, 12)

# Color palette
COLORS = {
    "price": "#1f77b4",
    "demand": "#ff7f0e",
    "solar": "#ffcc00",
    "wind": "#2ca02c",
    "spike": "#d62728",
    "normal": "#7f7f7f",
}
