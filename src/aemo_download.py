"""
AEMO NEMWeb data downloader.

Downloads dispatch price data from AEMO's public archive.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import logging
from typing import List, Optional
import time

from . import config

logger = logging.getLogger(__name__)

# AEMO Archive URLs
NEMWEB_ARCHIVE = "https://nemweb.com.au/Reports/Archive"
NEMWEB_CURRENT = "https://nemweb.com.au/Reports/Current"


def download_dispatch_price_month(
    year: int,
    month: int,
    save_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Download monthly DISPATCHIS (dispatch price) data from AEMO Archive.

    Parameters
    ----------
    year : int
        Year (e.g., 2024)
    month : int
        Month (1-12)
    save_dir : Path, optional
        Directory to save files

    Returns
    -------
    Path or None
        Path to downloaded/extracted CSV file
    """
    if save_dir is None:
        save_dir = config.DATA_RAW

    save_dir.mkdir(parents=True, exist_ok=True)

    # Construct URL for monthly archive
    # Format: PUBLIC_DISPATCHIS_YYYYMM01000000_YYYYMM+1_01000000.zip
    month_str = f"{year}{month:02d}"

    # Try different URL patterns
    patterns = [
        f"{NEMWEB_ARCHIVE}/DispatchIS_Reports/PUBLIC_DISPATCHIS_{month_str}.zip",
    ]

    for url in patterns:
        try:
            logger.info(f"Trying: {url}")
            response = requests.get(url, timeout=60)

            if response.status_code == 200:
                # Extract ZIP
                with ZipFile(BytesIO(response.content)) as zf:
                    for name in zf.namelist():
                        if name.endswith('.CSV') or name.endswith('.csv'):
                            output_path = save_dir / name
                            with open(output_path, 'wb') as f:
                                f.write(zf.read(name))
                            logger.info(f"Saved: {output_path}")
                            return output_path

        except Exception as e:
            logger.warning(f"Failed {url}: {e}")
            continue

    logger.error(f"Could not download data for {year}-{month:02d}")
    return None


def download_dispatch_price_range(
    start_year: int,
    start_month: int,
    end_year: int,
    end_month: int,
    save_dir: Optional[Path] = None
) -> List[Path]:
    """
    Download multiple months of dispatch price data.

    Returns list of downloaded file paths.
    """
    downloaded = []

    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)

    while current <= end:
        path = download_dispatch_price_month(current.year, current.month, save_dir)
        if path:
            downloaded.append(path)

        # Move to next month
        if current.month == 12:
            current = datetime(current.year + 1, 1, 1)
        else:
            current = datetime(current.year, current.month + 1, 1)

        # Be nice to AEMO servers
        time.sleep(1)

    return downloaded


def load_dispatchis_csv(file_path: Path, region: str = "NSW1") -> pd.DataFrame:
    """
    Load DISPATCHIS CSV file and extract price/demand data.

    Parameters
    ----------
    file_path : Path
        Path to CSV file
    region : str
        Region to filter (default: NSW1)

    Returns
    -------
    pd.DataFrame
        DataFrame with timestamp index, rrp, total_demand columns
    """
    # AEMO files have multiple record types - we want DISPATCH,PRICE
    # Read all lines and filter

    rows = []

    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')

            # Look for DISPATCH,REGION_SUMMARY or DISPATCH,PRICE records
            if len(parts) > 5:
                if parts[0] == 'D' and parts[1] == 'DISPATCH':
                    if parts[2] == 'PRICE' or parts[2] == 'REGION_SUMMARY':
                        rows.append(parts)

    if not rows:
        logger.warning(f"No price data found in {file_path}")
        return pd.DataFrame()

    # Parse based on record type
    # DISPATCH,PRICE format varies - find column indices dynamically
    # Common columns: SETTLEMENTDATE, REGIONID, RRP, TOTALDEMAND

    # First, find the header row (I record)
    headers = None
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) > 5 and parts[0] == 'I' and parts[1] == 'DISPATCH':
                if parts[2] == 'PRICE' or parts[2] == 'REGION_SUMMARY':
                    headers = parts
                    break

    if headers is None:
        logger.warning("Could not find header row")
        return pd.DataFrame()

    # Find column indices
    try:
        date_idx = headers.index('SETTLEMENTDATE')
        region_idx = headers.index('REGIONID')
        rrp_idx = headers.index('RRP')
    except ValueError as e:
        logger.warning(f"Missing required column: {e}")
        return pd.DataFrame()

    # Try to find demand column
    demand_idx = None
    for col in ['TOTALDEMAND', 'DEMAND', 'INITIALSUPPLY']:
        if col in headers:
            demand_idx = headers.index(col)
            break

    # Parse data rows
    data = []
    for row in rows:
        try:
            if len(row) > max(date_idx, region_idx, rrp_idx):
                row_region = row[region_idx].strip('"')
                if row_region == region:
                    record = {
                        'timestamp': pd.to_datetime(row[date_idx].strip('"')),
                        'rrp': float(row[rrp_idx]) if row[rrp_idx] else None,
                    }
                    if demand_idx and len(row) > demand_idx:
                        record['total_demand'] = float(row[demand_idx]) if row[demand_idx] else None
                    data.append(record)
        except (ValueError, IndexError) as e:
            continue

    if not data:
        logger.warning(f"No {region} data found")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.set_index('timestamp')
    df = df.sort_index()

    # Remove duplicates
    df = df[~df.index.duplicated(keep='first')]

    logger.info(f"Loaded {len(df)} records from {file_path}")
    return df


def create_sample_data(days: int = 30, save: bool = True) -> pd.DataFrame:
    """
    Create synthetic sample data for testing when AEMO download fails.

    This creates realistic-looking price data with:
    - Daily patterns (morning/evening peaks)
    - Random spikes
    - Demand correlation

    Parameters
    ----------
    days : int
        Number of days of data
    save : bool
        Whether to save to processed folder

    Returns
    -------
    pd.DataFrame
        Sample data
    """
    import numpy as np

    np.random.seed(42)

    # Create 5-minute timestamps
    start = datetime.now() - timedelta(days=days)
    timestamps = pd.date_range(start=start, periods=days * 288, freq='5T')

    n = len(timestamps)

    # Base price with daily pattern
    hours = timestamps.hour + timestamps.minute / 60
    daily_pattern = 50 + 30 * np.sin((hours - 6) * np.pi / 12)  # Peak around 6pm
    daily_pattern = np.clip(daily_pattern, 20, 100)

    # Add random variation
    noise = np.random.normal(0, 15, n)
    prices = daily_pattern + noise

    # Add random spikes (about 1% of intervals)
    spike_mask = np.random.random(n) < 0.01
    prices[spike_mask] = prices[spike_mask] + np.random.exponential(200, spike_mask.sum())

    # Clip negative prices (rare but possible)
    prices = np.clip(prices, -100, 15000)

    # Create demand (correlated with price)
    base_demand = 8000 + 2000 * np.sin((hours - 8) * np.pi / 12)
    demand = base_demand + np.random.normal(0, 500, n)
    demand = np.clip(demand, 5000, 14000)

    # Create solar (daytime only)
    solar = np.zeros(n)
    daytime = (hours >= 6) & (hours <= 18)
    solar[daytime] = 2000 * np.sin((hours[daytime] - 6) * np.pi / 12)
    solar = solar + np.random.normal(0, 200, n)
    solar = np.clip(solar, 0, 3000)

    # Create wind (random)
    wind = 500 + np.random.normal(0, 300, n)
    wind = wind + 200 * np.sin(np.arange(n) / 100)  # Some periodicity
    wind = np.clip(wind, 0, 1500)

    df = pd.DataFrame({
        'rrp': prices,
        'total_demand': demand,
        'solar': solar,
        'wind': wind,
    }, index=timestamps)

    df.index.name = 'timestamp'

    # Localize timezone
    df.index = df.index.tz_localize('Australia/Sydney')

    if save:
        config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
        output_path = config.DATA_PROCESSED / 'nsw_sample.parquet'
        df.to_parquet(output_path)
        logger.info(f"Saved sample data to {output_path}")

    return df


def test_aemo_connection() -> bool:
    """Test if AEMO NEMWeb is accessible."""
    try:
        response = requests.get(NEMWEB_ARCHIVE, timeout=10)
        print(f"AEMO NEMWeb status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"AEMO connection failed: {e}")
        return False
