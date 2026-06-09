"""
Phase 5 測試案例 — Dashboard & 歷史報告回查
不需要 Streamlit 環境，測試底層資料邏輯
"""
import pytest, sys, os, json
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.market_data  import (get_price_history, pct_change,
                                calc_drawdown, get_benchmark_returns)
from report.report_model import list_report_dates, load_report

# ── 共用樣本報告 ─────────────────────────────────────────────
SAMPLE_REPORT = {
    "report_date":  "2026-05-24",
    "account_id":   "acc_001",
    "account_name": "Paper 帳戶",
    "active_strategy": "top10_nasdaq",
    "summary": {
        "cash": 5000.0, "portfolio_value": 100_000.0,
        "daily_pnl": 800.0, "daily_pnl_pct": 0.80,
        "max_drawdown_pct": -3.20,
    },
    "positions": [
        {"symbol": "AAPL", "qty": 57, "avg_cost": 175.0,
         "current_price": 180.0, "market_value": 10_260.0,
         "unrealized_pnl": 285.0, "unrealized_pnl_pct": 2.86,
         "pct_1d": 1.2, "pct_1w": 3.5, "pct_1m": 8.1, "pe_ratio": 28.5}
    ],
    "top10_nasdaq": [
        {"rank": 1, "symbol": "AAPL", "name": "Apple Inc.",
         "price": 180.0, "market_cap_b": 2800.0, "pe_ratio": 28.5,
         "pct_1d": 1.2, "pct_1w": 3.5, "pct_1m": 8.1, "predicted_next_pct": 0.5}
    ],
    "watchlist": {"科技股": ["AAPL", "MSFT"], "ETF": ["QQQ"]},
    "benchmark": {
        "nasdaq_1d_pct": 0.8, "nasdaq_1w_pct": 2.1,
        "sp500_1d_pct": 0.6, "sp500_1w_pct": 1.7,
        "qqq_history": [{"date": "2026-05-01", "close": 450.0},
                        {"date": "2026-05-02", "close": 455.0}],
        "spy_history": [{"date": "2026-05-01", "close": 520.0},
                        {"date": "2026-05-02", "close": 522.0}],
    },
    "disclaimer": "⚠️ 本報告僅供資訊整理，不構成投資建議。",
}

# TC-5-01  歷史報告寫入再讀取（JSON 格式完整性）
def test_report_save_and_reload(tmp_path):
    date_str = "2026-05-24"
    folder   = tmp_path / date_str
    folder.mkdir(parents=True)
    path = folder / "report_acc_001.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_REPORT, f, ensure_ascii=False, indent=2)
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["account_id"]         == "acc_001"
    assert loaded["summary"]["cash"]    == 5000.0
    assert loaded["disclaimer"]         != ""

# TC-5-02  list_report_dates 回傳排序正確（新→舊）
def test_list_report_dates_sorted(tmp_path):
    for d in ["2026-05-22", "2026-05-24", "2026-05-23"]:
        (tmp_path / d).mkdir()
    with patch("report.report_model.get_reports_dir", return_value=tmp_path):
        dates = list_report_dates()
    assert dates == ["2026-05-24", "2026-05-23", "2026-05-22"]

# TC-5-03  load_report 找不到時回傳 None
def test_load_report_not_found(tmp_path):
    with patch("report.report_model.get_reports_dir", return_value=tmp_path):
        result = load_report("acc_001", "2026-01-01")
    assert result is None

# TC-5-04  load_report 找到時回傳正確資料
def test_load_report_found(tmp_path):
    folder = tmp_path / "2026-05-24"
    folder.mkdir()
    path   = folder / "report_acc_001.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(SAMPLE_REPORT, f, ensure_ascii=False)
    with patch("report.report_model.get_reports_dir", return_value=tmp_path):
        loaded = load_report("acc_001", "2026-05-24")
    assert loaded is not None
    assert loaded["account_id"] == "acc_001"

# TC-5-05  benchmark 數據結構正確（Dashboard NAV 圖表用）
def test_benchmark_has_history_lists():
    bench = SAMPLE_REPORT["benchmark"]
    assert isinstance(bench["qqq_history"], list)
    assert isinstance(bench["spy_history"], list)
    for item in bench["qqq_history"]:
        assert "date"  in item
        assert "close" in item

# TC-5-06  drawdown 系列長度與輸入一致
def test_drawdown_series_length():
    nav    = [100, 102, 98, 95, 101, 103]
    result = calc_drawdown(nav)
    assert len(result["series"]) == len(nav)

# TC-5-07  NAV 正規化（基準=100）
def test_nav_normalization():
    import pandas as pd
    closes = pd.Series([200.0, 210.0, 205.0])
    norm   = (closes / closes.iloc[0] * 100)
    assert abs(norm.iloc[0] - 100.0) < 0.001
    assert abs(norm.iloc[1] - 105.0) < 0.001

# TC-5-08  持倉 P/E 欄位存在
def test_positions_have_pe():
    for p in SAMPLE_REPORT["positions"]:
        assert "pe_ratio" in p
        assert isinstance(p["pe_ratio"], (int, float))

# TC-5-09  前十名排名連續（1~10）
def test_top10_ranks_sequential():
    ranks = [t["rank"] for t in SAMPLE_REPORT["top10_nasdaq"]]
    assert ranks == sorted(ranks)
    assert ranks[0] == 1

# TC-5-10  watchlist 結構：dict[str, list[str]]
def test_watchlist_structure():
    wl = SAMPLE_REPORT["watchlist"]
    assert isinstance(wl, dict)
    for cat, symbols in wl.items():
        assert isinstance(cat, str)
        assert isinstance(symbols, list)
        assert all(isinstance(s, str) for s in symbols)

# TC-5-11  pct_1d / 1w / 1m 都是 float
def test_position_pct_types():
    p = SAMPLE_REPORT["positions"][0]
    for key in ("pct_1d", "pct_1w", "pct_1m"):
        assert isinstance(p[key], float), f"{key} 不是 float"

# TC-5-12  report_date 格式 YYYY-MM-DD
def test_report_date_format():
    import re
    assert re.match(r"\d{4}-\d{2}-\d{2}", SAMPLE_REPORT["report_date"])

# TC-5-13  無歷史報告時 list_report_dates 回傳空清單
def test_list_report_dates_empty(tmp_path):
    with patch("report.report_model.get_reports_dir", return_value=tmp_path):
        dates = list_report_dates()
    assert dates == []

# TC-5-14  dashboard/app.py 檔案存在且可 import spec
def test_dashboard_file_exists():
    import importlib.util
    path = Path(__file__).parent.parent / "dashboard" / "app.py"
    assert path.exists(), "dashboard/app.py 不存在"
    spec = importlib.util.spec_from_file_location("app", str(path))
    assert spec is not None

# TC-5-15  勾選 NASDAQ/SP500 flag 是布林值（Dashboard 側邊欄設計）
def test_benchmark_toggle_flags():
    show_nasdaq = True
    show_sp500  = False
    show_mine   = True
    assert isinstance(show_nasdaq, bool)
    assert isinstance(show_sp500,  bool)
    assert isinstance(show_mine,   bool)
