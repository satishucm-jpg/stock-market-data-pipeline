import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Stock Market Analytics", layout="wide")

session = get_active_session()

st.title("Stock Market Analytics Dashboard")
st.caption("Historical stock trends and the latest real-time market quote.")

tickers_df = session.sql("""
    SELECT DISTINCT ticker
    FROM STOCK_MARKET_DB.ANALYTICS.DAILY_STOCK_METRICS
    ORDER BY ticker
""").to_pandas()

ticker = st.selectbox("Choose a stock", tickers_df["TICKER"].tolist(), index=0)

latest_quote = session.sql(f"""
    SELECT
        symbol,
        current_price,
        price_change,
        percent_change,
        day_high,
        day_low,
        market_event_time
    FROM STOCK_MARKET_DB.ANALYTICS.LATEST_STOCK_QUOTES
    WHERE symbol = '{ticker}'
""").to_pandas()

if not latest_quote.empty:
    quote = latest_quote.iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest price", f"${quote['CURRENT_PRICE']:,.2f}")
    col2.metric("Daily change", f"${quote['PRICE_CHANGE']:,.2f}")
    col3.metric("Daily change %", f"{quote['PERCENT_CHANGE']:,.2f}%")
    col4.metric("Day range", f"${quote['DAY_LOW']:,.2f} – ${quote['DAY_HIGH']:,.2f}")
else:
    st.info(f"No real-time quote is currently available for {ticker}.")

history_df = session.sql(f"""
    SELECT
        trade_date,
        close_price,
        moving_average_20,
        moving_average_50,
        daily_return_percent,
        volatility_20
    FROM STOCK_MARKET_DB.ANALYTICS.DAILY_STOCK_METRICS
    WHERE ticker = '{ticker}'
      AND trade_date >= DATEADD(year, -5, CURRENT_DATE())
    ORDER BY trade_date
""").to_pandas()

st.subheader(f"{ticker}: Closing Price and Moving Averages")

price_chart = history_df.set_index("TRADE_DATE")[
    ["CLOSE_PRICE", "MOVING_AVERAGE_20", "MOVING_AVERAGE_50"]
]
st.line_chart(price_chart)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Daily Return %")
    st.bar_chart(history_df.set_index("TRADE_DATE")["DAILY_RETURN_PERCENT"])

with col2:
    st.subheader("20-Day Volatility")
    st.line_chart(history_df.set_index("TRADE_DATE")["VOLATILITY_20"])

st.subheader("Latest Real-Time Quotes")
all_quotes_df = session.sql("""
    SELECT
        symbol,
        current_price,
        price_change,
        percent_change,
        market_event_time
    FROM STOCK_MARKET_DB.ANALYTICS.LATEST_STOCK_QUOTES
    ORDER BY symbol
""").to_pandas()

st.dataframe(all_quotes_df, use_container_width=True)