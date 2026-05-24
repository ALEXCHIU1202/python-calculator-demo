"""
AlpacaBot Dashboard — 雲端版
部署於 Streamlit Community Cloud，不依賴本機環境
執行: streamlit run dashboard/app.py
設定: .streamlit/secrets.toml（本機）或 Streamlit Cloud Secrets（雲端）
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os, json
from datetime import date, datetime
from pathlib import Path

# ── 路徑設定（確保 import 在任何工作目錄都正常）────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.config       import load_config, get_watchlist, get_reports_dir
from core.alpaca_client import AlpacaAccount
from core.market_data  import (get_top10_analysis, get_benchmark_returns,
                                get_price_history, pct_change, calc_drawdown)
from report.report_model import list_report_dates

# ── 頁面設定 ────────────────────────────────────────────
st.set_page_config(
    page_title="AlpacaBot Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "AlpacaBot — 全自動美股追蹤系統\n⚠️ 僅供研究參考，不構成投資建議"}
)

# ── CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
  .disclaimer {
    background: #fff8e1; border-left: 4px solid #ffc107;
    padding: 10px 14px; border-radius: 4px;
    font-size: 0.82rem; color: #5d4037; margin-top: 12px;
  }
  .env-badge {
    display:inline-block; padding:2px 10px; border-radius:10px;
    font-size:0.75rem; font-weight:600; margin-left:8px;
  }
  .cloud { background:#e8f5e9; color:#2e7d32; }
  .local { background:#e3f2fd; color:#1565c0; }
</style>
""", unsafe_allow_html=True)

# ── 載入設定（雲端/本機自動偵測）───────────────────────
@st.cache_resource(ttl=300)
def load_cfg():
    try:
        cfg = load_config()
        return cfg, None
    except Exception as e:
        return None, str(e)

cfg, cfg_err = load_cfg()
if cfg_err:
    st.error(f"⚠️ 設定載入失敗：{cfg_err}")
    st.info("請設定 Streamlit Secrets 或環境變數 ACCOUNTS_JSON")
    st.stop()

# ── 偵測執行環境 ─────────────────────────────────────────
def detect_env() -> str:
    try:
        import streamlit as st
        _ = st.secrets["account_1"]
        return "cloud"
    except Exception:
        return "local"

env_label = detect_env()
env_badge = (
    '<span class="env-badge cloud">☁️ Streamlit Cloud</span>'
    if env_label == "cloud"
    else '<span class="env-badge local">💻 本機環境</span>'
)

# ── 建立帳戶物件 ─────────────────────────────────────────
@st.cache_resource(ttl=300)
def build_accounts():
    accounts = []
    for a in cfg.get("accounts", []):
        if a.get("enabled", True):
            try:
                accounts.append(AlpacaAccount(a))
            except Exception as e:
                st.warning(f"帳戶 {a.get('name')} 連線失敗：{e}")
    return accounts

accounts = build_accounts()
if not accounts:
    st.error("沒有可用的帳戶，請確認 Secrets 設定")
    st.stop()

# ── 側邊欄 ───────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### ⚙️ 設定 {env_badge}", unsafe_allow_html=True)
    acc_map      = {a.name: a for a in accounts}
    selected_name = st.selectbox("帳戶", list(acc_map.keys()))
    acc          = acc_map[selected_name]

    st.markdown("---")
    view_mode = st.radio("檢視模式", ["📡 即時資料", "📁 歷史報告"])

    selected_date = None
    if view_mode == "📁 歷史報告":
        dates = list_report_dates()
        if dates:
            selected_date = st.selectbox("選擇日期", dates)
        else:
            st.info("尚無歷史報告")

    st.markdown("---")
    st.markdown("**圖表顯示**")
    show_nasdaq = st.checkbox("NASDAQ (QQQ)",  value=True)
    show_sp500  = st.checkbox("S&P500 (SPY)",  value=True)
    show_mine   = st.checkbox("我的帳戶",       value=True)

    st.markdown("---")
    if st.button("🔄 重新整理資料"):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"最後更新：{datetime.now().strftime('%H:%M:%S')}")

# ── 資料取得（帶快取，減少 API 呼叫次數）──────────────────
@st.cache_data(ttl=300, show_spinner=False)
def fetch_live_data(acc_id: str, api_key: str, api_secret: str, base_url: str):
    a = next((x for x in accounts if x.id == acc_id), None)
    if not a:
        return None
    acct = a.get_account()
    pos  = a.get_positions()
    return {
        "cash":         float(acct.cash),
        "portfolio":    float(acct.portfolio_value),
        "equity":       float(acct.equity),
        "last_equity":  float(acct.last_equity),
        "positions":    pos,
        "is_open":      a.is_market_open(),
    }

@st.cache_data(ttl=600, show_spinner=False)
def fetch_top10():
    return get_top10_analysis()

@st.cache_data(ttl=600, show_spinner=False)
def fetch_benchmark():
    return get_benchmark_returns(60)

@st.cache_data(ttl=600, show_spinner=False)
def fetch_position_perf(symbol: str):
    hist = get_price_history(symbol, 30)
    return {
        "1d": pct_change(hist, 1),
        "1w": pct_change(hist, 5),
        "1m": pct_change(hist, 21),
    }

def load_history_report(acc_id: str, rpt_date: str):
    reports_dir = get_reports_dir()
    path = reports_dir / rpt_date / f"report_{acc_id}.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# ── 取資料 ───────────────────────────────────────────────
st.title(f"📊 AlpacaBot Dashboard")

if view_mode == "📁 歷史報告" and selected_date:
    report = load_history_report(acc.id, selected_date)
    if not report:
        st.warning(f"找不到 {selected_date} 的報告")
        st.stop()
    summary   = report["summary"]
    positions = report["positions"]
    top10     = report["top10_nasdaq"]
    bench     = report["benchmark"]
    watchlist = report.get("watchlist", get_watchlist())
    st.info(f"📅 歷史報告：{selected_date}")
else:
    with st.spinner("載入即時資料..."):
        live = fetch_live_data(acc.id, acc.api_key, acc.api_secret, acc.base_url)
    if not live:
        st.error("無法取得帳戶資料")
        st.stop()

    daily_pnl = live["equity"] - live["last_equity"]
    daily_pct = (daily_pnl / live["last_equity"] * 100) if live["last_equity"] else 0
    summary   = {
        "cash": live["cash"], "portfolio_value": live["portfolio"],
        "daily_pnl": daily_pnl, "daily_pnl_pct": daily_pct,
        "max_drawdown_pct": 0.0,
    }
    positions = live["positions"]
    with st.spinner("載入市場資料..."):
        top10 = fetch_top10()
        bench = fetch_benchmark()
    watchlist = get_watchlist()

    # 補充持倉績效
    for p in positions:
        perf        = fetch_position_perf(p["symbol"])
        p["pct_1d"] = perf["1d"]
        p["pct_1w"] = perf["1w"]
        p["pct_1m"] = perf["1m"]
        p["pe_ratio"] = next((t["pe_ratio"] for t in top10 if t["symbol"] == p["symbol"]), 0)

    # 市場狀態提示
    if live.get("is_open"):
        st.success("🟢 美股市場開盤中")
    else:
        st.info("🔴 美股市場已收盤（顯示最後收盤資料）")

# ── KPI 卡片 ─────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("💵 現金水位",   f"${summary['cash']:,.0f}")
c2.metric("💼 帳戶總值",   f"${summary['portfolio_value']:,.0f}")
c3.metric("📈 今日損益",
          f"${summary['daily_pnl']:+,.0f}",
          f"{summary['daily_pnl_pct']:+.2f}%")
c4.metric("📉 最大回撤",   f"{summary['max_drawdown_pct']:.2f}%")

st.markdown("---")

# ── 持倉清單 ─────────────────────────────────────────────
st.subheader("📋 持倉清單")
if positions:
    df = pd.DataFrame(positions)
    cols_needed = ["symbol","qty","avg_cost","current_price","market_value",
                   "unrealized_pnl","pct_1d","pct_1w","pct_1m","pe_ratio"]
    df = df[[c for c in cols_needed if c in df.columns]]
    df.columns = ["股票","股數","成本","現價","市值","未實現損益","1日%","1週%","1月%","P/E"]

    def color_num(val):
        try:
            return "color:green;font-weight:600" if float(val) >= 0 else "color:red;font-weight:600"
        except Exception:
            return ""

    styled = df.style\
        .applymap(color_num, subset=["未實現損益","1日%","1週%","1月%"])\
        .format({"成本":"${:.2f}","現價":"${:.2f}","市值":"${:,.0f}",
                 "未實現損益":"${:+,.0f}","1日%":"{:+.2f}%",
                 "1週%":"{:+.2f}%","1月%":"{:+.2f}%","P/E":"{:.1f}"})
    st.dataframe(styled, use_container_width=True)
else:
    st.info("目前無持倉")

st.markdown("---")

# ── Top 10 長條圖 ─────────────────────────────────────────
st.subheader("🏆 NASDAQ 市值前十")
tab_chart, tab_table = st.tabs(["📊 長條圖", "📋 詳細資料"])
df10 = pd.DataFrame(top10)
with tab_chart:
    colors = ["#2e7d32" if v >= 0 else "#c62828" for v in df10["pct_1d"]]
    fig = go.Figure(go.Bar(
        x=df10["symbol"], y=df10["pct_1d"],
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in df10["pct_1d"]],
        textposition="outside"
    ))
    fig.update_layout(
        title="今日漲跌幅 (%)", yaxis_title="%", plot_bgcolor="white", height=380,
        yaxis=dict(zeroline=True, zerolinecolor="#ccc", zerolinewidth=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("⚠️ 次日預測僅為技術指標估算，不構成投資建議")

with tab_table:
    show_cols = ["rank","symbol","name","price","market_cap_b",
                 "pct_1d","pct_1w","pct_1m","pe_ratio","predicted_next_pct"]
    df_show = df10[[c for c in show_cols if c in df10.columns]].copy()
    df_show.columns = ["#","股票","公司","現價","市值B","1日%","1週%","1月%","P/E","次日預測"]
    st.dataframe(df_show.style.format({
        "現價":"${:.2f}","市值B":"${:,.0f}",
        "1日%":"{:+.2f}%","1週%":"{:+.2f}%","1月%":"{:+.2f}%",
        "次日預測":"{:+.2f}%","P/E":"{:.1f}"
    }), use_container_width=True)

st.markdown("---")

# ── NAV 走勢 & 回撤 ───────────────────────────────────────
st.subheader("📈 NAV 走勢 & 基準對比")
qqq_hist = bench.get("qqq_history", [])
spy_hist = bench.get("spy_history", [])

if qqq_hist:
    qqq_df = pd.DataFrame(qqq_hist)
    spy_df = pd.DataFrame(spy_hist)

    def normalize(series):
        s = pd.to_numeric(series, errors="coerce").dropna()
        return (s / s.iloc[0] * 100) if len(s) > 0 else s

    fig2 = go.Figure()
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
    if show_mine and qqq_df is not None and len(qqq_df) > 0:
        n = len(qqq_df)
        base = summary["portfolio_value"]
        nav_series = normalize(pd.Series([base] * n))
        fig2.add_trace(go.Scatter(
            x=qqq_df["date"], y=nav_series,
            name="我的帳戶", line=dict(color="#6a1b9a", width=2, dash="dot")
        ))
    fig2.update_layout(
        title="相對績效（基準=100）", yaxis_title="相對淨值",
        plot_bgcolor="white", height=360,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig2, use_container_width=True)

    # 回撤圖
    if show_nasdaq and not qqq_df.empty:
        dd = calc_drawdown(pd.to_numeric(qqq_df["close"], errors="coerce").dropna().tolist())
        fig3 = go.Figure(go.Scatter(
            x=qqq_df["date"][:len(dd["series"])], y=dd["series"],
            fill="tozeroy", name="NASDAQ 回撤",
            line=dict(color="#1565c0"), fillcolor="rgba(21,101,192,0.12)"
        ))
        fig3.update_layout(
            title=f"最大回撤：{dd['max_drawdown_pct']:.2f}%",
            yaxis_title="回撤 (%)", plot_bgcolor="white", height=260
        )
        st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── 關注清單 ──────────────────────────────────────────────
st.subheader("👁 我的關注清單")
watch_tabs = st.tabs(list(watchlist.keys()))
for tab, (cat, symbols) in zip(watch_tabs, watchlist.items()):
    with tab:
        rows = []
        for sym in symbols:
            try:
                perf = fetch_position_perf(sym)
                rows.append({"股票": sym, "1日%": perf["1d"],
                             "1週%": perf["1w"], "1月%": perf["1m"]})
            except Exception:
                rows.append({"股票": sym, "1日%": 0, "1週%": 0, "1月%": 0})
        df_w = pd.DataFrame(rows)
        st.dataframe(df_w.style.format(
            {"1日%": "{:+.2f}%","1週%": "{:+.2f}%","1月%": "{:+.2f}%"}
        ), use_container_width=True)

# ── 歷史報告回查 ──────────────────────────────────────────
st.markdown("---")
with st.expander("📁 歷史報告清單"):
    dates = list_report_dates()
    if dates:
        st.write(f"共 {len(dates)} 份報告，最新：**{dates[0]}**")
        for d in dates[:10]:
            col_d, col_btn = st.columns([3, 1])
            col_d.write(d)
            path = get_reports_dir() / d / f"report_{acc.id}.json"
            if path.exists():
                with open(path, "rb") as f:
                    col_btn.download_button("⬇ 下載", f, file_name=f"report_{d}.json",
                                            key=f"dl_{d}", mime="application/json")
    else:
        st.info("尚無歷史報告（GitHub Actions 執行後會自動產生）")

# ── 免責聲明 ──────────────────────────────────────────────
st.markdown("""
<div class="disclaimer">
⚠️ 本儀表板所有內容（排名、績效、分析、預測）<b>僅供資訊整理與研究參考，不構成任何投資建議。</b>
投資人應自行評估風險，本系統不負任何投資盈虧責任。
</div>
""", unsafe_allow_html=True)
