"""
LLM 統一介面 — 自動選擇可用的 AI 服務
優先順序：Groq（免費、快速）→ Google Gemini（備用）→ Anthropic Claude（付費）
"""
import logging
import time

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, config):
        self.provider = None

        # ── 優先：Groq（免費、無 IP 限制、超快）────────────────────────────
        if getattr(config, 'GROQ_API_KEY', ''):
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=config.GROQ_API_KEY)
                self._groq_model = getattr(config, 'GROQ_MODEL', 'llama-3.3-70b-versatile')
                self.provider = 'groq'
                logger.info(f"AI 引擎：Groq ({self._groq_model}) — 免費方案")
            except ImportError:
                logger.warning("groq 套件未安裝，嘗試 Gemini…")
            except Exception as e:
                logger.warning(f"Groq 初始化失敗：{e}，嘗試 Gemini…")

        # ── 備用：Google Gemini ───────────────────────────────────────────
        if self.provider is None and getattr(config, 'GEMINI_API_KEY', ''):
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                self._gemini_model = getattr(config, 'GEMINI_MODEL', 'models/gemini-1.5-flash')
                self.provider = 'gemini'
                logger.info(f"AI 引擎：Google Gemini ({self._gemini_model}) — 免費方案")
            except ImportError:
                logger.warning("google-genai 未安裝，嘗試 Anthropic…")
            except Exception as e:
                logger.warning(f"Gemini 初始化失敗：{e}，嘗試 Anthropic…")

        # ── 備用：Anthropic Claude ────────────────────────────────────────
        if self.provider is None and getattr(config, 'ANTHROPIC_API_KEY', ''):
            try:
                import anthropic
                self._anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
                self._anthropic_model = config.ANALYSIS_MODEL
                self.provider = 'anthropic'
                logger.info(f"AI 引擎：Anthropic Claude ({config.ANALYSIS_MODEL})")
            except Exception as e:
                logger.warning(f"Anthropic 初始化失敗：{e}")

        if self.provider is None:
            raise ValueError(
                "未設定任何 AI API Key！\n"
                "請在 GitHub Secrets 加入 GROQ_API_KEY（免費，推薦）"
            )

    def complete(self, prompt: str, max_tokens: int = 4096) -> str:
        if self.provider == 'groq':
            return self._groq_complete(prompt, max_tokens)
        if self.provider == 'gemini':
            return self._gemini_complete(prompt, max_tokens)
        return self._anthropic_complete(prompt, max_tokens)

    # ── Groq ─────────────────────────────────────────────────────────────

    def _groq_complete(self, prompt: str, max_tokens: int) -> str:
        for attempt in range(3):
            try:
                resp = self._groq_client.chat.completions.create(
                    model=self._groq_model,
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=min(max_tokens, 8000),
                    temperature=0.3,
                )
                return resp.choices[0].message.content or ''
            except Exception as e:
                err = str(e)
                if '429' in err or 'rate' in err.lower():
                    wait = 20 * (attempt + 1)
                    logger.warning(f"Groq 速率限制，等待 {wait}s 後重試…")
                    time.sleep(wait)
                else:
                    raise
        raise RuntimeError("Groq API 重試次數耗盡")

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
                if resp.text:
                    return resp.text
                if resp.candidates:
                    parts = resp.candidates[0].content.parts
                    return ''.join(p.text for p in parts if hasattr(p, 'text'))
                raise ValueError("Gemini 回傳空回應")
            except Exception as e:
                err = str(e)
                if '429' in err or 'quota' in err.lower() or 'rate' in err.lower():
                    wait = 30 * (attempt + 1)
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
