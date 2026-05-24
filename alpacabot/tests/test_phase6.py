"""Phase 6 測試案例 — 進階分析"""
import pytest, sys, os
import pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.market_data import (get_price_history, pct_change,
                               predict_next_day, calc_drawdown,
                               get_stock_info, get_top10_analysis)

# TC-6-01
def test_pe_ratio_reasonable():
    info = get_stock_info("AAPL")
    pe   = info.get("pe_ratio", 0)
    assert isinstance(pe, float)
    assert 0 <= pe < 1000

# TC-6-02
def test_benchmark_returns_structure():
    from core.market_data import get_benchmark_returns
    bench = get_benchmark_returns(30)
    assert "nasdaq_1d" in bench
    assert "sp500_1d"  in bench
    assert "qqq_history" in bench
    assert isinstance(bench["qqq_history"], list)

# TC-6-03
def test_drawdown_calculation():
    nav    = [100, 105, 108, 100, 95, 98, 102]
    result = calc_drawdown(nav)
    assert result["max_drawdown_pct"] < 0
    assert abs(result["max_drawdown_pct"] - (-12.04)) < 1.0
    assert len(result["series"]) == 7

# TC-6-04
def test_drawdown_flat():
    nav    = [100, 100, 100]
    result = calc_drawdown(nav)
    assert result["max_drawdown_pct"] == 0.0

# TC-6-05
def test_predict_next_day_range():
    hist       = get_price_history("AAPL", 30)
    prediction = predict_next_day(hist)
    assert isinstance(prediction, float)
    assert -5.0 <= prediction <= 5.0

# TC-6-06
def test_predict_insufficient_data():
    df     = pd.DataFrame({"Close": [100.0, 101.0]})
    result = predict_next_day(df)
    assert result == 0.0

# TC-6-07
def test_pct_change_positive():
    df = pd.DataFrame({"Close": [100.0, 102.0]})
    assert pct_change(df, 1) == 2.0

# TC-6-08
def test_pct_change_negative():
    df = pd.DataFrame({"Close": [100.0, 90.0]})
    assert pct_change(df, 1) == -10.0

# TC-6-09
def test_top10_analysis_disclaimer():
    """top10 分析結果包含預測欄位，需搭配免責聲明使用"""
    top10 = get_top10_analysis()
    assert len(top10) == 10
    for item in top10:
        assert "predicted_next_pct" in item
        assert "pe_ratio"           in item

# TC-6-10
def test_top10_ranks_correct():
    top10 = get_top10_analysis()
    ranks = [t["rank"] for t in top10]
    assert ranks == list(range(1, 11))
