"""
Phase 1 - 市場資料模組
NASDAQ Top10、歷史績效、本益比、技術指標
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

NASDAQ_TOP10 = ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","GOOG","TSLA","AVGO","COST"]
NASDAQ_TOP100_SAMPLE = NASDAQ_TOP10 + [
    "NFLX","ADBE","AMD","INTC","QCOM","TXN","AMAT","MU","LRCX","KLAC",
    "PANW","CRWD","SNPS","CDNS","MRVL","ASML","ADP","PAYX","ORLY","CTAS"
]

def get_nasdaq_top10() -> list[str]:
    return NASDAQ_TOP10.copy()

def get_nasdaq_top100() -> list[str]:
    return NASDAQ_TOP100_SAMPLE.copy()

def get_stock_info(symbol: str) -> dict:
    try:
        ticker = yf.Ticker(symbol)
        info   = ticker.info
        return {
            "symbol":       symbol,
            "name":         info.get("longName", symbol),
            "price":        info.get("currentPrice") or info.get("regularMarketPrice", 0),
            "market_cap":   info.get("marketCap", 0),
            "pe_ratio":     round(info.get("trailingPE", 0) or 0, 2),
            "volume":       info.get("volume", 0),
            "sector":       info.get("sector", ""),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}

def get_top10_analysis() -> list[dict]:
    results = []
    for i, sym in enumerate(NASDAQ_TOP10):
        info = get_stock_info(sym)
        hist = get_price_history(sym, days=30)
        pct_1d = pct_change(hist, 1)
        pct_1w = pct_change(hist, 5)
        pct_1m = pct_change(hist, 21)
        prediction = predict_next_day(hist)
        results.append({
            "rank":              i + 1,
            "symbol":            sym,
            "name":              info.get("name", sym),
            "price":             info.get("price", 0),
            "market_cap_b":      round(info.get("market_cap", 0) / 1e9, 1),
            "pe_ratio":          info.get("pe_ratio", 0),
            "pct_1d":            pct_1d,
            "pct_1w":            pct_1w,
            "pct_1m":            pct_1m,
            "predicted_next_pct": prediction,
        })
    return results

def get_price_history(symbol: str, days: int = 60) -> pd.DataFrame:
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=f"{days+10}d")
    return df.tail(days).reset_index()

def pct_change(df: pd.DataFrame, periods: int) -> float:
    if df is None or len(df) < periods + 1:
        return 0.0
    closes = df["Close"].values
    if len(closes) < 2:
        return 0.0
    end   = closes[-1]
    start = closes[-(periods + 1)] if len(closes) > periods else closes[0]
    return round((end - start) / start * 100, 2) if start else 0.0

def predict_next_day(df: pd.DataFrame) -> float:
    """
    簡單技術指標預測（RSI + 動能）
    ⚠️ 僅供參考，不構成投資建議
    """
    if df is None or len(df) < 15:
        return 0.0
    closes = pd.Series(df["Close"].values, dtype=float)
    delta  = closes.diff()
    gain   = delta.clip(lower=0).rolling(14).mean()
    loss   = (-delta.clip(upper=0)).rolling(14).mean()
    rs     = gain / (loss + 1e-9)
    rsi    = 100 - (100 / (1 + rs))
    last_rsi = float(rsi.iloc[-1])
    momentum = float(closes.pct_change(5).iloc[-1] * 100)
    signal = 0.0
    if last_rsi < 30:
        signal += 0.5
    elif last_rsi > 70:
        signal -= 0.5
    signal += momentum * 0.1
    return round(max(-5.0, min(5.0, signal)), 2)

def _to_history_records(df) -> list:
    """DataFrame → list[dict]，日期轉為字串，避免 Timestamp JSON 序列化錯誤"""
    d = df[["Date", "Close"]].rename(columns={"Date": "date", "Close": "close"}).copy()
    d["date"] = d["date"].astype(str).str[:10]
    return d.to_dict("records")

def get_benchmark_returns(days: int = 60) -> dict:
    try:
        qqq  = get_price_history("QQQ",  days)
        spy  = get_price_history("SPY",  days)
        return {
            "nasdaq_1d":  pct_change(qqq, 1),
            "nasdaq_1w":  pct_change(qqq, 5),
            "nasdaq_1m":  pct_change(qqq, 21),
            "sp500_1d":   pct_change(spy, 1),
            "sp500_1w":   pct_change(spy, 5),
            "sp500_1m":   pct_change(spy, 21),
            "qqq_history": _to_history_records(qqq),
            "spy_history": _to_history_records(spy),
        }
    except Exception as e:
        return {"error": str(e)}

def calc_drawdown(nav_series: list[float]) -> dict:
    if not nav_series:
        return {"max_drawdown_pct": 0.0, "series": []}
    arr     = np.array(nav_series, dtype=float)
    peak    = np.maximum.accumulate(arr)
    dd      = (arr - peak) / peak * 100
    max_dd  = float(dd.min())
    return {"max_drawdown_pct": round(max_dd, 2), "series": dd.tolist()}
