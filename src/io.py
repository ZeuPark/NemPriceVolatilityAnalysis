"""
Data I/O functions for NEM Price Volatility Analysis.

Handles:
- Loading raw AEMO data
- Preprocessing and cleaning
- Saving processed data
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Union
import glob
import logging

from . import config

logger = logging.getLogger(__name__)


def load_raw_price_data(
    file_path: Union[str, Path],
    region: str = config.REGION
) -> pd.DataFrame:
    """
    Load raw AEMO price/demand data from CSV.

    Expected columns (AEMO DISPATCHPRICE format):
    - SETTLEMENTDATE: Timestamp
    - REGIONID: Region identifier
    - RRP: Regional Reference Price
    - TOTALDEMAND: Total demand (optional)

    Parameters
    ----------
    file_path : str or Path
        Path to the CSV file
    region : str
        Region to filter (default: NSW1)

    Returns
    -------
    pd.DataFrame
        Cleaned dataframe with datetime index
    """
    df = pd.read_csv(file_path)

    # Handle different column naming conventions
    col_map = {
        'SETTLEMENTDATE': 'timestamp',
        'TRADING_INTERVAL': 'timestamp',
        'INTERVAL_DATETIME': 'timestamp',
        'REGIONID': 'region',
        'RRP': 'rrp',
        'TOTALDEMAND': 'total_demand',
        'DEMAND': 'total_demand',
    }

    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Filter region
    if 'region' in df.columns:
        df = df[df['region'] == region].copy()

    # Parse timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.tz_localize(config.TIMEZONE, ambiguous='infer', nonexistent='shift_forward')

    # Sort by time
    df = df.sort_index()

    # Keep only needed columns
    keep_cols = ['rrp', 'total_demand', 'region']
    df = df[[c for c in keep_cols if c in df.columns]]

    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df


def load_raw_generation_data(
    file_path: Union[str, Path],
    region: str = config.REGION
) -> pd.DataFrame:
    """
    Load raw AEMO generation data (SCADA or aggregated).

    Parameters
    ----------
    file_path : str or Path
        Path to the CSV file
    region : str
        Region to filter

    Returns
    -------
    pd.DataFrame
        Generation data with solar, wind columns
    """
    df = pd.read_csv(file_path)

    col_map = {
        'SETTLEMENTDATE': 'timestamp',
        'INTERVAL_DATETIME': 'timestamp',
        'REGIONID': 'region',
    }

    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    if 'region' in df.columns:
        df = df[df['region'] == region].copy()

    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.tz_localize(config.TIMEZONE, ambiguous='infer', nonexistent='shift_forward')

    df = df.sort_index()
    return df


def load_all_raw_files(
    pattern: str,
    loader_func: callable,
    **kwargs
) -> pd.DataFrame:
    """
    Load and concatenate multiple raw files matching a glob pattern.

    Parameters
    ----------
    pattern : str
        Glob pattern for files (e.g., "data/raw/*.csv")
    loader_func : callable
        Function to load individual files
    **kwargs
        Additional arguments passed to loader_func

    Returns
    -------
    pd.DataFrame
        Combined dataframe
    """
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No files found matching {pattern}")

    dfs = []
    for f in files:
        try:
            df = loader_func(f, **kwargs)
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Error loading {f}: {e}")

    combined = pd.concat(dfs)
    combined = combined[~combined.index.duplicated(keep='first')]
    combined = combined.sort_index()

    logger.info(f"Combined {len(files)} files, {len(combined)} total rows")
    return combined


def resample_to_5min_grid(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resample data to exact 5-minute grid.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe with datetime index

    Returns
    -------
    pd.DataFrame
        Resampled dataframe with 5-min frequency
    """
    # Create regular 5-min grid
    start = df.index.min().floor('5T')
    end = df.index.max().ceil('5T')
    grid = pd.date_range(start=start, end=end, freq='5T', tz=config.TIMEZONE)

    # Reindex to grid
    df_resampled = df.reindex(grid, method='nearest', tolerance=pd.Timedelta('2.5min'))
    df_resampled.index.name = 'timestamp'

    # Mark missing values
    df_resampled['is_missing'] = df_resampled['rrp'].isna()

    logger.info(f"Resampled to 5-min grid: {len(df_resampled)} intervals, "
                f"{df_resampled['is_missing'].sum()} missing")

    return df_resampled


def save_processed_data(df: pd.DataFrame, filename: str) -> Path:
    """
    Save processed dataframe to parquet.

    Parameters
    ----------
    df : pd.DataFrame
        Processed dataframe
    filename : str
        Output filename (without extension)

    Returns
    -------
    Path
        Path to saved file
    """
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    output_path = config.DATA_PROCESSED / f"{filename}.parquet"
    df.to_parquet(output_path)
    logger.info(f"Saved processed data to {output_path}")
    return output_path


def load_processed_data(filename: str) -> pd.DataFrame:
    """
    Load processed dataframe from parquet.

    Parameters
    ----------
    filename : str
        Filename (without extension)

    Returns
    -------
    pd.DataFrame
        Loaded dataframe
    """
    input_path = config.DATA_PROCESSED / f"{filename}.parquet"
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df


def merge_price_and_generation(
    price_df: pd.DataFrame,
    gen_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge price/demand data with generation data.

    Parameters
    ----------
    price_df : pd.DataFrame
        Price and demand data
    gen_df : pd.DataFrame
        Generation data (solar, wind, etc.)

    Returns
    -------
    pd.DataFrame
        Merged dataframe
    """
    merged = price_df.join(gen_df, how='left', rsuffix='_gen')

    # Remove duplicate columns
    dup_cols = [c for c in merged.columns if c.endswith('_gen')]
    merged = merged.drop(columns=dup_cols)

    return merged
