# pages/3_Volatility_Adjusted.py
import streamlit as st
from datetime import date
from utils import get_data, add_rolling_volume, add_pct_change, basic_breakout_signal
import pandas as pd
import numpy as np
import io

def compute_atr(data, ticker, window=14):
    """
    Compute the Average True Range using the standard formula:
    TR = max( High-Low, abs(High - prevClose), abs(Low - prevClose) )
    ATR = rolling mean of TR
    """
    df = data.copy()
    df["prev_close"] = df[("Close",ticker)].shift(1)
    df["tr1"] = df[("High",ticker)] - df[("Low",ticker)]
    df["tr2"] = (df[("High",ticker)] - df["prev_close"]).abs()
    df["tr3"] = (df[("Low",ticker)] - df["prev_close"]).abs()
    df["TR"] = df[["tr1","tr2","tr3"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(window).mean()
    return df["ATR"]

def run_volatility_adjusted_page():
    st.title("Volatility-Adjusted Filter Enhancement")

    st.write("""
    This page adds a volatility filter using ATR. 
    For instance, only count a breakout if today's (High - Low) is at least X * ATR.
    """)

    with st.form("vol_adjusted_form"):
        ticker = st.text_input("Ticker", value="AAPL")
        ticker = ticker.upper()
        start_date = st.date_input("Start Date", value=date(2021,1,1))
        end_date = st.date_input("End Date", value=date.today())
        vol_threshold = st.number_input("Volume Threshold (%)", value=200.0)
        daily_threshold = st.number_input("Price Change Threshold (%)", value=2.0)
        atr_multiplier = st.number_input("ATR Multiplier", value=1.5)
        holding_period = st.number_input("Holding Period (Days)", value=10)
        generate = st.form_submit_button("Generate Report")

    if generate:
        data = get_data(ticker, start_date, end_date)
        if data.empty:
            st.error("No data returned.")
            return

        data = add_rolling_volume(data,ticker)
        data = add_pct_change(data,ticker)

        # Compute ATR
        data["ATR"] = compute_atr(data, ticker=ticker,window=14)

        # Basic breakout signal
        data = basic_breakout_signal(data, vol_threshold_factor=vol_threshold/100.0, daily_threshold=daily_threshold,ticker=ticker)

        # Now add a volatility condition
        # e.g. if today's High - Low >= atr_multiplier * ATR
        data["vol_filter"] = (data[("High",ticker)] - data[("Low",ticker)]) >= (atr_multiplier * data["ATR"])

        # Combined condition
        data["is_breakout"] = data["is_breakout"] & data["vol_filter"]

        # For demonstration, let's do a simple holding period return, no SL/TP
        results = []
        data = data.reset_index(drop=False)
        for i in range(len(data)):
            if data["is_breakout"].iloc[i]:
                buy_date = data["Date"].iloc[i]
                buy_price = data[("Close",ticker)].iloc[i]
                sell_idx = i + int(holding_period)
                if sell_idx < len(data):
                    sell_date = data["Date"].iloc[sell_idx]
                    sell_price = data[("Close",ticker)].iloc[sell_idx]
                    ret = (sell_price - buy_price)/buy_price * 100.0
                else:
                    sell_date = None
                    sell_price = None
                    ret = None

                results.append({
                    "Buy Date": buy_date,
                    "Buy Price": buy_price,
                    "Sell Date": sell_date,
                    "Sell Price": sell_price,
                    "Return %": ret
                })

        df_results = pd.DataFrame(results)
        if df_results.empty:
            st.write("No trades found.")
        else:
            st.dataframe(df_results)
            avg_ret = df_results["Return %"].dropna().mean()
            st.write(f"Number of trades: {len(df_results)}")
            st.write(f"Average return: {avg_ret:.2f}%")

            buf = io.StringIO()
            df_results.to_csv(buf, index=False)
            st.download_button("Download CSV", buf.getvalue(), file_name="volatility_adjusted_trades.csv")


def main():
    run_volatility_adjusted_page()

if __name__ == "__main__":
    main()
