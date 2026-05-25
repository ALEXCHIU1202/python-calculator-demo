import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(dotenv_path=BASE_DIR / '.env', override=True)


class Config:
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')

    EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    EMAIL_RECIPIENTS = [r.strip() for r in os.getenv('EMAIL_RECIPIENTS', '').split(',') if r.strip()]
    EMAIL_SMTP_HOST = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))

    DAILY_RUN_TIME = os.getenv('DAILY_RUN_TIME', '08:00')

    REPORT_DIR = BASE_DIR / 'reports'
    LOG_DIR = BASE_DIR / 'logs'
    TEMPLATE_DIR = BASE_DIR / 'templates'

    MAX_NEWS_ITEMS = int(os.getenv('MAX_NEWS_ITEMS', '80'))
    ANALYSIS_MODEL = 'claude-opus-4-7'

    # Groq（免費，優先使用，速度快、無 IP 限制）
    GROQ_API_KEY   = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL     = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

    # Google Gemini（備用免費方案）
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    GEMINI_MODEL   = os.getenv('GEMINI_MODEL', 'models/gemini-1.5-flash')

    RSS_FEEDS = [
        {'name': 'Reuters Business',   'url': 'https://feeds.reuters.com/reuters/businessNews',              'category': 'general'},
        {'name': 'Yahoo Finance',       'url': 'https://finance.yahoo.com/rss/headline',                      'category': 'finance'},
        {'name': 'MarketWatch',         'url': 'https://feeds.marketwatch.com/marketwatch/topstories/',        'category': 'finance'},
        {'name': 'CNBC Top News',       'url': 'https://www.cnbc.com/id/100003114/device/rss/rss.html',       'category': 'finance'},
        {'name': 'Federal Reserve',     'url': 'https://www.federalreserve.gov/feeds/press_all.xml',          'category': 'central_bank'},
        {'name': 'WSJ Markets',         'url': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',               'category': 'finance'},
        {'name': 'Investing.com',       'url': 'https://www.investing.com/rss/news.rss',                      'category': 'finance'},
        {'name': 'FT Home',             'url': 'https://www.ft.com/rss/home/us',                              'category': 'finance'},
        {'name': 'Bloomberg Markets',   'url': 'https://feeds.bloomberg.com/markets/news.rss',                'category': 'finance'},
        {'name': 'Seeking Alpha',       'url': 'https://seekingalpha.com/market_currents.xml',                'category': 'finance'},
    ]

    MARKET_INDICES = {
        '^GSPC':    {'name': 'S&P 500',     'region': '美國'},
        '^DJI':     {'name': 'Dow Jones',   'region': '美國'},
        '^IXIC':    {'name': 'NASDAQ',      'region': '美國'},
        '^N225':    {'name': 'Nikkei 225',  'region': '日本'},
        '^HSI':     {'name': 'Hang Seng',   'region': '香港'},
        '^GDAXI':   {'name': 'DAX',         'region': '德國'},
        '^FTSE':    {'name': 'FTSE 100',    'region': '英國'},
        '000001.SS':{'name': 'Shanghai',    'region': '中國'},
    }
