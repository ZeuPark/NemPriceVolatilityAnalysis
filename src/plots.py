"""
Visualization functions for NEM Price Volatility Analysis.

8 key graphs:
1. NSW RRP time series
2. RRP distribution histogram
3. Weekday-hour heatmap
4. Monthly spike count bar chart
5. Pre-spike average profile
6. Spike vs non-spike feature boxplot
7. Volatility vs renewable share scatter
8. Case study multi-line plots
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from typing import Optional, List, Dict, Tuple
from pathlib import Path

from . import config

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")


def save_figure(fig: plt.Figure, name: str, dpi: int = config.FIGURE_DPI) -> Path:
    """Save figure to reports/figures directory."""
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = config.FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    return path


# =============================================================================
# GRAPH 1: RRP TIME SERIES
# =============================================================================

def plot_rrp_timeseries(
    df: pd.DataFrame,
    price_col: str = 'rrp',
    spike_threshold: Optional[float] = None,
    title: str = "NSW Regional Reference Price (RRP)",
    save_name: Optional[str] = "01_rrp_timeseries"
) -> plt.Figure:
    """
    Plot full RRP time series with optional spike threshold line.

    Purpose: Overview of price behavior over the analysis period.
    """
    fig, ax = plt.subplots(figsize=config.FIGURE_SIZE_WIDE)

    ax.plot(df.index, df[price_col], color=config.COLORS['price'],
            linewidth=0.5, alpha=0.8, label='RRP')

    if spike_threshold:
        ax.axhline(y=spike_threshold, color=config.COLORS['spike'],
                   linestyle='--', linewidth=1.5, label=f'Spike threshold (${spike_threshold})')

    ax.set_xlabel('Date')
    ax.set_ylabel('RRP ($/MWh)')
    ax.set_title(title)
    ax.legend(loc='upper right')

    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 2: RRP DISTRIBUTION
# =============================================================================

def plot_rrp_distribution(
    df: pd.DataFrame,
    price_col: str = 'rrp',
    log_scale: bool = True,
    percentiles: List[float] = [90, 95, 99],
    save_name: Optional[str] = "02_rrp_distribution"
) -> plt.Figure:
    """
    Plot RRP distribution with histogram and percentile markers.

    Purpose: Show price distribution shape, especially the heavy right tail.
    """
    fig, axes = plt.subplots(1, 2, figsize=config.FIGURE_SIZE_WIDE)

    prices = df[price_col].dropna()

    # Left: Linear scale histogram
    ax1 = axes[0]
    ax1.hist(prices, bins=100, color=config.COLORS['price'],
             alpha=0.7, edgecolor='white')
    ax1.set_xlabel('RRP ($/MWh)')
    ax1.set_ylabel('Frequency')
    ax1.set_title('RRP Distribution (Linear Scale)')

    # Add percentile lines
    for p in percentiles:
        val = prices.quantile(p / 100)
        ax1.axvline(x=val, color=config.COLORS['spike'], linestyle='--',
                    alpha=0.7, label=f'{p}th: ${val:.0f}')
    ax1.legend()

    # Right: Log scale or zoomed tail
    ax2 = axes[1]
    if log_scale:
        # Log-transform positive prices
        log_prices = np.log10(prices[prices > 0])
        ax2.hist(log_prices, bins=100, color=config.COLORS['price'],
                 alpha=0.7, edgecolor='white')
        ax2.set_xlabel('log10(RRP)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('RRP Distribution (Log Scale)')
    else:
        # Focus on tail
        tail = prices[prices > prices.quantile(0.9)]
        ax2.hist(tail, bins=50, color=config.COLORS['spike'],
                 alpha=0.7, edgecolor='white')
        ax2.set_xlabel('RRP ($/MWh)')
        ax2.set_ylabel('Frequency')
        ax2.set_title('RRP Distribution (Top 10%)')

    plt.tight_layout()

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 3: WEEKDAY-HOUR HEATMAP
# =============================================================================

def plot_weekday_hour_heatmap(
    df: pd.DataFrame,
    price_col: str = 'rrp',
    agg_func: str = 'mean',
    save_name: Optional[str] = "03_weekday_hour_heatmap"
) -> plt.Figure:
    """
    Plot average/median price by weekday and hour.

    Purpose: Reveal typical price patterns (peak hours, weekend differences).
    """
    fig, ax = plt.subplots(figsize=config.FIGURE_SIZE_SQUARE)

    # Add time features if not present
    df_temp = df.copy()
    if 'hour' not in df_temp.columns:
        df_temp['hour'] = df_temp.index.hour
    if 'weekday' not in df_temp.columns:
        df_temp['weekday'] = df_temp.index.weekday

    # Pivot
    pivot = df_temp.pivot_table(
        values=price_col,
        index='weekday',
        columns='hour',
        aggfunc=agg_func
    )

    # Plot heatmap
    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    sns.heatmap(pivot, ax=ax, cmap='YlOrRd', annot=False,
                cbar_kws={'label': f'{agg_func.title()} RRP ($/MWh)'})

    ax.set_yticklabels(weekday_labels, rotation=0)
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Day of Week')
    ax.set_title(f'{agg_func.title()} RRP by Weekday and Hour')

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 4: MONTHLY SPIKE COUNT
# =============================================================================

def plot_monthly_spike_count(
    event_df: pd.DataFrame,
    save_name: Optional[str] = "04_monthly_spike_count"
) -> plt.Figure:
    """
    Plot bar chart of spike events by month.

    Purpose: Show seasonal patterns in spike frequency.
    """
    fig, ax = plt.subplots(figsize=config.FIGURE_SIZE_WIDE)

    # Group by month
    event_df['year_month'] = event_df['start_time'].dt.to_period('M')
    monthly = event_df.groupby('year_month').size()

    # Plot
    x = range(len(monthly))
    ax.bar(x, monthly.values, color=config.COLORS['spike'], alpha=0.8, edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels([str(m) for m in monthly.index], rotation=45, ha='right')
    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Spike Events')
    ax.set_title('Spike Events by Month')

    # Add mean line
    ax.axhline(y=monthly.mean(), color='black', linestyle='--',
               linewidth=1, label=f'Mean: {monthly.mean():.1f}')
    ax.legend()

    plt.tight_layout()

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 5: PRE-SPIKE AVERAGE PROFILE
# =============================================================================

def plot_pre_spike_profile(
    df: pd.DataFrame,
    event_df: pd.DataFrame,
    window_before: int = 60,
    window_after: int = 30,
    save_name: Optional[str] = "05_pre_spike_profile"
) -> plt.Figure:
    """
    Plot average profile of price/demand/renewables around spike events.

    Purpose: Visualize what typically happens before and during spikes.
    """
    fig, axes = plt.subplots(2, 2, figsize=config.FIGURE_SIZE_TALL)

    intervals_before = window_before // config.INTERVAL_MINUTES
    intervals_after = window_after // config.INTERVAL_MINUTES
    total_intervals = intervals_before + intervals_after + 1

    # Collect aligned windows around each event
    profiles = {'rrp': [], 'total_demand': [], 'solar': [], 'wind': []}

    for _, event in event_df.iterrows():
        start_time = event['start_time']
        window_start = start_time - pd.Timedelta(minutes=window_before)
        window_end = start_time + pd.Timedelta(minutes=window_after)

        window_data = df.loc[window_start:window_end]

        if len(window_data) >= total_intervals * 0.8:  # Allow some missing
            for col in profiles.keys():
                if col in window_data.columns:
                    # Align to fixed length
                    values = window_data[col].values[:total_intervals]
                    if len(values) == total_intervals:
                        profiles[col].append(values)

    # Time axis (minutes relative to spike)
    time_axis = np.arange(-window_before, window_after + config.INTERVAL_MINUTES,
                          config.INTERVAL_MINUTES)[:total_intervals]

    plot_configs = [
        ('rrp', axes[0, 0], 'RRP ($/MWh)', config.COLORS['price']),
        ('total_demand', axes[0, 1], 'Total Demand (MW)', config.COLORS['demand']),
        ('solar', axes[1, 0], 'Solar Output (MW)', config.COLORS['solar']),
        ('wind', axes[1, 1], 'Wind Output (MW)', config.COLORS['wind']),
    ]

    for col, ax, ylabel, color in plot_configs:
        if profiles[col]:
            arr = np.array(profiles[col])
            mean_profile = np.nanmean(arr, axis=0)
            std_profile = np.nanstd(arr, axis=0)

            ax.plot(time_axis, mean_profile, color=color, linewidth=2, label='Mean')
            ax.fill_between(time_axis, mean_profile - std_profile,
                           mean_profile + std_profile, color=color, alpha=0.2)
            ax.axvline(x=0, color=config.COLORS['spike'], linestyle='--',
                      linewidth=1.5, label='Spike start')
            ax.set_xlabel('Minutes relative to spike')
            ax.set_ylabel(ylabel)
            ax.legend(loc='upper left')
            ax.set_title(f'{col.replace("_", " ").title()} Around Spikes (n={len(profiles[col])})')
        else:
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title(col.replace("_", " ").title())

    plt.tight_layout()

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 6: SPIKE VS NON-SPIKE BOXPLOT
# =============================================================================

def plot_spike_feature_comparison(
    df: pd.DataFrame,
    is_spike: pd.Series,
    feature_cols: List[str],
    save_name: Optional[str] = "06_spike_feature_comparison"
) -> plt.Figure:
    """
    Boxplot comparing features between spike and non-spike periods.

    Purpose: Show which features differ most between spike and normal.
    """
    n_features = len(feature_cols)
    n_cols = min(3, n_features)
    n_rows = (n_features + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
    if n_features == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, col in enumerate(feature_cols):
        ax = axes[i]
        if col not in df.columns:
            ax.text(0.5, 0.5, f'{col}\nnot available', ha='center', va='center')
            continue

        # Prepare data
        plot_df = pd.DataFrame({
            'value': df[col],
            'group': is_spike.map({True: 'Spike', False: 'Normal'})
        }).dropna()

        # Create boxplot
        sns.boxplot(data=plot_df, x='group', y='value', ax=ax,
                   palette={'Spike': config.COLORS['spike'],
                           'Normal': config.COLORS['normal']})

        ax.set_xlabel('')
        ax.set_ylabel(col.replace('_', ' ').title())
        ax.set_title(col.replace('_', ' ').title())

    # Hide unused axes
    for i in range(n_features, len(axes)):
        axes[i].set_visible(False)

    plt.suptitle('Feature Comparison: Spike vs Non-Spike Periods', y=1.02)
    plt.tight_layout()

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 7: VOLATILITY VS RENEWABLE SHARE
# =============================================================================

def plot_volatility_vs_renewable(
    df: pd.DataFrame,
    volatility_col: str = 'volatility_1h',
    renewable_col: str = 'renewable_share',
    save_name: Optional[str] = "07_volatility_vs_renewable"
) -> plt.Figure:
    """
    Scatter plot of volatility vs renewable share with trend line.

    Purpose: Quantify relationship between renewables and price volatility.
    """
    fig, axes = plt.subplots(1, 2, figsize=config.FIGURE_SIZE_WIDE)

    # Prepare data
    plot_df = df[[volatility_col, renewable_col]].dropna()

    # Left: Scatter plot with regression
    ax1 = axes[0]

    # Subsample for visibility if too many points
    if len(plot_df) > 5000:
        sample = plot_df.sample(5000, random_state=42)
    else:
        sample = plot_df

    ax1.scatter(sample[renewable_col], sample[volatility_col],
               alpha=0.3, s=10, color=config.COLORS['price'])

    # Add trend line
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        plot_df[renewable_col], plot_df[volatility_col]
    )
    x_line = np.array([plot_df[renewable_col].min(), plot_df[renewable_col].max()])
    y_line = slope * x_line + intercept
    ax1.plot(x_line, y_line, color=config.COLORS['spike'], linewidth=2,
            label=f'R² = {r_value**2:.3f}')

    ax1.set_xlabel('Renewable Share')
    ax1.set_ylabel('Price Volatility (1h rolling std)')
    ax1.set_title('Volatility vs Renewable Share')
    ax1.legend()

    # Right: Binned comparison
    ax2 = axes[1]

    # Bin renewable share
    bins = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
    labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50%+']
    plot_df['bin'] = pd.cut(plot_df[renewable_col], bins=bins, labels=labels)

    binned = plot_df.groupby('bin')[volatility_col].agg(['mean', 'std', 'count'])

    x = range(len(binned))
    ax2.bar(x, binned['mean'], yerr=binned['std'], color=config.COLORS['wind'],
           alpha=0.8, capsize=3)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=45)
    ax2.set_xlabel('Renewable Share Bin')
    ax2.set_ylabel('Mean Volatility')
    ax2.set_title('Mean Volatility by Renewable Share')

    # Add count labels
    for i, (idx, row) in enumerate(binned.iterrows()):
        ax2.annotate(f'n={int(row["count"])}', (i, row['mean'] + row['std']),
                    ha='center', fontsize=8)

    plt.tight_layout()

    if save_name:
        save_figure(fig, save_name)

    return fig


# =============================================================================
# GRAPH 8: CASE STUDY PLOTS
# =============================================================================

def plot_case_study(
    df: pd.DataFrame,
    event: pd.Series,
    hours_before: int = 6,
    hours_after: int = 6,
    case_number: int = 1,
    save_name: Optional[str] = None
) -> plt.Figure:
    """
    Detailed multi-line plot for a single spike event case study.

    Purpose: Deep dive into individual spike events with full context.
    """
    fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)

    # Get window
    start = event['start_time'] - pd.Timedelta(hours=hours_before)
    end = event['end_time'] + pd.Timedelta(hours=hours_after)
    window = df.loc[start:end]

    # Panel 1: Price
    ax1 = axes[0]
    ax1.plot(window.index, window['rrp'], color=config.COLORS['price'],
             linewidth=1.5, label='RRP')
    ax1.axvline(x=event['start_time'], color=config.COLORS['spike'],
                linestyle='--', label='Spike start')
    ax1.axvline(x=event['end_time'], color=config.COLORS['spike'],
                linestyle=':', label='Spike end')
    ax1.set_ylabel('RRP ($/MWh)')
    ax1.legend(loc='upper right')
    ax1.set_title(f'Case Study #{case_number}: Spike on {event["start_time"].strftime("%Y-%m-%d %H:%M")}'
                  f' (Max: ${event["max_price"]:.0f}/MWh)')

    # Panel 2: Demand
    ax2 = axes[1]
    if 'total_demand' in window.columns:
        ax2.plot(window.index, window['total_demand'],
                color=config.COLORS['demand'], linewidth=1.5, label='Total Demand')
        ax2.axvline(x=event['start_time'], color=config.COLORS['spike'], linestyle='--')
        ax2.axvline(x=event['end_time'], color=config.COLORS['spike'], linestyle=':')
        ax2.set_ylabel('Demand (MW)')
        ax2.legend(loc='upper right')
    else:
        ax2.text(0.5, 0.5, 'Demand data not available', ha='center', va='center',
                transform=ax2.transAxes)

    # Panel 3: Renewables
    ax3 = axes[2]
    has_renewable = False
    if 'solar' in window.columns:
        ax3.plot(window.index, window['solar'], color=config.COLORS['solar'],
                linewidth=1.5, label='Solar')
        has_renewable = True
    if 'wind' in window.columns:
        ax3.plot(window.index, window['wind'], color=config.COLORS['wind'],
                linewidth=1.5, label='Wind')
        has_renewable = True

    if has_renewable:
        ax3.axvline(x=event['start_time'], color=config.COLORS['spike'], linestyle='--')
        ax3.axvline(x=event['end_time'], color=config.COLORS['spike'], linestyle=':')
        ax3.set_ylabel('Generation (MW)')
        ax3.legend(loc='upper right')
    else:
        ax3.text(0.5, 0.5, 'Renewable data not available', ha='center', va='center',
                transform=ax3.transAxes)

    # Panel 4: Renewable share (if available)
    ax4 = axes[3]
    if 'renewable_share' in window.columns:
        ax4.plot(window.index, window['renewable_share'] * 100,
                color=config.COLORS['wind'], linewidth=1.5, label='Renewable %')
        ax4.axvline(x=event['start_time'], color=config.COLORS['spike'], linestyle='--')
        ax4.axvline(x=event['end_time'], color=config.COLORS['spike'], linestyle=':')
        ax4.set_ylabel('Renewable Share (%)')
        ax4.legend(loc='upper right')
    else:
        ax4.text(0.5, 0.5, 'Renewable share not available', ha='center', va='center',
                transform=ax4.transAxes)

    ax4.set_xlabel('Time')

    # Format x-axis
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    plt.xticks(rotation=45)

    plt.tight_layout()

    if save_name is None:
        save_name = f"08_case_study_{case_number}"
    save_figure(fig, save_name)

    return fig


def plot_all_case_studies(
    df: pd.DataFrame,
    event_df: pd.DataFrame,
    n_cases: int = 3,
    selection_method: str = 'max_price'
) -> List[plt.Figure]:
    """
    Generate case study plots for top N events.

    Parameters
    ----------
    df : pd.DataFrame
        Full data
    event_df : pd.DataFrame
        Event table
    n_cases : int
        Number of case studies
    selection_method : str
        How to select events ('max_price', 'random', 'diverse')
    """
    if selection_method == 'max_price':
        selected = event_df.nlargest(n_cases, 'max_price')
    elif selection_method == 'random':
        selected = event_df.sample(n_cases, random_state=42)
    elif selection_method == 'diverse':
        # Select from different months/hours
        selected = event_df.groupby('month').apply(
            lambda x: x.nlargest(1, 'max_price')
        ).head(n_cases)
    else:
        selected = event_df.head(n_cases)

    figs = []
    for i, (_, event) in enumerate(selected.iterrows(), 1):
        fig = plot_case_study(df, event, case_number=i)
        figs.append(fig)

    return figs
