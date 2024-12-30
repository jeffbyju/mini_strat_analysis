# Home.py
import streamlit as st

def main():
    st.title("Mini Strategy Analysis: Volume & Price Breakouts - Home")

    st.markdown("""
    Welcome to the enhanced breakout strategy app!  
    Choose a page from the sidebar to explore different enhancements:
    - Original Mini Strategy Analysis
    - Stop Loss / Take Profit  
    - Volatility Adjusted Filter  
    - Multiple Time Horizons  
    """)

if __name__ == "__main__":
    main()