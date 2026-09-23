import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import hashlib
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
        font-weight: 800;
        background: linear-gradient(90deg, #00C853, #00B0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .sub-header {
        text-align: center;
        color: #8892a6;
        margin-bottom: 2rem;
    }
    .auth-header {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00C853, #00B0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 1.5rem 0 0.5rem 0;
    }
    .auth-sub {
        text-align: center;
        color: #8892a6;
        margin-bottom: 2rem;
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_users():
    if 'users' not in st.session_state:
        st.session_state.users = {
            'admin': hash_password('admin123'),
            'demo': hash_password('demo123')
        }
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'watchlists' not in st.session_state:
        st.session_state.watchlists = {}

def get_user_watchlist():
    user = st.session_state.current_user
    if user not in st.session_state.watchlists:
        st.session_state.watchlists[user] = []
    return st.session_state.watchlists[user]

def login_signup_page():
    st.markdown('<div class="auth-header">📈 AI Stock Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-sub">Login to start your investment analysis</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
        with tab1:
            username = st.text_input("Username", key="login_username", placeholder="admin")
            password = st.text_input("Password", type="password", key="login_password", placeholder="admin123")
            if st.button("Login", use_container_width=True, type="primary"):
                if username in st.session_state.users and st.session_state.users[username] == hash_password(password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.success(f"✅ Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
            st.markdown("---")
            st.caption("**Demo Credentials:**")
            st.caption("Username: `admin` | Password: `admin123`")
        with tab2:
            new_user = st.text_input("New Username", key="signup_username")
            new_pass = st.text_input("New Password", type="password", key="signup_password")
            confirm_pass = st.text_input("Confirm Password", type="password", key="signup_confirm")
            if st.button("Create Account", use_container_width=True, type="primary"):
                if not new_user or not new_pass:
                    st.error("❌ Please fill all fields")
                elif len(new_user) < 3:
                    st.error("❌ Username must be at least 3 characters")
                elif len(new_pass) < 4:
                    st.error("❌ Password must be at least 4 characters")
                elif new_pass != confirm_pass:
                    st.error("❌ Passwords don't match")
                elif new_user in st.session_state.users:
                    st.error("❌ Username already exists")
                else:
                    st.session_state.users[new_user] = hash_password(new_pass)
                    st.success(f"✅ Account created, {new_user}! Now go to Login tab.")

init_users()
if not st.session_state.logged_in:
    login_signup_page()
    st.stop()

user_watchlist = get_user_watchlist()

st.markdown('<div class="main-header">📈 AI Stock & Market Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Real-time NSE Data • AI-Powered Insights • Smart Decisions</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔍 Stock Search")
    ticker_input = st.text_input("Enter NSE Ticker", value="RELIANCE", help="Example: RELIANCE, TCS, INFY").upper().strip()
    period = st.selectbox("Time Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
    chart_type = st.radio("Chart Type", ["Candlestick", "Line", "Area"])
    st.markdown("---")
    compare_mode = st.checkbox("⚖️ Compare with another stock")
    ticker_input_2 = ""
    if compare_mode:
        ticker_input_2 = st.text_input("Second NSE Ticker", value="TCS").upper().strip()
    st.markdown("---")
    st.header(f"⭐ My Watchlist ({len(user_watchlist)})")
    if not user_watchlist:
        st.caption("No stocks saved yet.")
    else:
        for w_ticker in user_watchlist:
            try:
                w_stock = yf.Ticker(f"{w_ticker}.NS")
                w_data = w_stock.history(period="5d")
                if not w_data.empty:
                    w_price = w_data['Close'].iloc[-1]
                    w_change = 0
                    if len(w_data) > 1:
                        w_prev = w_data['Close'].iloc[-2]
                        w_change = ((w_price - w_prev) / w_prev) * 100
                    if w_change >= 0:
                        st.markdown(f"**{w_ticker}** — ₹{w_price:.2f} 🟢 `{w_change:+.2f}%`")
                    else:
                        st.markdown(f"**{w_ticker}** — ₹{w_price:.2f} 🔴 `{w_change:+.2f}%`")
                    if st.button(f"❌ Remove {w_ticker}", key=f"rm_{w_ticker}", use_container_width=True):
                        user_watchlist.remove(w_ticker)
                        st.rerun()
            except:
                st.caption(f"{w_ticker}: error")
    st.markdown("---")
    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False
    if st.button("🤖 Open AI Chat" if not st.session_state.show_chat else "❌ Close Chat", use_container_width=True, type="primary"):
        st.session_state.show_chat = not st.session_state.show_chat
        st.rerun()
    st.markdown("---")
    st.caption(f"👤 Logged in as: **{st.session_state.current_user}**")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.show_chat = False
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("⚠️ Educational tool only. Not financial advice.")

ticker = f"{ticker_input}.NS"
# Sentiment keywords
POSITIVE_WORDS = ['surge', 'gain', 'rise', 'profit', 'growth', 'up', 'high', 'record', 'strong', 'bullish', 'upgrade', 'beat', 'positive', 'jump', 'soar', 'rally', 'boom', 'win', 'expand']
NEGATIVE_WORDS = ['fall', 'drop', 'loss', 'decline', 'down', 'low', 'weak', 'bearish', 'downgrade', 'miss', 'negative', 'crash', 'slump', 'plunge', 'cut', 'layoff', 'fraud', 'lawsuit', 'debt']

def analyze_sentiment(text):
    """Keyword-based sentiment analysis"""
    if not text:
        return "Neutral", 0
    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    if pos > neg:
        return "Positive", 1
    elif neg > pos:
        return "Negative", -1
    else:
        return "Neutral", 0

@st.cache_data(ttl=600)
def fetch_news(ticker):
    """Fetch news from yfinance"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        return news[:8] if news else []
    except:
        return []
@st.cache_data(ttl=300)
def fetch_data(ticker, period):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    info = stock.info
    return data, info

latest_price = 0
latest_rsi = 0
latest_macd = 0
latest_signal = 0
latest_ma50 = 0
latest_ma200 = 0
score = 0
data = None

try:
    with st.spinner(f"Loading {ticker} data..."):
        data, info = fetch_data(ticker, period)
    if data.empty:
        st.error(f"❌ No data found for {ticker}.")
        st.stop()
    data = data.dropna()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['MA200'] = data['Close'].rolling(window=200).mean()
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = exp1 - exp2
    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
    latest_rsi = data['RSI'].iloc[-1]
    latest_macd = data['MACD'].iloc[-1]
    latest_signal = data['Signal_Line'].iloc[-1]
    latest_ma50 = data['MA50'].iloc[-1]
    latest_ma200 = data['MA200'].iloc[-1]
    latest_price = data['Close'].iloc[-1]

    col_name, col_btn = st.columns([3, 1])
    with col_name:
        company_name = info.get("longName", ticker_input)
        st.subheader(f"🏢 {company_name}")
    with col_btn:
        if ticker_input in user_watchlist:
            if st.button("⭐ Remove from Watchlist", use_container_width=True):
                user_watchlist.remove(ticker_input)
                st.rerun()
        else:
            if st.button("⭐ Add to Watchlist", use_container_width=True, type="primary"):
                user_watchlist.append(ticker_input)
                st.rerun()

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
        st.metric("Volume", f"{data['Volume'].iloc[-1]/1e6:.2f}M")

    st.markdown("---")
    st.subheader(f"📊 {chart_type} Chart — {period}")
    if chart_type == "Candlestick":
        fig = go.Figure(data=[go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], increasing_line_color='#00C853', decreasing_line_color='#D50000')])
    elif chart_type == "Line":
        fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], mode='lines', line=dict(color='#00B0FF', width=2))])
    else:
        fig = go.Figure(data=[go.Scatter(x=data.index, y=data['Close'], mode='lines', fill='tozeroy', line=dict(color='#00C853', width=2))])
    fig.update_layout(template='plotly_dark', height=500, xaxis_rangeslider_visible=False, hovermode='x unified', margin=dict(l=0, r=0, t=30, b=0), yaxis_title='Price (₹)')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Trading Volume")
    vol_fig = go.Figure(data=[go.Bar(x=data.index, y=data['Volume'], marker_color='#00B0FF')])
    vol_fig.update_layout(template='plotly_dark', height=250, margin=dict(l=0, r=0, t=10, b=0), yaxis_title='Volume')
    st.plotly_chart(vol_fig, use_container_width=True)

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

    st.markdown("---")
    st.subheader("🎯 AI Trading Signal")
    if latest_rsi < 30: score += 1
    if latest_rsi > 70: score -= 1
    if latest_macd > latest_signal: score += 1
    else: score -= 1
    if latest_ma50 > latest_ma200: score += 1
    else: score -= 1
    if score >= 2:
        st.success(f"🟢 **STRONG BUY** — Score: {score}/3")
    elif score == 1:
        st.info(f"🔵 **BUY** — Score: {score}/3")
    elif score == 0:
        st.warning(f"🟡 **HOLD** — Score: {score}/3")
    elif score == -1:
        st.warning(f"🟠 **SELL** — Score: {score}/3")
    else:
        st.error(f"🔴 **STRONG SELL** — Score: {score}/3")
    st.caption("⚠️ This is AI-generated analysis, not financial advice.")

except Exception as e:
    st.error(f"⚠️ Error: {str(e)}")
# ==========================================
# NEWS + SENTIMENT
# ==========================================
st.markdown("---")
st.subheader("📰 Latest News & Sentiment")

news_items = fetch_news(ticker)

if not news_items:
    st.info("No recent news available for this stock.")
else:
    total_score = 0
    news_data = []
    
    for item in news_items:
        title = item.get('title', '')
        publisher = item.get('publisher', 'Unknown')
        link = item.get('link', '#')
        sentiment, s_score = analyze_sentiment(title)
        total_score += s_score
        news_data.append({
            'title': title,
            'publisher': publisher,
            'link': link,
            'sentiment': sentiment
        })
    
    # Overall sentiment gauge
    avg_score = total_score / len(news_data)
    if avg_score > 0.3:
        st.success(f"📊 **Overall Sentiment: BULLISH** (Score: {avg_score:+.2f})")
    elif avg_score < -0.3:
        st.error(f"📊 **Overall Sentiment: BEARISH** (Score: {avg_score:+.2f})")
    else:
        st.info(f"📊 **Overall Sentiment: NEUTRAL** (Score: {avg_score:+.2f})")
    
    # News list
    for n in news_data:
        if n['sentiment'] == 'Positive':
            badge = "🟢 Positive"
        elif n['sentiment'] == 'Negative':
            badge = "🔴 Negative"
        else:
            badge = "⚪ Neutral"
        
        st.markdown(f"**{n['title']}**")
        st.caption(f"📰 {n['publisher']} | Sentiment: {badge} | [Read more]({n['link']})")
        st.markdown("")

    st.caption("⚠️ Sentiment analysis is keyword-based. Not financial advice.")
# ==========================================
# STOCK COMPARISON
# ==========================================
if compare_mode and ticker_input_2 and data is not None:
    st.markdown("---")
    st.subheader("⚖️ Stock Comparison")
    ticker_2 = f"{ticker_input_2}.NS"
    try:
        with st.spinner(f"Loading {ticker_2} data..."):
            data2, info2 = fetch_data(ticker_2, period)
        if data2.empty:
            st.error(f"❌ No data found for {ticker_2}")
        else:
            data2 = data2.dropna()
            data2['MA50'] = data2['Close'].rolling(window=50).mean()
            data2['MA200'] = data2['Close'].rolling(window=200).mean()
            delta2 = data2['Close'].diff()
            gain2 = (delta2.where(delta2 > 0, 0)).rolling(window=14).mean()
            loss2 = (-delta2.where(delta2 < 0, 0)).rolling(window=14).mean()
            rs2 = gain2 / loss2
            data2['RSI'] = 100 - (100 / (1 + rs2))
            exp1_2 = data2['Close'].ewm(span=12, adjust=False).mean()
            exp2_2 = data2['Close'].ewm(span=26, adjust=False).mean()
            data2['MACD'] = exp1_2 - exp2_2
            data2['Signal_Line'] = data2['MACD'].ewm(span=9, adjust=False).mean()
            rsi_2 = data2['RSI'].iloc[-1]
            macd_2 = data2['MACD'].iloc[-1]
            signal_2 = data2['Signal_Line'].iloc[-1]
            ma50_2 = data2['MA50'].iloc[-1]
            ma200_2 = data2['MA200'].iloc[-1]
            price_2 = data2['Close'].iloc[-1]
            score2 = 0
            if rsi_2 < 30: score2 += 1
            if rsi_2 > 70: score2 -= 1
            if macd_2 > signal_2: score2 += 1
            else: score2 -= 1
            if ma50_2 > ma200_2: score2 += 1
            else: score2 -= 1
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"### 📈 {ticker_input}")
                st.metric("Price", f"₹{latest_price:.2f}")
                st.metric("RSI (14)", f"{latest_rsi:.2f}")
                st.metric("MACD", f"{latest_macd:.2f}")
                st.metric("MA50", f"₹{latest_ma50:.2f}")
                st.metric("Trading Score", f"{score}/3")
            with col2:
                st.markdown(f"### 📈 {ticker_input_2}")
                st.metric("Price", f"₹{price_2:.2f}")
                st.metric("RSI (14)", f"{rsi_2:.2f}")
                st.metric("MACD", f"{macd_2:.2f}")
                st.metric("MA50", f"₹{ma50_2:.2f}")
                st.metric("Trading Score", f"{score2}/3")
            st.markdown("### 🏆 Verdict")
            if score > score2:
                st.success(f"**{ticker_input}** looks better (Score: {score} vs {score2})")
            elif score2 > score:
                st.success(f"**{ticker_input_2}** looks better (Score: {score2} vs {score})")
            else:
                st.info(f"Both stocks equally rated (Score: {score} vs {score2})")
            st.markdown("### 📊 Price Comparison (Normalized to 100)")
            fig_compare = go.Figure()
            fig_compare.add_trace(go.Scatter(x=data.index, y=(data['Close'] / data['Close'].iloc[0]) * 100, mode='lines', name=ticker_input, line=dict(color='#00C853', width=2)))
            fig_compare.add_trace(go.Scatter(x=data2.index, y=(data2['Close'] / data2['Close'].iloc[0]) * 100, mode='lines', name=ticker_input_2, line=dict(color='#00B0FF', width=2)))
            fig_compare.update_layout(template='plotly_dark', height=400, hovermode='x unified', margin=dict(l=0, r=0, t=30, b=0), yaxis_title='Normalized Price (Base = 100)')
            st.plotly_chart(fig_compare, use_container_width=True)
            st.caption("⚠️ Comparison based on technical indicators only. Not financial advice.")
    except Exception as e:
        st.warning(f"⚠️ Could not compare: {str(e)}")

# ==========================================
# AI CHATBOT
# ==========================================
if st.session_state.show_chat:
    st.markdown("---")
    st.subheader("🤖 AI Stock Assistant")
    st.caption("Ask anything about stocks — replies in your language")
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel('gemini-3.6-flash')
        if "messages" not in st.session_state:
            st.session_state.messages = []
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        if prompt := st.chat_input("Ask anything about stocks..."):
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
            
            IMPORTANT: Detect the language of the user's question and reply in the SAME language.
            - If user asks in Hinglish (Roman Hindi), reply in Hinglish.
            - If user asks in English, reply in English.
            - If user asks in Hindi (Devanagari script), reply in Hindi.
            
            Keep answers short, clear, and educational.
            
            Current stock data:
            {context}
            
            User question: {prompt}
            
            Give helpful response. Do NOT give financial advice.
            """
            with st.chat_message("assistant"):
                with st.spinner("AI is thinking..."):
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.warning("⚠️ Please add GOOGLE_API_KEY in Streamlit Secrets.")
        st.caption(f"Error: {str(e)}")

st.markdown("---")
st.caption(f"Data source: Yahoo Finance | Last updated: {datetime.now().strftime('%d %b %Y, %H:%M')}")
