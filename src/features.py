"""
Feature engineering for NEM Price Volatility Analysis.

Includes:
- Spike event detection and merging
- Pre-spike feature extraction
- Volatility indicators
- Renewable share calculation
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional
import logging

from . import config

logger = logging.getLogger(__name__)


# =============================================================================
# SPIKE DETECTION
# =============================================================================

def detect_spikes_absolute(
    df: pd.DataFrame,
    threshold: float = config.SPIKE_ABSOLUTE_THRESHOLD,
    price_col: str = 'rrp'
) -> pd.Series:
    """
    Detect price spikes using absolute threshold.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with price column
    threshold : float
        Price threshold ($/MWh)
    price_col : str
        Name of price column

    Returns
    -------
    pd.Series
        Boolean series indicating spike intervals
    """
    return df[price_col] >= threshold


def detect_spikes_percentile(
    df: pd.DataFrame,
    percentile: float = config.SPIKE_PERCENTILE,
    price_col: str = 'rrp'
) -> Tuple[pd.Series, float]:
    """
    Detect price spikes using percentile threshold.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with price column
    percentile : float
        Percentile threshold (e.g., 99 for top 1%)
    price_col : str
        Name of price column

    Returns
    -------
    Tuple[pd.Series, float]
        Boolean series indicating spikes, and the computed threshold
    """
    threshold = df[price_col].quantile(percentile / 100)
    is_spike = df[price_col] >= threshold
    logger.info(f"Percentile {percentile} threshold: ${threshold:.2f}/MWh")
    return is_spike, threshold


def merge_spike_events(
    is_spike: pd.Series,
    max_gap_intervals: int = config.SPIKE_MERGE_INTERVALS
) -> pd.Series:
    """
    Merge nearby spike intervals into single events.

    Parameters
    ----------
    is_spike : pd.Series
        Boolean series indicating spike intervals
    max_gap_intervals : int
        Maximum gap (in 5-min intervals) to merge

    Returns
    -------
    pd.Series
        Event ID for each interval (0 = non-spike)
    """
    # Identify event boundaries
    event_starts = is_spike & (~is_spike.shift(1, fill_value=False))
    event_ids = event_starts.cumsum()
    event_ids = event_ids.where(is_spike, 0)

    # Merge events with small gaps
    if max_gap_intervals > 0:
        for _ in range(max_gap_intervals):
            # Find gaps that should be merged
            prev_event = event_ids.shift(1, fill_value=0)
            next_event = event_ids.shift(-1, fill_value=0)

            # Fill single gaps
            fill_mask = (event_ids == 0) & (prev_event > 0) & (next_event > 0)
            event_ids = event_ids.where(~fill_mask, prev_event)

    return event_ids


def create_spike_event_table(
    df: pd.DataFrame,
    event_ids: pd.Series,
    price_col: str = 'rrp'
) -> pd.DataFrame:
    """
    Create summary table of spike events.

    Parameters
    ----------
    df : pd.DataFrame
        Full data with prices
    event_ids : pd.Series
        Event ID for each interval
    price_col : str
        Name of price column

    Returns
    -------
    pd.DataFrame
        Event summary with columns:
        - event_id
        - start_time
        - end_time
        - duration_min
        - max_price
        - mean_price
        - hour
        - weekday
        - month
    """
    events = []

    for eid in event_ids[event_ids > 0].unique():
        mask = event_ids == eid
        event_data = df[mask]

        start_time = event_data.index.min()
        end_time = event_data.index.max()

        events.append({
            'event_id': eid,
            'start_time': start_time,
            'end_time': end_time,
            'duration_min': len(event_data) * config.INTERVAL_MINUTES,
            'max_price': event_data[price_col].max(),
            'mean_price': event_data[price_col].mean(),
            'hour': start_time.hour,
            'weekday': start_time.weekday(),
            'month': start_time.month,
        })

    event_df = pd.DataFrame(events)
    logger.info(f"Created {len(event_df)} spike events")
    return event_df


# =============================================================================
# PRE-SPIKE FEATURES
# =============================================================================

def compute_pre_spike_features(
    df: pd.DataFrame,
    event_df: pd.DataFrame,
    window_minutes: int = config.PRE_SPIKE_WINDOW_MINUTES
) -> pd.DataFrame:
    """
    Compute features from the window before each spike event.

    Features:
    - demand_change_pct: % change in demand
    - solar_change_pct: % change in solar output
    - wind_change_pct: % change in wind output
    - price_slope: Linear slope of price
    - price_volatility: Std dev of price

    Parameters
    ----------
    df : pd.DataFrame
        Full data with all columns
    event_df : pd.DataFrame
        Spike event table
    window_minutes : int
        Lookback window in minutes

    Returns
    -------
    pd.DataFrame
        Event table with added feature columns
    """
    window_intervals = window_minutes // config.INTERVAL_MINUTES
    features = []

    for _, event in event_df.iterrows():
        start_time = event['start_time']

        # Get pre-spike window
        window_end = start_time
        window_start = start_time - pd.Timedelta(minutes=window_minutes)
        pre_window = df.loc[window_start:window_end].iloc[:-1]  # Exclude spike start

        if len(pre_window) < 2:
            features.append({
                'event_id': event['event_id'],
                'demand_change_pct': np.nan,
                'solar_change_pct': np.nan,
                'wind_change_pct': np.nan,
                'price_slope': np.nan,
                'price_volatility': np.nan,
            })
            continue

        feat = {'event_id': event['event_id']}

        # Demand change
        if 'total_demand' in pre_window.columns:
            demand_start = pre_window['total_demand'].iloc[0]
            demand_end = pre_window['total_demand'].iloc[-1]
            if demand_start > 0:
                feat['demand_change_pct'] = (demand_end - demand_start) / demand_start * 100
            else:
                feat['demand_change_pct'] = np.nan
        else:
            feat['demand_change_pct'] = np.nan

        # Solar change
        if 'solar' in pre_window.columns:
            solar_start = pre_window['solar'].iloc[0]
            solar_end = pre_window['solar'].iloc[-1]
            if solar_start > 0:
                feat['solar_change_pct'] = (solar_end - solar_start) / solar_start * 100
            else:
                feat['solar_change_pct'] = 0 if solar_end == 0 else np.inf
        else:
            feat['solar_change_pct'] = np.nan

        # Wind change
        if 'wind' in pre_window.columns:
            wind_start = pre_window['wind'].iloc[0]
            wind_end = pre_window['wind'].iloc[-1]
            if wind_start > 0:
                feat['wind_change_pct'] = (wind_end - wind_start) / wind_start * 100
            else:
                feat['wind_change_pct'] = 0 if wind_end == 0 else np.inf
        else:
            feat['wind_change_pct'] = np.nan

        # Price features
        if 'rrp' in pre_window.columns:
            prices = pre_window['rrp'].values
            feat['price_volatility'] = np.std(prices)
            # Linear slope (simple: last - first / n)
            feat['price_slope'] = (prices[-1] - prices[0]) / len(prices)
        else:
            feat['price_volatility'] = np.nan
            feat['price_slope'] = np.nan

        features.append(feat)

    feature_df = pd.DataFrame(features)
    result = event_df.merge(feature_df, on='event_id', how='left')

    return result


def compute_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add time-based features to dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with datetime index

    Returns
    -------
    pd.DataFrame
        Data with added time features
    """
    df = df.copy()
    df['hour'] = df.index.hour
    df['weekday'] = df.index.weekday
    df['month'] = df.index.month
    df['is_weekend'] = df['weekday'] >= 5
    df['is_peak_hour'] = df['hour'].isin(range(7, 22))

    return df


# =============================================================================
# VOLATILITY INDICATORS
# =============================================================================

def compute_rolling_volatility(
    df: pd.DataFrame,
    price_col: str = 'rrp',
    windows: dict = config.VOLATILITY_WINDOWS
) -> pd.DataFrame:
    """
    Compute rolling price volatility indicators.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with price column
    price_col : str
        Name of price column
    windows : dict
        Window names and sizes (in intervals)

    Returns
    -------
    pd.DataFrame
        Data with added volatility columns
    """
    df = df.copy()

    for name, window_size in windows.items():
        col_name = f'volatility_{name}'
        df[col_name] = df[price_col].rolling(window=window_size, min_periods=1).std()

    return df


def compute_daily_volatility_ratio(
    df: pd.DataFrame,
    price_col: str = 'rrp'
) -> pd.DataFrame:
    """
    Compute daily max/mean price ratio.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with price column
    price_col : str
        Name of price column

    Returns
    -------
    pd.DataFrame
        Daily volatility ratio
    """
    daily = df.groupby(df.index.date).agg({
        price_col: ['max', 'mean', 'std', 'min']
    })
    daily.columns = ['max_price', 'mean_price', 'std_price', 'min_price']
    daily['volatility_ratio'] = daily['max_price'] / daily['mean_price']
    daily['price_range'] = daily['max_price'] - daily['min_price']

    return daily


# =============================================================================
# RENEWABLE SHARE
# =============================================================================

def compute_renewable_share(
    df: pd.DataFrame,
    solar_col: str = 'solar',
    wind_col: str = 'wind',
    total_col: str = 'total_generation'
) -> pd.DataFrame:
    """
    Compute renewable energy share.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with generation columns
    solar_col : str
        Name of solar column
    wind_col : str
        Name of wind column
    total_col : str
        Name of total generation column (if available)

    Returns
    -------
    pd.DataFrame
        Data with renewable share column
    """
    df = df.copy()

    # Sum renewables
    solar = df[solar_col] if solar_col in df.columns else 0
    wind = df[wind_col] if wind_col in df.columns else 0
    df['renewable_output'] = solar + wind

    # Compute share
    if total_col in df.columns:
        df['renewable_share'] = df['renewable_output'] / df[total_col]
    elif 'total_demand' in df.columns:
        # Approximate using demand as proxy for generation
        df['renewable_share'] = df['renewable_output'] / df['total_demand']
    else:
        logger.warning("Cannot compute renewable share: no total generation or demand")
        df['renewable_share'] = np.nan

    # Handle edge cases
    df['renewable_share'] = df['renewable_share'].clip(0, 1)

    return df


def bin_renewable_share(
    df: pd.DataFrame,
    share_col: str = 'renewable_share',
    bins: List[float] = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
) -> pd.DataFrame:
    """
    Bin renewable share into categories.

    Parameters
    ----------
    df : pd.DataFrame
        Input data with renewable share column
    share_col : str
        Name of share column
    bins : List[float]
        Bin edges

    Returns
    -------
    pd.DataFrame
        Data with binned renewable share
    """
    df = df.copy()
    labels = [f'{bins[i]:.0%}-{bins[i+1]:.0%}' for i in range(len(bins)-1)]
    df['renewable_share_bin'] = pd.cut(df[share_col], bins=bins, labels=labels)

    return df
