"""
全球股市影響力聲明監測系統
每日自動蒐集新聞 → Claude AI 分析 → 生成 HTML 報告 → Email 通知
"""

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule

from config import Config
from modules.analyzer import Analyzer
from modules.data_collector import DataCollector
from modules.email_sender import EmailSender
from modules.report_generator import ReportGenerator


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"monitor_{datetime.now().strftime('%Y%m')}.log"
    fmt = '%(asctime)s [%(levelname)-8s] %(name)s: %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ],
    )


def validate_config(cfg: Config) -> bool:
    errors = []
    if not cfg.ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY 未設定")
    if not cfg.EMAIL_SENDER:
        errors.append("EMAIL_SENDER 未設定")
    if not cfg.EMAIL_PASSWORD:
        errors.append("EMAIL_PASSWORD 未設定")
    if not cfg.EMAIL_RECIPIENTS:
        errors.append("EMAIL_RECIPIENTS 未設定")
    if errors:
        for e in errors:
            logging.error(f"設定錯誤：{e}")
        return False
    return True


def run_pipeline(cfg: Config) -> None:
    logger = logging.getLogger('pipeline')
    sep = '═' * 60
    logger.info(sep)
    logger.info(f"  開始執行分析管線  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(sep)

    try:
        # 1. 蒐集新聞
        logger.info("【Step 1/4】 蒐集多源新聞…")
        collector = DataCollector(cfg)
        articles = collector.collect_all()
        if not articles:
            logger.warning("未蒐集到任何文章，略過本次執行")
            return
        logger.info(f"  共蒐集 {len(articles)} 篇文章")

        # 2. Claude AI 分析
        logger.info("【Step 2/4】 Claude AI 分析中…")
        analyzer = Analyzer(cfg)
        analysis = analyzer.analyze(articles)
        stats = analysis['stats']
        logger.info(
            f"  分析完成 | 市場影響: {stats['market_moving']} | "
            f"高影響: {stats['high_impact']} | "
            f"多頭: {stats['bullish']} | 空頭: {stats['bearish']}"
        )

        # 3. 生成 HTML 報告
        logger.info("【Step 3/4】 生成 HTML 報告…")
        generator = ReportGenerator(cfg)
        _html, report_path = generator.generate(analysis)
        logger.info(f"  報告路徑：{report_path}")

        # 4. 發送 Email
        logger.info("【Step 4/4】 發送 Email 通知…")
        sender = EmailSender(cfg)
        ok = sender.send_report(report_path, stats, analysis.get('daily_report', ''))
        logger.info("  Email 發送成功 ✓" if ok else "  Email 發送失敗 ✗")

        logger.info(sep)
        logger.info("  管線執行完成")
        logger.info(sep)

    except Exception:
        logger.exception("管線執行異常")


def main() -> None:
    cfg = Config()
    setup_logging(cfg.LOG_DIR)
    logger = logging.getLogger('main')

    logger.info("全球股市影響力聲明監測系統 啟動")

    if not validate_config(cfg):
        logger.error("請複製 .env.example 為 .env 並填寫必要設定後重新執行")
        sys.exit(1)

    logger.info(f"每日執行時間：{cfg.DAILY_RUN_TIME}")
    logger.info(f"收件人：{cfg.EMAIL_RECIPIENTS}")
    logger.info(f"分析模型：{cfg.ANALYSIS_MODEL}")

    # 啟動時立即執行一次
    run_pipeline(cfg)

    # 排程每日固定時間執行
    schedule.every().day.at(cfg.DAILY_RUN_TIME).do(run_pipeline, cfg=cfg)
    logger.info(f"排程已設定，下次執行時間：每日 {cfg.DAILY_RUN_TIME}")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    main()
