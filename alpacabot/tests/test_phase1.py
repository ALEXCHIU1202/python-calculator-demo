"""Phase 1 測試案例"""
import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.alpaca_client import get_all_accounts, load_accounts
from core.market_data   import (get_nasdaq_top10, get_stock_info,
                                 get_price_history, pct_change, get_top10_analysis)

@pytest.fixture(scope="module")
def acc():
    accounts = get_all_accounts()
    assert len(accounts) > 0, "需要至少一個帳戶"
    return accounts[0]

# TC-1-01
def test_account_status_active(acc):
    account = acc.get_account()
    assert str(account.status) in ["ACTIVE", "AccountStatus.ACTIVE"]

# TC-1-02
def test_cash_positive(acc):
    cash = acc.get_cash()
    assert isinstance(cash, float)
    assert cash >= 0

# TC-1-03
def test_positions_format(acc):
    positions = acc.get_positions()
    assert isinstance(positions, list)
    for p in positions:
        assert "symbol"       in p
        assert "qty"          in p
        assert "market_value" in p

# TC-1-04
def test_latest_price_positive(acc):
    price = acc.get_latest_price("AAPL")
    assert isinstance(price, float)
    assert price > 0

# TC-1-05
def test_historical_bars(acc):
    bars = acc.get_bars("AAPL", days=30)
    assert len(bars) >= 15  # 扣除假日至少 15 根
    assert "close" in bars[0]

# TC-1-06
def test_nasdaq_top10_count():
    symbols = get_nasdaq_top10()
    assert len(symbols) == 10
    assert "AAPL" in symbols

# TC-1-07
def test_multi_account_load():
    cfg = load_accounts()
    assert "accounts" in cfg
    assert len(cfg["accounts"]) >= 1
    for a in cfg["accounts"]:
        assert "id"         in a
        assert "api_key"    in a
        assert "api_secret" in a

# TC-1-08
def test_paper_url(acc):
    assert "paper-api" in acc.base_url or "api.alpaca" in acc.base_url

# TC-1-09
def test_invalid_key_raises():
    from core.alpaca_client import AlpacaAccount
    from alpaca.common.exceptions import APIError
    bad_cfg = {
        "id": "bad", "name": "bad",
        "api_key": "BADKEY", "api_secret": "BADSECRET",
        "base_url": "https://paper-api.alpaca.markets",
        "active_strategy": "", "email": "", "enabled": True
    }
    bad_acc = AlpacaAccount(bad_cfg)
    with pytest.raises(Exception):
        bad_acc.get_account()

# TC-1-10
def test_get_bars_returns_data():
    """yfinance 休市日也能取到資料"""
    hist = get_price_history("AAPL", 30)
    assert hist is not None
    assert len(hist) > 0

# TC-1-11
def test_pct_change_calculation():
    import pandas as pd
    df = pd.DataFrame({"Close": [100.0, 110.0, 105.0]})
    result = pct_change(df, 1)
    assert abs(result - (-4.55)) < 0.1  # (105-110)/110 * 100

# TC-1-12
def test_stock_info_has_fields():
    info = get_stock_info("AAPL")
    assert "symbol"    in info
    assert "price"     in info
    assert "pe_ratio"  in info
    assert info["symbol"] == "AAPL"
