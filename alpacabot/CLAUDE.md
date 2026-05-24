# AlpacaBot — 專案記憶文件
> 給 Claude 和未來開發者快速上手用

## 快速概覽
- 全自動美股交易系統，基於 Alpaca Markets API
- Python 3.11 + Streamlit Dashboard + GitHub Actions 每日自動執行

## 最重要的設計原則（必讀）
1. **策略 = JSON**：`strategies/*.json`，新增策略不動 Python
2. **Model/View 分離**：`report/report_model.py`（資料）vs `report/report_view.py`（呈現）
3. **每個 Phase 測試全綠才進下一個**
4. **只買整數股**，Top 10 各 10% 均配
5. **免責聲明**必須出現在所有報告與 Email

## 帳戶設定
- 檔案：`accounts/accounts.json`
- 多帳戶支援，每帳戶獨立設定 `active_strategy`
- GitHub Actions 中用 `ACCOUNTS_JSON` secret 傳入

## 目錄速查
| 目錄 | 用途 |
|---|---|
| `core/` | Alpaca 連線、策略引擎、市場資料 |
| `strategies/` | JSON 策略定義 |
| `report/` | Model（JSON）和 View（HTML/Email） |
| `dashboard/` | Streamlit app |
| `notifications/` | Email 發送 |
| `reports/` | 歷史報告（YYYY-MM-DD/report_{acc_id}.json） |
| `tests/` | pytest 測試 |
| `.github/workflows/` | GitHub Actions |

## 執行方式
```bash
# 安裝套件
pip install -r requirements.txt

# 執行策略（日常）
python -m core.strategy_engine --mode=daily

# 產生報告
python -m report.report_model

# 發送 Email
python -m notifications.email_sender

# 啟動 Dashboard
streamlit run dashboard/app.py

# 執行測試
pytest tests/ -v
```

## 再平衡觸發條件
1. 每月 1 日
2. 現金佔帳戶比例 > 5%（有新資金進入）

## 新增策略步驟
1. 在 `strategies/` 新增 `your_strategy.json`
2. 在 `accounts.json` 將帳戶 `active_strategy` 改為新策略 ID
3. 完成（不需改 Python）

## GitHub Secrets 設定
| Secret | 說明 |
|---|---|
| `ACCOUNTS_JSON` | 完整 accounts.json 內容 |
| `EMAIL_PASSWORD` | Gmail App Password |

## 注意事項
- 所有報告必須含免責聲明：「不構成投資建議」
- API Key 不進 git（.gitignore 排除 accounts.json）
- 每日 UTC 13:30（美東 09:30）自動執行
