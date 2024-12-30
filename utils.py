# utils.py
import yfinance as yf
import pandas as pd
import numpy as np

def get_data(ticker, start, end, interval="1d"):
    """
    Fetch market data from yfinance.
    interval='1d' for daily, '1h' or '15m' for intraday, etc.
    """
    data = yf.download(ticker, start=start, end=end, interval=interval)
    data.sort_index(inplace=True)
    return data

def add_rolling_volume(data,ticker):
    """
    Add 20-day rolling average volume (shifted by 1 day to avoid lookahead).
    """
    data["20d_avg_volume"] = data[("Volume",ticker)].rolling(window=20).mean().shift(1)
    return data

def add_pct_change(data,ticker):
    """
    Add daily % change in 'Close' from previous day.
    """
    data["pct_change"] = data[("Close",ticker)].pct_change() * 100
    return data

def basic_breakout_signal(data, vol_threshold_factor, daily_threshold, ticker):
    """
    Mark breakout days in `data['is_breakout']`.
    Conditions:
    1. Volume > vol_threshold_factor * 20-day avg volume
    2. pct_change >= daily_threshold
    """
    data["is_breakout"] = False
    cond_vol = data[("Volume",ticker)] > (vol_threshold_factor * data["20d_avg_volume"])
    cond_price = data["pct_change"] >= daily_threshold
    data.loc[cond_vol & cond_price, "is_breakout"] = True
    return data
