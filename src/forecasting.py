"""Prévision de la demande journalière : moyenne mobile, SARIMA, Random Forest (notebook 05)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.statespace.sarimax import SARIMAX

SARIMA_ORDER = (1, 1, 1)
SARIMA_SEASONAL_ORDER = (1, 1, 1, 7)


def build_daily_series(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Série du nombre de réservations par jour pour chaque hôtel."""
    daily = df.groupby(["arrival_date", "hotel"]).size().reset_index(name="demand")
    series = {}
    for hotel in ["City Hotel", "Resort Hotel"]:
        s = daily[daily["hotel"] == hotel].set_index("arrival_date")["demand"]
        s.index = pd.to_datetime(s.index)
        series[hotel] = s
    return series


def train_test_split_series(series: pd.Series, train_ratio: float = 0.8):
    cut = int(len(series) * train_ratio)
    return series.iloc[:cut], series.iloc[cut:]


def moving_average_forecast(train: pd.Series, test: pd.Series, window: int = 7) -> np.ndarray:
    """Baseline : moyenne des `window` derniers jours (mise à jour avec les valeurs réelles)."""
    history = list(train)
    preds = []
    for i in range(len(test)):
        preds.append(np.mean(history[-window:]))
        history.append(test.iloc[i])
    return np.array(preds)


def sarima_forecast(train: pd.Series, steps: int) -> np.ndarray:
    fit = SARIMAX(train, order=SARIMA_ORDER, seasonal_order=SARIMA_SEASONAL_ORDER).fit(disp=False)
    return np.asarray(fit.forecast(steps=steps))


def create_features(series: pd.Series) -> pd.DataFrame:
    """Variables calendaires + retards (lags) pour le Random Forest."""
    data = pd.DataFrame({"demand": series})
    data["day_of_week"] = data.index.dayofweek
    data["month"] = data.index.month
    data["day_of_year"] = data.index.dayofyear
    data["lag_1"] = data["demand"].shift(1)
    data["lag_7"] = data["demand"].shift(7)
    data["rolling_7"] = data["demand"].shift(1).rolling(7).mean()
    return data.dropna()


def random_forest_forecast(series: pd.Series, train: pd.Series, test: pd.Series,
                           n_estimators: int = 200, random_state: int = 42):
    """Retourne (valeurs réelles alignées, prédictions)."""
    feats = create_features(series)
    train_ml = feats.loc[: train.index[-1]]
    test_ml = feats.loc[test.index[0]:]
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    model.fit(train_ml.drop("demand", axis=1), train_ml["demand"])
    return test_ml["demand"], model.predict(test_ml.drop("demand", axis=1))


def future_forecast(series: pd.Series, hotel: str, steps: int = 30) -> pd.DataFrame:
    """Prévision SARIMA à `steps` jours après la fin de l'historique."""
    preds = sarima_forecast(series, steps)
    dates = pd.date_range(series.index.max() + pd.Timedelta(days=1), periods=steps, freq="D")
    out = pd.DataFrame({"Date": dates, "Hotel": hotel, "Predicted_Bookings": preds})
    out["Predicted_Bookings"] = out["Predicted_Bookings"].clip(lower=0)
    return out


def select_final_predictions(predictions: pd.DataFrame) -> pd.DataFrame:
    """Modèle retenu par hôtel : SARIMA (City Hotel) et Random Forest (Resort Hotel)."""
    out = predictions.copy()
    out["Predicted_Bookings"] = np.where(out["Hotel"] == "City Hotel", out["SARIMA"], out["Random_Forest"])
    return out[["Date", "Hotel", "Actual_Bookings", "Predicted_Bookings"]]


def run_forecasting(df: pd.DataFrame, horizon: int = 30):
    """Pipeline complet. Retourne (comparaison_modèles, prédictions_test, prévision_future)."""
    from evaluation import compare_models  # import local : exécution depuis src/

    all_pred, all_cmp, all_future = [], [], []
    for hotel, s in build_daily_series(df).items():
        train, test = train_test_split_series(s)
        ma = moving_average_forecast(train, test)
        sar = sarima_forecast(train, len(test))
        actual_rf, rf = random_forest_forecast(s, train, test)
        all_cmp.append(compare_models(hotel, test.values,
                                      {"Moving Average": ma, "SARIMA": sar, "Random Forest": rf}))
        all_pred.append(pd.DataFrame({"Date": test.index, "Hotel": hotel, "Actual_Bookings": test.values,
                                      "Moving_Average": ma, "SARIMA": sar, "Random_Forest": rf}))
        all_future.append(future_forecast(s, hotel, horizon))
    return (pd.concat(all_cmp, ignore_index=True),
            pd.concat(all_pred, ignore_index=True),
            pd.concat(all_future, ignore_index=True))
