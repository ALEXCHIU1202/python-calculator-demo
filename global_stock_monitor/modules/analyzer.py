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
你是一位資深財經分析師兼台灣股市專家。請從以下新聞中，找出所有具有股市影響力的重要人物發言或決策行動（包含：政治領袖如川普、副總統、聯準會官員、各國央行首長、知名科技CEO如黃仁勳、庫克、馬斯克、重要投資人如巴菲特等）。

【輸出格式】每行一則，三個欄位用｜分隔：
人名｜發言或行動摘要（20字以內）｜對台股影響預測（35字以內，說明影響哪些台灣類股或個股、多空方向）

【規則】
- 只列真正影響市場的重大發言，排除無關緊要的雜訊
- 最多 12 則，按影響力由高到低排列
- 只輸出條列清單，不加標題、編號或任何說明文字

今日新聞：
{news}
"""

# ── 台股 K 線分析 Prompt ──────────────────────────────────────────────────────

_TAIWAN_STOCKS_PROMPT = """\
你是一位台股技術分析師。請根據以下台股加權指數與前十大科技股的近期數據，進行分析並預測今日走勢。

請依序輸出三個區塊：

<<<TAIWAN_INDEX_START>>>
（前一日台股整體表現：加權指數漲跌幅、成交量、整體市場情緒判斷，約100字）
<<<TAIWAN_INDEX_END>>>

<<<TAIWAN_TOP10_START>>>
（前十大科技股K線分析：逐一說明各股昨日漲跌、均線多空排列、RSI強弱，點出強勢股與弱勢股，約350字）
<<<TAIWAN_TOP10_END>>>

<<<TAIWAN_PREDICTION_START>>>
（今日科技股走勢預測：根據昨日K線型態預測今日整體方向，明確點出最看好個股與需注意個股，約150字）
<<<TAIWAN_PREDICTION_END>>>

【格式要求】繁體中文，段落式書寫

台股數據如下：
{taiwan_data}
"""

# ── 四大板塊分析（合併單次呼叫）────────────────────────────────────────────

_COMBINED_SECTORS_PROMPT = """\
你是一位台灣股市資深分析師。請根據下方新聞，依序完成四段繁體中文分析（每段約300字，段落式書寫，不用條列符號）。

每段必須以下列標記開頭和結尾，不可省略：

<<<TECH_START>>>
在此填入科技股分析：那斯達克/費城半導體SOX昨晚走勢、輝達/蘋果/AMD等重點個股、台積電/聯發科/鴻海/廣達今日預期表現，最後說明多頭或空頭。
<<<TECH_END>>>

<<<TRADITIONAL_START>>>
在此填入傳統產業分析：汽車/化工/鋼鐵/油價走勢、台塑/中鋼/裕隆/和泰車等影響，多空判斷。
<<<TRADITIONAL_END>>>

<<<BIOTECH_START>>>
在此填入生醫科技分析：XBI/IBB指數、重要FDA消息、台灣生醫股影響，多空判斷。
<<<BIOTECH_END>>>

<<<FINANCE_START>>>
在此填入財經金融分析：聯準會動態/美元指數/台幣匯率走勢、富邦金/國泰金/玉山金影響，多空判斷。
<<<FINANCE_END>>>

新聞資料：
{news}
"""


# 台灣前十大科技股
_TAIWAN_TECH_STOCKS = [
    ('2330.TW', '台積電'),
    ('2454.TW', '聯發科'),
    ('2317.TW', '鴻海'),
    ('2382.TW', '廣達'),
    ('3711.TW', '日月光投控'),
    ('2308.TW', '台達電'),
    ('2303.TW', '聯電'),
    ('3034.TW', '聯詠'),
    ('2379.TW', '瑞昱'),
    ('2357.TW', '華碩'),
]


class Analyzer:
    def __init__(self, config):
        self.llm = LLMClient(config)
        self.config = config

    def analyze(self, articles: List[Dict]) -> Dict:
        logger.info(f"開始分析 {len(articles)} 篇文章…")
        analyzed: List[Dict] = []
        batch_size = 20  # 每批20篇，減少AI呼叫次數（原本10篇/批）

        for i in range(0, len(articles), batch_size):
            batch = articles[i: i + batch_size]
            analyzed.extend(self._analyze_batch(batch))
            if i + batch_size < len(articles):
                time.sleep(5)  # gemini-1.5-flash: 15 RPM，每5秒1次安全

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
        """生成結構化日報 Dict：影響力人物發言 + 四大板塊分析 + 台股K線分析（3 次 AI 呼叫）"""

        # 準備新聞摘要文本（取前25篇，影響力最高的）
        news_text = '\n\n'.join(
            f"[{i+1}] 標題：{a['title']}\n"
            f"     發言者/機構：{a.get('key_entity', a.get('source', ''))}\n"
            f"     核心聲明：{a.get('key_statement', a.get('summary', ''))[:150]}\n"
            f"     情緒：{a.get('sentiment', '')} | 影響分數：{a.get('impact_score', 0)}/10"
            for i, a in enumerate(analyzed[:25])
        )

        result: Dict = {}

        # ── 第1次呼叫：影響力人物發言 ────────────────────────────────────────
        logger.info("  [1/3] 生成影響力人物發言速報…")
        try:
            # 用 replace 替換，避免新聞文字含 { } 導致 .format() 爆錯
            prompt1 = _INFLUENCER_PROMPT.replace('{news}', news_text)
            raw = self.llm.complete(prompt1, max_tokens=600).strip()
            logger.info(f"  影響人物回傳片段: {raw[:100]!r}")
            result['influencers'] = self._parse_influencers(raw)
        except Exception as exc:
            logger.error(f"影響力人物分析失敗: {exc}")
            result['influencers'] = []

        time.sleep(3)

        # ── 第2次呼叫：四大板塊（分隔符格式，比 JSON 更穩定）──────────────────
        logger.info("  [2/3] 生成四大板塊分析（科技/傳產/生醫/財經）…")
        try:
            # 用 replace 替換，避免新聞文字含 { } 導致 .format() 爆錯
            prompt2 = _COMBINED_SECTORS_PROMPT.replace('{news}', news_text)
            raw = self.llm.complete(prompt2, max_tokens=3500).strip()
            logger.info(f"  板塊分析回傳片段: {raw[:200]!r}")
            sectors = self._parse_sectors(raw)
            logger.info(f"  解析結果 tech={len(sectors.get('tech',''))}字, "
                        f"traditional={len(sectors.get('traditional',''))}字, "
                        f"biotech={len(sectors.get('biotech',''))}字, "
                        f"finance={len(sectors.get('finance',''))}字")
            result['tech']        = sectors.get('tech')        or '科技股分析暫時無法取得。'
            result['traditional'] = sectors.get('traditional') or '傳統產業分析暫時無法取得。'
            result['biotech']     = sectors.get('biotech')     or '生醫科技分析暫時無法取得。'
            result['finance']     = sectors.get('finance')     or '財經金融分析暫時無法取得。'
        except Exception as exc:
            logger.error(f"四大板塊分析失敗: {exc}")
            fallback = '分析暫時無法取得，請查閱附件完整報告。'
            result.setdefault('tech',        fallback)
            result.setdefault('traditional', fallback)
            result.setdefault('biotech',     fallback)
            result.setdefault('finance',     fallback)

        time.sleep(3)

        # ── 第3次呼叫：台股 K 線分析 ─────────────────────────────────────────
        logger.info("  [3/3] 生成台股 K 線分析…")
        try:
            taiwan_data = self._fetch_taiwan_stock_data()
            logger.info(f"  台股數據長度: {len(taiwan_data)} 字元")
            prompt3 = _TAIWAN_STOCKS_PROMPT.replace('{taiwan_data}', taiwan_data)
            raw = self.llm.complete(prompt3, max_tokens=1500).strip()
            logger.info(f"  台股分析回傳片段: {raw[:200]!r}")
            result['taiwan_stocks'] = self._parse_taiwan(raw)
        except Exception as exc:
            logger.error(f"台股分析失敗: {exc}")
            result['taiwan_stocks'] = {'index_summary': '', 'top10_analysis': '', 'prediction': ''}

        return result

    def _parse_influencers(self, raw: str) -> List[Dict]:
        """解析影響力人物發言，格式：人名｜發言摘要｜台股影響"""
        result = []
        for line in raw.split('\n'):
            line = line.strip().lstrip('•-·*·0123456789. 　')
            if not line:
                continue
            sep = '｜' if '｜' in line else ('|' if '|' in line else None)
            if sep:
                parts = [p.strip() for p in line.split(sep)]
                result.append({
                    'person':        parts[0] if len(parts) > 0 else '',
                    'statement':     parts[1] if len(parts) > 1 else line,
                    'taiwan_impact': parts[2] if len(parts) > 2 else '',
                })
            elif '：' in line:
                parts = line.split('：', 1)
                if len(parts[0]) <= 15:
                    result.append({'person': parts[0].strip(), 'statement': parts[1].strip(), 'taiwan_impact': ''})
                else:
                    result.append({'person': '', 'statement': line, 'taiwan_impact': ''})
            elif len(line) > 5:
                result.append({'person': '', 'statement': line, 'taiwan_impact': ''})
        return result[:12]

    def _fetch_taiwan_stock_data(self) -> str:
        """用 yfinance 抓取台股加權指數與前十大科技股 K 線數據"""
        import yfinance as yf
        lines = []

        # 台股加權指數
        try:
            hist = yf.Ticker('^TWII').history(period='5d')
            if not hist.empty and len(hist) >= 2:
                last, prev = hist.iloc[-1], hist.iloc[-2]
                chg = (last['Close'] - prev['Close']) / prev['Close'] * 100
                lines += [
                    '■ 台股加權指數（前一交易日）',
                    f'  收盤 {last["Close"]:.0f} 點（{chg:+.2f}%）'
                    f'  最高 {last["High"]:.0f}｜最低 {last["Low"]:.0f}',
                    f'  成交量 {last["Volume"]:,.0f}',
                    '',
                ]
        except Exception as e:
            logger.warning(f'台股指數數據失敗: {e}')
            lines += ['台股加權指數數據暫時無法取得', '']

        lines.append('■ 前十大科技股近期 K 線數據')
        for ticker, name in _TAIWAN_TECH_STOCKS:
            try:
                hist = yf.Ticker(ticker).history(period='30d')
                if hist.empty or len(hist) < 5:
                    continue
                close = hist['Close'].dropna()
                last  = hist.iloc[-1]
                prev  = hist.iloc[-2] if len(hist) >= 2 else last
                chg   = (last['Close'] - prev['Close']) / prev['Close'] * 100

                ma5  = close.rolling(5).mean().iloc[-1]  if len(close) >= 5  else None
                ma10 = close.rolling(10).mean().iloc[-1] if len(close) >= 10 else None
                ma20 = close.rolling(20).mean().iloc[-1] if len(close) >= 20 else None

                rsi_str = 'N/A'
                if len(close) >= 15:
                    delta = close.diff()
                    gain  = delta.clip(lower=0).rolling(14).mean().iloc[-1]
                    loss  = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
                    if loss and loss != 0:
                        rsi_str = f'{100 - 100 / (1 + gain / loss):.0f}'

                trend = ('多頭排列' if ma5 and ma20 and ma5 > ma20
                         else '空頭排列' if ma5 and ma20 and ma5 < ma20
                         else '均線糾結')

                ma_parts = [f'MA5={ma5:.1f}' if ma5 else '',
                            f'MA10={ma10:.1f}' if ma10 else '',
                            f'MA20={ma20:.1f}' if ma20 else '']
                lines.append(
                    f'\n{name}({ticker.replace(".TW","")})：'
                    f'收{last["Close"]:.1f}元（{chg:+.1f}%）'
                    f' {" ".join(p for p in ma_parts if p)}'
                    f' RSI={rsi_str} 趨勢:{trend}'
                )
            except Exception as e:
                logger.warning(f'無法取得 {name} 數據: {e}')

        return '\n'.join(lines)

    def _parse_taiwan(self, raw: str) -> Dict:
        """解析台股分析三個區塊"""
        raw_upper = raw.upper()
        mapping = {
            'index_summary':  ('<<<TAIWAN_INDEX_START>>>',      '<<<TAIWAN_INDEX_END>>>'),
            'top10_analysis': ('<<<TAIWAN_TOP10_START>>>',      '<<<TAIWAN_TOP10_END>>>'),
            'prediction':     ('<<<TAIWAN_PREDICTION_START>>>', '<<<TAIWAN_PREDICTION_END>>>'),
        }
        result: Dict = {}
        for key, (s_tag, e_tag) in mapping.items():
            s = raw_upper.find(s_tag)
            e = raw_upper.find(e_tag)
            result[key] = raw[s + len(s_tag): e].strip() if s >= 0 and e > s else ''
        return result

    def _parse_sectors(self, raw: str) -> Dict:
        """用 <<<TAG_START>>> / <<<TAG_END>>> 分隔符解析四大板塊"""
        raw_upper = raw.upper()
        mapping = {
            'tech':        ('<<<TECH_START>>>',        '<<<TECH_END>>>'),
            'traditional': ('<<<TRADITIONAL_START>>>', '<<<TRADITIONAL_END>>>'),
            'biotech':     ('<<<BIOTECH_START>>>',     '<<<BIOTECH_END>>>'),
            'finance':     ('<<<FINANCE_START>>>',     '<<<FINANCE_END>>>'),
        }
        result: Dict = {}
        for key, (start_tag, end_tag) in mapping.items():
            s = raw_upper.find(start_tag)
            e = raw_upper.find(end_tag)
            if s >= 0 and e > s:
                content = raw[s + len(start_tag): e].strip()
                result[key] = content if content else ''
            else:
                result[key] = ''
        return result

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
