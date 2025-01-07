# pages/1_Intraday_Data.py
import streamlit as st
from datetime import date
from utils import get_data, add_rolling_volume, add_pct_change, basic_breakout_signal
import pandas as pd
import numpy as np
import io
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
import io

def calculate_breakouts_and_returns(data, vol_threshold, daily_threshold, holding_period, start_date, end_date, ticker):
    """
    Calculate breakout signals and returns after a given holding period.
    
    Parameters:
    -----------
    data : pd.DataFrame
        Stock price data with columns: ['Open', 'High', 'Low', 'Close', 'Volume'] and date index.
    vol_threshold : float
        Factor by which the day's volume should exceed the 20-day average volume 
        (e.g., 2.0 means 200%).
    daily_threshold : float
        The minimum percent daily change from previous close to consider a breakout (e.g., 2.0 for 2%).
    holding_period : int
        Number of days to hold after a breakout day.

    Returns:
    --------
    result_df : pd.DataFrame
        A DataFrame containing breakout days and subsequent returns.
    """
    data.reset_index(inplace=True)

    cond1 = (pd.to_datetime(data['Date']) <= pd.to_datetime(end_date)) & (pd.to_datetime(data['Date']) >= pd.to_datetime(start_date))

    # Create a 20-day rolling average volume
    data['20d_avg_volume'] = data['Volume'].rolling(window=20).mean()

    # We'll shift the 20d_avg_volume forward by 1 day so that for day d,
    # we only look at the volume average from days (d-20) to (d-1).
    data['20d_avg_volume'] = data['20d_avg_volume'].shift(1)

    # Calculate daily % change from previous close
    data['pct_change'] = data['Close'].pct_change() * 100

    # Identify breakout days
    data['is_breakout'] = False

    # For day d, breakout if:
    # 1) volume[d] > vol_threshold * 20d_avg_volume[d]
    # 2) pct_change[d] >= daily_threshold
    cond2 = data[('Volume',ticker)] > (vol_threshold * data['20d_avg_volume'])
    cond3 = data['pct_change'] >= daily_threshold

    print("Shape of data:", data.shape)
    print("Shape of cond1:", cond1.shape, "Type:", type(cond1), "Unique vals:", cond1.unique() if type(cond1)==bool else cond1.head())
    print("Shape of cond2:", cond2.shape, "Type:", type(cond2), "Unique vals:", cond2.unique() if type(cond2)==bool else cond2.head())
    print("Shape of cond3:", cond3.shape, "Type:", type(cond3), "Unique vals:", cond3.unique() if type(cond3)==bool else cond3.head())
    print(data.columns)
    data.loc[cond1 & cond2 & cond3,'is_breakout'] = True

    # Prepare results DataFrame
    # For each breakout day, we compute the buy price (Close[d]) and 
    # the sell price (Close[d+holding_period]) if available.
    trades = []
    for i in range(len(data)):
        if data['is_breakout'].iloc[i]:
            buy_date = data['Date'].iloc[i]
            buy_price = data[('Close',ticker)].iloc[i]
            sell_index = i + holding_period
            if sell_index < len(data):
                sell_date = data['Date'].iloc[sell_index]
                sell_price = data[('Close',ticker)].iloc[sell_index]
                holding_return = (sell_price - buy_price) / buy_price * 100.0
                trades.append({
                    'Buy Date': buy_date,
                    'Buy Price': buy_price,
                    'Sell Date': sell_date,
                    'Sell Price': sell_price,
                    'Holding Return (%)': holding_return
                })
            else:
                # Not enough data to calculate a full holding period
                trades.append({
                    'Buy Date': buy_date,
                    'Buy Price': buy_price,
                    'Sell Date': None,
                    'Sell Price': None,
                    'Holding Return (%)': None
                })

    result_df = pd.DataFrame(trades)
    return result_df

# ---------------------------- STREAMLIT APP ----------------------------
def main():
    st.title("Mini Strategy Analysis: Volume & Price Breakouts")

    # --- Sidebar or main input form ---
    with st.form("user_inputs"):
        ticker = st.text_input("Ticker (e.g., AAPL)", value="AAPL")
        ticker = ticker.upper()
        start_date = st.date_input("Start Date", value=date(2020, 1, 1))
        end_date = st.date_input("End Date", value=date.today())
        
        vol_threshold = st.number_input(
            "Percent Volume Breakout Threshold (e.g., 200 means 200%)", 
            min_value=1.0, max_value=10000.0, value=200.0
        )
        daily_threshold = st.number_input(
            "Daily Change Threshold (in %, e.g., 2 means 2%)", 
            min_value=0.0, max_value=100.0, value=2.0
        )
        holding_period = st.number_input(
            "Holding Period (number of days to hold after breakout)", 
            min_value=1, max_value=365, value=10
        )

        generate_report = st.form_submit_button("Generate Report")

    if generate_report:
        # Fetch data using yfinance
        data = yf.download(ticker)
        
        if data.empty:
            st.error("No data returned. Check ticker or date range.")
            return
        
        # Ensure data is sorted by date
        data.sort_index(inplace=True)

        # Run breakout logic
        results = calculate_breakouts_and_returns(
            data, 
            vol_threshold=vol_threshold/100.0,  # Convert 200% to 2.0 factor
            daily_threshold=daily_threshold, 
            holding_period=holding_period,
            start_date=start_date,
            end_date=end_date,
            ticker=ticker
        )

        if results.empty:
            st.write("No breakouts found with the given criteria.")
        else:
            st.write("Breakout Results:", results)

            # Calculate average return or other stats
            valid_returns = results.dropna(subset=['Holding Return (%)'])
            if not valid_returns.empty:
                avg_return = valid_returns['Holding Return (%)'].mean()
                st.write(f"Number of trades: {len(valid_returns)}")
                st.write(f"Average Return: {avg_return:.2f}%")

            # Create a downloadable CSV
            csv_buffer = io.StringIO()
            results.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"{ticker}_breakout_report.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()
