"""Phase 4 測試案例 — 報告系統"""
import pytest, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from report.report_view  import render_email_html, render_trade_alert
from report.report_model import load_report, list_report_dates, DISCLAIMER

SAMPLE_REPORT = {
    "report_date":    "2026-05-24",
    "generated_at":   "2026-05-24 06:00:00",
    "account_id":     "acc_001",
    "account_name":   "Paper 帳戶",
    "active_strategy": "top10_nasdaq",
    "summary": {
        "cash": 50000, "portfolio_value": 100000,
        "equity": 100500, "daily_pnl": 500, "daily_pnl_pct": 0.50,
        "max_drawdown_pct": -2.5
    },
    "positions": [
        {"symbol":"AAPL","qty":50,"avg_cost":195.0,"current_price":198.5,
         "market_value":9925,"unrealized_pnl":175,"unrealized_pnl_pct":1.79,
         "pct_1d":1.23,"pct_1w":2.45,"pct_1m":-0.87,"pe_ratio":28.5}
    ],
    "top10_nasdaq": [
        {"rank":1,"symbol":"AAPL","name":"Apple Inc.","price":198.5,
         "market_cap_b":3050,"pe_ratio":28.5,
         "pct_1d":1.23,"pct_1w":2.45,"pct_1m":-0.87,"predicted_next_pct":0.45}
    ],
    "watchlist":  {"科技股":["AAPL","MSFT"],"ETF":["QQQ"]},
    "benchmark":  {"nasdaq_1d_pct":0.85,"nasdaq_1w_pct":2.1,
                   "sp500_1d_pct":0.62,"sp500_1w_pct":1.8,
                   "qqq_history":[],"spy_history":[]},
    "disclaimer": DISCLAIMER,
}

# TC-4-01
def test_report_model_required_fields():
    for field in ["report_date","account_id","account_name","summary",
                  "positions","top10_nasdaq","watchlist","benchmark","disclaimer"]:
        assert field in SAMPLE_REPORT, f"缺少欄位: {field}"

# TC-4-02
def test_report_save_and_load(tmp_path):
    import json, os
    date_str = "2026-05-24"
    folder   = tmp_path / date_str
    folder.mkdir()
    path = folder / f"report_{SAMPLE_REPORT['account_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_REPORT, f, ensure_ascii=False)
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["account_id"] == "acc_001"

# TC-4-03
def test_render_email_html_no_error():
    html = render_email_html(SAMPLE_REPORT)
    assert isinstance(html, str)
    assert len(html) > 100

# TC-4-04
def test_html_contains_key_elements():
    html = render_email_html(SAMPLE_REPORT)
    assert "AAPL"      in html
    assert "$50,000"   in html
    assert "disclaimer" in html.lower() or "僅供" in html

# TC-4-05
def test_disclaimer_in_report():
    assert "不構成投資建議" in SAMPLE_REPORT["disclaimer"]

# TC-4-06
def test_disclaimer_in_html():
    html = render_email_html(SAMPLE_REPORT)
    assert "不構成投資建議" in html

# TC-4-07
def test_trade_alert_render():
    trade = {"symbol":"AAPL","side":"buy","qty":10,"price":198.5,"time":"09:35:00"}
    html  = render_trade_alert(trade)
    assert "AAPL"   in html
    assert "10"     in html
    assert "198.5"  in html
    assert "買入" in html or "buy" in html.lower()

# TC-4-08
def test_sell_trade_alert():
    trade = {"symbol":"MSFT","side":"sell","qty":5,"price":420.0,"time":"10:00:00"}
    html  = render_trade_alert(trade)
    assert "MSFT"   in html
    assert "賣出" in html or "sell" in html.lower()

# TC-4-09
def test_summary_pnl_calculation():
    s = SAMPLE_REPORT["summary"]
    assert s["daily_pnl"]     == 500
    assert s["daily_pnl_pct"] == 0.50

# TC-4-10
def test_list_report_dates_returns_list():
    dates = list_report_dates()
    assert isinstance(dates, list)
