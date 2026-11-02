"""Détection de réservations atypiques avec Isolation Forest (notebook 04)."""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

FEATURES = [
    "adr",
    "total_stay_nights",
    "lead_time",
    "total_guests",
    "total_of_special_requests",
]


def detect_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.02,
    random_state: int = 42,
    features: list[str] | None = None,
) -> pd.DataFrame:
    """Ajoute `anomaly` (1/-1) et `anomaly_flag` ("Normal"/"Anomaly")."""
    features = features or FEATURES
    df = df.copy()
    model = IsolationForest(contamination=contamination, random_state=random_state)
    df["anomaly"] = model.fit_predict(df[features])
    df["anomaly_flag"] = df["anomaly"].map({1: "Normal", -1: "Anomaly"})
    return df


def compare_normal_vs_anomaly(df: pd.DataFrame, features: list[str] | None = None) -> pd.DataFrame:
    """Moyennes des variables clés pour réservations normales vs anomalies."""
    features = features or FEATURES
    return df.groupby("anomaly_flag")[features].mean().round(2)


def anomaly_revenue_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("anomaly_flag")["estimated_revenue"]
        .agg(["count", "mean", "median", "sum"])
        .round(2)
    )


def anomaly_summary_by_hotel(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df[df["anomaly_flag"] == "Anomaly"]
        .groupby("hotel")
        .agg(
            anomalies=("anomaly_flag", "size"),
            avg_adr=("adr", "mean"),
            avg_stay=("total_stay_nights", "mean"),
            avg_lead_time=("lead_time", "mean"),
            revenue=("estimated_revenue", "sum"),
        )
        .reset_index()
        .round(2)
    )
