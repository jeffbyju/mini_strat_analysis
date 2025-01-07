# pages/2_Stop_Loss_TP.py
import streamlit as st
from datetime import date
from utils import get_data, add_rolling_volume, add_pct_change, basic_breakout_signal
import pandas as pd
import io

def calculate_trades_with_sl_tp(data, holding_period, stop_loss_pct, take_profit_pct,ticker):
    """
    For each breakout day (is_breakout == True), buy at close[d].
    Then check each subsequent day until holding_period is reached:
    - If price drops below buy_price * (1 - stop_loss_pct), exit
    - If price rises above buy_price * (1 + take_profit_pct), exit
    - Otherwise, exit on the last day (d+holding_period)
    """
    trades = []
    data = data.reset_index(drop=False)  # so we can iterate easily
    for i in range(len(data)):
        if data["is_breakout"].iloc[i]:
            buy_date = data["Date"].iloc[i]
            buy_price = data[("Close",ticker)].iloc[i]
            sl_price = buy_price * (1 - stop_loss_pct)
            tp_price = buy_price * (1 + take_profit_pct)

            sell_date = None
            sell_price = None

            # Walk forward up to holding_period
            for j in range(i+1, min(i+holding_period+1, len(data))):
                current_price = data[("Close",ticker)].iloc[j]
                current_date = data["Date"].iloc[j]

                # Check stop loss
                if current_price < sl_price:
                    sell_date = current_date
                    sell_price = current_price
                    break
                # Check take profit
                if current_price > tp_price:
                    sell_date = current_date
                    sell_price = current_price
                    break

            # If we never triggered SL or TP, we exit on day i+holding_period (if it exists)
            if sell_date is None:
                final_idx = i + holding_period
                if final_idx < len(data):
                    sell_date = data["Date"].iloc[final_idx]
                    sell_price = data[("Close",ticker)].iloc[final_idx]

            # Calculate return
            if sell_price is not None:
                trade_return = (sell_price - buy_price)/buy_price * 100.0
            else:
                trade_return = None

            trades.append({
                "Buy Date": buy_date,
                "Buy Price": buy_price,
                "Sell Date": sell_date,
                "Sell Price": sell_price,
                "Stop Loss %": stop_loss_pct * 100,
                "Take Profit %": take_profit_pct * 100,
                "Return %": trade_return
            })
    return pd.DataFrame(trades)

def run_stop_loss_tp_page():
    st.title("Stop Loss & Take Profit Enhancement")

    st.write("""
    Here we add an optional stop loss and take profit. 
    If triggered before the normal holding period ends, we exit immediately.
    Otherwise, we exit at the end of the holding period.
    """)

    with st.form("sl_tp_form"):
        ticker = st.text_input("Ticker", value="AAPL")
        ticker = ticker.upper()
        start_date = st.date_input("Start Date", value=date(2022,1,1))
        end_date = st.date_input("End Date", value=date.today())
        vol_threshold = st.number_input("Volume Threshold (%)", value=200.0)
        daily_threshold = st.number_input("Price Change Threshold (%)", value=2.0)
        holding_period = st.number_input("Holding Period (Days)", value=10)
        stop_loss_input = st.number_input("Stop Loss (%)", value=5.0)
        take_profit_input = st.number_input("Take Profit (%)", value=10.0)

        generate = st.form_submit_button("Generate Report")

    if generate:
        data = get_data(ticker, start_date, end_date)
        if data.empty:
            st.error("No data returned.")
            return

        # basic prep
        data = add_rolling_volume(data,ticker)
        data = add_pct_change(data,ticker)
        data = basic_breakout_signal(
            data,
            vol_threshold_factor=vol_threshold/100.0,
            daily_threshold=daily_threshold,
            ticker=ticker
        )

        # Now compute trades with SL/TP
        results = calculate_trades_with_sl_tp(
            data,
            holding_period=int(holding_period),
            stop_loss_pct=stop_loss_input/100.0,
            take_profit_pct=take_profit_input/100.0,
            ticker=ticker
        )

        if results.empty:
            st.write("No trades found.")
        else:
            st.dataframe(results)
            avg_ret = results["Return %"].dropna().mean()
            st.write(f"Number of trades: {len(results)}")
            st.write(f"Average return: {avg_ret:.2f}%")

            buf = io.StringIO()
            results.to_csv(buf, index=False)
            st.download_button("Download CSV", buf.getvalue(), file_name="sl_tp_trades.csv")


def main():
    run_stop_loss_tp_page()

if __name__ == "__main__":
    main()
