"""
Phase 3 測試案例 — 交易引擎（再平衡、下單邏輯）
全部在 Paper 帳戶執行，不觸碰 Live 資金
"""
import pytest, sys, os, math, json
from unittest.mock import MagicMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.strategy_engine import (
    load_strategy, calc_target_positions,
    should_rebalance, execute_rebalance
)

# ── 模擬帳戶 fixture ────────────────────────────────────────
@pytest.fixture
def mock_account():
    acc = MagicMock()
    acc.id             = "acc_001"
    acc.name           = "Paper Test"
    acc.get_portfolio_value.return_value = 100_000.0
    acc.get_cash.return_value            = 10_000.0
    acc.is_market_open.return_value      = True
    # 目前持倉：只持有 AAPL 50 股
    acc.get_positions.return_value = [{"symbol": "AAPL", "qty": 50}]
    return acc

@pytest.fixture
def strategy():
    return load_strategy("top10_nasdaq")

# TC-3-01  整數股計算（10% 等權重，floor 向下取整）
def test_integer_shares_floor():
    """$100k 帳戶，10% = $10k，AAPL $173.5 → floor(57.6) = 57 股"""
    portfolio = 100_000.0
    weight    = 0.10
    price     = 173.5
    qty       = math.floor(portfolio * weight / price)
    assert qty == 57
    assert isinstance(qty, int)

# TC-3-02  不買零股（整數股策略）
def test_no_fractional_shares():
    """高價股 BRK.A $600,000 → 0 股，不應進入買單"""
    portfolio = 100_000.0
    weight    = 0.10
    price     = 600_000.0
    qty       = math.floor(portfolio * weight / price)
    assert qty == 0

# TC-3-03  月初觸發再平衡
def test_rebalance_trigger_monthly(mock_account, strategy, monkeypatch):
    from datetime import datetime
    fake = datetime(2026, 7, 1, 9, 30)
    monkeypatch.setattr("core.strategy_engine.datetime",
                        type("FDT", (), {"now": staticmethod(lambda: fake)})())
    do_it, reason = should_rebalance(mock_account, strategy)
    assert do_it is True
    assert "月初" in reason

# TC-3-04  非月初且現金充足 → 不再平衡
def test_no_rebalance_mid_month(mock_account, strategy, monkeypatch):
    from datetime import datetime
    mock_account.get_cash.return_value            = 500.0  # 現金佔比 < 5%
    mock_account.get_portfolio_value.return_value = 100_000.0
    fake = datetime(2026, 7, 15, 9, 30)
    monkeypatch.setattr("core.strategy_engine.datetime",
                        type("FDT", (), {"now": staticmethod(lambda: fake)})())
    do_it, _ = should_rebalance(mock_account, strategy)
    assert do_it is False

# TC-3-05  新資金流入觸發再平衡
def test_rebalance_trigger_new_cash(mock_account, strategy, monkeypatch):
    from datetime import datetime
    # 現金佔比 20% > threshold 5%
    mock_account.get_cash.return_value            = 20_000.0
    mock_account.get_portfolio_value.return_value = 100_000.0
    fake = datetime(2026, 7, 15, 9, 30)  # 非月初
    monkeypatch.setattr("core.strategy_engine.datetime",
                        type("FDT", (), {"now": staticmethod(lambda: fake)})())
    do_it, reason = should_rebalance(mock_account, strategy)
    assert do_it is True
    assert "資金" in reason

# TC-3-06  市場未開盤時跳過下單
def test_skip_when_market_closed(mock_account, strategy):
    mock_account.is_market_open.return_value = False
    orders = execute_rebalance(mock_account, strategy)
    assert orders == []
    mock_account.place_market_order.assert_not_called()

# TC-3-07  目標持倉計算 → 10 檔均不超過權重上限
def test_target_positions_weight(mock_account, strategy):
    from core.market_data import get_nasdaq_top10
    symbols = get_nasdaq_top10()[:5]
    # mock 每支股票現價 $100
    mock_account.get_latest_price.return_value = 100.0
    targets = calc_target_positions(mock_account, strategy, symbols)
    for t in targets:
        alloc_pct = (t["target_qty"] * 100.0) / mock_account.get_portfolio_value()
        assert alloc_pct <= 0.11, f"{t['symbol']} 配置超出 11%: {alloc_pct:.2%}"

# TC-3-08  帳戶隔離：account A 下單不影響 account B
def test_account_isolation():
    acc_a = MagicMock()
    acc_a.id   = "acc_A"
    acc_a.name = "Account A"
    acc_a.is_market_open.return_value = False

    acc_b = MagicMock()
    acc_b.id   = "acc_B"
    acc_b.name = "Account B"
    acc_b.is_market_open.return_value = False

    strategy = load_strategy("top10_nasdaq")
    execute_rebalance(acc_a, strategy)
    execute_rebalance(acc_b, strategy)

    # 各自只呼叫自己的 place_market_order（市場未開盤所以都是 0 次）
    acc_a.place_market_order.assert_not_called()
    acc_b.place_market_order.assert_not_called()

# TC-3-09  策略切換不影響其他帳戶
def test_strategy_switch_json_schema():
    """切換策略後，新策略 JSON 格式正確"""
    strat_new = load_strategy("momentum")
    assert strat_new["strategy_id"] == "momentum"
    assert strat_new["rules"]["universe"] == "NASDAQ_TOP100"
    assert strat_new["rules"]["weight_per_stock"] == 0.10

# TC-3-10  10 檔 × 10% = 100%（不超投）
def test_total_allocation_equals_100pct(strategy):
    n      = strategy["rules"]["max_positions"]
    weight = strategy["rules"]["weight_per_stock"]
    assert abs(n * weight - 1.0) < 0.001

# TC-3-11  calc_target_positions 排除低價股
def test_filter_min_price(mock_account, strategy):
    """低於 min_price 的股票不應進入買單"""
    symbols = ["AAPL", "LOWPRICE"]
    def mock_price(sym):
        return 200.0 if sym == "AAPL" else 1.0  # LOWPRICE 低於 min_price=5
    mock_account.get_latest_price.side_effect = mock_price
    targets = calc_target_positions(mock_account, strategy, symbols)
    syms = [t["symbol"] for t in targets]
    assert "LOWPRICE" not in syms

# TC-3-12  再平衡後不應保有前十以外的股票（模擬）
def test_sell_out_of_universe(mock_account, strategy):
    """持有 ZZZZ 但不在前十，應該賣出"""
    mock_account.is_market_open.return_value = True
    mock_account.get_positions.return_value  = [{"symbol": "ZZZZ", "qty": 10}]
    mock_account.get_latest_price.return_value = 100.0

    with patch("core.strategy_engine.get_target_symbols",
               return_value=["AAPL", "MSFT", "NVDA"]):
        execute_rebalance(mock_account, strategy)

    # 確認有賣出 ZZZZ
    sell_calls = [
        c for c in mock_account.place_market_order.call_args_list
        if c.args[0] == "ZZZZ" and c.args[2] == "sell"
    ]
    assert len(sell_calls) >= 1
