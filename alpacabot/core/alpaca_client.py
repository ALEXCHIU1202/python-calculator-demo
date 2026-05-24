"""
Phase 1 - Alpaca API 封裝
支援 Paper & Live 環境，多帳戶
"""
import json, os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pytz

ACCOUNTS_PATH = os.path.join(os.path.dirname(__file__), "../accounts/accounts.json")

def load_accounts():
    with open(ACCOUNTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class AlpacaAccount:
    def __init__(self, config: dict):
        self.id       = config["id"]
        self.name     = config["name"]
        self.email    = config.get("email", "")
        self.enabled  = config.get("enabled", True)
        self.active_strategy = config.get("active_strategy", "")
        self.api_key  = config["api_key"]
        self.api_secret = config["api_secret"]
        self.base_url = config["base_url"]
        self.is_paper = "paper" in self.base_url

        self.trading = TradingClient(
            api_key=self.api_key,
            secret_key=self.api_secret,
            paper=self.is_paper
        )
        self.data = StockHistoricalDataClient(
            api_key=self.api_key,
            secret_key=self.api_secret
        )

    # ── 帳戶資訊 ──────────────────────────────
    def get_account(self):
        return self.trading.get_account()

    def get_cash(self) -> float:
        return float(self.get_account().cash)

    def get_portfolio_value(self) -> float:
        return float(self.get_account().portfolio_value)

    def get_positions(self) -> list[dict]:
        positions = self.trading.get_all_positions()
        result = []
        for p in positions:
            result.append({
                "symbol":       p.symbol,
                "qty":          float(p.qty),
                "avg_cost":     float(p.avg_entry_price),
                "current_price":float(p.current_price),
                "market_value": float(p.market_value),
                "unrealized_pnl": float(p.unrealized_pl),
                "unrealized_pnl_pct": float(p.unrealized_plpc) * 100,
            })
        return result

    # ── 下單 ────────────────────────────────────
    def place_market_order(self, symbol: str, qty: int, side: str) -> dict:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        req = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY
        )
        order = self.trading.submit_order(req)
        return {
            "order_id": str(order.id),
            "symbol":   order.symbol,
            "side":     side,
            "qty":      qty,
            "status":   str(order.status),
            "submitted_at": str(order.submitted_at)
        }

    def cancel_all_orders(self):
        self.trading.cancel_orders()

    # ── 市場資料 ────────────────────────────────
    def get_latest_price(self, symbol: str) -> float:
        req = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quote = self.data.get_stock_latest_quote(req)
        return float(quote[symbol].ask_price or quote[symbol].bid_price)

    def get_bars(self, symbol: str, days: int = 30) -> list[dict]:
        """優先用 Alpaca 數據 API；免費帳戶無法存取時自動切換 yfinance"""
        try:
            end   = datetime.now(pytz.UTC)
            start = end - timedelta(days=days + 10)
            req   = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start, end=end
            )
            bars   = self.data.get_stock_bars(req)
            result = []
            for b in bars[symbol]:
                result.append({
                    "date":   b.timestamp.strftime("%Y-%m-%d"),
                    "open":   float(b.open),
                    "high":   float(b.high),
                    "low":    float(b.low),
                    "close":  float(b.close),
                    "volume": int(b.volume),
                })
            return result[-days:]
        except Exception:
            import yfinance as yf
            df = yf.Ticker(symbol).history(period=f"{days+10}d").tail(days).reset_index()
            result = []
            for _, row in df.iterrows():
                result.append({
                    "date":   str(row["Date"])[:10],
                    "open":   float(row["Open"]),
                    "high":   float(row["High"]),
                    "low":    float(row["Low"]),
                    "close":  float(row["Close"]),
                    "volume": int(row["Volume"]),
                })
            return result

    def is_market_open(self) -> bool:
        clock = self.trading.get_clock()
        return clock.is_open

    def switch_strategy(self, strategy_id: str):
        cfg = load_accounts()
        for acc in cfg["accounts"]:
            if acc["id"] == self.id:
                acc["active_strategy"] = strategy_id
                self.active_strategy   = strategy_id
        with open(ACCOUNTS_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        print(f"[{self.name}] 策略已切換至 {strategy_id}")


def get_all_accounts() -> list[AlpacaAccount]:
    cfg = load_accounts()
    return [AlpacaAccount(a) for a in cfg["accounts"] if a.get("enabled", True)]
