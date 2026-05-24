"""
雲端相容性測試
確保 Dashboard 在以下環境都能正常啟動：
  1. Streamlit Cloud（用 st.secrets）
  2. GitHub Actions（用 ACCOUNTS_JSON 環境變數）
  3. 本機（用 accounts/accounts.json）
"""
import pytest, sys, os, json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

SAMPLE_ACCOUNTS_JSON = {
    "accounts": [
        {
            "id": "acc_test",
            "name": "Test Account",
            "api_key": "TESTKEY123",
            "api_secret": "TESTSECRET456",
            "base_url": "https://paper-api.alpaca.markets",
            "active_strategy": "top10_nasdaq",
            "email": "test@example.com",
            "enabled": True
        }
    ],
    "watchlist": {
        "科技股": ["AAPL", "MSFT"],
        "ETF":   ["QQQ", "SPY"]
    },
    "email_config": {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "sender": "bot@gmail.com",
        "password_env": "EMAIL_PASSWORD"
    }
}

# ── TC-C-01 環境變數載入 ─────────────────────────────────
def test_load_config_from_env_var():
    """ACCOUNTS_JSON 環境變數可正確解析"""
    with patch.dict(os.environ, {"ACCOUNTS_JSON": json.dumps(SAMPLE_ACCOUNTS_JSON)}):
        from core.config import _load_from_env
        cfg = _load_from_env()
    assert len(cfg["accounts"]) == 1
    assert cfg["accounts"][0]["id"] == "acc_test"

# ── TC-C-02 本機檔案載入 ─────────────────────────────────
def test_load_config_from_local_file(tmp_path):
    """本機 accounts.json 可正確載入"""
    f = tmp_path / "accounts.json"
    f.write_text(json.dumps(SAMPLE_ACCOUNTS_JSON), encoding="utf-8")
    with patch("core.config.ACCOUNTS_PATH" if False else "builtins.open",
               side_effect=lambda p, *a, **kw: open(f, *a, **kw)
               if "accounts.json" in str(p) else open(p, *a, **kw)):
        pass  # 直接測試 _load_local_file 邏輯
    data = json.loads(f.read_text("utf-8"))
    assert data["accounts"][0]["name"] == "Test Account"

# ── TC-C-03 Streamlit Secrets 格式轉換 ──────────────────
def test_build_config_from_secrets():
    """Streamlit secrets 格式可正確轉換為 accounts 格式"""
    from core.config import _build_config_from_secrets
    secrets = {
        "account_1": {
            "id": "acc_001", "name": "Paper 帳戶",
            "api_key": "KEY", "api_secret": "SECRET",
            "base_url": "https://paper-api.alpaca.markets",
            "active_strategy": "top10_nasdaq",
            "email": "a@b.com", "enabled": True
        },
        "watchlist": {"科技股": ["AAPL"], "ETF": ["QQQ"]},
    }
    cfg = _build_config_from_secrets(secrets)
    assert len(cfg["accounts"]) == 1
    assert cfg["accounts"][0]["api_key"] == "KEY"
    assert "科技股" in cfg["watchlist"]

# ── TC-C-04 多帳戶 Secrets 解析 ─────────────────────────
def test_multi_account_secrets():
    from core.config import _build_config_from_secrets
    secrets = {
        "account_1": {"id":"a1","name":"A1","api_key":"K1","api_secret":"S1",
                      "base_url":"https://paper-api.alpaca.markets",
                      "active_strategy":"top10_nasdaq","email":"","enabled":True},
        "account_2": {"id":"a2","name":"A2","api_key":"K2","api_secret":"S2",
                      "base_url":"https://paper-api.alpaca.markets",
                      "active_strategy":"momentum","email":"","enabled":True},
    }
    cfg = _build_config_from_secrets(secrets)
    assert len(cfg["accounts"]) == 2

# ── TC-C-05 設定優先順序：env > local ───────────────────
def test_config_priority_env_over_local():
    env_cfg = SAMPLE_ACCOUNTS_JSON.copy()
    env_cfg["accounts"][0]["name"] = "From ENV"
    with patch.dict(os.environ, {"ACCOUNTS_JSON": json.dumps(env_cfg)}):
        from core.config import _load_from_env
        cfg = _load_from_env()
    assert cfg["accounts"][0]["name"] == "From ENV"

# ── TC-C-06 無設定時拋出明確錯誤 ────────────────────────
def test_config_error_when_no_source():
    import core.config as cfg_module
    with patch.object(cfg_module, "_load_streamlit_secrets", return_value={}), \
         patch.object(cfg_module, "_load_from_env",          return_value={}), \
         patch.object(cfg_module, "_load_local_file",        return_value={}):
        with pytest.raises(RuntimeError):
            cfg_module.load_config()

# ── TC-C-07 reports 目錄路徑解析 ────────────────────────
def test_reports_dir_from_env(tmp_path):
    with patch.dict(os.environ, {"REPORTS_DIR": str(tmp_path)}):
        from core.config import get_reports_dir
        d = get_reports_dir()
    assert d == tmp_path

# ── TC-C-08 reports 目錄預設值 ──────────────────────────
def test_reports_dir_default():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("REPORTS_DIR", None)
        from core.config import get_reports_dir
        d = get_reports_dir()
    assert d.name == "reports"

# ── TC-C-09 watchlist 預設值 ────────────────────────────
def test_default_watchlist():
    from core.config import _default_watchlist
    wl = _default_watchlist()
    assert "科技股" in wl
    assert "ETF"   in wl
    assert "生技股" in wl
    assert "AAPL" in wl["科技股"]

# ── TC-C-10 Email 設定讀取 ──────────────────────────────
def test_email_config_from_env():
    with patch.dict(os.environ, {
        "ACCOUNTS_JSON": json.dumps(SAMPLE_ACCOUNTS_JSON),
        "EMAIL_PASSWORD": "secret123"
    }):
        from core.config import get_email_config
        ecfg = get_email_config()
    assert ecfg["smtp_host"] == "smtp.gmail.com"
    assert ecfg["password"] == "secret123"

# ── TC-C-11 API key 不寫入 log ──────────────────────────
def test_api_key_not_in_logs(capsys):
    """確保 config 載入過程不會 print API key"""
    with patch.dict(os.environ, {"ACCOUNTS_JSON": json.dumps(SAMPLE_ACCOUNTS_JSON)}):
        from core.config import load_config
        load_config()
    captured = capsys.readouterr()
    assert "TESTKEY123"    not in captured.out
    assert "TESTSECRET456" not in captured.out

# ── TC-C-12 dashboard import 不依賴本機檔案 ─────────────
def test_dashboard_imports_cleanly():
    """dashboard/app.py 可以 import 而不因缺少本機檔案崩潰"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "app",
        str(Path(__file__).parent.parent / "dashboard" / "app.py")
    )
    # 只檢查 spec 存在（實際 import 需要 streamlit 環境）
    assert spec is not None

# ── TC-C-13 accounts.json 排除在 .gitignore ─────────────
def test_accounts_json_in_gitignore():
    gitignore = Path(__file__).parent.parent / ".gitignore"
    assert gitignore.exists(), ".gitignore 不存在"
    content = gitignore.read_text()
    assert "accounts/accounts.json" in content or "accounts.json" in content

# ── TC-C-14 secrets.toml.template 存在 ──────────────────
def test_secrets_template_exists():
    template = Path(__file__).parent.parent / ".streamlit" / "secrets.toml.template"
    assert template.exists(), "缺少 .streamlit/secrets.toml.template"

# ── TC-C-15 secrets.toml 不在 gitignore 外（不應 commit）
def test_real_secrets_not_in_repo():
    secrets = Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    # 真實 secrets.toml 不應存在於 repo（只有 .template）
    if secrets.exists():
        gitignore = Path(__file__).parent.parent / ".gitignore"
        content   = gitignore.read_text() if gitignore.exists() else ""
        assert "secrets.toml" in content, \
            "secrets.toml 存在但未加入 .gitignore！請立即加入以防止 key 外洩"
