"""Métriques d'évaluation des modèles de prévision (notebook 05)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def safe_mape(actual, predicted) -> float:
    """MAPE en ignorant les jours où la valeur réelle vaut 0."""
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    mask = actual != 0
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def forecast_metrics(actual, predicted) -> dict[str, float]:
    """MAE, RMSE, MAPE et biais de prévision (prédit - réel)."""
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    mask = ~np.isnan(predicted)
    actual, predicted = actual[mask], predicted[mask]
    return {
        "MAE": round(mean_absolute_error(actual, predicted), 2),
        "RMSE": round(float(np.sqrt(mean_squared_error(actual, predicted))), 2),
        "MAPE": round(safe_mape(actual, predicted), 2),
        "Forecast_Bias": round(float(np.mean(predicted - actual)), 2),
    }


def compare_models(hotel: str, actual, predictions: dict[str, np.ndarray]) -> pd.DataFrame:
    """Tableau comparatif des modèles pour un hôtel.

    `predictions` : {"Moving Average": array, "SARIMA": array, "Random Forest": array}
    """
    rows = [{"Hotel": hotel, "Model": name, **forecast_metrics(actual, pred)}
            for name, pred in predictions.items()]
    return pd.DataFrame(rows)


def best_model(results: pd.DataFrame, metric: str = "MAE") -> pd.DataFrame:
    """Meilleur modèle par hôtel (plus petite valeur de `metric`)."""
    return results.loc[results.groupby("Hotel")[metric].idxmin()].reset_index(drop=True)
