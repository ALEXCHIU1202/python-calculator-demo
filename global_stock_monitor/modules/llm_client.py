"""
LLM 統一介面 — 自動選擇可用的 AI 服務
優先順序：Google Gemini（免費）→ Anthropic Claude（付費）
"""
import logging
import time

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config):
        self.provider = None

        # ── 優先使用 Gemini（免費）────────────────────────────────────────
        if getattr(config, 'GEMINI_API_KEY', ''):
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                self._gemini_model = getattr(config, 'GEMINI_MODEL', 'gemini-2.0-flash')
                self.provider = 'gemini'
                logger.info(f"AI 引擎：Google Gemini ({self._gemini_model}) — 免費方案")
            except ImportError:
                logger.warning("google-genai 未安裝，改用 Anthropic")
            except Exception as e:
                logger.warning(f"Gemini 初始化失敗：{e}，改用 Anthropic")

        # ── 備用：Anthropic Claude ────────────────────────────────────────
        if self.provider is None and getattr(config, 'ANTHROPIC_API_KEY', ''):
            import anthropic
            self._anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self._anthropic_model = config.ANALYSIS_MODEL
            self.provider = 'anthropic'
            logger.info(f"AI 引擎：Anthropic Claude ({config.ANALYSIS_MODEL})")

        if self.provider is None:
            raise ValueError(
                "未設定任何 AI API Key！\n"
                "請在 .env 加入 GEMINI_API_KEY（免費）或 ANTHROPIC_API_KEY"
            )

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        if self.provider == 'gemini':
            return self._gemini_complete(prompt, max_tokens)
        return self._anthropic_complete(prompt, max_tokens)

    # ── Gemini ───────────────────────────────────────────────────────────

    def _gemini_complete(self, prompt: str, max_tokens: int) -> str:
        from google.genai import types
        for attempt in range(3):
            try:
                resp = self._gemini_client.models.generate_content(
                    model=self._gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=max_tokens,
                    ),
                )
                # 安全取得文字：優先 resp.text，備用 candidates
                if resp.text:
                    return resp.text
                if resp.candidates:
                    parts = resp.candidates[0].content.parts
                    return ''.join(p.text for p in parts if hasattr(p, 'text'))
                raise ValueError("Gemini 回傳空回應")
            except Exception as e:
                err = str(e)
                if '429' in err or 'quota' in err.lower() or 'rate' in err.lower():
                    wait = 30 * (attempt + 1)   # 30s / 60s / 90s
                    logger.warning(f"Gemini 速率限制，等待 {wait}s 後重試…")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError("Gemini API 重試次數耗盡")

    # ── Anthropic ────────────────────────────────────────────────────────

    def _anthropic_complete(self, prompt: str, max_tokens: int) -> str:
        resp = self._anthropic.messages.create(
            model=self._anthropic_model,
            max_tokens=max_tokens,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return resp.content[0].text
