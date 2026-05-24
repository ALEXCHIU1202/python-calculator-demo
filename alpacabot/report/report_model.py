"""
Phase 4 - 報告 Model（產生 JSON）
Model 與 View 完全分離，Model 只負責產生資料
"""
import json, os
from datetime import datetime, date
from core.alpaca_client import get_all_accounts, load_accounts
from core.market_data import (
    get_top10_analysis, get_benchmark_returns,
    get_price_history, pct_change, calc_drawdown
)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "../reports")
DISCLAIMER = "⚠️ 本報告僅供資訊整理與研究參考，不構成投資建議。投資人應自行評估風險。"

def build_report(account_id: str = None, report_date: str = None) -> list[dict]:
    accounts = get_all_accounts()
    if account_id:
        accounts = [a for a in accounts if a.id == account_id]
    if not report_date:
        report_date = date.today().strftime("%Y-%m-%d")

    top10    = get_top10_analysis()
    bench    = get_benchmark_returns(days=60)
    cfg      = load_accounts()
    watchlist = cfg.get("watchlist", {})

    reports = []
    for acc in accounts:
        print(f"📊 產生報告: {acc.name}")
        try:
            account_info   = acc.get_account()
            cash           = float(account_info.cash)
            portfolio_val  = float(account_info.portfolio_value)
            equity         = float(account_info.equity)
            last_equity    = float(account_info.last_equity)
            daily_pnl      = equity - last_equity
            daily_pnl_pct  = (daily_pnl / last_equity * 100) if last_equity else 0

            positions_raw  = acc.get_positions()
            positions      = []
            for p in positions_raw:
                hist   = get_price_history(p["symbol"], 30)
                positions.append({
                    **p,
                    "pct_1d": pct_change(hist, 1),
                    "pct_1w": pct_change(hist, 5),
                    "pct_1m": pct_change(hist, 21),
                    "pe_ratio": next((t["pe_ratio"] for t in top10 if t["symbol"] == p["symbol"]), 0),
                })

            # NAV 歷史（用 portfolio_value 模擬）
            nav_history = [portfolio_val]
            dd_data     = calc_drawdown(nav_history)

            report = {
                "report_date":    report_date,
                "generated_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "account_id":     acc.id,
                "account_name":   acc.name,
                "active_strategy": acc.active_strategy,
                "summary": {
                    "cash":             round(cash, 2),
                    "portfolio_value":  round(portfolio_val, 2),
                    "equity":           round(equity, 2),
                    "daily_pnl":        round(daily_pnl, 2),
                    "daily_pnl_pct":    round(daily_pnl_pct, 2),
                    "max_drawdown_pct": dd_data["max_drawdown_pct"],
                },
                "positions":     positions,
                "top10_nasdaq":  top10,
                "watchlist":     watchlist,
                "benchmark":     {
                    "nasdaq_1d_pct": bench.get("nasdaq_1d", 0),
                    "nasdaq_1w_pct": bench.get("nasdaq_1w", 0),
                    "sp500_1d_pct":  bench.get("sp500_1d", 0),
                    "sp500_1w_pct":  bench.get("sp500_1w", 0),
                    "qqq_history":   bench.get("qqq_history", []),
                    "spy_history":   bench.get("spy_history", []),
                },
                "disclaimer": DISCLAIMER,
            }
            reports.append(report)
            _save_report(report, report_date)
        except Exception as e:
            print(f"  ❌ 帳戶 {acc.id} 報告失敗: {e}")

    return reports

def _save_report(report: dict, report_date: str):
    folder = os.path.join(REPORTS_DIR, report_date)
    os.makedirs(folder, exist_ok=True)
    acc_id = report["account_id"]
    path   = os.path.join(folder, f"report_{acc_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  ✅ 報告已儲存: {path}")

def load_report(account_id: str, report_date: str) -> dict | None:
    path = os.path.join(REPORTS_DIR, report_date, f"report_{account_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_report_dates() -> list[str]:
    if not os.path.exists(REPORTS_DIR):
        return []
    return sorted(os.listdir(REPORTS_DIR), reverse=True)

if __name__ == "__main__":
    build_report()
