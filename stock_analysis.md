# 📈 全球股市影響力聲明監測系統 — Stock Analysis

> 每日自動蒐集全球財經新聞，透過 **Claude AI** 分析重量級人士聲明對股市的潛在影響，生成專業 HTML 報告與 1000 字繁中市場日報，定時寄送至指定信箱。

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Claude AI](https://img.shields.io/badge/Claude_AI-Anthropic-D97706?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## 目錄

- [專案簡介](#專案簡介)
- [核心功能](#核心功能)
- [系統架構](#系統架構)
- [安裝與設定](#安裝與設定)
- [執行方式](#執行方式)
- [Email 報告格式](#email-報告格式)
- [新聞來源](#新聞來源)
- [監測指數](#監測指數)
- [API 說明](#api-說明)
- [常見問題](#常見問題)

---

## 專案簡介

本系統針對**影響全球股市的關鍵聲明**進行每日自動監測，主要追蹤對象包含：

| 類別 | 對象範例 |
|------|----------|
| 🏦 央行官員 | Fed 主席、ECB 總裁、BOJ 總裁 |
| 💼 企業高層 | Fortune 500 CEO 財報說明與展望 |
| 🏛️ 政府要員 | 美國總統、財政部長、各國政策聲明 |
| 📊 知名投資人 | 巴菲特、索羅斯等市場意見領袖 |
| 🌍 地緣政治 | 貿易協議、制裁、衝突相關聲明 |

每日 08:00 自動執行，將分析結果以 **HTML 精美報告 + 1000 字專業日報** 形式寄送至指定信箱。

---

## 核心功能

### 🗞️ 多源新聞蒐集
- 同步蒐集 10+ 個 RSS 來源，每日 80–100 篇文章
- 支援 NewsAPI 選填擴充（每日額外 30 篇）
- 自動去重、HTML 標籤清洗

### 🤖 Claude AI 深度分析
每篇文章自動產出：

```json
{
  "is_market_moving": true,
  "impact_score": 9,
  "sentiment": "bearish",
  "affected_markets": ["S&P 500", "US Treasury", "Tech Sector"],
  "key_entity": "Federal Reserve Chair Powell",
  "key_statement": "Interest rates will remain higher for longer than markets expect",
  "reason": "Signals delayed rate cuts, pressuring equity valuations"
}
```

### 📝 1000 字市場日報（繁體中文）
由 Claude AI 自動撰寫，五大章節：

1. **今日市場概況** — 美歐亞股整體走勢
2. **重大聲明深度分析** — 逐一解析前 5–10 大影響事件
3. **板塊與區域影響** — 科技、金融、能源、各區域差異
4. **風險與機會分析** — 下行風險 + 潛在投資機會
5. **明日市場展望** — 走勢預測 + 關鍵待觀察事件

### 📊 HTML 互動報告
- 深色專業主題（GitHub Dark 風格）
- 即時主要指數行情條（8 大市場）
- Chart.js 情緒圓餅圖 + 影響分數長條圖
- 高影響警示卡片（紅/橙色標示，按分數排序）
- 完整市場影響事件列表（含連結）

### 📧 每日 Email 通知
- **信件本文**：統計摘要卡片 + 完整 1000 字分析報告
- **附件**：含互動圖表的 HTML 完整報告

---

## 系統架構

```
global_stock_monitor/
├── main.py                  # 主程式（含 schedule 每日排程）
├── run_once.py              # 單次執行（適合 Windows 工作排程器）
├── setup_and_run.py         # 互動式初始設定腳本
├── config.py                # 所有設定集中管理（RSS、指數、路徑）
├── .env                     # 環境變數（需自行建立，勿上傳 Git）
├── .env.example             # 環境變數範本
├── requirements.txt         # Python 套件相依清單
│
├── modules/
│   ├── data_collector.py    # 多源新聞蒐集（RSS + NewsAPI）
│   ├── analyzer.py          # Claude AI 批次分析 + 1000 字日報生成
│   ├── report_generator.py  # HTML 報告生成（Jinja2 + yfinance）
│   └── email_sender.py      # SMTP Email 發送（HTML body + 附件）
│
├── templates/
│   └── report_template.html # Jinja2 模板（深色主題 + Chart.js）
│
├── reports/                 # 每日 HTML 報告自動儲存
└── logs/                    # 執行日誌（依月份歸檔）
```

### 資料流程

```
RSS Feeds ──┐
NewsAPI ────┤──► DataCollector ──► Analyzer (Claude AI) ──► ReportGenerator ──► EmailSender
            │         │                   │                        │                  │
            │      80篇文章         JSON分析結果             HTML報告+日報        寄送信箱
            └─────────────────────────────────────────────────────────────────────────────
```

---

## 安裝與設定

### 系統需求

- Python **3.11+**
- 穩定網路連線（RSS 蒐集需對外連線）
- [Anthropic API Key](https://console.anthropic.com)（儲值 $5 USD 起）
- Gmail 帳號（需開啟兩步驟驗證）

### 1. 複製專案並安裝套件

```bash
git clone https://github.com/ALEXCHIU1202/python-calculator-demo.git
cd python-calculator-demo/global_stock_monitor
pip install -r requirements.txt
```

### 2. 建立環境設定

```bash
cp .env.example .env
```

編輯 `.env`：

```env
# ── 必填 ──────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxx     # Anthropic Console 取得
EMAIL_SENDER=your@gmail.com                  # Gmail 寄件帳號
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx           # Gmail 16 碼應用程式密碼
EMAIL_RECIPIENTS=your@gmail.com              # 收件人（逗號分隔多人）

# ── 選填 ──────────────────────────────────────
DAILY_RUN_TIME=08:00                         # 每日執行時間
MAX_NEWS_ITEMS=80                            # 最大蒐集文章數
NEWS_API_KEY=                                # NewsAPI Key（可留空）
```

> **Gmail 應用程式密碼**：[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
> → 選「郵件」→ 產生 16 碼密碼

### 3. 快速設定（互動式）

```bash
python setup_and_run.py
```

腳本會逐步引導填入設定，完成後立即執行一次。

---

## 執行方式

### 方式 A：持續背景執行

```bash
python main.py
```

啟動後立即執行一次，並於每日 `DAILY_RUN_TIME` 自動重複執行。適合伺服器部署。

### 方式 B：單次執行

```bash
python run_once.py
```

執行一次完整流程後結束。適合手動測試或 Windows 工作排程器。

### 方式 C：Windows 工作排程器（推薦生產環境）

1. 開啟「**工作排程器**」→ 建立基本工作
2. 觸發程序：每天 **08:00**
3. 動作：啟動程式
   - 程式：`python`
   - 引數：`D:\path\to\global_stock_monitor\run_once.py`
4. 儲存後，系統重開機仍會自動執行

---

## Email 報告格式

每日收到的郵件結構：

```
主旨：📊 全球股市日報｜2026/05/24

┌─────────────────────────────────────────┐
│  📊 全球股市影響力聲明監測日報          │
│  2026年05月24日 08:01                   │
├──────────┬──────────┬──────────┬────────┤
│ 80 篇    │ 32 件    │ 8 件     │ 6.4    │
│ 分析文章  │ 市場影響  │ 高影響   │ 平均分數│
├─────────────────────────────────────────┤
│ 情緒：▲多頭 18  ▼空頭 9  ●中性 5       │
│ ████████████████░░░░░░░                  │
├─────────────────────────────────────────┤
│ 今日市場分析報告                         │
│                                         │
│ 一、今日市場概況                         │
│ 全球股市今日呈現分化走勢...             │
│                                         │
│ 二、重大聲明與事件深度分析              │
│ ...（約 350 字）                        │
│                                         │
│ 三、板塊與區域影響評估                  │
│ ...（約 150 字）                        │
│                                         │
│ 四、風險與機會分析                      │
│ ...（約 150 字）                        │
│                                         │
│ 五、明日市場展望                        │
│ ...（約 200 字）                        │
├─────────────────────────────────────────┤
│  詳細圖表報告請開啟附件 HTML 檔案        │
└─────────────────────────────────────────┘
附件：report_20260524_0801.html
```

---

## 新聞來源

| 來源 | 類型 | 更新頻率 |
|------|------|----------|
| Reuters Business | 綜合財經 | 即時 |
| Yahoo Finance | 財經 | 即時 |
| MarketWatch | 財經 | 即時 |
| CNBC Top News | 財經 | 即時 |
| Federal Reserve | 央行官方 | 不定期 |
| Wall Street Journal | 財經 | 即時 |
| Investing.com | 財經 | 即時 |
| Financial Times | 財經 | 即時 |
| Bloomberg Markets | 財經 | 即時 |
| Seeking Alpha | 投資分析 | 即時 |
| NewsAPI（選填） | 綜合 | 即時 |

---

## 監測指數

| 代碼 | 名稱 | 區域 |
|------|------|------|
| `^GSPC` | S&P 500 | 美國 |
| `^DJI` | Dow Jones | 美國 |
| `^IXIC` | NASDAQ | 美國 |
| `^N225` | Nikkei 225 | 日本 |
| `^HSI` | Hang Seng | 香港 |
| `^GDAXI` | DAX | 德國 |
| `^FTSE` | FTSE 100 | 英國 |
| `000001.SS` | 上海指數 | 中國 |

行情資料由 [yfinance](https://github.com/ranaroussi/yfinance) 提供。

---

## API 說明

### Anthropic API 費用估算

| 操作 | 模型 | 約費用（每日） |
|------|------|----------------|
| 80 篇文章批次分析（8 批） | claude-opus-4-7 | ~$0.08 |
| 市場展望生成 | claude-opus-4-7 | ~$0.02 |
| 1000 字日報生成 | claude-opus-4-7 | ~$0.03 |
| **每日合計** | — | **~$0.13** |

> 每月約 **$4 USD**，Anthropic 新帳號儲值 $5 USD 可使用約 1 個月。

### 切換模型（降低成本）

於 `config.py` 修改：

```python
ANALYSIS_MODEL = 'claude-haiku-4-5'   # 最快、最便宜（每日約 $0.01）
ANALYSIS_MODEL = 'claude-sonnet-4-5'  # 平衡品質與成本（每日約 $0.04）
ANALYSIS_MODEL = 'claude-opus-4-7'    # 最高品質（每日約 $0.13）
```

---

## 常見問題

**Q：`credit balance is too low` 錯誤**

前往 [console.anthropic.com/settings/billing](https://console.anthropic.com/settings/billing) 儲值，最低 $5 USD。

---

**Q：Gmail 發送失敗**

確認以下三點：
1. Gmail 已開啟「兩步驟驗證」
2. 使用的是「應用程式密碼」（16 碼），不是 Gmail 登入密碼
3. `.env` 中 `EMAIL_PASSWORD` 不含空格（`abbwvrxncewfzfsy`，非 `abbw vrxn cewf zfsy`）

---

**Q：某些 RSS 來源回傳 0 篇**

部分 RSS（Reuters、Yahoo Finance）有地區限制或格式更新。可在 `config.py` 的 `RSS_FEEDS` 中調整或移除無效來源，不影響整體運作。

---

**Q：如何新增收件人**

`.env` 中用逗號分隔：

```env
EMAIL_RECIPIENTS=user1@gmail.com,user2@gmail.com,user3@company.com
```

---

**Q：如何變更每日執行時間**

`.env` 中修改（24 小時制）：

```env
DAILY_RUN_TIME=07:30   # 每日 07:30 執行
```

---

## 注意事項

- 本系統產出內容**僅供參考，不構成任何投資建議**
- `.env` 檔案含有敏感資訊，已列入 `.gitignore`，請勿上傳至公開 Git 倉庫
- 建議定期清理 `reports/` 資料夾，每份 HTML 報告約 200–500 KB
- Anthropic API 依 token 用量計費，建議於 Console 設定月度用量上限

---

## License

MIT License — 歡迎自由使用與修改。
