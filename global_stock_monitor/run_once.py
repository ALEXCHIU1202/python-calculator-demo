"""
單次執行腳本 — 適合用 Windows 工作排程器呼叫，或手動測試。
用法：python run_once.py
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import Config
from modules.analyzer import Analyzer
from modules.data_collector import DataCollector
from modules.email_sender import EmailSender
from modules.report_generator import ReportGenerator


def main() -> None:
    cfg = Config()
    cfg.LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_file = cfg.LOG_DIR / f"monitor_{datetime.now().strftime('%Y%m')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)-8s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger('run_once')

    if not cfg.GEMINI_API_KEY and not cfg.ANTHROPIC_API_KEY:
        logger.error("未設定任何 AI API Key（GEMINI_API_KEY 或 ANTHROPIC_API_KEY），請確認設定")
        sys.exit(1)

    logger.info("=== 單次執行啟動 ===")

    collector = DataCollector(cfg)
    articles = collector.collect_all()
    logger.info(f"蒐集到 {len(articles)} 篇文章")

    if not articles:
        logger.warning("無文章可分析")
        return

    analyzer = Analyzer(cfg)
    analysis = analyzer.analyze(articles)

    generator = ReportGenerator(cfg)
    _html, report_path = generator.generate(analysis)
    logger.info(f"報告已儲存：{report_path}")

    if cfg.EMAIL_SENDER and cfg.EMAIL_RECIPIENTS:
        sender = EmailSender(cfg)
        sender.send_report(report_path, analysis['stats'], analysis.get('daily_report', ''))
    else:
        logger.info("Email 未設定，略過發送（報告已存於 reports/ 資料夾）")

    logger.info("=== 執行完成 ===")


if __name__ == '__main__':
    main()
