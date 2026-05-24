"""
Phase 2 - 策略引擎
JSON 策略載入 → 計算目標部位 → 執行下單
新增策略只需新增 JSON，不改 Python
"""
import json, os, math, argparse
from datetime import datetime
from core.alpaca_client import get_all_accounts, AlpacaAccount
from core.market_data import get_nasdaq_top10, get_nasdaq_top100, get_price_history, pct_change

STRATEGIES_DIR = os.path.join(os.path.dirname(__file__), "../strategies")

def load_strategy(strategy_id: str) -> dict:
    path = os.path.join(STRATEGIES_DIR, f"{strategy_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Strategy not found: {strategy_id}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_target_symbols(strategy: dict) -> list[str]:
    universe = strategy["rules"]["universe"]
    if universe == "NASDAQ_TOP10_MARKET_CAP":
        return get_nasdaq_top10()
    elif universe == "NASDAQ_TOP100":
        symbols = get_nasdaq_top100()
        days    = strategy["rules"].get("lookback_days", 20)
        momentum = []
        for sym in symbols:
            try:
                hist = get_price_history(sym, days + 5)
                chg  = pct_change(hist, days)
                momentum.append((sym, chg))
            except:
                pass
        momentum.sort(key=lambda x: x[1], reverse=True)
        top_n = strategy["rules"].get("max_positions", 10)
        return [s for s, _ in momentum[:top_n]]
    return []

def calc_target_positions(account: AlpacaAccount, strategy: dict, symbols: list[str]) -> list[dict]:
    portfolio_value = account.get_portfolio_value()
    weight          = strategy["rules"]["weight_per_stock"]
    filters         = strategy.get("filters", {})
    exclude         = filters.get("exclude_symbols", [])
    min_price       = filters.get("min_price", 0)
    targets = []
    for sym in symbols:
        if sym in exclude:
            continue
        try:
            price = account.get_latest_price(sym)
            if price < min_price:
                continue
            alloc_usd = portfolio_value * weight
            qty       = math.floor(alloc_usd / price)
            if qty < 1:
                continue
            targets.append({"symbol": sym, "target_qty": qty, "price": price})
        except Exception as e:
            print(f"  ⚠️ {sym} 取價失敗: {e}")
    return targets

def execute_rebalance(account: AlpacaAccount, strategy: dict) -> list[dict]:
    if not account.is_market_open():
        print(f"[{account.name}] 市場未開盤，跳過下單")
        return []
    symbols  = get_target_symbols(strategy)
    targets  = calc_target_positions(account, strategy, symbols)
    current  = {p["symbol"]: p["qty"] for p in account.get_positions()}
    orders   = []
    target_map = {t["symbol"]: t for t in targets}

    # 賣出不在目標清單的持倉
    for sym, qty in current.items():
        if sym not in target_map:
            print(f"  🔴 賣出 {sym} x {int(qty)}")
            try:
                o = account.place_market_order(sym, int(qty), "sell")
                orders.append(o)
            except Exception as e:
                print(f"  ❌ 賣出 {sym} 失敗: {e}")

    # 調整至目標數量
    for t in targets:
        sym, target_qty = t["symbol"], t["target_qty"]
        current_qty = int(current.get(sym, 0))
        diff = target_qty - current_qty
        if diff > 0:
            print(f"  🟢 買入 {sym} x {diff}")
            try:
                o = account.place_market_order(sym, diff, "buy")
                orders.append(o)
            except Exception as e:
                print(f"  ❌ 買入 {sym} 失敗: {e}")
        elif diff < 0:
            print(f"  🔴 減持 {sym} x {abs(diff)}")
            try:
                o = account.place_market_order(sym, abs(diff), "sell")
                orders.append(o)
            except Exception as e:
                print(f"  ❌ 減持 {sym} 失敗: {e}")
    return orders

def should_rebalance(account: AlpacaAccount, strategy: dict) -> tuple[bool, str]:
    triggers = strategy["rules"].get("rebalance_triggers", [])
    today    = datetime.now()

    if "monthly_first_day" in triggers and today.day == 1:
        return True, "每月初再平衡"

    if "new_cash_inflow" in triggers:
        threshold = strategy["rules"].get("new_cash_threshold_pct", 0.05)
        cash      = account.get_cash()
        portfolio = account.get_portfolio_value()
        if portfolio > 0 and cash / portfolio > threshold:
            return True, f"新資金流入（現金佔比 {cash/portfolio:.1%}）"

    return False, ""

def run_daily(mode: str = "daily"):
    accounts = get_all_accounts()
    print(f"\n{'='*50}")
    print(f"AlpacaBot 執行 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"帳戶數量: {len(accounts)}")
    print(f"{'='*50}")

    all_results = []
    for acc in accounts:
        print(f"\n📌 帳戶: {acc.name} ({acc.id})")
        try:
            strategy = load_strategy(acc.active_strategy)
            print(f"   策略: {strategy['name']}")
            do_rebalance, reason = should_rebalance(acc, strategy)
            if do_rebalance or mode == "force":
                print(f"   ♻️  觸發再平衡: {reason or '手動'}")
                orders = execute_rebalance(acc, strategy)
            else:
                print("   ⏭️  今日不需再平衡")
                orders = []
            all_results.append({"account_id": acc.id, "orders": orders, "success": True})
        except Exception as e:
            print(f"   ❌ 帳戶執行失敗: {e}")
            all_results.append({"account_id": acc.id, "error": str(e), "success": False})

    return all_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="daily", choices=["daily", "force"])
    args = parser.parse_args()
    run_daily(args.mode)
