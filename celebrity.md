# 📊 全球股市影響力聲明監測系統

> **Celebrity Statement Market Monitor** — 每日自動追蹤全球重量級人士聲明，分析其對股市的潛在影響，並透過 Email 發送 1000 字專業日報。

---

## 專案簡介

本系統蒐集來自全球各大財經媒體、央行官網、RSS 訂閱的即時新聞，透過 **Claude AI** 分析每則聲明的市場影響力，自動產出 HTML 視覺化報告與繁體中文 1000 字市場日報，每日定時寄送至指定信箱。

**監測對象包含：**
- 🏦 央行官員（Fed、ECB、BOJ 等）政策聲明
- 💼 企業 CEO 財報說明與展望
- 🏛️ 政府領導人政策宣布
- 📈 知名投資人市場看法
- 🌍 地緣政治事件聲明

---

## 功能特色

| 功能 | 說明 |
|------|------|
| **多源新聞蒐集** | Reuters、Yahoo Finance、CNBC、MarketWatch、WSJ、FT、Bloomberg、Fed、Investing.com 等 10+ 個 RSS 來源 |
| **Claude AI 分析** | 每篇文章自動評分（影響力 1–10）、情緒判斷（多頭/空頭/中性）、核心聲明萃取 |
| **1000 字市場日報** | Claude AI 生成繁體中文專業分析報告，含五大章節：市場概況、重大事件分析、板塊影響、風險機會、明日展望 |
| **即時指數行情** | S&P 500、NASDAQ、道瓊、日經、恆生、DAX、FTSE 100、上証 |
| **HTML 互動報告** | 深色專業主題、Chart.js 圓餅圖與長條圖、高影響警示卡片 |
| **每日 Email 通知** | HTML 精美排版 + 完整報告 HTML 附件，每日 08:00 自動發送 |

---

## 系統架構

```
global_stock_monitor/
├── main.py                  # 主程式（含每日排程 scheduler）
├── run_once.py              # 單次執行（適合 Windows 工作排程器）
├── config.py                # 所有設定集中管理
├── .env.example             # 環境變數範本
├── requirements.txt         # Python 套件相依
│
├── modules/
│   ├── data_collector.py    # 多源新聞蒐集（RSS + NewsAPI）
│   ├── analyzer.py          # Claude AI 分析 + 1000 字日報生成
│   ├── report_generator.py  # HTML 報告生成（含即時股價）
│   └── email_sender.py      # Email 發送（HTML + 附件）
│
├── templates/
│   └── report_template.html # Jinja2 HTML 報告模板
│
├── reports/                 # 自動儲存每日 HTML 報告
└── logs/                    # 執行日誌（月份歸檔）
```

### 執行流程

```
蒐集新聞 → Claude AI 批次分析 → 生成 1000 字日報 → 渲染 HTML 報告 → 發送 Email
```

---

## 快速開始

### 1. 安裝套件

```bash
cd global_stock_monitor
pip install -r requirements.txt
```

**requirements.txt 內容：**
```
anthropic>=0.30.0
requests>=2.31.0
feedparser>=6.0.11
beautifulsoup4>=4.12.3
jinja2>=3.1.4
schedule>=1.2.2
python-dotenv>=1.0.1
yfinance>=0.2.46
lxml>=5.2.0
```

### 2. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`，填入以下必要設定：

```env
# 必填：Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx

# 必填：Gmail 寄件設定
EMAIL_SENDER=your@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx   # 16 碼應用程式密碼
EMAIL_RECIPIENTS=recipient@gmail.com

# 每日執行時間（預設 08:00）
DAILY_RUN_TIME=08:00

# 選填：NewsAPI（可增加新聞量）
NEWS_API_KEY=
```

> **Gmail 應用程式密碼設定：**
> Google 帳戶 → 安全性 → 兩步驟驗證 → 應用程式密碼 → 選擇「郵件」→ 產生 16 碼密碼

### 3. 執行

**方式 A：持續背景執行（推薦開發測試）**
```bash
python main.py
```
啟動後立即執行一次，並於每日 `DAILY_RUN_TIME` 自動重複執行。

**方式 B：單次執行（推薦 Windows 工作排程器）**
```bash
python run_once.py
```

**方式 C：Windows 工作排程器設定**
1. 開啟「工作排程器」→ 建立基本工作
2. 觸發程序：每天 08:00
3. 動作：啟動程式 → `python` → 引數 `C:\path\to\run_once.py`

---

## Email 報告格式

每日收到的郵件包含：

### 📧 信件本文
- 數據摘要卡片（分析文章數、市場影響事件、高影響事件、平均分數）
- 情緒條形圖（多頭 / 空頭 / 中性 比例）
- **1000 字市場分析日報**（五章節）：
  1. 今日市場概況
  2. 重大聲明與事件深度分析
  3. 板塊與區域影響評估
  4. 風險與機會分析
  5. 明日市場展望

### 📎 附件（HTML 報告）
- 即時主要指數行情條（含漲跌幅）
- 情緒分布圓餅圖 + 影響分數長條圖
- 高影響警示卡（紅/橙色標示）
- 完整市場影響事件列表

---

## 監測指數

| 代碼 | 名稱 | 區域 |
|------|------|------|
| ^GSPC | S&P 500 | 美國 |
| ^DJI | Dow Jones | 美國 |
| ^IXIC | NASDAQ | 美國 |
| ^N225 | Nikkei 225 | 日本 |
| ^HSI | Hang Seng | 香港 |
| ^GDAXI | DAX | 德國 |
| ^FTSE | FTSE 100 | 英國 |
| 000001.SS | Shanghai | 中國 |

---

## 新聞來源

| 來源 | 類型 |
|------|------|
| Reuters Business | 綜合財經 |
| Yahoo Finance | 財經 |
| MarketWatch | 財經 |
| CNBC Top News | 財經 |
| Federal Reserve | 央行 |
| Wall Street Journal | 財經 |
| Investing.com | 財經 |
| Financial Times | 財經 |
| Bloomberg Markets | 財經 |
| Seeking Alpha | 投資 |
| NewsAPI（選填） | 綜合 |

---

## 技術說明

### AI 分析流程

每批次（10 篇）送入 Claude，要求回傳 JSON 格式：

```json
{
  "is_market_moving": true,
  "impact_score": 9,
  "sentiment": "bearish",
  "affected_markets": ["S&P 500", "US Treasury", "Tech Sector"],
  "key_entity": "Federal Reserve Chair",
  "key_statement": "Interest rates will remain higher for longer...",
  "reason": "Signals delayed rate cuts, pressures equity valuations"
}
```

### 使用模型

- **分析模型**：`claude-opus-4-7`（可於 `config.py` 調整）
- **每日報告**：最多輸出 2200 tokens（約 1000 繁中字）

---

## 環境需求

- Python 3.11+
- Anthropic API Key（[取得連結](https://console.anthropic.com/)）
- Gmail 帳號（需開啟兩步驟驗證）
- 穩定網路連線（蒐集 RSS 需對外連線）

---

## 注意事項

- 本系統產出內容**僅供參考，不構成任何投資建議**
- Anthropic API 依使用量計費，建議設定用量上限
- RSS 來源若有變動可於 `config.py` 的 `RSS_FEEDS` 調整
- 報告自動儲存於 `reports/` 資料夾，建議定期清理

---

## License

MIT License — 自由使用與修改，請勿用於商業投資顧問服務。
