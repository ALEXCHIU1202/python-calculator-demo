import json
import logging
import time
from typing import Dict, List

from modules.llm_client import LLMClient

logger = logging.getLogger(__name__)

_BATCH_PROMPT = """\
You are a senior global financial market analyst. Analyze the news articles below and identify market-moving content.

For EACH article return a JSON object with exactly these fields:
  "title"           : exact article title (string)
  "is_market_moving": true if the article contains statements that could move markets (bool)
  "impact_score"    : integer 1-10 (10 = maximum market impact)
  "sentiment"       : "bullish" | "bearish" | "neutral"
  "affected_markets": array of impacted indices, sectors, or regions (string[])
  "key_entity"      : main speaker / institution / company (string)
  "key_statement"   : core market-relevant statement, ≤150 chars (string)
  "reason"          : why it could move markets, ≤100 chars (string)

Market-moving events include: central bank policy decisions or hints, major earnings surprises,
M&A announcements, geopolitical crises, significant macro data, major regulatory actions,
key government or executive statements.

Return ONLY a valid JSON array. No markdown fences. No other text.

Articles:
"""

_OUTLOOK_PROMPT = """\
As a chief market strategist, write a concise market outlook briefing (3 short paragraphs) \
based on today's high-impact statements listed below.

Para 1: Overall market sentiment and likely short-term direction.
Para 2: Key risks and opportunities to watch.
Para 3: Sectors / regions most affected and investment implications.

Professional tone, analytical, under 280 words total. Write in Traditional Chinese (繁體中文).

Key statements today:
{statements}
"""

_DAILY_REPORT_PROMPT = """\
你是一位資深全球股市首席分析師，請根據以下今日市場數據與新聞分析，撰寫一份約1000字的專業市場日報。

【報告格式要求】
- 語言：繁體中文，使用專業財金術語
- 字數：約1000字（全文合計）
- 標題格式：使用「一、二、三、四、五」編號，不要使用 Markdown # 符號
- 段落分明，每節換行

【報告結構】
一、今日市場概況（約150字）
  描述全球主要股市今日整體走勢，包含美股、歐股、亞股的表現方向。

二、重大聲明與事件深度分析（約350字）
  逐一分析今日影響力分數最高的重大聲明與事件（至少5則），說明：
  - 聲明發出者與背景
  - 對市場的具體意義與可能影響
  - 短中期效應預測

三、板塊與區域影響評估（約150字）
  分析科技、金融、能源、消費、醫療等板塊，以及美國、歐洲、亞太各區域的差異化影響。

四、風險與機會分析（約150字）
  列出當前市場面臨的主要下行風險，及值得關注的潛在投資機會與題材。

五、明日市場展望（約200字）
  根據今日訊號，預測明日市場走勢方向，並點出明日需重點關注的數據、事件或聲明。

【今日市場數據摘要】
{data}
"""


class Analyzer:
    def __init__(self, config):
        self.llm = LLMClient(config)
        self.config = config

    def analyze(self, articles: List[Dict]) -> Dict:
        logger.info(f"開始分析 {len(articles)} 篇文章…")
        analyzed: List[Dict] = []
        batch_size = 10

        for i in range(0, len(articles), batch_size):
            batch = articles[i: i + batch_size]
            analyzed.extend(self._analyze_batch(batch))
            if i + batch_size < len(articles):
                time.sleep(1)

        # Sort by impact descending
        analyzed.sort(key=lambda x: x.get('impact_score', 0), reverse=True)

        outlook = self._generate_outlook(analyzed)
        stats = self._compute_stats(analyzed)
        daily_report = self._generate_daily_report(analyzed, stats)

        return {'articles': analyzed, 'market_outlook': outlook, 'stats': stats, 'daily_report': daily_report}

    # ── Batch analysis ────────────────────────────────────────────────────────

    def _analyze_batch(self, articles: List[Dict]) -> List[Dict]:
        text = '\n\n'.join(
            f"[{i + 1}] Title: {a['title']}\nSource: {a['source']}\nSummary: {a['summary']}"
            for i, a in enumerate(articles)
        )
        try:
            raw = self.llm.complete(_BATCH_PROMPT + text, max_tokens=4096).strip()
            start, end = raw.find('['), raw.rfind(']') + 1
            if start >= 0 and end > start:
                parsed: List[Dict] = json.loads(raw[start:end])
                for i, item in enumerate(parsed):
                    if i < len(articles):
                        item.setdefault('link', articles[i].get('link', ''))
                        item.setdefault('published', articles[i].get('published', ''))
                        item.setdefault('source', articles[i].get('source', ''))
                return parsed
        except Exception as exc:
            logger.error(f"批次分析失敗: {exc}")
        return [self._fallback(a) for a in articles]

    def _fallback(self, article: Dict) -> Dict:
        return {
            'title': article['title'],
            'is_market_moving': False,
            'impact_score': 2,
            'sentiment': 'neutral',
            'affected_markets': [],
            'key_entity': article.get('source', 'Unknown'),
            'key_statement': article['summary'][:150],
            'reason': 'Analysis unavailable',
            'link': article.get('link', ''),
            'published': article.get('published', ''),
            'source': article.get('source', ''),
        }

    # ── Market outlook ────────────────────────────────────────────────────────

    def _generate_outlook(self, analyzed: List[Dict]) -> str:
        high = [a for a in analyzed if a.get('is_market_moving') and a.get('impact_score', 0) >= 6]
        if not high:
            return (
                "今日暫無重大市場影響事件，整體市場應維持相對平穩。\n\n"
                "主要觀察重點為技術面支撐水準與成交量變化。\n\n"
                "建議持續關注後續央行政策動向及總經數據。"
            )
        statements = '\n'.join(
            f"- [{a.get('key_entity', 'Unknown')}] "
            f"{a.get('key_statement', a['title'])} "
            f"(影響分數 {a.get('impact_score', 0)}/10, {a.get('sentiment', 'neutral')})"
            for a in high[:8]
        )
        try:
            return self.llm.complete(_OUTLOOK_PROMPT.format(statements=statements), max_tokens=700).strip()
        except Exception as exc:
            logger.error(f"市場展望生成失敗: {exc}")
            return "市場展望分析暫時無法取得，請稍後再試。"

    # ── Daily 1000-word report ────────────────────────────────────────────────

    def _generate_daily_report(self, analyzed: List[Dict], stats: Dict) -> str:
        candidates = [a for a in analyzed if a.get('is_market_moving')]
        # Use top 10 by impact score
        top = sorted(candidates, key=lambda x: x.get('impact_score', 0), reverse=True)[:10]

        if not top:
            top = analyzed[:5]  # fallback: use first 5 articles

        events_text = '\n\n'.join(
            f"事件 {i+1}（影響分數 {a.get('impact_score', 0)}/10 | {a.get('sentiment', 'neutral')}）\n"
            f"標題：{a['title']}\n"
            f"發言者/機構：{a.get('key_entity', '不明')}\n"
            f"核心聲明：{a.get('key_statement', '')}\n"
            f"影響範圍：{', '.join(a.get('affected_markets', [])) or '不明'}\n"
            f"影響原因：{a.get('reason', '')}"
            for i, a in enumerate(top)
        )

        data_summary = (
            f"統計數據\n"
            f"分析文章總數：{stats['total']}｜市場影響事件：{stats['market_moving']}｜"
            f"高影響事件（7+）：{stats['high_impact']}\n"
            f"情緒：多頭 {stats['bullish']} / 空頭 {stats['bearish']} / 中性 {stats['neutral']}\n"
            f"平均影響分數：{stats['avg_impact']}/10\n\n"
            f"今日重大事件（按影響力排序）\n"
            f"{'─'*50}\n"
            f"{events_text}"
        )

        try:
            return self.llm.complete(_DAILY_REPORT_PROMPT.format(data=data_summary), max_tokens=2200).strip()
        except Exception as exc:
            logger.error(f"每日報告生成失敗: {exc}")
            return "每日市場報告生成失敗，請查看附件 HTML 完整報告。"

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _compute_stats(self, analyzed: List[Dict]) -> Dict:
        total = len(analyzed)
        bullish = sum(1 for a in analyzed if a.get('sentiment') == 'bullish')
        bearish = sum(1 for a in analyzed if a.get('sentiment') == 'bearish')
        return {
            'total': total,
            'market_moving': sum(1 for a in analyzed if a.get('is_market_moving')),
            'bullish': bullish,
            'bearish': bearish,
            'neutral': total - bullish - bearish,
            'high_impact': sum(1 for a in analyzed if a.get('impact_score', 0) >= 7),
            'avg_impact': round(
                sum(a.get('impact_score', 0) for a in analyzed) / total, 1
            ) if total else 0,
        }
