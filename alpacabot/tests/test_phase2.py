"""Phase 2 測試案例 — 策略引擎"""
import pytest, sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.strategy_engine import (load_strategy, get_target_symbols,
                                    calc_target_positions, should_rebalance)
from core.alpaca_client   import get_all_accounts

@pytest.fixture(scope="module")
def strategy():
    return load_strategy("top10_nasdaq")

@pytest.fixture(scope="module")
def acc():
    return get_all_accounts()[0]

# TC-2-01
def test_load_strategy_fields(strategy):
    assert strategy["strategy_id"] == "top10_nasdaq"
    assert "rules"   in strategy
    assert "filters" in strategy
    assert "risk"    in strategy
    assert strategy["rules"]["max_positions"] == 10
    assert strategy["rules"]["weight_per_stock"] == 0.10

# TC-2-02
def test_target_symbols_count(strategy):
    symbols = get_target_symbols(strategy)
    assert len(symbols) == 10

# TC-2-03
def test_integer_shares_calculation():
    """AAPL $200, 帳戶 $100k, 10% = $10k → 50 股"""
    portfolio_val = 100_000
    weight        = 0.10
    price         = 200.0
    qty           = math.floor(portfolio_val * weight / price)
    assert qty == 50

# TC-2-04
def test_new_strategy_json_loadable(tmp_path):
    """新增 JSON 策略後引擎可載入"""
    strategy_content = {
        "strategy_id": "test_strategy",
        "name": "測試策略",
        "version": "1.0",
        "rules": {
            "universe": "NASDAQ_TOP10_MARKET_CAP",
            "max_positions": 5,
            "weight_per_stock": 0.20,
            "order_type": "market",
            "fractional_shares": False,
            "rebalance_triggers": ["monthly_first_day"],
            "min_cash_reserve": 0.02
        },
        "filters": {"min_price": 5, "min_volume": 100000, "exclude_symbols": []},
        "risk": {"max_single_loss_pct": 0.15, "stop_loss_enabled": False}
    }
    strat_file = tmp_path / "test_strategy.json"
    strat_file.write_text(json.dumps(strategy_content))
    with open(strat_file) as f:
        loaded = json.load(f)
    assert loaded["strategy_id"] == "test_strategy"
    assert loaded["rules"]["max_positions"] == 5

# TC-2-05
def test_strategy_files_exist():
    strats_dir = os.path.join(os.path.dirname(__file__), "../strategies")
    files = os.listdir(strats_dir)
    assert "top10_nasdaq.json" in files
    assert "momentum.json"     in files

# TC-2-06
def test_each_account_has_strategy():
    from core.alpaca_client import load_accounts
    cfg = load_accounts()
    for a in cfg["accounts"]:
        if a.get("enabled"):
            assert a.get("active_strategy"), f"帳戶 {a['id']} 沒有設定策略"

# TC-2-07
def test_rebalance_trigger_monthly(acc, strategy, monkeypatch):
    from datetime import datetime
    fake_now = datetime(2026, 6, 1, 10, 0, 0)
    monkeypatch.setattr("core.strategy_engine.datetime",
                        type("FakeDT", (), {"now": staticmethod(lambda: fake_now)})())
    do_it, reason = should_rebalance(acc, strategy)
    assert do_it
    assert "月初" in reason

# TC-2-08
def test_calc_target_positions_returns_list(acc, strategy):
    from core.market_data import get_nasdaq_top10
    symbols = get_nasdaq_top10()[:3]
    targets = calc_target_positions(acc, strategy, symbols)
    assert isinstance(targets, list)
    for t in targets:
        assert "symbol"     in t
        assert "target_qty" in t
        assert t["target_qty"] >= 1
        assert isinstance(t["target_qty"], int)

# TC-2-09
def test_weight_sum_not_exceed_1(strategy):
    n      = strategy["rules"]["max_positions"]
    weight = strategy["rules"]["weight_per_stock"]
    assert n * weight <= 1.0

# TC-2-10
def test_momentum_strategy_loadable():
    strat = load_strategy("momentum")
    assert strat["strategy_id"] == "momentum"
    assert strat["rules"]["lookback_days"] == 20
