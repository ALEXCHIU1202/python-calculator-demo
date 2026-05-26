import logging
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Union

logger = logging.getLogger(__name__)

_WEEKDAY = ['一', '二', '三', '四', '五', '六', '日']


class EmailSender:
    def __init__(self, config):
        self.config = config

    def send_report(
        self,
        report_path: Path,
        stats: Dict,
        daily_report: Union[Dict, str] = None,
    ) -> bool:
        if not self.config.EMAIL_RECIPIENTS:
            logger.warning("未設定收件人，略過發送")
            return False

        # 相容舊格式（daily_report 為 str 時轉為空 dict）
        if not isinstance(daily_report, dict):
            daily_report = {}

        now = datetime.now()
        date_str = f"{now.year}年{now.month:02d}月{now.day:02d}日（週{_WEEKDAY[now.weekday()]}）"

        msg = MIMEMultipart('mixed')
        msg['Subject'] = f"📊 台股開盤前情勢日報｜{now.strftime('%Y/%m/%d')}"
        msg['From']    = self.config.EMAIL_SENDER
        msg['To']      = ', '.join(self.config.EMAIL_RECIPIENTS)

        alt = MIMEMultipart('alternative')
        alt.attach(MIMEText(self._plain(date_str, stats, daily_report), 'plain', 'utf-8'))
        alt.attach(MIMEText(self._html(date_str, stats, daily_report), 'html', 'utf-8'))
        msg.attach(alt)

        if report_path and report_path.exists():
            with open(report_path, 'rb') as f:
                att = MIMEBase('text', 'html')
                att.set_payload(f.read())
            encoders.encode_base64(att)
            att.add_header('Content-Disposition', f'attachment; filename="{report_path.name}"')
            msg.attach(att)

        try:
            with smtplib.SMTP(self.config.EMAIL_SMTP_HOST, self.config.EMAIL_SMTP_PORT) as srv:
                srv.ehlo(); srv.starttls()
                srv.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
                srv.sendmail(self.config.EMAIL_SENDER, self.config.EMAIL_RECIPIENTS, msg.as_string())
            logger.info(f"Email 已發送至 {self.config.EMAIL_RECIPIENTS}")
            return True
        except Exception as exc:
            logger.error(f"Email 發送失敗: {exc}")
            return False

    # ── 純文字版 ──────────────────────────────────────────────────────────────

    def _plain(self, date_str: str, stats: Dict, report: Dict) -> str:
        sep = '─' * 50
        influencers = report.get('influencers', [])
        infl_lines = []
        for r in influencers:
            person = r.get('person', '－')
            stmt   = r.get('statement', '')
            impact = r.get('taiwan_impact', '')
            infl_lines.append(f"  {person}   {stmt}")
            if impact:
                infl_lines.append(f"    └ 台股影響：{impact}")
        infl_text = '\n'.join(infl_lines) or '  （無重大發言）'

        tw = report.get('taiwan_stocks', {})
        tw_index  = tw.get('index_summary', '')
        tw_top10  = tw.get('top10_analysis', '')
        tw_pred   = tw.get('prediction', '')

        def sec(title, content):
            return f"\n【{title}】\n{content or '（分析暫時無法取得）'}\n"

        taiwan_section = ''
        if tw_index or tw_top10 or tw_pred:
            taiwan_section = (
                f"\n{'─'*50}\n"
                f"🇹🇼 台股技術分析\n"
                f"{sep}\n"
                + (f"▌ 昨日指數表現\n{tw_index}\n\n" if tw_index else '')
                + (f"▌ 前十大科技股 K 線\n{tw_top10}\n\n" if tw_top10 else '')
                + (f"▌ 今日走勢預測\n{tw_pred}\n" if tw_pred else '')
            )

        return (
            f"台股開盤前情勢日報\n"
            f"日期：{date_str}\n"
            f"分析文章數：{stats.get('total',0)}｜市場影響事件：{stats.get('market_moving',0)}\n"
            f"多頭：{stats.get('bullish',0)}  空頭：{stats.get('bearish',0)}  中性：{stats.get('neutral',0)}\n"
            f"{sep}\n\n"
            f"⚡ 重量級人物發言速報\n"
            f"{infl_text}\n"
            f"{taiwan_section}"
            f"{sep}"
            f"{sec('💻 科技股分析（主要焦點）', report.get('tech',''))}"
            f"{sep}"
            f"{sec('🏭 傳統產業分析', report.get('traditional',''))}"
            f"{sep}"
            f"{sec('🔬 生醫科技分析', report.get('biotech',''))}"
            f"{sep}"
            f"{sec('💰 財經金融分析', report.get('finance',''))}"
            f"{sep}\n"
            f"詳細圖表報告請開啟附件 HTML 檔案。\n"
            f"本報告由 AI 自動生成，僅供參考，不構成投資建議。\n"
        )

    # ── HTML 版 ───────────────────────────────────────────────────────────────

    def _html(self, date_str: str, stats: Dict, report: Dict) -> str:
        bull = stats.get('bullish', 0)
        bear = stats.get('bearish', 0)
        neut = stats.get('neutral', 0)
        total_sent = bull + bear + neut or 1

        # 市場情緒
        if bull > bear * 1.5:
            mood_text, mood_color = '整體偏多頭 ▲', '#15803d'
        elif bear > bull * 1.5:
            mood_text, mood_color = '整體偏空頭 ▼', '#b91c1c'
        else:
            mood_text, mood_color = '多空分歧 ◆', '#b45309'

        # 影響力人物發言列表
        influencers_html = self._render_influencers(report.get('influencers', []))

        # 台股技術分析
        taiwan_stocks_html = self._render_taiwan_stocks(report.get('taiwan_stocks', {}))

        # 四大板塊分析
        tech_html        = self._render_text(report.get('tech', ''))
        traditional_html = self._render_text(report.get('traditional', ''))
        biotech_html     = self._render_text(report.get('biotech', ''))
        finance_html     = self._render_text(report.get('finance', ''))

        bar_bull = int(bull / total_sent * 100)
        bar_bear = int(bear / total_sent * 100)

        return f"""\
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>台股開盤前情勢日報</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;
             font-family:'Microsoft JhengHei','PingFang TC','Noto Sans TC',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:20px 10px;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="max-width:700px;margin:0 auto;border-radius:16px;
              overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.13);">

  <!-- ▌ 頂部標題 -->
  <tr><td>
    <div style="background:linear-gradient(135deg,#0c1e3c 0%,#1a3a6c 55%,#0c1e3c 100%);
                padding:28px 36px 20px;text-align:center;">
      <div style="font-size:11px;color:rgba(255,255,255,.4);letter-spacing:3px;margin-bottom:6px;">
        台灣股市 · 開盤前情勢分析
      </div>
      <div style="font-size:22px;font-weight:700;color:#fff;line-height:1.3;">
        📊 台股開盤前美股情勢日報
      </div>
      <div style="font-size:13px;color:rgba(255,255,255,.6);margin-top:8px;">
        {date_str}
      </div>
      <div style="display:inline-block;margin-top:10px;padding:3px 14px;
                  background:rgba(255,255,255,.1);border-radius:100px;
                  font-size:11px;color:rgba(180,210,255,.85);">
        ⚡ 由 Groq AI 自動分析
      </div>
    </div>
  </td></tr>

  <!-- ▌ 情緒 + 統計列 -->
  <tr><td style="background:#1a2f5a;padding:10px 36px;">
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      <td style="color:rgba(255,255,255,.65);font-size:13px;">
        蒐集 <strong style="color:#fff;">{stats.get('total',0)}</strong> 篇文章 ｜
        市場影響 <strong style="color:#fbbf24;">{stats.get('market_moving',0)}</strong> 則
      </td>
      <td style="text-align:right;">
        <span style="font-size:13px;font-weight:700;color:{mood_color};
                     background:rgba(255,255,255,.08);padding:2px 12px;border-radius:100px;">
          {mood_text}
        </span>
      </td>
    </tr></table>
    <!-- 情緒進度條 -->
    <div style="background:rgba(255,255,255,.1);border-radius:4px;height:5px;margin-top:8px;overflow:hidden;">
      <div style="display:flex;height:100%;">
        <div style="width:{bar_bull}%;background:#22c55e;"></div>
        <div style="width:{bar_bear}%;background:#ef4444;"></div>
        <div style="flex:1;background:rgba(255,255,255,.15);"></div>
      </div>
    </div>
    <div style="font-size:10px;color:rgba(255,255,255,.4);margin-top:4px;">
      多頭 {bull} · 空頭 {bear} · 中性 {neut}
    </div>
  </td></tr>

  <!-- ▌ 重量級人物發言速報 -->
  <tr><td style="background:#0f172a;padding:0;">
    <div style="padding:16px 36px 6px;">
      <div style="font-size:12px;font-weight:700;color:#fbbf24;letter-spacing:2px;margin-bottom:12px;">
        ⚡ 重量級人物發言速報
      </div>
      {influencers_html}
    </div>
    <div style="height:1px;background:linear-gradient(90deg,transparent,#334155,transparent);margin:10px 0;"></div>
  </td></tr>

  <!-- ▌ 分隔線 -->
  <tr><td style="padding:0;">
    <div style="height:4px;background:linear-gradient(90deg,#0d9488,#0891b2,#0d9488);"></div>
  </td></tr>

  <!-- ▌ 🇹🇼 台股技術分析 -->
  {taiwan_stocks_html}

  <!-- ▌ 分隔線 -->
  <tr><td style="padding:0;">
    <div style="height:4px;background:linear-gradient(90deg,#3b82f6,#8b5cf6,#3b82f6);"></div>
  </td></tr>

  <!-- ▌ 💻 科技股（主要焦點，特別強調） -->
  {self._section_block(
      '💻 科技股分析',
      '★ 主要焦點',
      tech_html,
      header_bg='linear-gradient(135deg,#1e3a8a,#2563eb)',
      badge_bg='#fbbf24',
      badge_color='#1e3a8a',
      body_bg='#eff6ff',
      border_color='#3b82f6',
  )}

  <!-- ▌ 🏭 傳統產業 -->
  {self._section_block(
      '🏭 傳統產業分析',
      '汽車・化工・鋼鐵・石化',
      traditional_html,
      header_bg='linear-gradient(135deg,#78350f,#d97706)',
      badge_bg='rgba(255,255,255,.15)',
      badge_color='rgba(255,255,255,.8)',
      body_bg='#fffbeb',
      border_color='#d97706',
  )}

  <!-- ▌ 🔬 生醫科技 -->
  {self._section_block(
      '🔬 生醫科技分析',
      '生技・醫材・製藥',
      biotech_html,
      header_bg='linear-gradient(135deg,#064e3b,#059669)',
      badge_bg='rgba(255,255,255,.15)',
      badge_color='rgba(255,255,255,.8)',
      body_bg='#f0fdf4',
      border_color='#10b981',
  )}

  <!-- ▌ 💰 財經金融 -->
  {self._section_block(
      '💰 財經金融分析',
      '利率・匯率・銀行・保險',
      finance_html,
      header_bg='linear-gradient(135deg,#4c1d95,#7c3aed)',
      badge_bg='rgba(255,255,255,.15)',
      badge_color='rgba(255,255,255,.8)',
      body_bg='#faf5ff',
      border_color='#7c3aed',
  )}

  <!-- ▌ 底部說明 -->
  <tr><td>
    <div style="background:#0c1e3c;padding:18px 36px;text-align:center;">
      <div style="font-size:12px;color:rgba(255,255,255,.65);margin-bottom:4px;">
        📎 詳細互動圖表報告請開啟附件 HTML 檔案
      </div>
      <div style="font-size:10px;color:rgba(255,255,255,.3);margin-top:6px;line-height:1.7;">
        本報告由 Groq AI 自動分析 {stats.get('total',0)} 篇全球財經新聞生成。<br>
        僅供參考，不構成任何投資建議，投資有風險，請審慎評估。
      </div>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    # ── 輔助：影響力人物列表（含台股影響預測）────────────────────────────────

    def _render_influencers(self, influencers: List[Dict]) -> str:
        if not influencers:
            return '<div style="color:rgba(255,255,255,.35);font-size:13px;padding:8px 0 12px;">（今日無重大影響力人物發言）</div>'

        rows = []
        for r in influencers:
            person = r.get('person', '').strip()
            stmt   = r.get('statement', '').strip()
            impact = r.get('taiwan_impact', '').strip()
            if not stmt:
                continue
            person_cell = (
                f'<span style="display:inline-block;min-width:85px;'
                f'font-weight:700;color:#fbbf24;font-size:13px;">{person}</span>'
                if person else ''
            )
            impact_row = ''
            if impact:
                indent = '85px' if person else '0'
                impact_row = (
                    f'<div style="margin-top:3px;padding-left:{indent};'
                    f'font-size:12px;color:#5eead4;line-height:1.5;">'
                    f'🇹🇼 台股影響：{impact}'
                    f'</div>'
                )
            rows.append(
                f'<div style="padding:7px 0;border-bottom:1px solid rgba(255,255,255,.06);">'
                f'  <div style="font-size:13px;color:rgba(230,240,255,.85);line-height:1.5;">'
                f'    {person_cell}'
                f'    <span style="color:rgba(255,255,255,.8);">{stmt}</span>'
                f'  </div>'
                f'  {impact_row}'
                f'</div>'
            )
        return '\n'.join(rows) + '<div style="height:8px;"></div>'

    # ── 輔助：台股技術分析區塊 ─────────────────────────────────────────────────

    def _render_taiwan_stocks(self, taiwan: Dict) -> str:
        index_summary  = taiwan.get('index_summary', '')
        top10_analysis = taiwan.get('top10_analysis', '')
        prediction     = taiwan.get('prediction', '')

        # 如果三個區塊都是空的就顯示提示
        if not index_summary and not top10_analysis and not prediction:
            no_data = (
                '<p style="color:#94a3b8;font-size:13px;text-align:center;padding:12px 0;">'
                '台股數據暫時無法取得，請稍後再試。'
                '</p>'
            )
            return self._taiwan_block(no_data)

        parts = []

        if index_summary:
            parts.append(
                f'<div style="background:rgba(13,148,136,.12);border-left:3px solid #0d9488;'
                f'border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:14px;">'
                f'  <div style="font-size:11px;font-weight:700;color:#0d9488;'
                f'letter-spacing:1.5px;margin-bottom:6px;">▌ 昨日加權指數表現</div>'
                f'  {self._render_text_teal(index_summary)}'
                f'</div>'
            )

        if top10_analysis:
            parts.append(
                f'<div style="margin-bottom:14px;">'
                f'  <div style="font-size:11px;font-weight:700;color:#0891b2;'
                f'letter-spacing:1.5px;margin-bottom:8px;padding-left:4px;">▌ 前十大科技股 K 線分析</div>'
                f'  {self._render_text_teal(top10_analysis)}'
                f'</div>'
            )

        if prediction:
            parts.append(
                f'<div style="background:rgba(8,145,178,.1);border:1px solid rgba(8,145,178,.3);'
                f'border-radius:8px;padding:12px 14px;">'
                f'  <div style="font-size:11px;font-weight:700;color:#38bdf8;'
                f'letter-spacing:1.5px;margin-bottom:6px;">🔮 今日科技股走勢預測</div>'
                f'  {self._render_text_teal(prediction)}'
                f'</div>'
            )

        return self._taiwan_block('\n'.join(parts))

    def _taiwan_block(self, content_html: str) -> str:
        return f"""
  <tr><td style="padding:0;border-top:3px solid #0d9488;">
    <!-- 台股板塊標題 -->
    <div style="background:linear-gradient(135deg,#042f2e,#0d9488);padding:12px 36px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:15px;font-weight:700;color:#fff;">🇹🇼 台股技術分析</td>
        <td style="text-align:right;">
          <span style="font-size:10px;padding:2px 10px;border-radius:100px;
                       background:rgba(255,255,255,.15);color:rgba(255,255,255,.85);white-space:nowrap;">
            K線・均線・RSI・走勢預測
          </span>
        </td>
      </tr></table>
    </div>
    <!-- 台股板塊內容 -->
    <div style="background:#f0fdfa;padding:20px 36px 22px;
                border-left:4px solid #0d9488;">
      {content_html}
    </div>
  </td></tr>"""

    # ── 輔助：板塊區塊 ────────────────────────────────────────────────────────

    def _section_block(
        self,
        title: str,
        subtitle: str,
        content_html: str,
        header_bg: str,
        badge_bg: str,
        badge_color: str,
        body_bg: str,
        border_color: str,
    ) -> str:
        return f"""
  <tr><td style="padding:0;border-top:3px solid {border_color};">
    <!-- 板塊標題 -->
    <div style="background:{header_bg};padding:12px 36px;">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:15px;font-weight:700;color:#fff;">{title}</td>
        <td style="text-align:right;">
          <span style="font-size:10px;padding:2px 10px;border-radius:100px;
                       background:{badge_bg};color:{badge_color};white-space:nowrap;">
            {subtitle}
          </span>
        </td>
      </tr></table>
    </div>
    <!-- 板塊內容 -->
    <div style="background:{body_bg};padding:20px 36px 22px;
                border-left:4px solid {border_color};">
      {content_html}
    </div>
  </td></tr>"""

    # ── 輔助：純文字轉 HTML 段落（深色背景用）────────────────────────────────

    def _render_text_teal(self, text: str) -> str:
        """將純文字轉為 HTML，適用於台股分析區塊（淺色背景）。"""
        if not text:
            return '<p style="color:#94a3b8;">（無內容）</p>'
        parts = []
        for line in text.split('\n'):
            s = line.strip()
            if not s:
                continue
            parts.append(
                f'<p style="font-size:13.5px;color:#134e4a;line-height:1.85;'
                f'margin:0 0 8px;text-align:justify;">{s}</p>'
            )
        return '\n'.join(parts) if parts else '<p style="color:#94a3b8;">（無內容）</p>'

    # ── 輔助：純文字轉 HTML 段落 ───────────────────────────────────────────────

    def _render_text(self, text: str) -> str:
        """將 AI 回傳的純文字段落轉為 HTML，處理換行與縮排。"""
        if not text:
            return '<p style="color:#9ca3af;">分析內容暫時無法取得。</p>'

        parts = []
        for line in text.split('\n'):
            s = line.strip()
            if not s:
                continue
            # 若是「一、二、三、四」開頭的小標題
            section_nums = ('一、','二、','三、','四、','五、','六、','七、','八、','九、','十、')
            if any(s.startswith(n) for n in section_nums):
                parts.append(
                    f'<div style="font-size:14px;font-weight:700;color:#1e3a6e;'
                    f'margin:16px 0 6px;padding:6px 12px;'
                    f'background:rgba(30,58,138,.07);'
                    f'border-left:3px solid #3b82f6;border-radius:0 6px 6px 0;">'
                    f'{s}</div>'
                )
            else:
                parts.append(
                    f'<p style="font-size:14px;color:#374151;line-height:1.85;'
                    f'margin:0 0 10px;text-align:justify;">{s}</p>'
                )
        return '\n'.join(parts) if parts else '<p style="color:#9ca3af;">（無內容）</p>'
