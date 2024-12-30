# pages/4_Multiple_Time_Horizons.py
import streamlit as st
from datetime import date
from utils import get_data, add_rolling_volume, add_pct_change, basic_breakout_signal
import pandas as pd
import numpy as np
import io

def calculate_returns_for_horizons(data, horizons, ticker):
    """
    For each breakout day, compute the returns for multiple holding horizons.
    Returns a table with columns:
      - Breakout Date, Buy Price
      - Sell Date (for each horizon), Sell Price, Return, ...
    """
    results = []
    data = data.reset_index(drop=False)
    for i in range(len(data)):
        if data["is_breakout"].iloc[i]:
            row = {
                "Breakout Date": data["Date"].iloc[i],
                "Buy Price": data[("Close",ticker)].iloc[i]
            }
            buy_price = data[("Close",ticker)].iloc[i]

            for h in horizons:
                idx_sell = i + h
                col_ret = f"Return_{h}d"
                if idx_sell < len(data):
                    sell_price = data[("Close",ticker)].iloc[idx_sell]
                    sell_date = data["Date"].iloc[idx_sell]
                    ret = (sell_price - buy_price)/buy_price * 100.0
                    row[f"Sell Date {h}d"] = sell_date
                    row[f"Sell Price {h}d"] = sell_price
                    row[col_ret] = ret
                else:
                    row[f"Sell Date {h}d"] = None
                    row[f"Sell Price {h}d"] = None
                    row[col_ret] = None

            results.append(row)
    return pd.DataFrame(results)

def run_multiple_horizons_page():
    st.title("Multiple Time Horizons Enhancement")

    st.write("""
    Input multiple holding periods (comma-separated) to see results for each.
    For example, "5, 10, 20" will show returns if we hold for 5 days, 10 days, or 20 days.
    """)

    with st.form("multi_horizon_form"):
        ticker = st.text_input("Ticker", "AAPL")
        start_date = st.date_input("Start Date", value=date(2021,1,1))
        end_date = st.date_input("End Date", value=date.today())
        vol_threshold = st.number_input("Volume Threshold (%)", value=200.0)
        daily_threshold = st.number_input("Price Change Threshold (%)", value=2.0)
        horizon_input = st.text_input("Holding Periods (comma-separated)", value="5,10,20")
        generate = st.form_submit_button("Generate Report")

    if generate:
        # Parse horizons
        horizon_list = []
        for h in horizon_input.split(","):
            h_str = h.strip()
            if h_str.isdigit():
                horizon_list.append(int(h_str))

        if not horizon_list:
            st.error("Please provide at least one valid integer horizon.")
            return

        data = get_data(ticker, start_date, end_date)
        if data.empty:
            st.error("No data returned.")
            return

        data = add_rolling_volume(data,ticker=ticker)
        data = add_pct_change(data,ticker=ticker)
        data = basic_breakout_signal(data, vol_threshold_factor=vol_threshold/100.0, daily_threshold=daily_threshold,ticker=ticker)

        df_results = calculate_returns_for_horizons(data, horizon_list,ticker=ticker)

        if df_results.empty:
            st.write("No breakouts found for the given parameters.")
        else:
            st.dataframe(df_results)

            # We can also compute average returns across each horizon
            summary = {}
            for h in horizon_list:
                col_ret = f"Return_{h}d"
                valid = df_results[col_ret].dropna()
                if len(valid) > 0:
                    summary[f"Avg Return {h}d"] = valid.mean()
                else:
                    summary[f"Avg Return {h}d"] = None

            st.write("Summary of average returns:", summary)

            buf = io.StringIO()
            df_results.to_csv(buf, index=False)
            st.download_button("Download CSV", buf.getvalue(), file_name="multiple_horizons.csv")


def main():
    run_multiple_horizons_page()

if __name__ == "__main__":
    main()
