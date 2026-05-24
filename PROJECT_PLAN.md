# 🚀 AlpacaBot — 全自動美股交易系統 專案計劃

> 版本：v1.0 | 建立日期：2026-05-24
> 本文件為專案核心記憶，新進開發者請先完整閱讀。

---

## 📌 專案概述

| 項目 | 說明 |
|---|---|
| 平台 | Alpaca Markets（支援 Paper & Live） |
| 語言 | Python 3.11+ |
| 儀表板 | Streamlit |
| 自動化 | GitHub Actions |
| 報告格式 | JSON（Model）+ HTML/Email（View） |
| 策略描述 | JSON（新增策略不需改 Python） |
| 多帳戶 | 支援，每帳戶同時只能使用一個策略 |

---

## ⚠️ 重要聲明

> 本系統所有輸出內容（排名、績效、分析）**僅供資訊整理與研究參考，不構成投資建議**。
> 投資人應自行評估風險，本系統不負任何投資盈虧責任。

---

## 🗂️ 專案目錄結構

```
alpacabot/
├── accounts/                  # 帳戶設定
│   └── accounts.json
├── strategies/                # 策略 JSON 定義
│   ├── top10_nasdaq.json
│   └── momentum.json
├── reports/                   # 歷史報告儲存
│   └── YYYY-MM-DD/
│       ├── report_model.json
│       └── report_email.html
├── core/                      # 核心引擎
│   ├── alpaca_client.py       # Alpaca API 封裝
│   ├── strategy_engine.py     # 策略執行引擎
│   ├── order_manager.py       # 下單管理
│   ├── rebalancer.py          # 再平衡邏輯
│   └── market_data.py         # 市場資料取得
├── report/                    # 報告系統（Model/View 分離）
│   ├── report_model.py        # 產生 JSON 報告 Model
│   └── report_view.py         # 渲染 Email HTML View
├── dashboard/                 # Streamlit 儀表板
│   └── app.py
├── notifications/             # 通知系統
│   └── email_sender.py
├── .github/
│   └── workflows/
│       └── daily_trading.yml  # GitHub Actions 主流程
├── tests/                     # 測試案例
│   ├── test_phase1.py
│   ├── test_phase2.py
│   ├── test_phase3.py
│   ├── test_phase4.py
│   └── test_phase5.py
├── CLAUDE.md                  # 專案記憶（給 Claude/開發者）
└── PROJECT_PLAN.md            # 本文件
```

---

## 🔑 核心設計原則

1. **策略即 JSON**：新增交易策略只需新增一個 JSON 檔，不動 Python
2. **Model/View 分離**：日報的資料（JSON）與呈現（HTML/Email）完全分離
3. **多帳戶架構**：一個 workflow 走過所有帳戶，各帳戶獨立執行對應策略
4. **歷史可回查**：每日報告永久儲存，使用者可查詢任意日期
5. **整數股**：所有買賣只買整數股（不支援碎股）
6. **10% 均等配置**：Top 10 股票各佔帳戶資金 10%
7. **再平衡觸發**：① 每月初 ② 有新資金進入時

---

## 📋 開發階段總覽

| 階段 | 名稱 | 主要功能 | 估計工時 |
|---|---|---|---|
| Phase 1 | 基礎建設 | Alpaca 連線、帳戶查詢、市場資料 | 3 天 |
| Phase 2 | 策略引擎 | JSON 策略載入、下單、再平衡 | 4 天 |
| Phase 3 | 儀表板 | Streamlit Dashboard | 4 天 |
| Phase 4 | 報告系統 | JSON Model、Email View、歷史儲存 | 3 天 |
| Phase 5 | GitHub Actions | 自動化主流程、多帳戶 workflow | 2 天 |
| Phase 6 | 進階分析 | 預測、本益比、NAV/回撤對比圖 | 4 天 |

> ✅ **每個階段測試通過後才開始下一階段**

---

## 📦 Phase 1：基礎建設

### 功能清單
- [ ] Alpaca API 封裝（Paper & Live 切換）
- [ ] 帳戶資訊查詢（現金、持倉、帳戶淨值）
- [ ] 市場資料取得（即時股價、歷史 K 線）
- [ ] NASDAQ Top 10 市值股票篩選
- [ ] 多帳戶設定檔（`accounts.json`）

### accounts.json 結構
```json
{
  "accounts": [
    {
      "id": "acc_001",
      "name": "我的Paper帳戶",
      "api_key": "PKNVUQMS6TPTNIYJFJ2EBDLKTV",
      "api_secret": "FWiEYR3L2aNT7GuieaBKuNkjDcmzHS2TKLufC8Ph2fP2",
      "base_url": "https://paper-api.alpaca.markets",
      "active_strategy": "top10_nasdaq",
      "email": "user@example.com",
      "enabled": true
    }
  ]
}
```

### ✅ Phase 1 測試案例（test_phase1.py）
```
TC-1-01  連線至 Alpaca API 成功，回傳帳戶狀態 ACTIVE
TC-1-02  查詢現金水位，數值 > 0
TC-1-03  查詢持倉清單，格式正確（symbol, qty, market_value）
TC-1-04  取得 AAPL 即時股價，回傳數值 > 0
TC-1-05  取得 AAPL 過去 30 天歷史 K 線，筆數 >= 20
TC-1-06  篩選 NASDAQ 市值前 10，回傳 10 個 symbol
TC-1-07  多帳戶：載入 accounts.json，正確解析 2 個以上帳戶
TC-1-08  Paper / Live 環境切換，連線 URL 正確
TC-1-09  API Key 錯誤時，拋出明確錯誤訊息
TC-1-10  市場休市時，取得資料仍正常（回傳最後成交價）
```

---

## 📦 Phase 2：策略引擎

### 功能清單
- [ ] JSON 策略載入器
- [ ] 策略執行引擎（買進/賣出邏輯）
- [ ] 下單管理（市價單、限價單、整數股計算）
- [ ] 再平衡引擎（月初 + 新資金觸發）
- [ ] 帳戶策略切換

### 策略 JSON 結構（top10_nasdaq.json）
```json
{
  "strategy_id": "top10_nasdaq",
  "name": "NASDAQ 市值前十均等配置",
  "description": "每天買入 NASDAQ 市值前 10 名股票，各佔帳戶總資金 10%",
  "version": "1.0",
  "rules": {
    "universe": "NASDAQ_TOP10_MARKET_CAP",
    "max_positions": 10,
    "weight_per_stock": 0.10,
    "order_type": "market",
    "fractional_shares": false,
    "rebalance_triggers": ["monthly_first_day", "new_cash_inflow"],
    "min_cash_reserve": 0.02
  },
  "filters": {
    "min_price": 5,
    "min_volume": 1000000,
    "exclude_symbols": []
  },
  "risk": {
    "max_single_loss_pct": 0.15,
    "stop_loss_enabled": false
  }
}
```

### momentum.json（動能策略範例）
```json
{
  "strategy_id": "momentum",
  "name": "動能策略",
  "description": "買入過去 20 天漲幅最大的 10 檔 NASDAQ 股票",
  "version": "1.0",
  "rules": {
    "universe": "NASDAQ_TOP100",
    "lookback_days": 20,
    "max_positions": 10,
    "weight_per_stock": 0.10,
    "order_type": "market",
    "fractional_shares": false,
    "rebalance_triggers": ["monthly_first_day", "new_cash_inflow"]
  },
  "filters": {
    "min_price": 10,
    "min_volume": 500000,
    "exclude_symbols": []
  },
  "risk": {
    "max_single_loss_pct": 0.20,
    "stop_loss_enabled": true,
    "stop_loss_pct": 0.08
  }
}
```

### ✅ Phase 2 測試案例（test_phase2.py）
```
TC-2-01  載入 top10_nasdaq.json，正確解析所有欄位
TC-2-02  計算每檔應買入股數（10% × 帳戶淨值 ÷ 股價，取整數）
TC-2-03  帳戶 $100,000、AAPL $200，應買入 50 股（整數）
TC-2-04  新增策略 JSON 後，引擎可自動載入，無需改 Python
TC-2-05  帳戶切換策略，舊策略停止，新策略生效
TC-2-06  同一帳戶同一時間只有一個策略執行
TC-2-07  月初觸發再平衡，部位調整至目標權重 ±1%
TC-2-08  新資金進入（現金增加 > 5%），觸發再平衡
TC-2-09  下單成功，回傳 order_id，狀態為 filled / accepted
TC-2-10  市場休市時不下單，記錄 skip 原因
TC-2-11  買入金額超過可用現金，自動減量至可用範圍
TC-2-12  止損觸發（若策略啟用），自動送出賣單
```

---

## 📦 Phase 3：Streamlit 儀表板

### 功能清單
- [ ] 多帳戶切換選單
- [ ] 現金水位卡片
- [ ] 持倉清單表格（含 1D/1W/1M 績效）
- [ ] Top 10 股票績效視覺化
- [ ] 三大關注類別（自訂股票清單）
- [ ] NAV 走勢圖（vs NASDAQ、S&P500，可勾選）
- [ ] 回撤圖（Drawdown）
- [ ] 歷史報告回查
- [ ] 本益比（P/E）每日顯示

### 儀表板頁面規劃

```
┌─────────────────────────────────────────────────┐
│  🏦 AlpacaBot Dashboard   [帳戶選單 ▼]          │
├──────────┬──────────┬──────────┬────────────────┤
│ 💵現金   │📈帳戶淨值 │📊今日損益 │🔄 最後更新時間 │
│ $100,000 │$100,000  │ +$0.00   │ 2026-05-24     │
├──────────┴──────────┴──────────┴────────────────┤
│ 📋 持倉清單                                      │
│  Symbol | 股數 | 成本 | 現價 | 1D% | 1W% | 1M% │
├─────────────────────────────────────────────────┤
│ 📊 Top 10 績效長條圖（可排序）                   │
├─────────────────────────────────────────────────┤
│ 📈 NAV 走勢  ☑NASDAQ ☑S&P500 ☐我的帳戶        │
├─────────────────────────────────────────────────┤
│ 📉 回撤圖（Drawdown Chart）                      │
├─────────────────────────────────────────────────┤
│ 👁 我的關注清單                                   │
│  [科技股] [ETF] [生技股]                         │
└─────────────────────────────────────────────────┘
```

### ✅ Phase 3 測試案例（test_phase3.py）
```
TC-3-01  Dashboard 啟動，無 Error，頁面正常載入
TC-3-02  切換帳戶，數據正確更新
TC-3-03  現金水位顯示正確（與 API 一致）
TC-3-04  持倉清單：1D/1W/1M 績效計算正確
TC-3-05  Top 10 長條圖正確顯示 10 個 symbol
TC-3-06  NAV 圖：勾選 NASDAQ，顯示 NASDAQ 走勢線
TC-3-07  NAV 圖：取消勾選 S&P500，線條消失
TC-3-08  回撤圖：最大回撤數值與計算一致
TC-3-09  本益比：至少 5 檔股票顯示 P/E 數值
TC-3-10  歷史報告：點選日期，正確載入該日 JSON
TC-3-11  關注清單：新增股票後，頁面即時更新
TC-3-12  RWD：手機版（375px）不跑版
```

---

## 📦 Phase 4：報告系統

### 功能清單
- [ ] 每日報告 JSON Model 產生
- [ ] Email HTML View 渲染
- [ ] 每天上午 06:00 發送 Email
- [ ] 歷史報告儲存（reports/YYYY-MM-DD/）
- [ ] 交易即時通知（有成交時立刻發 Email）

### 每日報告 JSON Model（report_model.json）
```json
{
  "report_date": "2026-05-24",
  "account_id": "acc_001",
  "account_name": "我的Paper帳戶",
  "summary": {
    "cash": 100000,
    "portfolio_value": 100000,
    "nav": 100000,
    "daily_pnl": 0,
    "daily_pnl_pct": 0.0,
    "total_pnl": 0,
    "total_pnl_pct": 0.0,
    "max_drawdown_pct": 0.0
  },
  "positions": [
    {
      "symbol": "AAPL",
      "qty": 50,
      "avg_cost": 195.00,
      "current_price": 198.50,
      "market_value": 9925,
      "unrealized_pnl": 175,
      "pnl_1d_pct": 1.23,
      "pnl_1w_pct": 2.45,
      "pnl_1m_pct": -0.87,
      "pe_ratio": 28.5
    }
  ],
  "top10_nasdaq": [
    {
      "rank": 1,
      "symbol": "AAPL",
      "price": 198.50,
      "market_cap_b": 3050,
      "pct_change_1d": 1.23,
      "predicted_next_day_pct": 0.45,
      "pe_ratio": 28.5
    }
  ],
  "watchlist": {
    "tech": ["AAPL", "MSFT", "NVDA"],
    "etf": ["QQQ", "SPY", "VGT"],
    "biotech": ["MRNA", "BNTX", "GILD"]
  },
  "trades_today": [
    {
      "time": "09:35:00",
      "symbol": "AAPL",
      "side": "buy",
      "qty": 50,
      "price": 195.00,
      "status": "filled"
    }
  ],
  "benchmark": {
    "nasdaq_1d_pct": 0.85,
    "sp500_1d_pct": 0.62
  },
  "disclaimer": "本報告僅供資訊整理與研究參考，不構成投資建議。"
}
```

### Email 通知類型

| 類型 | 觸發時機 | 寄送內容 |
|---|---|---|
| 日報 | 每天 06:00 | 帳戶摘要、持倉、Top10、損益 |
| 交易通知 | 有成交時即時 | 哪檔、買/賣、股數、成交價 |
| 再平衡通知 | 再平衡執行後 | 調整明細、前後部位對比 |
| 風險警示 | 單日虧損 > 5% | 立即通知，說明哪檔造成 |

### ✅ Phase 4 測試案例（test_phase4.py）
```
TC-4-01  產生 report_model.json，欄位完整無缺漏
TC-4-02  JSON 報告存入 reports/2026-05-24/ 目錄
TC-4-03  report_view.py 讀取 JSON，渲染出 HTML 不報錯
TC-4-04  Email HTML 在 Gmail、Outlook 正確顯示
TC-4-05  06:00 定時發送，收件匣收到
TC-4-06  交易成交後 5 分鐘內收到即時通知 Email
TC-4-07  Email 包含免責聲明文字
TC-4-08  回查 7 天前報告，JSON 可正確載入
TC-4-09  多帳戶各自發送各自的報告
TC-4-10  Email 發送失敗時，錯誤記錄到 log，不中斷主流程
```

---

## 📦 Phase 5：GitHub Actions 自動化

### 功能清單
- [ ] 主 Workflow（每天執行一次）
- [ ] 依序走過所有啟用帳戶
- [ ] 根據帳戶選定策略執行買賣
- [ ] 產生報告並上傳 Artifact
- [ ] 執行結果通知

### GitHub Actions Workflow（daily_trading.yml）
```yaml
name: Daily Trading & Report

on:
  schedule:
    - cron: '30 13 * * 1-5'   # UTC 13:30 = 美東 09:30（開盤）
  workflow_dispatch:            # 手動觸發

jobs:
  run-all-accounts:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Load accounts & run strategies
        env:
          ACCOUNTS_CONFIG: ${{ secrets.ACCOUNTS_CONFIG }}
          EMAIL_PASSWORD: ${{ secrets.EMAIL_PASSWORD }}
        run: python core/strategy_engine.py --mode=daily

      - name: Generate daily reports
        run: python report/report_model.py

      - name: Send email notifications
        run: python notifications/email_sender.py

      - name: Upload reports
        uses: actions/upload-artifact@v4
        with:
          name: daily-reports-${{ github.run_id }}
          path: reports/
```

### ✅ Phase 5 測試案例（test_phase5.py）
```
TC-5-01  Workflow 手動觸發，所有 step 成功（綠燈）
TC-5-02  兩個帳戶設定，Workflow 依序處理兩個帳戶
TC-5-03  帳戶 A 執行策略 A、帳戶 B 執行策略 B，互不干擾
TC-5-04  某帳戶 API Key 失效，該帳戶跳過但其他繼續執行
TC-5-05  報告 Artifact 正確上傳，可下載
TC-5-06  Secrets 不外洩（log 中無明文 API Key）
TC-5-07  美股休市日（週末/假日），Workflow 自動跳過下單
TC-5-08  Cron 排程時間正確（美東 09:30）
TC-5-09  執行時間 < 10 分鐘（不超出 Actions 限制）
TC-5-10  Workflow 失敗時，GitHub 寄出失敗通知信
```

---

## 📦 Phase 6：進階分析

### 功能清單
- [ ] 次日漲跌預測（技術指標模型）
- [ ] 本益比（P/E Ratio）每日計算
- [ ] NAV vs NASDAQ vs S&P500 對比走勢圖
- [ ] 最大回撤（Max Drawdown）計算與視覺化
- [ ] NASDAQ Top 10 每日輪動分析

### 預測模型說明（白話）
```
本系統使用技術指標（非 AI）進行次日方向預測：
- RSI（相對強弱指標）：衡量股票是否超買或超賣
- MACD（趨勢動能）：判斷上漲或下跌動能
- 布林通道：判斷股價是否偏離正常範圍
預測結果僅為參考，不代表實際漲跌，請勿作為投資依據。
```

### ✅ Phase 6 測試案例（test_phase6.py）
```
TC-6-01  P/E Ratio 計算：AAPL P/E 與 Yahoo Finance 誤差 < 5%
TC-6-02  NAV 走勢圖：含我的帳戶、NASDAQ、S&P500 三條線
TC-6-03  勾選/取消 NASDAQ，圖表即時更新
TC-6-04  最大回撤計算：測試資料集回撤 -20%，計算結果 -20% ±0.5%
TC-6-05  次日預測輸出格式：{symbol, direction, confidence_pct}
TC-6-06  預測報告包含免責聲明
TC-6-07  Top 10 輪動：本週 vs 上週名單差異正確列出
```

---

## 🔐 安全性設計

| 項目 | 做法 |
|---|---|
| API Key | 存在 GitHub Secrets，不進 repo |
| Email 密碼 | 存在 GitHub Secrets |
| accounts.json | 本地開發用，`.gitignore` 排除 |
| Token 輪換 | 建議每 90 天更換一次 API Key |

---

## 📚 技術堆疊

| 用途 | 套件 |
|---|---|
| Alpaca API | `alpaca-trade-api` / `alpaca-py` |
| 市場資料 | `yfinance`、`alpaca-py` |
| 儀表板 | `streamlit` |
| 圖表 | `plotly` |
| Email | `smtplib` + `jinja2`（HTML 模板） |
| 資料處理 | `pandas`、`numpy` |
| 技術指標 | `ta-lib` / `pandas-ta` |
| 測試 | `pytest` |
| 排程 | GitHub Actions（雲端）、`schedule`（本地測試） |

---

## 🚦 開發里程碑

```
Week 1：Phase 1 完成 + 測試通過
Week 2：Phase 2 完成 + 測試通過
Week 3：Phase 3 完成 + 測試通過
Week 4：Phase 4 完成 + 測試通過
Week 5：Phase 5 完成 + 測試通過
Week 6：Phase 6 完成 + 整合測試
Week 7：End-to-End 測試、Bug Fix、文件補完
Week 8：上線（切換至 Live 帳戶）
```

---

## 🧠 CLAUDE.md 專案記憶摘要

> 每次開發前，Claude 或新進開發者應讀取本節。

- 策略加在 `strategies/*.json`，不改 Python
- 報告 Model 在 `report/report_model.py`，View 在 `report/report_view.py`
- GitHub Actions 是唯一的生產排程方式
- 所有 API Key 走 GitHub Secrets，不進 code
- 每個 Phase 必須 pytest 全綠才進下一個
- 再平衡邏輯：月初 + 新資金（現金增加 > 5%）
- 只買整數股，Top 10 各 10% 均配
- 免責聲明必須出現在每份報告與 Email 中
