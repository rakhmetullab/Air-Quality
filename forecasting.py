# forecasting.py - Функциональность для прогнозирования загрязнения

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from config import FACILITIES_COORD, POLLUTANTS, MODEL_HISTORY_HOURS, FORECAST_HOURS, HAZARD_THRESHOLDS
from data_service import fetch_pollution_history

# Игнорируем предупреждения о сходимости для упрощения пользовательского интерфейса
warnings.simplefilter('ignore', ConvergenceWarning)

def render_forecast() -> None:
    """
    Отображает страницу прогнозирования загрязнения с моделью SARIMA.
    """
    st.header("🔮 SARIMA Forecast")
    
    # Выбор объекта и загрязнителя
    facility = st.selectbox("Select Facility for Forecast", list(FACILITIES_COORD.keys()), key="fc_facility")
    pollutant = st.selectbox("Select Pollutant", POLLUTANTS, key="fc_pollutant")
    lat, lon = FACILITIES_COORD[facility]
    
    # Получение исторических данных
    df = fetch_pollution_history(lat, lon, MODEL_HISTORY_HOURS)
    if df.empty:
        st.error("Insufficient historical data for modeling.")
        return

    # Подготовка данных для моделирования
    series = df[df['pollutant'] == pollutant]['value']
    series = series.resample('1H').mean().ffill()

    st.write(f"Training SARIMA model on last {MODEL_HISTORY_HOURS}h of {pollutant.upper()}")
    
    # Обучение модели SARIMA
    try:
        model = SARIMAX(
            series,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, 24),
            enforce_stationarity=False,
            enforce_invertibility=False
        )
        res = model.fit(disp=False)
    except Exception as e:
        st.error(f"Model fitting error: {e}")
        return

    # Получение прогноза
    forecast = res.get_forecast(steps=FORECAST_HOURS)
    fc_index = pd.date_range(start=series.index[-1] + pd.Timedelta(hours=1),
                            periods=FORECAST_HOURS, freq='1H')
    fc_mean = forecast.predicted_mean
    conf = forecast.conf_int()

    # Построение графика
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series, mode='lines', name='Observed'))
    fig.add_trace(go.Scatter(x=fc_index, y=fc_mean, mode='lines', name='Forecast'))
    fig.add_trace(go.Scatter(
        x=list(fc_index) + list(fc_index[::-1]),
        y=list(conf.iloc[:,0]) + list(conf.iloc[:,1][::-1]),
        fill='toself', showlegend=False
    ))
    fig.update_layout(template='plotly_dark', xaxis_title='UTC Time', yaxis_title='µg/m³')
    st.plotly_chart(fig, use_container_width=True)

    # Отображение данных прогноза
    df_fc = pd.DataFrame({
        'Forecast': fc_mean.values,
        'Lower CI': conf.iloc[:,0].values,
        'Upper CI': conf.iloc[:,1].values
    }, index=fc_index)
    st.dataframe(df_fc)

    # Проверка на превышение пороговых значений
    st.markdown("---")
    st.subheader("⚠️ Hazardous Level Alerts")
    threshold = HAZARD_THRESHOLDS.get(pollutant)
    if threshold:
        over = df_fc['Forecast'] > threshold
        if over.any():
            times = ', '.join([t.strftime('%Y-%m-%d %H:%M') for t in df_fc[over].index])
            st.error(f"Forecasted {pollutant.upper()} exceeds {threshold} µg/m³ at: {times} UTC")
        else:
            st.success(f"No forecasted {pollutant.upper()} exceed the threshold of {threshold} µg/m³.")
    else:
        st.info("No hazardous threshold defined for this pollutant.")