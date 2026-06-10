"""
雲端相容設定模組
優先順序：Streamlit Secrets → 環境變數 → 本機 accounts.json
確保 Dashboard 在任何環境都能啟動，不依賴本機檔案
"""
import os, json
from pathlib import Path

# ── 嘗試載入 Streamlit Secrets ──────────────────────
def _load_streamlit_secrets() -> dict:
    try:
        import streamlit as st
        raw = dict(st.secrets)
        # st.secrets 是 AttrDict，需要轉成普通 dict
        return {k: dict(v) if hasattr(v, 'items') else v for k, v in raw.items()}
    except Exception:
        return {}

# ── 嘗試載入環境變數中的 JSON ────────────────────────
def _load_from_env() -> dict:
    raw = os.environ.get("ACCOUNTS_JSON", "")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return {}

# ── 本機 accounts.json fallback ─────────────────────
def _load_local_file() -> dict:
    local = Path(__file__).parent.parent / "accounts" / "accounts.json"
    if local.exists():
        with open(local, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_config() -> dict:
    """
    統一設定入口，自動選擇可用的設定來源。
    回傳與 accounts.json 相同結構的 dict。
    """
    # 1. Streamlit Cloud Secrets（格式：[account_1], [account_2]...）
    secrets = _load_streamlit_secrets()
    if secrets and any(k.startswith("account") for k in secrets):
        return _build_config_from_secrets(secrets)

    # 2. 環境變數 ACCOUNTS_JSON
    env_cfg = _load_from_env()
    if env_cfg.get("accounts"):
        return env_cfg

    # 3. 本機檔案
    local_cfg = _load_local_file()
    if local_cfg.get("accounts"):
        return local_cfg

    raise RuntimeError(
        "找不到設定來源！請設定以下任一項：\n"
        "  • Streamlit Secrets（雲端部署）\n"
        "  • 環境變數 ACCOUNTS_JSON\n"
        "  • 本機 accounts/accounts.json"
    )

def _build_config_from_secrets(secrets: dict) -> dict:
    """
    Streamlit secrets.toml 格式轉換為 accounts.json 格式
    """
    accounts = []
    # 支援 [account_1], [account_2] ... 格式
    for key, val in secrets.items():
        if key.startswith("account") and isinstance(val, dict):
            accounts.append({
                "id":              val.get("id", key),
                "name":            val.get("name", key),
                "api_key":         val.get("api_key", ""),
                "api_secret":      val.get("api_secret", ""),
                "base_url":        val.get("base_url", "https://paper-api.alpaca.markets"),
                "active_strategy": val.get("active_strategy", "top10_nasdaq"),
                "email":           val.get("email", ""),
                "enabled":         val.get("enabled", True),
            })

    watchlist    = secrets.get("watchlist", {})
    email_config = secrets.get("email_config", {})

    return {
        "accounts":     accounts,
        "watchlist":    dict(watchlist) if watchlist else _default_watchlist(),
        "email_config": dict(email_config) if email_config else _default_email_config(),
    }

def _default_watchlist() -> dict:
    return {
        "科技股": ["AAPL","MSFT","NVDA","GOOGL","META"],
        "ETF":   ["QQQ","SPY","VGT","ARKK","XLK"],
        "生技股": ["MRNA","BNTX","GILD","AMGN","BIIB"],
    }

def _default_email_config() -> dict:
    return {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "sender":    os.environ.get("EMAIL_SENDER", ""),
        "password_env": "EMAIL_PASSWORD",
    }

def get_accounts_list() -> list[dict]:
    return load_config().get("accounts", [])

def get_watchlist() -> dict:
    return load_config().get("watchlist", _default_watchlist())

def get_email_config() -> dict:
    cfg = load_config().get("email_config", {})
    cfg["password"] = os.environ.get(cfg.get("password_env", "EMAIL_PASSWORD"), "")
    return cfg

def get_reports_dir() -> Path:
    """
    報告目錄：優先用 REPORTS_DIR 環境變數，否則用相對路徑
    GitHub Actions commit 後，reports/ 就在 repo 中
    """
    env_dir = os.environ.get("REPORTS_DIR", "")
    if env_dir:
        return Path(env_dir)
    return Path(__file__).parent.parent / "reports"
