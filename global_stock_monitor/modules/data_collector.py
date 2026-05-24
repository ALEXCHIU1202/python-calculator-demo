import hashlib
import logging
from datetime import datetime
from typing import Dict, List

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DataCollector:
    def __init__(self, config):
        self.config = config
        self._seen: set[str] = set()

    def collect_all(self) -> List[Dict]:
        articles: List[Dict] = []
        articles.extend(self._collect_rss())
        if self.config.NEWS_API_KEY:
            articles.extend(self._collect_newsapi())
        return self._deduplicate(articles)[: self.config.MAX_NEWS_ITEMS]

    # ── RSS ──────────────────────────────────────────────────────────────────

    def _collect_rss(self) -> List[Dict]:
        articles: List[Dict] = []
        for feed_info in self.config.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_info['url'])
                for entry in feed.entries[:15]:
                    item = self._parse_entry(entry, feed_info)
                    if item:
                        articles.append(item)
                logger.info(f"[RSS] {feed_info['name']}: {len(feed.entries[:15])} 筆")
            except Exception as exc:
                logger.warning(f"[RSS] {feed_info['name']} 失敗: {exc}")
        return articles

    def _parse_entry(self, entry, feed_info: Dict) -> Dict | None:
        try:
            title = entry.get('title', '').strip()
            if not title or len(title) < 10:
                return None
            raw_summary = entry.get('summary', entry.get('description', ''))
            summary = BeautifulSoup(raw_summary, 'html.parser').get_text()[:500].strip()
            return {
                'title': title,
                'summary': summary,
                'link': entry.get('link', ''),
                'published': entry.get('published', datetime.now().isoformat()),
                'source': feed_info['name'],
                'category': feed_info['category'],
            }
        except Exception:
            return None

    # ── NewsAPI ───────────────────────────────────────────────────────────────

    def _collect_newsapi(self) -> List[Dict]:
        try:
            resp = requests.get(
                'https://newsapi.org/v2/top-headlines',
                params={
                    'apiKey': self.config.NEWS_API_KEY,
                    'category': 'business',
                    'language': 'en',
                    'pageSize': 30,
                },
                timeout=10,
            )
            resp.raise_for_status()
            articles = []
            for item in resp.json().get('articles', []):
                title = item.get('title', '') or ''
                if title and '[Removed]' not in title:
                    articles.append({
                        'title': title,
                        'summary': item.get('description', '') or '',
                        'link': item.get('url', ''),
                        'published': item.get('publishedAt', ''),
                        'source': item.get('source', {}).get('name', 'NewsAPI'),
                        'category': 'finance',
                    })
            logger.info(f"[NewsAPI] {len(articles)} 筆")
            return articles
        except Exception as exc:
            logger.warning(f"[NewsAPI] 失敗: {exc}")
            return []

    # ── Dedup ─────────────────────────────────────────────────────────────────

    def _deduplicate(self, articles: List[Dict]) -> List[Dict]:
        unique: List[Dict] = []
        for article in articles:
            key = hashlib.md5(article['title'].lower().encode()).hexdigest()
            if key not in self._seen:
                self._seen.add(key)
                unique.append(article)
        return unique
