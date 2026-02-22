"""
OpenNEM API client for fetching NSW electricity market data.

API Documentation: https://api.opennem.org.au/docs
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from typing import Optional
import logging
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

BASE_URL = "https://api.opennem.org.au"


def fetch_nsw_power_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    months_back: int = 6
) -> pd.DataFrame:
    """
    Fetch NSW power generation and price data from OpenNEM.

    Parameters
    ----------
    start_date : str, optional
        Start date in 'YYYY-MM-DD' format
    end_date : str, optional
        End date in 'YYYY-MM-DD' format
    months_back : int
        If dates not specified, fetch this many months back

    Returns
    -------
    pd.DataFrame
        DataFrame with columns: timestamp, price, demand, solar, wind, etc.
    """
    # Calculate date range if not specified
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_dt = datetime.now() - timedelta(days=months_back * 30)
        start_date = start_dt.strftime('%Y-%m-%d')

    logger.info(f"Fetching NSW data from {start_date} to {end_date}")

    # OpenNEM energy endpoint for NSW
    url = f"{BASE_URL}/stats/power/network/NEM/NSW1"

    params = {
        'interval': '5m',
        'date_min': start_date,
        'date_max': end_date,
    }

    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise

    # Parse response into DataFrame
    df = _parse_opennem_response(data)

    logger.info(f"Fetched {len(df)} records")
    return df


def _parse_opennem_response(data: dict) -> pd.DataFrame:
    """
    Parse OpenNEM API response into a clean DataFrame.
    """
    all_series = {}

    for series in data.get('data', []):
        fuel_tech = series.get('fuel_tech') or series.get('type') or series.get('id', 'unknown')
        history = series.get('history', {})

        if not history:
            continue

        # Get time series data
        start = pd.to_datetime(history.get('start'))
        interval_str = history.get('interval', '5m')

        # Parse interval
        if interval_str == '5m':
            freq = '5T'
        elif interval_str == '30m':
            freq = '30T'
        else:
            freq = '5T'

        values = history.get('data', [])

        if not values:
            continue

        # Create datetime index
        timestamps = pd.date_range(start=start, periods=len(values), freq=freq)

        # Map fuel_tech to our column names
        col_name = _map_fuel_tech(fuel_tech)
        if col_name:
            all_series[col_name] = pd.Series(values, index=timestamps)

    # Combine all series
    if not all_series:
        raise ValueError("No data found in API response")

    df = pd.DataFrame(all_series)
    df.index.name = 'timestamp'

    # Ensure we have key columns
    _ensure_columns(df)

    return df


def _map_fuel_tech(fuel_tech: str) -> Optional[str]:
    """Map OpenNEM fuel_tech codes to our column names."""
    mapping = {
        # Price
        'price': 'rrp',
        'trading_price': 'rrp',

        # Demand
        'demand': 'total_demand',
        'demand_total': 'total_demand',

        # Renewables
        'solar_utility': 'solar_utility',
        'solar_rooftop': 'solar_rooftop',
        'wind': 'wind',

        # Other generation
        'coal_black': 'coal_black',
        'coal_brown': 'coal_brown',
        'gas_ccgt': 'gas_ccgt',
        'gas_ocgt': 'gas_ocgt',
        'gas_recip': 'gas_recip',
        'hydro': 'hydro',
        'battery_charging': 'battery_charging',
        'battery_discharging': 'battery_discharging',
        'pumps': 'pumps',

        # Imports/Exports
        'imports': 'imports',
        'exports': 'exports',
    }

    return mapping.get(fuel_tech.lower(), None)


def _ensure_columns(df: pd.DataFrame) -> None:
    """Ensure we have the key columns, create aggregates if needed."""

    # Aggregate solar
    if 'solar' not in df.columns:
        solar_cols = [c for c in df.columns if 'solar' in c.lower()]
        if solar_cols:
            df['solar'] = df[solar_cols].sum(axis=1)

    # Aggregate coal
    if 'coal' not in df.columns:
        coal_cols = [c for c in df.columns if 'coal' in c.lower()]
        if coal_cols:
            df['coal'] = df[coal_cols].sum(axis=1)

    # Aggregate gas
    if 'gas' not in df.columns:
        gas_cols = [c for c in df.columns if 'gas' in c.lower()]
        if gas_cols:
            df['gas'] = df[gas_cols].sum(axis=1)


def fetch_and_save_nsw_data(
    months_back: int = 6,
    output_name: str = 'nsw_opennem'
) -> Path:
    """
    Fetch NSW data and save to processed folder.

    Parameters
    ----------
    months_back : int
        Number of months to fetch
    output_name : str
        Output filename (without extension)

    Returns
    -------
    Path
        Path to saved file
    """
    df = fetch_nsw_power_data(months_back=months_back)

    # Localize timezone
    if df.index.tz is None:
        df.index = df.index.tz_localize('Australia/Sydney', ambiguous='infer')

    # Save to parquet
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    output_path = config.DATA_PROCESSED / f"{output_name}.parquet"
    df.to_parquet(output_path)

    logger.info(f"Saved {len(df)} records to {output_path}")

    return output_path


def test_api_connection() -> bool:
    """Test if OpenNEM API is accessible."""
    try:
        response = requests.get(f"{BASE_URL}/stats/power/network/NEM", timeout=10)
        response.raise_for_status()
        print("OpenNEM API connection successful!")
        return True
    except Exception as e:
        print(f"OpenNEM API connection failed: {e}")
        return False
