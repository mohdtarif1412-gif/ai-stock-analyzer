import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import google.generativeai as genai
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
    # ---------- TECHNICAL INDICATORS ----------
    # 1. Moving Averages
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()

    # 2. RSI (14 day)
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # 3. MACD
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

    # Latest values nikalo
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal_Line'].iloc[-1]
    latest_ma50 = data['MA50'].iloc[-1]
    latest_ma200 = data['MA200'].iloc[-1]
    latest_price = data['Close'].iloc[-1]
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
# ---------- TECHNICAL ANALYSIS SECTION ----------
st.markdown("---")
st.subheader("📊 Technical Indicators")

tcol1, tcol2, tcol3 = st.columns(3)

with tcol1:
    if latest_rsi < 30:
        st.metric("RSI (14)", f"{latest_rsi:.2f}", "Oversold 🟢")
    elif latest_rsi > 70:
        st.metric("RSI (14)", f"{latest_rsi:.2f}", "Overbought 🔴")
    else:
        st.metric("RSI (14)", f"{latest_rsi:.2f}", "Neutral ⚪")

with tcol2:
    macd_status = "Bullish" if latest_macd > latest_signal else "Bearish"
    st.metric("MACD", f"{latest_macd:.2f}", macd_status)

with tcol3:
    ma_status = "Uptrend" if latest_ma50 > latest_ma200 else "Downtrend"
    st.metric("MA50 vs MA200", f"₹{latest_ma50:.2f} / ₹{latest_ma200:.2f}", ma_status)

# ---------- BUY/SELL SIGNAL ----------
st.markdown("---")
st.subheader("🎯 AI Trading Signal")

score = 0
if latest_rsi < 30: score += 1
if latest_rsi > 70: score -= 1
if latest_macd > latest_signal: score += 1
else: score -= 1
if latest_ma50 > latest_ma200: score += 1
else: score -= 1

if score >= 2:
    st.success(f"🟢 **STRONG BUY** — Score: {score}/3 (Indicators bullish hai)")
elif score == 1:
    st.info(f"🔵 **BUY** — Score: {score}/3 (Thoda positive trend)")
elif score == 0:
    st.warning(f"🟡 **HOLD** — Score: {score}/3 (Market confused hai)")
elif score == -1:
    st.warning(f"🟠 **SELL** — Score: {score}/3 (Thoda negative trend)")
else:
    st.error(f"🔴 **STRONG SELL** — Score: {score}/3 (Indicators bearish hai)")

st.caption("⚠️ Ye AI-generated signal hai, financial advice nahi.")
st.markdown("---")
st.caption(f"Data source: Yahoo Finance | Last updated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
# ---------- AI CHATBOT ----------
st.markdown("---")
st.subheader("🤖 AI Stock Assistant")
st.caption("Stock ke bare me kuch bhi pucho — Hinglish me jawab milega")

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if prompt := st.chat_input("Stock ke bare me kuch bhi pucho..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        context = f"""
        Stock: {ticker_input}
        Current Price: ₹{latest_price:.2f}
        RSI: {latest_rsi:.2f}
        MACD: {latest_macd:.2f}
        MA50: ₹{latest_ma50:.2f}
        MA200: ₹{latest_ma200:.2f}
        Trading Signal Score: {score}/3
        """
        
        full_prompt = f"""
        You are an expert stock market AI assistant helping retail investors.
        Answer in simple Hinglish (Hindi + English mix, Roman script).
        Keep answers short, clear, and educational.
        
        Current stock data:
        {context}
        
        User question: {prompt}
        
        Give a helpful, educational response. Do NOT give direct financial advice.
        """
        
        with st.chat_message("assistant"):
            with st.spinner("AI soch raha hai..."):
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
        
        st.session_state.messages.append({"role": "assistant", "content": response.text})

except Exception as e:
    st.warning("⚠️ Chatbot ke liye Streamlit Secrets me GOOGLE_API_KEY add karo.")
    st.caption(f"Error detail: {str(e)}")
