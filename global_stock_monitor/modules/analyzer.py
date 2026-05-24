import json
import logging
import time
from typing import Dict, List

from modules.llm_client import LLMClient

logger = logging.getLogger(__name__)

# ── 批次分析 Prompt（保持不變，供 HTML 附件使用）────────────────────────────

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

# ── 影響力人物發言 Prompt ────────────────────────────────────────────────────

_INFLUENCER_PROMPT = """\
你是一位資深財經分析師。請從以下新聞中，找出所有具有股市影響力的重要人物發言或決策行動（包含：政治領袖如川普、副總統、聯準會官員、各國央行首長、知名科技CEO如黃仁勳、庫克、馬斯克、重要投資人如巴菲特等）。

【輸出格式】每行一則，格式為：
人名｜發言或行動摘要（30字以內，直接說重點）

【規則】
- 只列真正影響市場的重大發言，排除無關緊要的雜訊
- 最多 15 則，按影響力由高到低排列
- 只輸出條列清單，不加標題、編號或任何說明文字

今日新聞：
{news}
"""

# ── 四大板塊分析 Prompts ──────────────────────────────────────────────────────

_SECTOR_TECH_PROMPT = """\
你是一位專注台股科技類股的資深分析師。根據以下昨晚（台灣時間）美股及全球市場新聞，針對科技類股進行深度分析，核心任務是推估對台股科技族群今日開盤的具體影響。

【分析架構】
一、美股科技板塊整體表現（那斯達克指數、費城半導體指數SOX昨晚走勢方向）
二、重點個股動態（輝達NVDA、蘋果AAPL、超微AMD、英特爾INTC、台積電ADR等，重點說明漲跌與原因）
三、對台灣科技股影響推估（台積電2330、聯發科2454、鴻海2317、廣達2382、緯創3231、聯電2303等，預期今日表現方向）
四、多空方向判斷（明確說明今日台股科技族群偏多或偏空，信心程度高中低）

【格式要求】
- 繁體中文，400～500字
- 段落式書寫，不使用條列符號「•、-、*」或Markdown語法
- 分析需具體，避免流於空泛

今日新聞：
{news}"""

_SECTOR_TRADITIONAL_PROMPT = """\
你是一位台股傳統產業分析師。根據以下昨晚美股及全球市場新聞，分析傳統產業（汽車、化工、鋼鐵、石化、塑料、紡織等）動態，核心任務是評估對台灣相關傳統產業族群的影響。

【分析架構】
一、全球傳統產業板塊昨晚整體表現方向
二、汽車業（電動車、燃油車政策）、化工業、鋼鐵業等重要消息
三、原物料走勢（國際油價WTI/布蘭特、銅價、鋼鐵價格）對台廠的影響
四、對台灣傳統產業股影響推估與多空判斷（台塑集團、中鋼、裕隆、和泰車等）

【格式要求】
- 繁體中文，400～500字
- 段落式書寫
- 若相關新聞較少，可結合宏觀環境（匯率、通膨、供應鏈）進行推估

今日新聞：
{news}
"""

_SECTOR_BIOTECH_PROMPT = """\
你是一位台股生醫科技分析師。根據以下昨晚美股及全球市場新聞，分析生醫科技產業動態，核心任務是評估對台灣生醫、醫療器材、製藥類股的影響。

【分析架構】
一、美股生醫板塊表現（XBI、IBB等生技ETF昨晚走勢）
二、重要藥廠（輝瑞、莫德納、嬌生等）、醫療器材公司重大消息
三、重大臨床試驗結果、FDA審查通過/駁回消息
四、對台灣生醫股影響推估與多空判斷（醫療法規趨勢、台廠受惠機會）

【格式要求】
- 繁體中文，400～500字
- 段落式書寫
- 若生醫新聞較少，可結合整體風險偏好（Risk-on/Risk-off）環境進行評估

今日新聞：
{news}
"""

_SECTOR_FINANCE_PROMPT = """\
你是一位財金市場分析師。根據以下昨晚美股及全球市場新聞，分析財經金融動態（利率政策、匯率、銀行業、保險業、ETF資金流向等），核心任務是評估對台灣金融類股的影響。

【分析架構】
一、聯準會最新動態與利率預期（FedWatch升降息機率變化、官員發言方向）
二、美元指數（DXY）走勢與新台幣匯率預估（強弱方向）
三、美股金融板塊表現（銀行、保險、投行昨晚整體方向）
四、對台灣金融股影響推估與多空判斷（富邦金2881、國泰金2882、玉山金2884、兆豐金2886等）

【格式要求】
- 繁體中文，400～500字
- 段落式書寫

今日新聞：
{news}
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

    # ── Market outlook（供 HTML 報告附件使用）────────────────────────────────

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

    # ── 結構化日報（Email 使用）──────────────────────────────────────────────

    def _generate_daily_report(self, analyzed: List[Dict], stats: Dict) -> Dict:
        """生成結構化日報 Dict：影響力人物發言 + 四大板塊分析"""

        # 準備新聞摘要文本（取前30篇，影響力最高的）
        news_text = '\n\n'.join(
            f"[{i+1}] 標題：{a['title']}\n"
            f"     發言者/機構：{a.get('key_entity', a.get('source', ''))}\n"
            f"     核心聲明：{a.get('key_statement', a.get('summary', ''))[:200]}\n"
            f"     情緒：{a.get('sentiment', '')} | 影響分數：{a.get('impact_score', 0)}/10"
            for i, a in enumerate(analyzed[:30])
        )

        result: Dict = {}

        # 1. 影響力人物發言
        logger.info("  生成影響力人物發言速報…")
        try:
            raw = self.llm.complete(_INFLUENCER_PROMPT.format(news=news_text), max_tokens=800).strip()
            result['influencers'] = self._parse_influencers(raw)
        except Exception as exc:
            logger.error(f"影響力人物分析失敗: {exc}")
            result['influencers'] = []
        time.sleep(2)

        # 2. 科技股
        logger.info("  生成科技股分析…")
        try:
            result['tech'] = self.llm.complete(
                _SECTOR_TECH_PROMPT.format(news=news_text), max_tokens=1200
            ).strip()
        except Exception as exc:
            logger.error(f"科技股分析失敗: {exc}")
            result['tech'] = '科技股分析暫時無法取得，請查閱附件完整報告。'
        time.sleep(2)

        # 3. 傳統產業
        logger.info("  生成傳統產業分析…")
        try:
            result['traditional'] = self.llm.complete(
                _SECTOR_TRADITIONAL_PROMPT.format(news=news_text), max_tokens=1200
            ).strip()
        except Exception as exc:
            logger.error(f"傳統產業分析失敗: {exc}")
            result['traditional'] = '傳統產業分析暫時無法取得，請查閱附件完整報告。'
        time.sleep(2)

        # 4. 生醫科技
        logger.info("  生成生醫科技分析…")
        try:
            result['biotech'] = self.llm.complete(
                _SECTOR_BIOTECH_PROMPT.format(news=news_text), max_tokens=1200
            ).strip()
        except Exception as exc:
            logger.error(f"生醫科技分析失敗: {exc}")
            result['biotech'] = '生醫科技分析暫時無法取得，請查閱附件完整報告。'
        time.sleep(2)

        # 5. 財經金融
        logger.info("  生成財經金融分析…")
        try:
            result['finance'] = self.llm.complete(
                _SECTOR_FINANCE_PROMPT.format(news=news_text), max_tokens=1200
            ).strip()
        except Exception as exc:
            logger.error(f"財經金融分析失敗: {exc}")
            result['finance'] = '財經金融分析暫時無法取得，請查閱附件完整報告。'

        return result

    def _parse_influencers(self, raw: str) -> List[Dict]:
        """解析影響力人物發言，格式：人名｜發言摘要"""
        result = []
        for line in raw.split('\n'):
            line = line.strip().lstrip('•-·*·0123456789. 　')
            if not line:
                continue
            # 嘗試全形直線 ｜
            if '｜' in line:
                parts = line.split('｜', 1)
                result.append({'person': parts[0].strip(), 'statement': parts[1].strip()})
            # 嘗試半形直線 |
            elif '|' in line:
                parts = line.split('|', 1)
                result.append({'person': parts[0].strip(), 'statement': parts[1].strip()})
            # 嘗試冒號格式 「人名：發言」
            elif '：' in line:
                parts = line.split('：', 1)
                if len(parts[0]) <= 15:  # 人名不應太長
                    result.append({'person': parts[0].strip(), 'statement': parts[1].strip()})
                else:
                    result.append({'person': '', 'statement': line})
            elif len(line) > 5:
                result.append({'person': '', 'statement': line})
        return result[:15]

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
