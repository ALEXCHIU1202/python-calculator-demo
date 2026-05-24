import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import yfinance as yf
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.config.REPORT_DIR.mkdir(parents=True, exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(str(config.TEMPLATE_DIR)))

    def generate(self, analysis: Dict) -> Tuple[str, Path]:
        market_data = self._fetch_market_data()
        now = datetime.now()
        articles = analysis['articles']

        template = self.env.get_template('report_template.html')
        html = template.render(
            date=now.strftime('%Y年%m月%d日'),
            weekday=['一', '二', '三', '四', '五', '六', '日'][now.weekday()],
            time=now.strftime('%H:%M'),
            market_data=market_data,
            articles=articles,
            articles_json=json.dumps(articles, ensure_ascii=False),
            market_outlook=analysis['market_outlook'],
            stats=analysis['stats'],
            high_impact=[a for a in articles if a.get('impact_score', 0) >= 7],
            market_moving=[a for a in articles if a.get('is_market_moving')],
        )

        filename = f"report_{now.strftime('%Y%m%d_%H%M')}.html"
        path = self.config.REPORT_DIR / filename
        path.write_text(html, encoding='utf-8')
        logger.info(f"報告已儲存：{path}")
        return html, path

    # ── Market data ───────────────────────────────────────────────────────────

    def _fetch_market_data(self) -> List[Dict]:
        results: List[Dict] = []
        for ticker, info in self.config.MARKET_INDICES.items():
            base = {'ticker': ticker, 'name': info['name'], 'region': info['region']}
            try:
                fast = yf.Ticker(ticker).fast_info
                price = fast.last_price
                prev = fast.previous_close
                change = price - prev
                pct = change / prev * 100
                results.append({
                    **base,
                    'price': round(price, 2),
                    'change': round(change, 2),
                    'change_pct': round(pct, 2),
                    'up': change >= 0,
                })
            except Exception as exc:
                logger.warning(f"市場資料失敗 {ticker}: {exc}")
                results.append({**base, 'price': None, 'change': None, 'change_pct': None, 'up': None})
        return results
