"""
Phase 4 - 報告 View（JSON → HTML Email）
只負責渲染，不含任何業務邏輯
"""
from jinja2 import Template

EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; background:#f4f6f8; margin:0; padding:20px; }
  .card { background:#fff; border-radius:12px; padding:20px; margin-bottom:16px;
          box-shadow:0 2px 8px rgba(0,0,0,0.08); }
  h1 { color:#1a237e; font-size:1.5rem; margin:0 0 4px; }
  h2 { color:#283593; font-size:1.1rem; border-bottom:2px solid #e8eaf6;
       padding-bottom:6px; margin-bottom:12px; }
  .meta { color:#90a4ae; font-size:0.82rem; }
  .kpi-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
  .kpi { background:#f5f7ff; border-radius:8px; padding:12px; text-align:center; }
  .kpi .val { font-size:1.4rem; font-weight:700; color:#1565c0; }
  .kpi .lbl { font-size:0.75rem; color:#78909c; margin-top:2px; }
  .pos-up   { color:#2e7d32; font-weight:600; }
  .pos-down { color:#c62828; font-weight:600; }
  table { width:100%; border-collapse:collapse; font-size:0.88rem; }
  th { background:#e8eaf6; color:#3949ab; padding:8px 10px; text-align:left; }
  td { padding:7px 10px; border-bottom:1px solid #f0f0f0; }
  tr:hover td { background:#fafafa; }
  .badge { display:inline-block; padding:2px 8px; border-radius:10px;
           font-size:0.75rem; font-weight:600; }
  .badge-up   { background:#e8f5e9; color:#2e7d32; }
  .badge-down { background:#ffebee; color:#c62828; }
  .disclaimer { background:#fff8e1; border-left:4px solid #ffc107;
                padding:10px 14px; border-radius:4px; font-size:0.82rem; color:#5d4037; }
</style>
</head>
<body>

<div class="card">
  <h1>📊 AlpacaBot 每日報告</h1>
  <p class="meta">帳戶：{{ report.account_name }} ｜ 日期：{{ report.report_date }} ｜ 策略：{{ report.active_strategy }}</p>
</div>

<div class="card">
  <h2>💼 帳戶摘要</h2>
  <div class="kpi-grid">
    <div class="kpi">
      <div class="val">${{ "{:,.0f}".format(report.summary.cash) }}</div>
      <div class="lbl">現金水位</div>
    </div>
    <div class="kpi">
      <div class="val">${{ "{:,.0f}".format(report.summary.portfolio_value) }}</div>
      <div class="lbl">帳戶總值</div>
    </div>
    <div class="kpi">
      <div class="val {{ 'pos-up' if report.summary.daily_pnl >= 0 else 'pos-down' }}">
        {{ '+' if report.summary.daily_pnl >= 0 else '' }}{{ "{:,.0f}".format(report.summary.daily_pnl) }}
        ({{ '{:+.2f}'.format(report.summary.daily_pnl_pct) }}%)
      </div>
      <div class="lbl">今日損益</div>
    </div>
  </div>
</div>

{% if report.positions %}
<div class="card">
  <h2>📋 持倉清單</h2>
  <table>
    <tr><th>股票</th><th>股數</th><th>現價</th><th>市值</th><th>1D%</th><th>1W%</th><th>1M%</th><th>P/E</th></tr>
    {% for p in report.positions %}
    <tr>
      <td><b>{{ p.symbol }}</b></td>
      <td>{{ "{:,.0f}".format(p.qty) }}</td>
      <td>${{ "{:,.2f}".format(p.current_price) }}</td>
      <td>${{ "{:,.0f}".format(p.market_value) }}</td>
      <td class="{{ 'pos-up' if p.pct_1d >= 0 else 'pos-down' }}">{{ '{:+.2f}'.format(p.pct_1d) }}%</td>
      <td class="{{ 'pos-up' if p.pct_1w >= 0 else 'pos-down' }}">{{ '{:+.2f}'.format(p.pct_1w) }}%</td>
      <td class="{{ 'pos-up' if p.pct_1m >= 0 else 'pos-down' }}">{{ '{:+.2f}'.format(p.pct_1m) }}%</td>
      <td>{{ p.pe_ratio if p.pe_ratio else 'N/A' }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
{% endif %}

<div class="card">
  <h2>🏆 NASDAQ 市值前十排名</h2>
  <table>
    <tr><th>#</th><th>股票</th><th>現價</th><th>市值(B)</th><th>1日漲跌</th><th>P/E</th><th>次日預測</th></tr>
    {% for t in report.top10_nasdaq %}
    <tr>
      <td>{{ t.rank }}</td>
      <td><b>{{ t.symbol }}</b><br><small style="color:#90a4ae">{{ t.name[:20] }}</small></td>
      <td>${{ "{:,.2f}".format(t.price) }}</td>
      <td>${{ "{:,.0f}".format(t.market_cap_b) }}B</td>
      <td class="{{ 'pos-up' if t.pct_1d >= 0 else 'pos-down' }}">{{ '{:+.2f}'.format(t.pct_1d) }}%</td>
      <td>{{ t.pe_ratio if t.pe_ratio else 'N/A' }}</td>
      <td>
        <span class="badge {{ 'badge-up' if t.predicted_next_pct >= 0 else 'badge-down' }}">
          {{ '{:+.2f}'.format(t.predicted_next_pct) }}%
        </span>
      </td>
    </tr>
    {% endfor %}
  </table>
</div>

<div class="card">
  <h2>👁 我的關注清單</h2>
  {% for cat, symbols in report.watchlist.items() %}
  <p><b>{{ cat }}</b>：{{ symbols | join('、') }}</p>
  {% endfor %}
</div>

<div class="card">
  <h2>📈 基準對比</h2>
  <div class="kpi-grid">
    <div class="kpi">
      <div class="val {{ 'pos-up' if report.benchmark.nasdaq_1d_pct >= 0 else 'pos-down' }}">
        {{ '{:+.2f}'.format(report.benchmark.nasdaq_1d_pct) }}%</div>
      <div class="lbl">NASDAQ 今日</div>
    </div>
    <div class="kpi">
      <div class="val {{ 'pos-up' if report.benchmark.sp500_1d_pct >= 0 else 'pos-down' }}">
        {{ '{:+.2f}'.format(report.benchmark.sp500_1d_pct) }}%</div>
      <div class="lbl">S&P500 今日</div>
    </div>
    <div class="kpi">
      <div class="val {{ 'pos-up' if report.summary.daily_pnl_pct >= 0 else 'pos-down' }}">
        {{ '{:+.2f}'.format(report.summary.daily_pnl_pct) }}%</div>
      <div class="lbl">我的帳戶今日</div>
    </div>
  </div>
</div>

<div class="disclaimer">{{ report.disclaimer }}</div>
<p style="text-align:center;color:#b0bec5;font-size:0.78rem;margin-top:16px;">
  由 AlpacaBot 自動生成 | {{ report.generated_at }}
</p>
</body>
</html>
"""

def render_email_html(report: dict) -> str:
    tpl = Template(EMAIL_TEMPLATE)
    return tpl.render(report=type("R", (), report)())

def render_trade_alert(trade: dict) -> str:
    side_emoji = "🟢 買入" if trade["side"] == "buy" else "🔴 賣出"
    return f"""
    <div style="font-family:Arial;padding:16px;background:#fff;border-radius:8px;border-left:4px solid {'#2e7d32' if trade['side']=='buy' else '#c62828'}">
      <h2 style="margin:0">{side_emoji} 交易通知</h2>
      <p>股票：<b>{trade['symbol']}</b></p>
      <p>數量：{trade['qty']} 股</p>
      <p>成交價：${trade.get('price', 'N/A')}</p>
      <p>時間：{trade.get('time', '')}</p>
      <p style="color:#9e9e9e;font-size:0.8rem">⚠️ 本通知僅供參考，不構成投資建議。</p>
    </div>
    """

def render_trade_summary_email(summary: dict) -> str:
    """
    交易完成後的摘要 Email
    summary 結構：
    {
      account_name, trade_date, orders: [...],
      account_before: {portfolio_value, cash},
      account_after:  {portfolio_value, cash},
    }
    """
    orders      = summary.get("orders", [])
    acc_name    = summary.get("account_name", "")
    trade_date  = summary.get("trade_date", "")
    before      = summary.get("account_before", {})
    after       = summary.get("account_after",  {})

    pnl         = after.get("portfolio_value", 0) - before.get("portfolio_value", 0)
    pnl_pct     = (pnl / before["portfolio_value"] * 100) if before.get("portfolio_value") else 0
    pnl_color   = "#2e7d32" if pnl >= 0 else "#c62828"
    pnl_sign    = "+" if pnl >= 0 else ""

    buys  = [o for o in orders if o.get("side") == "buy"]
    sells = [o for o in orders if o.get("side") == "sell"]

    def order_rows(order_list):
        rows = ""
        for o in order_list:
            amt   = o.get("amount", 0)
            pl    = o.get("pnl", None)
            pl_pct= o.get("pnl_pct", None)
            pl_html = ""
            if pl is not None:
                c = "#2e7d32" if pl >= 0 else "#c62828"
                s = "+" if pl >= 0 else ""
                pl_html = f'<td style="color:{c};font-weight:600">{s}${pl:,.0f}<br><small>{s}{pl_pct:.2f}%</small></td>'
            else:
                pl_html = "<td>—</td>"
            rows += f"""
            <tr>
              <td><b>{o.get('symbol','')}</b></td>
              <td>{int(o.get('qty', 0))} 股</td>
              <td>${o.get('price', 0):,.2f}</td>
              <td>${amt:,.0f}</td>
              {pl_html}
              <td style="color:#90a4ae;font-size:0.8rem">{o.get('status','')}</td>
            </tr>"""
        return rows

    sells_section = ""
    if sells:
        sells_section = f"""
        <div class="card">
          <h2>🔴 賣出明細</h2>
          <table>
            <tr><th>股票</th><th>股數</th><th>成交價</th><th>金額</th><th>損益</th><th>狀態</th></tr>
            {order_rows(sells)}
          </table>
        </div>"""

    buys_section = ""
    if buys:
        buys_section = f"""
        <div class="card">
          <h2>🟢 買入明細</h2>
          <table>
            <tr><th>股票</th><th>股數</th><th>成交價</th><th>金額</th><th>損益</th><th>狀態</th></tr>
            {order_rows(buys)}
          </table>
        </div>"""

    no_trade = ""
    if not orders:
        no_trade = '<div class="card"><p style="color:#90a4ae">今日持倉已是最佳配置，無需調整。</p></div>'

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8">
<style>
  body {{ font-family:'Segoe UI',Arial,sans-serif; background:#f4f6f8; margin:0; padding:20px; }}
  .card {{ background:#fff; border-radius:12px; padding:20px; margin-bottom:16px;
           box-shadow:0 2px 8px rgba(0,0,0,0.08); }}
  h1 {{ color:#1a237e; font-size:1.4rem; margin:0 0 4px; }}
  h2 {{ color:#283593; font-size:1.05rem; border-bottom:2px solid #e8eaf6;
        padding-bottom:6px; margin-bottom:12px; }}
  .meta {{ color:#90a4ae; font-size:0.82rem; }}
  .kpi-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }}
  .kpi {{ background:#f5f7ff; border-radius:8px; padding:12px; text-align:center; }}
  .kpi .val {{ font-size:1.3rem; font-weight:700; color:#1565c0; }}
  .kpi .lbl {{ font-size:0.75rem; color:#78909c; margin-top:2px; }}
  table {{ width:100%; border-collapse:collapse; font-size:0.88rem; }}
  th {{ background:#e8eaf6; color:#3949ab; padding:8px 10px; text-align:left; }}
  td {{ padding:7px 10px; border-bottom:1px solid #f0f0f0; }}
  .disclaimer {{ background:#fff8e1; border-left:4px solid #ffc107;
                 padding:10px 14px; border-radius:4px; font-size:0.82rem; color:#5d4037; }}
</style></head>
<body>

<div class="card">
  <h1>🤖 AlpacaBot 交易執行通知</h1>
  <p class="meta">帳戶：{acc_name} ｜ 日期：{trade_date}</p>
</div>

<div class="card">
  <h2>📊 帳戶變動</h2>
  <div class="kpi-grid">
    <div class="kpi">
      <div class="val">${after.get('portfolio_value', 0):,.0f}</div>
      <div class="lbl">最新帳戶總值</div>
    </div>
    <div class="kpi">
      <div class="val">${after.get('cash', 0):,.0f}</div>
      <div class="lbl">可用現金</div>
    </div>
    <div class="kpi">
      <div class="val" style="color:{pnl_color}">{pnl_sign}${pnl:,.0f}<br>
        <small>({pnl_sign}{pnl_pct:.2f}%)</small>
      </div>
      <div class="lbl">本次交易損益</div>
    </div>
  </div>
</div>

{sells_section}
{buys_section}
{no_trade}

<div class="disclaimer">⚠️ 本通知僅供資訊記錄，不構成投資建議。投資有風險，請審慎評估。</div>
<p style="text-align:center;color:#b0bec5;font-size:0.78rem;margin-top:12px;">
  由 AlpacaBot 自動生成
</p>
</body></html>"""
