"""
Phase 3 - Streamlit Dashboard
執行: streamlit run dashboard/app.py
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os, json
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.alpaca_client import get_all_accounts, load_accounts
from core.market_data   import (get_top10_analysis, get_benchmark_returns,
                                 get_price_history, pct_change, calc_drawdown)
from report.report_model import load_report, list_report_dates

st.set_page_config(
    page_title="AlpacaBot Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background:#fff; border-radius:12px; padding:16px 20px;
    box-shadow:0 2px 8px rgba(0,0,0,0.08); margin-bottom:8px;
  }
  .metric-val { font-size:1.8rem; font-weight:700; color:#1565c0; }
  .metric-lbl { font-size:0.8rem; color:#90a4ae; }
  .up   { color:#2e7d32 !important; }
  .down { color:#c62828 !important; }
  .disclaimer {
    background:#fff8e1; border-left:4px solid #ffc107;
    padding:10px 14px; border-radius:4px; font-size:0.82rem; color:#5d4037;
    margin-top:16px;
  }
</style>
""", unsafe_allow_html=True)

# ── 側邊欄 ─────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ 設定")
    accounts = get_all_accounts()
    acc_names = {a.name: a for a in accounts}
    selected_name = st.selectbox("帳戶", list(acc_names.keys()))
    acc = acc_names[selected_name]

    st.markdown("---")
    view_mode = st.radio("檢視模式", ["即時資料", "歷史報告"])

    if view_mode == "歷史報告":
        dates = list_report_dates()
        selected_date = st.selectbox("選擇日期", dates if dates else [str(date.today())])
    else:
        selected_date = None

    st.markdown("---")
    show_nasdaq = st.checkbox("顯示 NASDAQ", value=True)
    show_sp500  = st.checkbox("顯示 S&P500",  value=True)
    show_mine   = st.checkbox("顯示我的帳戶", value=True)

    st.markdown("---")
    if st.button("🔄 重新整理"):
        st.cache_data.clear()
        st.rerun()

# ── 取得資料 ───────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_account_data(acc_id, acc_key, acc_secret, base_url):
    from core.alpaca_client import AlpacaAccount
    cfg = {"id": acc_id, "name": acc_id, "api_key": acc_key,
           "api_secret": acc_secret, "base_url": base_url,
           "active_strategy": "", "email": "", "enabled": True}
    a = AlpacaAccount(cfg)
    return {
        "cash":      a.get_cash(),
        "portfolio": a.get_portfolio_value(),
        "positions": a.get_positions(),
        "account":   a.get_account(),
    }

@st.cache_data(ttl=600)
def fetch_top10():
    return get_top10_analysis()

@st.cache_data(ttl=600)
def fetch_benchmark():
    return get_benchmark_returns(60)

# ── 主頁面 ─────────────────────────────────────────
st.title("📊 AlpacaBot Dashboard")

if view_mode == "歷史報告" and selected_date:
    report = load_report(acc.id, selected_date)
    if report:
        summary   = report["summary"]
        positions = report["positions"]
        top10     = report["top10_nasdaq"]
        bench     = report["benchmark"]
        watchlist = report["watchlist"]
        st.info(f"📅 檢視歷史報告：{selected_date}")
    else:
        st.warning("此日期尚無報告")
        st.stop()
else:
    with st.spinner("載入即時資料..."):
        data      = fetch_account_data(acc.id, acc.api_key, acc.api_secret, acc.base_url)
        top10     = fetch_top10()
        bench     = fetch_benchmark()
        cfg       = load_accounts()
        watchlist = cfg.get("watchlist", {})
        acct      = data["account"]
        daily_pnl = float(acct.equity) - float(acct.last_equity)
        daily_pct = daily_pnl / float(acct.last_equity) * 100 if float(acct.last_equity) else 0
        summary   = {
            "cash":            data["cash"],
            "portfolio_value": data["portfolio"],
            "daily_pnl":       daily_pnl,
            "daily_pnl_pct":   daily_pct,
            "max_drawdown_pct": 0.0,
        }
        positions = data["positions"]
        for p in positions:
            hist        = get_price_history(p["symbol"], 30)
            p["pct_1d"] = pct_change(hist, 1)
            p["pct_1w"] = pct_change(hist, 5)
            p["pct_1m"] = pct_change(hist, 21)
            p["pe_ratio"] = next((t["pe_ratio"] for t in top10 if t["symbol"] == p["symbol"]), 0)

# ── KPI 卡片 ───────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💵 現金水位", f"${summary['cash']:,.0f}")
with col2:
    st.metric("💼 帳戶總值", f"${summary['portfolio_value']:,.0f}")
with col3:
    pnl = summary["daily_pnl"]
    pct = summary["daily_pnl_pct"]
    st.metric("📈 今日損益", f"${pnl:+,.0f}", f"{pct:+.2f}%")
with col4:
    st.metric("📉 最大回撤", f"{summary['max_drawdown_pct']:.2f}%")

st.markdown("---")

# ── 持倉清單 ───────────────────────────────────────
st.subheader("📋 持倉清單")
if positions:
    df = pd.DataFrame(positions)
    def color_pnl(v):
        return "color:green;font-weight:600" if v >= 0 else "color:red;font-weight:600"
    styled = (
        df[["symbol","qty","avg_cost","current_price","market_value",
            "unrealized_pnl","pct_1d","pct_1w","pct_1m","pe_ratio"]]
        .rename(columns={
            "symbol":"股票","qty":"股數","avg_cost":"成本",
            "current_price":"現價","market_value":"市值",
            "unrealized_pnl":"未實現損益",
            "pct_1d":"1日%","pct_1w":"1週%","pct_1m":"1月%","pe_ratio":"P/E"
        })
        .style
        .applymap(color_pnl, subset=["1日%","1週%","1月%","未實現損益"])
        .format({"成本":"${:.2f}","現價":"${:.2f}","市值":"${:,.0f}",
                 "未實現損益":"${:+,.0f}","1日%":"{:+.2f}%",
                 "1週%":"{:+.2f}%","1月%":"{:+.2f}%","P/E":"{:.1f}"})
    )
    st.dataframe(styled, use_container_width=True)
else:
    st.info("目前無持倉")

st.markdown("---")

# ── Top 10 長條圖 ──────────────────────────────────
st.subheader("🏆 NASDAQ 市值前十 — 今日表現")
tab1, tab2 = st.tabs(["長條圖", "詳細表格"])
with tab1:
    df10 = pd.DataFrame(top10)
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in df10["pct_1d"]]
    fig = go.Figure(go.Bar(
        x=df10["symbol"], y=df10["pct_1d"],
        marker_color=colors, text=[f"{v:+.2f}%" for v in df10["pct_1d"]],
        textposition="outside"
    ))
    fig.update_layout(
        title="今日漲跌幅 (%)", yaxis_title="%",
        plot_bgcolor="white", height=400,
        yaxis=dict(zeroline=True, zerolinecolor="#aaa", zerolinewidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)
with tab2:
    df10_show = df10[["rank","symbol","name","price","market_cap_b",
                       "pct_1d","pct_1w","pct_1m","pe_ratio","predicted_next_pct"]].copy()
    df10_show.columns = ["#","股票","公司名","現價($)","市值(B$)","1日%","1週%","1月%","P/E","次日預測%"]
    st.dataframe(df10_show.style.format({
        "現價($)":"${:.2f}","市值(B$)":"${:,.0f}",
        "1日%":"{:+.2f}%","1週%":"{:+.2f}%","1月%":"{:+.2f}%",
        "次日預測%":"{:+.2f}%","P/E":"{:.1f}"
    }), use_container_width=True)
    st.caption("⚠️ 次日預測僅為技術指標參考，不構成投資建議")

st.markdown("---")

# ── NAV & 回撤對比圖 ───────────────────────────────
st.subheader("📈 NAV 走勢 & 基準對比")
qqq_hist = bench.get("qqq_history", [])
spy_hist = bench.get("spy_history", [])

if qqq_hist:
    fig2 = go.Figure()
    qqq_df = pd.DataFrame(qqq_hist)
    spy_df = pd.DataFrame(spy_hist)

    def normalize(series):
        s = pd.to_numeric(series, errors="coerce")
        return (s / s.iloc[0] * 100).round(2) if len(s) > 0 else s

    if show_nasdaq and not qqq_df.empty:
        fig2.add_trace(go.Scatter(
            x=qqq_df["date"], y=normalize(qqq_df["close"]),
            name="NASDAQ (QQQ)", line=dict(color="#1565c0", width=2)
        ))
    if show_sp500 and not spy_df.empty:
        fig2.add_trace(go.Scatter(
            x=spy_df["date"], y=normalize(spy_df["close"]),
            name="S&P500 (SPY)", line=dict(color="#e65100", width=2)
        ))
    if show_mine:
        nav_val = summary["portfolio_value"]
        if qqq_df is not None and len(qqq_df) > 0:
            nav_series = [nav_val] * len(qqq_df)
            fig2.add_trace(go.Scatter(
                x=qqq_df["date"], y=normalize(pd.Series(nav_series)),
                name="我的帳戶", line=dict(color="#6a1b9a", width=2, dash="dot")
            ))
    fig2.update_layout(
        title="相對績效 (基準=100)", yaxis_title="相對淨值",
        plot_bgcolor="white", height=380,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 回撤圖
    if show_nasdaq and not qqq_df.empty:
        dd = calc_drawdown(qqq_df["close"].tolist())
        fig3 = go.Figure(go.Scatter(
            x=qqq_df["date"], y=dd["series"],
            fill="tozeroy", name="NASDAQ 回撤",
            line=dict(color="#1565c0"), fillcolor="rgba(21,101,192,0.15)"
        ))
        fig3.update_layout(
            title=f"最大回撤：{dd['max_drawdown_pct']:.2f}%",
            yaxis_title="回撤 (%)", plot_bgcolor="white", height=280
        )
        st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── 關注清單 ───────────────────────────────────────
st.subheader("👁 我的關注清單")
watch_tabs = st.tabs(list(watchlist.keys()))
for tab, (cat, symbols) in zip(watch_tabs, watchlist.items()):
    with tab:
        rows = []
        for sym in symbols:
            try:
                hist = get_price_history(sym, 30)
                rows.append({
                    "股票": sym,
                    "1日%": pct_change(hist, 1),
                    "1週%": pct_change(hist, 5),
                    "1月%": pct_change(hist, 21),
                })
            except:
                rows.append({"股票": sym, "1日%": 0, "1週%": 0, "1月%": 0})
        df_w = pd.DataFrame(rows)
        st.dataframe(
            df_w.style.format({"1日%":"{:+.2f}%","1週%":"{:+.2f}%","1月%":"{:+.2f}%"}),
            use_container_width=True
        )

# ── 歷史報告回查 ───────────────────────────────────
st.markdown("---")
st.subheader("📁 歷史報告")
dates = list_report_dates()
if dates:
    st.write(f"共有 {len(dates)} 份歷史報告，最新：{dates[0]}")
    with st.expander("查看所有日期"):
        st.write(dates)
else:
    st.info("尚無歷史報告，執行 report_model.py 產生第一份")

# ── 免責聲明 ───────────────────────────────────────
st.markdown("""
<div class="disclaimer">
⚠️ 本儀表板所有內容（排名、績效、分析、預測）<b>僅供資訊整理與研究參考，不構成投資建議。</b>
投資人應自行評估風險，本系統不負任何投資盈虧責任。
</div>
""", unsafe_allow_html=True)
