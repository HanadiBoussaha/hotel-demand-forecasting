"""Nettoyage des données de réservations et création des tables agrégées pour SQL.

Logique issue des notebooks 01_data_cleaning et 03_sql_analysis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MONTH_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12,
}


def load_raw(path: str) -> pd.DataFrame:
    """Charge le fichier brut hotel_bookings.csv."""
    return pd.read_csv(path)


def clean_bookings(df: pd.DataFrame) -> pd.DataFrame:
    """Nettoie le jeu de données brut et crée les variables dérivées.

    Étapes : valeurs manquantes, doublons, date d'arrivée, nuits totales,
    nombre d'invités, revenu estimé, ADR négatifs, outliers ADR (IQR),
    suppression des réservations sans invité.
    """
    df = df.copy()

    # Valeurs manquantes
    df["children"] = df["children"].fillna(0)
    df["country"] = df["country"].fillna("Unknown")
    df["agent"] = df["agent"].fillna(0)
    df["company"] = df["company"].fillna(0)

    # Doublons
    df = df.drop_duplicates().reset_index(drop=True)

    # Variables dérivées
    df["arrival_date"] = pd.to_datetime(
        df["arrival_date_year"].astype(str) + "-"
        + df["arrival_date_month"] + "-"
        + df["arrival_date_day_of_month"].astype(str),
        format="%Y-%B-%d",
    )
    df["total_stay_nights"] = df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
    df["total_guests"] = df["adults"] + df["children"] + df["babies"]
    df["estimated_revenue"] = df["adr"] * df["total_stay_nights"]

    # ADR invalides (négatifs) -> NaN le temps de calculer les bornes IQR
    df["adr_invalid"] = df["adr"] < 0
    df.loc[df["adr_invalid"], "adr"] = np.nan

    q1, q3 = df["adr"].quantile(0.25), df["adr"].quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    df["adr_outlier"] = (df["adr"] < lower) | (df["adr"] > upper)

    df["invalid_guest_count"] = df["total_guests"] == 0
    df.loc[df["adr_invalid"], "adr"] = 0

    # Suppression des réservations sans invité + recalcul du revenu
    df = df[df["total_guests"] > 0].copy()
    df["estimated_revenue"] = df["adr"] * df["total_stay_nights"]
    return df


def _agg_kpis(group, with_stay: bool = True) -> pd.DataFrame:
    spec = dict(
        bookings=("hotel", "size"),
        cancellations=("is_canceled", "sum"),
        avg_adr=("adr", "mean"),
        total_revenue=("estimated_revenue", "sum"),
        avg_lead_time=("lead_time", "mean"),
    )
    if with_stay:
        spec["avg_stay_nights"] = ("total_stay_nights", "mean")
    out = group.agg(**spec).reset_index()
    out["cancellation_rate"] = out["cancellations"] / out["bookings"] * 100
    return out


def build_daily_demand(df: pd.DataFrame) -> pd.DataFrame:
    return _agg_kpis(df.groupby(["arrival_date", "hotel"]))


def build_monthly_performance(df: pd.DataFrame) -> pd.DataFrame:
    out = _agg_kpis(df.groupby(["arrival_date_year", "arrival_date_month", "hotel"]))
    out["month_number"] = out["arrival_date_month"].map(MONTH_MAP)
    return out.sort_values(["arrival_date_year", "month_number", "hotel"])


def build_market_segment(df: pd.DataFrame) -> pd.DataFrame:
    return _agg_kpis(df.groupby(["hotel", "market_segment"]))


def build_channel_performance(df: pd.DataFrame) -> pd.DataFrame:
    return _agg_kpis(df.groupby(["hotel", "distribution_channel"]), with_stay=False)


def build_sql_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Retourne les 4 tables utilisées par sql/analysis.sql."""
    return {
        "daily_demand": build_daily_demand(df),
        "monthly_performance": build_monthly_performance(df),
        "market_segment": build_market_segment(df),
        "channel_performance": build_channel_performance(df),
    }
