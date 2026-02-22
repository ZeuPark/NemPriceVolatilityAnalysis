"""
Statistical analysis and simple models for spike driver analysis.

Includes:
- Statistical comparison between spike and non-spike periods
- Logistic regression for spike prediction
- Decision tree for interpretable feature importance
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats
import logging

from . import config

logger = logging.getLogger(__name__)


# =============================================================================
# STATISTICAL COMPARISON
# =============================================================================

def compare_spike_vs_normal(
    df: pd.DataFrame,
    is_spike: pd.Series,
    feature_cols: List[str]
) -> pd.DataFrame:
    """
    Compare feature distributions between spike and normal periods.

    Parameters
    ----------
    df : pd.DataFrame
        Data with features
    is_spike : pd.Series
        Boolean indicating spike intervals
    feature_cols : List[str]
        Columns to compare

    Returns
    -------
    pd.DataFrame
        Comparison statistics for each feature
    """
    results = []

    for col in feature_cols:
        if col not in df.columns:
            continue

        spike_vals = df.loc[is_spike, col].dropna()
        normal_vals = df.loc[~is_spike, col].dropna()

        if len(spike_vals) < 2 or len(normal_vals) < 2:
            continue

        # Basic stats
        result = {
            'feature': col,
            'spike_mean': spike_vals.mean(),
            'spike_median': spike_vals.median(),
            'spike_std': spike_vals.std(),
            'normal_mean': normal_vals.mean(),
            'normal_median': normal_vals.median(),
            'normal_std': normal_vals.std(),
            'spike_n': len(spike_vals),
            'normal_n': len(normal_vals),
        }

        # Effect size (Cohen's d)
        pooled_std = np.sqrt(
            ((len(spike_vals)-1) * spike_vals.std()**2 +
             (len(normal_vals)-1) * normal_vals.std()**2) /
            (len(spike_vals) + len(normal_vals) - 2)
        )
        if pooled_std > 0:
            result['cohens_d'] = (spike_vals.mean() - normal_vals.mean()) / pooled_std
        else:
            result['cohens_d'] = np.nan

        # Statistical test (Mann-Whitney U)
        try:
            stat, pval = stats.mannwhitneyu(spike_vals, normal_vals, alternative='two-sided')
            result['mannwhitney_stat'] = stat
            result['mannwhitney_pval'] = pval
        except Exception:
            result['mannwhitney_stat'] = np.nan
            result['mannwhitney_pval'] = np.nan

        results.append(result)

    return pd.DataFrame(results)


def analyze_event_features(
    event_df: pd.DataFrame,
    feature_cols: List[str]
) -> pd.DataFrame:
    """
    Summarize feature distributions for spike events.

    Parameters
    ----------
    event_df : pd.DataFrame
        Event table with features
    feature_cols : List[str]
        Feature columns to analyze

    Returns
    -------
    pd.DataFrame
        Summary statistics
    """
    summary = []

    for col in feature_cols:
        if col not in event_df.columns:
            continue

        vals = event_df[col].dropna()
        if len(vals) == 0:
            continue

        summary.append({
            'feature': col,
            'mean': vals.mean(),
            'median': vals.median(),
            'std': vals.std(),
            'min': vals.min(),
            'max': vals.max(),
            'q25': vals.quantile(0.25),
            'q75': vals.quantile(0.75),
            'n': len(vals),
        })

    return pd.DataFrame(summary)


# =============================================================================
# CORRELATION ANALYSIS
# =============================================================================

def compute_volatility_renewable_correlation(
    df: pd.DataFrame,
    volatility_cols: List[str],
    renewable_col: str = 'renewable_share'
) -> pd.DataFrame:
    """
    Compute correlation between volatility and renewable share.

    Parameters
    ----------
    df : pd.DataFrame
        Data with volatility and renewable columns
    volatility_cols : List[str]
        Volatility indicator columns
    renewable_col : str
        Renewable share column

    Returns
    -------
    pd.DataFrame
        Correlation results
    """
    results = []

    for vol_col in volatility_cols:
        if vol_col not in df.columns or renewable_col not in df.columns:
            continue

        valid = df[[vol_col, renewable_col]].dropna()
        if len(valid) < 10:
            continue

        # Pearson correlation
        pearson_r, pearson_p = stats.pearsonr(valid[vol_col], valid[renewable_col])

        # Spearman correlation
        spearman_r, spearman_p = stats.spearmanr(valid[vol_col], valid[renewable_col])

        results.append({
            'volatility_metric': vol_col,
            'pearson_r': pearson_r,
            'pearson_pval': pearson_p,
            'spearman_r': spearman_r,
            'spearman_pval': spearman_p,
            'n': len(valid),
        })

    return pd.DataFrame(results)


def compare_volatility_by_renewable_bin(
    df: pd.DataFrame,
    volatility_col: str,
    bin_col: str = 'renewable_share_bin'
) -> pd.DataFrame:
    """
    Compare volatility across renewable share bins.

    Parameters
    ----------
    df : pd.DataFrame
        Data with volatility and bin columns
    volatility_col : str
        Volatility column
    bin_col : str
        Renewable share bin column

    Returns
    -------
    pd.DataFrame
        Volatility by bin
    """
    grouped = df.groupby(bin_col)[volatility_col].agg(['mean', 'median', 'std', 'count'])
    grouped.columns = ['mean', 'median', 'std', 'n']
    return grouped.reset_index()


# =============================================================================
# CLASSIFICATION MODELS
# =============================================================================

def prepare_classification_data(
    df: pd.DataFrame,
    is_spike: pd.Series,
    feature_cols: List[str]
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Prepare data for spike classification.

    Parameters
    ----------
    df : pd.DataFrame
        Full data
    is_spike : pd.Series
        Target variable
    feature_cols : List[str]
        Feature columns

    Returns
    -------
    Tuple[pd.DataFrame, pd.Series]
        X (features), y (target)
    """
    available_cols = [c for c in feature_cols if c in df.columns]
    X = df[available_cols].copy()
    y = is_spike.copy()

    # Handle missing values
    valid_idx = X.notna().all(axis=1)
    X = X[valid_idx]
    y = y[valid_idx]

    return X, y


def fit_logistic_regression(
    X: pd.DataFrame,
    y: pd.Series
) -> Dict:
    """
    Fit logistic regression for spike prediction.

    Parameters
    ----------
    X : pd.DataFrame
        Features
    y : pd.Series
        Target

    Returns
    -------
    Dict
        Model results including coefficients and metrics
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import classification_report, roc_auc_score

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Fit model
    model = LogisticRegression(class_weight='balanced', max_iter=1000)
    model.fit(X_scaled, y)

    # Cross-validation
    cv_scores = cross_val_score(model, X_scaled, y, cv=5, scoring='roc_auc')

    # Predictions
    y_pred = model.predict(X_scaled)
    y_prob = model.predict_proba(X_scaled)[:, 1]

    # Coefficients
    coef_df = pd.DataFrame({
        'feature': X.columns,
        'coefficient': model.coef_[0],
        'abs_coefficient': np.abs(model.coef_[0])
    }).sort_values('abs_coefficient', ascending=False)

    return {
        'model': model,
        'scaler': scaler,
        'coefficients': coef_df,
        'cv_auc_mean': cv_scores.mean(),
        'cv_auc_std': cv_scores.std(),
        'train_auc': roc_auc_score(y, y_prob),
        'classification_report': classification_report(y, y_pred, output_dict=True)
    }


def fit_decision_tree(
    X: pd.DataFrame,
    y: pd.Series,
    max_depth: int = 4
) -> Dict:
    """
    Fit decision tree for interpretable spike prediction.

    Parameters
    ----------
    X : pd.DataFrame
        Features
    y : pd.Series
        Target
    max_depth : int
        Maximum tree depth

    Returns
    -------
    Dict
        Model results including feature importance
    """
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.metrics import roc_auc_score

    # Fit model
    model = DecisionTreeClassifier(
        max_depth=max_depth,
        class_weight='balanced',
        random_state=42
    )
    model.fit(X, y)

    # Cross-validation
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='roc_auc')

    # Feature importance
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    # Predictions
    y_prob = model.predict_proba(X)[:, 1]

    return {
        'model': model,
        'feature_importance': importance_df,
        'cv_auc_mean': cv_scores.mean(),
        'cv_auc_std': cv_scores.std(),
        'train_auc': roc_auc_score(y, y_prob),
    }


# =============================================================================
# TEMPORAL PATTERN ANALYSIS
# =============================================================================

def analyze_spike_timing(event_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyze when spikes occur (hour, weekday, month).

    Parameters
    ----------
    event_df : pd.DataFrame
        Event table with time features

    Returns
    -------
    Dict[str, pd.DataFrame]
        Counts by hour, weekday, month
    """
    results = {}

    # By hour
    results['by_hour'] = event_df.groupby('hour').size().reset_index(name='count')

    # By weekday
    results['by_weekday'] = event_df.groupby('weekday').size().reset_index(name='count')

    # By month
    results['by_month'] = event_df.groupby('month').size().reset_index(name='count')

    return results
