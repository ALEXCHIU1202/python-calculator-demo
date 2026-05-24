import logging
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

_WEEKDAY = ['一', '二', '三', '四', '五', '六', '日']


class EmailSender:
    def __init__(self, config):
        self.config = config

    def send_report(self, report_path: Path, stats: Dict, daily_report: str = '') -> bool:
        if not self.config.EMAIL_RECIPIENTS:
            logger.warning("未設定收件人，略過發送")
            return False

        now = datetime.now()
        date_str = f"{now.year}年{now.month:02d}月{now.day:02d}日（週{_WEEKDAY[now.weekday()]}）"

        msg = MIMEMultipart('mixed')
        msg['Subject'] = f"📊 全球股市日報｜{now.strftime('%Y/%m/%d')}"
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

    # ── 純文字版 ──────────────────────────────────────────────────────────

    def _plain(self, date_str: str, stats: Dict, report: str) -> str:
        sep = '─' * 40
        return (
            f"【全球股市影響力聲明監測日報】\n"
            f"日期：{date_str}\n"
            f"{sep}\n\n"
            f"今日數據摘要\n"
            f"分析文章數：{stats.get('total',0)}　市場影響事件：{stats.get('market_moving',0)}\n"
            f"高影響事件(7+)：{stats.get('high_impact',0)}　平均影響分數：{stats.get('avg_impact',0)}/10\n"
            f"多頭訊號：{stats.get('bullish',0)}　空頭訊號：{stats.get('bearish',0)}　中性：{stats.get('neutral',0)}\n\n"
            f"{sep}\n\n"
            f"{report}\n\n"
            f"{sep}\n"
            f"詳細圖表報告請開啟附件 HTML 檔案。\n"
            f"本報告由 Gemini AI 自動生成，僅供參考，不構成投資建議。\n"
        )

    # ── HTML 全中文版 ─────────────────────────────────────────────────────

    def _html(self, date_str: str, stats: Dict, report: str) -> str:
        bull = stats.get('bullish', 0)
        bear = stats.get('bearish', 0)
        neut = stats.get('neutral', 0)
        total_sent = bull + bear + neut or 1
        bar_bull = int(bull / total_sent * 100)
        bar_bear = int(bear / total_sent * 100)

        # 情緒總評
        if bull > bear * 1.5:
            mood_text, mood_color = '整體偏多頭', '#15803d'
        elif bear > bull * 1.5:
            mood_text, mood_color = '整體偏空頭', '#b91c1c'
        else:
            mood_text, mood_color = '多空分歧', '#b45309'

        def card(val, label, color):
            return (
                f'<td style="padding:6px;">'
                f'<div style="background:#fff;border-radius:12px;padding:16px 10px;'
                f'text-align:center;box-shadow:0 2px 8px rgba(0,0,0,.08);min-width:88px;">'
                f'<div style="font-size:30px;font-weight:700;color:{color};line-height:1;">{val}</div>'
                f'<div style="font-size:10px;color:#6b7280;margin-top:5px;letter-spacing:.5px;">{label}</div>'
                f'</div></td>'
            )

        report_html = self._format_report(report)

        return f"""\
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>全球股市日報</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;
             font-family:'Microsoft JhengHei','PingFang TC','Noto Sans TC',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="padding:24px 12px;">
<table width="100%" cellpadding="0" cellspacing="0"
       style="max-width:680px;margin:0 auto;border-radius:16px;
              overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,.12);">

  <!-- ▌ 頂部標題列 -->
  <tr><td>
    <div style="background:linear-gradient(135deg,#0f2044 0%,#1e4080 60%,#0f2044 100%);
                padding:30px 36px 24px;text-align:center;">
      <div style="font-size:11px;color:rgba(255,255,255,.45);letter-spacing:3px;margin-bottom:8px;">
        全球市場情報
      </div>
      <div style="font-size:24px;font-weight:700;color:#fff;line-height:1.3;">
        📊 全球股市影響力聲明監測
      </div>
      <div style="font-size:14px;color:rgba(255,255,255,.65);margin-top:10px;">
        {date_str}
      </div>
      <div style="display:inline-block;margin-top:10px;padding:4px 14px;
                  background:rgba(255,255,255,.1);border-radius:100px;
                  font-size:11px;color:rgba(180,210,255,.9);">
        ⚡ 由 Google Gemini AI 自動分析
      </div>
    </div>
  </td></tr>

  <!-- ▌ 今日情緒總評 -->
  <tr><td>
    <div style="background:#1e3a6e;padding:14px 36px;text-align:center;">
      <span style="font-size:14px;color:rgba(255,255,255,.7);">今日市場情緒：</span>
      <span style="font-size:16px;font-weight:700;color:{mood_color};
                  background:rgba(255,255,255,.1);padding:2px 14px;border-radius:100px;">
        {mood_text}
      </span>
    </div>
  </td></tr>

  <!-- ▌ 數據摘要卡片 -->
  <tr><td style="background:#f8fafc;padding:18px 12px 12px;">
    <div style="font-size:11px;color:#94a3b8;text-align:center;
                letter-spacing:1px;margin-bottom:10px;">今日數據摘要</div>
    <table width="100%" cellpadding="0" cellspacing="0"><tr>
      {card(stats.get('total',0),          '分析文章',   '#1e40af')}
      {card(stats.get('market_moving',0),  '市場影響',   '#c2410c')}
      {card(stats.get('high_impact',0),    '高影響事件', '#dc2626')}
      {card(str(stats.get('avg_impact',0))+'/10', '平均分數', '#7c3aed')}
    </tr></table>
  </td></tr>

  <!-- ▌ 情緒分析 -->
  <tr><td style="background:#fff;padding:16px 36px;border-top:1px solid #e2e8f0;">
    <div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:10px;">
      📊 情緒分布
    </div>
    <div style="display:flex;justify-content:space-between;
                font-size:13px;margin-bottom:8px;color:#555;">
      <span>
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                     background:#15803d;margin-right:5px;vertical-align:middle;"></span>
        多頭 <strong style="color:#15803d;">{bull}</strong> 篇
      </span>
      <span>
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                     background:#b91c1c;margin-right:5px;vertical-align:middle;"></span>
        空頭 <strong style="color:#b91c1c;">{bear}</strong> 篇
      </span>
      <span>
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;
                     background:#9ca3af;margin-right:5px;vertical-align:middle;"></span>
        中性 <strong style="color:#6b7280;">{neut}</strong> 篇
      </span>
    </div>
    <div style="background:#e5e7eb;border-radius:6px;height:8px;overflow:hidden;">
      <div style="display:flex;height:100%;">
        <div style="width:{bar_bull}%;background:#15803d;"></div>
        <div style="width:{bar_bear}%;background:#b91c1c;"></div>
        <div style="flex:1;background:#d1d5db;"></div>
      </div>
    </div>
  </td></tr>

  <!-- ▌ 分隔線 -->
  <tr><td style="padding:0;">
    <div style="height:4px;background:linear-gradient(90deg,#1e40af,#7c3aed,#1e40af);"></div>
  </td></tr>

  <!-- ▌ 1000 字市場日報 -->
  <tr><td style="background:#fff;padding:28px 36px;">
    <div style="font-size:11px;color:#94a3b8;letter-spacing:2px;margin-bottom:16px;">
      ── 今日市場分析報告 ──
    </div>
    {report_html}
  </td></tr>

  <!-- ▌ 底部說明 -->
  <tr><td>
    <div style="background:#0f2044;padding:20px 36px;text-align:center;">
      <div style="font-size:13px;color:rgba(255,255,255,.7);margin-bottom:6px;">
        📎 詳細圖表報告請開啟附件 HTML 檔案
      </div>
      <div style="font-size:11px;color:rgba(255,255,255,.35);margin-top:8px;line-height:1.6;">
        本報告由 Google Gemini AI 自動生成，蒐集 {stats.get('total',0)} 篇全球財經新聞分析。<br>
        僅供參考，不構成任何投資建議，投資有風險，請審慎評估。
      </div>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body>
</html>"""

    def _format_report(self, text: str) -> str:
        """將 AI 生成的純文字報告轉為 HTML，識別 一、二、 章節標題"""
        if not text:
            return '<p style="color:#9ca3af;">報告內容暫時無法取得。</p>'

        section_nums = ('一、','二、','三、','四、','五、','六、','七、','八、','九、','十、')
        parts = []
        for line in text.split('\n'):
            s = line.strip()
            if not s:
                continue
            if any(s.startswith(n) for n in section_nums):
                parts.append(
                    f'<div style="font-size:15px;font-weight:700;color:#1e3a6e;'
                    f'margin:22px 0 8px;padding:8px 14px;'
                    f'background:linear-gradient(90deg,#eff6ff,#f8fafc);'
                    f'border-left:4px solid #1e40af;border-radius:0 8px 8px 0;">'
                    f'{s}</div>'
                )
            else:
                parts.append(
                    f'<p style="font-size:14px;color:#374151;line-height:1.85;'
                    f'margin:0 0 10px;text-align:justify;">{s}</p>'
                )
        return '\n'.join(parts)
