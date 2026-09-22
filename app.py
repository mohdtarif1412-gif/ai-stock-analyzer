import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="AI Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00C853, #00B0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">📈 AI Stock & Market Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time NSE Data • AI-Powered Insights • Smart Decisions</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔍 Stock Search")
    ticker_input = st.text_input(
        "Enter NSE Ticker",
        value="RELIANCE",
        help="Example: RELIANCE, TCS, INFY, HDFCBANK"
    ).upper().strip()
    
    period = st.selectbox(
        "Time Period",
        ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=2
    )
    
    chart_type = st.radio(
        "Chart Type",
        ["Candlestick", "Line", "Area"]
    )
    
    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")

ticker = f"{ticker_input}.NS"

@st.cache_data(ttl=300)
def fetch_data(ticker, period):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    info = stock.info
    return data, info

try:
    with st.spinner(f"Loading {ticker} data..."):
        data, info = fetch_data(ticker, period)

    if data.empty:
        st.error(f"❌ No data found for {ticker}. Check the ticker symbol.")
        st.stop()
    data = data.dropna()
    company_name = info.get("longName", ticker_input)
    st.subheader(f"🏢 {company_name}")
    
    current_price = data['Close'].iloc[-1]
    prev_price = data['Close'].iloc[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Price", f"₹{current_price:.2f}", f"{change_pct:+.2f}%")
    with col2:
        st.metric("Day High", f"₹{data['High'].iloc[-1]:.2f}")
    with col3:
        st.metric("Day Low", f"₹{data['Low'].iloc[-1]:.2f}")
    with col4:
        volume = data['Volume'].iloc[-1]
        st.metric("Volume", f"{volume/1e6:.2f}M")

    st.markdown("---")
    st.subheader(f"📊 {chart_type} Chart — {period}")

    if chart_type == "Candlestick":
        fig = go.Figure(data=[go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            increasing_line_color='#00C853',
            decreasing_line_color='#D50000'
        )])
    elif chart_type == "Line":
        fig = go.Figure(data=[go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            line=dict(color='#00B0FF', width=2)
        )])
    else:
        fig = go.Figure(data=[go.Scatter(
            x=data.index,
            y=data['Close'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#00C853', width=2)
        )])

    fig.update_layout(
        template='plotly_dark',
        height=500,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        margin=dict(l=0, r=0, t=30, b=0),
        yaxis_title='Price (₹)'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Trading Volume")
    vol_fig = go.Figure(data=[go.Bar(
        x=data.index,
        y=data['Volume'],
        marker_color='#00B0FF'
    )])
    vol_fig.update_layout(
        template='plotly_dark',
        height=250,
        margin=dict(l=0, r=0, t=10, b=0),
        yaxis_title='Volume'
    )
    st.plotly_chart(vol_fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ Error: {str(e)}")

st.markdown("---")
st.caption(f"Data source: Yahoo Finance | Last updated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
