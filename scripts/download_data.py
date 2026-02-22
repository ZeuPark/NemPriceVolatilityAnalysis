"""
Download NSW electricity data from AEMO NEMWeb.

Usage:
    python scripts/download_data.py --days 7
    python scripts/download_data.py --days 180  # 6 months
"""

import requests
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
import argparse
import re
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src import config


def get_available_files():
    """Get list of available daily ZIP files from AEMO."""
    url = 'https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/'
    r = requests.get(url, timeout=30)
    r.raise_for_status()

    # Find daily ZIP files (format: PUBLIC_DISPATCHIS_YYYYMMDD.zip)
    zips = list(set(re.findall(r'PUBLIC_DISPATCHIS_\d{8}\.zip', r.text)))
    zips.sort()
    return zips


def download_and_parse_day(date_str: str) -> pd.DataFrame:
    """
    Download and parse one day of dispatch price data.

    Parameters
    ----------
    date_str : str
        Date in YYYYMMDD format

    Returns
    -------
    pd.DataFrame
        DataFrame with NSW1 price and demand data
    """
    url = f'https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/PUBLIC_DISPATCHIS_{date_str}.zip'

    print(f"  Downloading {date_str}...", end=" ", flush=True)

    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"FAILED: {e}")
        return pd.DataFrame()

    rows = []

    # Extract nested ZIPs
    with ZipFile(BytesIO(resp.content)) as outer_zip:
        inner_zips = [n for n in outer_zip.namelist() if n.endswith('.zip')]

        for inner_name in inner_zips:
            inner_content = outer_zip.read(inner_name)
            with ZipFile(BytesIO(inner_content)) as inner_zip:
                for csv_name in inner_zip.namelist():
                    if csv_name.endswith('.CSV'):
                        csv_content = inner_zip.read(csv_name).decode('utf-8', errors='ignore')

                        # Parse CSV content
                        for line in csv_content.split('\n'):
                            parts = line.strip().split(',')

                            # DISPATCH,PRICE record (version 5)
                            # Format: D,DISPATCH,PRICE,5,SETTLEMENTDATE,RUNNO,REGIONID,...,RRP,...
                            # Indices: 0,1,2,3,4,5,6,7,8,9
                            if (len(parts) > 10 and
                                parts[0] == 'D' and
                                parts[1] == 'DISPATCH' and
                                parts[2] == 'PRICE'):

                                region = parts[6].strip('"')
                                if region == 'NSW1':
                                    try:
                                        timestamp = parts[4].strip('"')
                                        rrp = float(parts[9])  # RRP is at index 9
                                        rows.append({
                                            'timestamp': timestamp,
                                            'rrp': rrp
                                        })
                                    except (ValueError, IndexError):
                                        pass

    if not rows:
        print("no data")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    df = df[~df.index.duplicated(keep='first')]

    print(f"{len(df)} records")
    return df


def main():
    parser = argparse.ArgumentParser(description='Download NSW electricity data from AEMO')
    parser.add_argument('--days', type=int, default=7, help='Number of days to download')
    parser.add_argument('--output', type=str, default='nsw_processed', help='Output filename')
    args = parser.parse_args()

    print(f"Fetching list of available files...")
    available = get_available_files()
    print(f"Found {len(available)} daily files")
    print(f"Available range: {available[0]} to {available[-1]}")

    # Select files to download
    to_download = available[-args.days:]
    print(f"\nDownloading {len(to_download)} days of data...")

    all_dfs = []
    for fname in to_download:
        date_str = fname.replace('PUBLIC_DISPATCHIS_', '').replace('.zip', '')
        df = download_and_parse_day(date_str)
        if len(df) > 0:
            all_dfs.append(df)

    if not all_dfs:
        print("ERROR: No data downloaded!")
        return 1

    # Combine all days
    combined = pd.concat(all_dfs)
    combined = combined.sort_index()
    combined = combined[~combined.index.duplicated(keep='first')]

    # Localize timezone
    combined.index = combined.index.tz_localize('Australia/Sydney', ambiguous='infer')

    # Save
    config.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    output_path = config.DATA_PROCESSED / f"{args.output}.parquet"
    combined.to_parquet(output_path)

    print(f"\n" + "="*50)
    print(f"DOWNLOAD COMPLETE")
    print(f"="*50)
    print(f"Records: {len(combined):,}")
    print(f"Date range: {combined.index.min()} to {combined.index.max()}")
    print(f"RRP range: ${combined['rrp'].min():.2f} to ${combined['rrp'].max():.2f}")
    print(f"Mean RRP: ${combined['rrp'].mean():.2f}")
    print(f"Saved to: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
