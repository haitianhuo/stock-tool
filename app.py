import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="自用看盘", layout="wide")
st.title("📈 自用看盘")

@st.cache_data(ttl=3600)
def load(code, days):
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
    df = ak.stock_zh_a_hist(symbol=code, period="daily",
                            start_date=start, end_date=end, adjust="qfq")
    df = df.rename(columns={"日期": "date", "开盘": "open", "收盘": "close",
                            "最高": "high", "最低": "low", "成交量": "volume",
                            "涨跌幅": "pct_chg"})
    df["date"] = pd.to_datetime(df["date"])
    return df.tail(days).reset_index(drop=True)

with st.sidebar:
    st.header("设置")
    raw = st.text_input("股票代码", "600519")
    days = st.slider("回看天数", 60, 500, 250)
    mas = st.multiselect("均线", [5, 10, 20, 60, 120], default=[5, 20, 60])

code = "".join(c for c in raw if c.isdigit())

try:
    df = load(code, days)
    for m in mas:
        df[f"MA{m}"] = df["close"].rolling(m).mean()

    last, prev = df.iloc[-1], df.iloc[-2]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最新价", f"{last['close']:.2f}", f"{last['pct_chg']:.2f}%")
    c2.metric("成交量(万手)", f"{last['volume']/10000:.1f}")
    c3.metric("MA20", f"{last.get('MA20', float('nan')):.2f}")
    c4.metric("MA60", f"{last.get('MA60', float('nan')):.2f}")

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df["date"], open=df["open"], high=df["high"],
                                 low=df["low"], close=df["close"], name="K线"))
    for m in mas:
        fig.add_trace(go.Scatter(x=df["date"], y=df[f"MA{m}"],
                                 name=f"MA{m}", line=dict(width=1)))
    fig.update_layout(height=420, xaxis_rangeslider_visible=False,
                      margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.caption("成交量")
    st.bar_chart(df.set_index("date")["volume"], height=180)

    with st.expander("最近 20 日数据"):
        st.dataframe(df.tail(20)[["date", "open", "close", "high", "low",
                                  "volume", "pct_chg"]], use_container_width=True)
except Exception as e:
    st.error(f"加载失败：{e}")
    st.info("检查代码是否为纯数字（如 600519），或稍后重试。")
