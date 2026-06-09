"""
Phase 4 - Email 通知模組
日報、即時交易通知、風險警示
"""
import smtplib, os, json
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from datetime             import date
from report.report_view   import render_email_html, render_trade_alert
from report.report_model  import load_report, build_report, list_report_dates
from core.alpaca_client   import load_accounts

def _get_email_cfg():
    cfg  = load_accounts()
    ecfg = cfg.get("email_config", {})
    # EMAIL_SENDER 環境變數優先（GitHub Actions Secret），否則用 JSON 設定
    sender = (os.environ.get("EMAIL_SENDER", "")
              or ecfg.get("sender", ""))
    return {
        "host":     ecfg.get("smtp_host", "smtp.gmail.com"),
        "port":     ecfg.get("smtp_port", 587),
        "sender":   sender,
        "password": os.environ.get(ecfg.get("password_env", "EMAIL_PASSWORD"), ""),
    }

def send_email(to: str, subject: str, html_body: str):
    ecfg = _get_email_cfg()
    if not ecfg["password"]:
        print(f"  ⚠️ EMAIL_PASSWORD 未設定，跳過發送（to: {to}）")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = ecfg["sender"]
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP(ecfg["host"], ecfg["port"]) as smtp:
            smtp.starttls()
            smtp.login(ecfg["sender"], ecfg["password"])
            smtp.sendmail(ecfg["sender"], to, msg.as_string())
        print(f"  ✅ Email 已發送至 {to}")
        return True
    except Exception as e:
        print(f"  ❌ Email 發送失敗: {e}")
        return False

def send_daily_reports(report_date: str = None):
    if not report_date:
        report_date = date.today().strftime("%Y-%m-%d")
    reports = build_report(report_date=report_date)
    cfg     = load_accounts()
    acc_map = {a["id"]: a for a in cfg["accounts"]}

    for report in reports:
        acc_id = report["account_id"]
        email  = acc_map.get(acc_id, {}).get("email", "")
        if not email:
            continue
        html    = render_email_html(report)
        subject = f"📊 AlpacaBot 日報 {report_date} | {report['account_name']} | 今日損益 {report['summary']['daily_pnl_pct']:+.2f}%"
        send_email(email, subject, html)

def send_trade_alert(account_email: str, account_name: str, trade: dict):
    side   = "買入" if trade["side"] == "buy" else "賣出"
    subject = f"🔔 交易通知 | {account_name} {side} {trade['symbol']} x {trade['qty']}"
    html    = render_trade_alert(trade)
    send_email(account_email, subject, html)

def send_risk_alert(account_email: str, account_name: str, loss_pct: float, detail: str):
    subject = f"⚠️ 風險警示 | {account_name} 單日虧損 {loss_pct:.2f}%"
    html = f"""
    <div style="font-family:Arial;padding:16px;background:#fff3e0;border-radius:8px;border-left:4px solid #e65100">
      <h2 style="color:#bf360c">⚠️ 風險警示</h2>
      <p>帳戶：<b>{account_name}</b></p>
      <p>今日虧損：<b style="color:#c62828">{loss_pct:.2f}%</b></p>
      <p>詳情：{detail}</p>
      <p style="color:#9e9e9e;font-size:0.8rem">⚠️ 本通知僅供參考，不構成投資建議。</p>
    </div>
    """
    send_email(account_email, subject, html)

if __name__ == "__main__":
    send_daily_reports()
