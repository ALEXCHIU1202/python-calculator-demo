"""
互動式設定腳本 — 引導你填入所有必要設定並立即執行分析
用法：python setup_and_run.py
"""
import getpass
import sys
from pathlib import Path


def ask(prompt: str, default: str = '') -> str:
    suffix = f' [{default}]' if default else ''
    val = input(f'{prompt}{suffix}: ').strip()
    return val if val else default


def main():
    print()
    print('=' * 55)
    print('  全球股市影響力聲明監測系統 — 初始設定')
    print('=' * 55)
    print()

    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        overwrite = ask('.env 已存在，是否重新設定？(y/N)', 'N')
        if overwrite.lower() != 'y':
            print('保留現有設定，直接執行…')
            _run()
            return

    print('請依序填入以下設定（直接按 Enter 使用預設值）')
    print()

    # API Key
    print('【1/4】Anthropic API Key')
    print('       取得方式：https://console.anthropic.com → API Keys → Create Key')
    api_key = ask('       請貼上 sk-ant-... Key')
    if not api_key.startswith('sk-'):
        print('       警告：Key 格式異常（應以 sk- 開頭），請確認後再試')
    print()

    # Gmail sender
    print('【2/4】Gmail 寄件帳號')
    print('       必須開啟「兩步驟驗證」才能使用應用程式密碼')
    email_sender = ask('       Gmail 地址')
    print()

    # Gmail app password
    print('【3/4】Gmail 應用程式密碼（16 碼）')
    print('       設定方式：Google 帳戶 > 安全性 > 兩步驟驗證 > 應用程式密碼')
    email_pw = getpass.getpass('       請輸入（輸入時不顯示）：')
    email_pw = email_pw.replace(' ', '')   # 去除空格
    print()

    # Recipients
    print('【4/4】收件人 Email')
    recipients = ask('       收件人（多人用逗號分隔）', 'qiukecheng41@gmail.com')
    print()

    # Run time
    run_time = ask('每日自動執行時間', '08:00')
    print()

    # Write .env
    env_content = (
        f'ANTHROPIC_API_KEY={api_key}\n'
        f'EMAIL_SENDER={email_sender}\n'
        f'EMAIL_PASSWORD={email_pw}\n'
        f'EMAIL_RECIPIENTS={recipients}\n'
        f'DAILY_RUN_TIME={run_time}\n'
        f'EMAIL_SMTP_HOST=smtp.gmail.com\n'
        f'EMAIL_SMTP_PORT=587\n'
        f'MAX_NEWS_ITEMS=80\n'
    )
    env_path.write_text(env_content, encoding='utf-8')

    print('=' * 55)
    print('  .env 設定完成')
    print(f'  API Key  : sk-...{api_key[-6:] if len(api_key) > 6 else "?"}')
    print(f'  寄件帳號 : {email_sender}')
    print(f'  收件人   : {recipients}')
    print(f'  每日時間 : {run_time}')
    print('=' * 55)
    print()

    go = ask('設定完成，是否立即執行一次？(Y/n)', 'Y')
    if go.lower() != 'n':
        _run()


def _run():
    print()
    print('正在執行分析管線…（預計需要 2–5 分鐘）')
    print()
    import runpy
    sys.argv = ['run_once.py']
    try:
        runpy.run_path(str(Path(__file__).parent / 'run_once.py'), run_name='__main__')
    except SystemExit:
        pass


if __name__ == '__main__':
    main()
