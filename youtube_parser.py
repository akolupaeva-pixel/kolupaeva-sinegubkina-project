!pip install youtube-transcript-api

import time
import re
from datetime import datetime
from typing import List, Optional

# Региональные YouTube-каналы
REGIONAL_CHANNELS = {
    "Екатеринбург": [
        ("UCZnMr7EGMpE-p2J-XzxbUQA", "E1.ru"),
        ("UCsKNHPP6AR3tFmQd2mKSk-g", "Екатеринбург Live"),
    ],
    "Челябинск": [
        ("UCNxO_FBIU_pLhxb-G9xd0Eg", "74.ru"),
        ("UCwQH6J7RVNZGlnNBrE7Jl4Q", "Урал-Информ ТВ"),
    ],
    "Краснодар": [
        ("UCmJ-Qp9WJqxSqm1lTNy7b3w", "Краснодар ТВ"),
        ("UCkK9UDnn7TqIdkjydFjJkTQ", "93.ru"),
    ],
    "Ростов": [
        ("UCW2o-b1HLbAfXsRY7bPBDMg", "161.ru"),
        ("UCE8o9tJGOq1mRxc4kpRRkVA", "Дон-ТР"),
    ],
    "Москва": [
        ("UCgPTCRFfCnqOkqcQnhFQQdg", "Москва 24"),
        ("UCxMTxFP8G0fMiAYB9TsAIbA", "Mash"),
    ],
    "Санкт-Петербург": [
        ("UCViuKbDnJYLJIEIqKlYl9_g", "Фонтанка СПб"),
        ("UCwmkOEQe9iAWNOGRhOVyLiQ", "Петербург ТВ"),
    ],
    "Новосибирск": [
        ("UCrx5_IQpUOGKNGqQq0MHFCQ", "НГС Новосибирск"),
        ("UC4uQnm74y6tHMGIqSpTEfig", "ОТС"),
    ],
    "Омск": [
        ("UCO2SijbOa_z2bx_6G5fGksg", "НГС55"),
        ("UCkiBhON9L7kV3YhgbCpEt2Q", "Омск Здесь"),
    ],
}


class YouTubeTranscriptParser(BaseParser):
    """
    Парсер субтитров YouTube через youtube-transcript-api + RSS.
    Не требует Selenium, работает в Colab.
    """

    def __init__(self, region: str):
        if region not in REGIONAL_CHANNELS:
            raise ValueError(f"Регион '{region}' не поддерживается. "
                             f"Доступные: {list(REGIONAL_CHANNELS.keys())}")
        super().__init__(region=region, source_name="youtube_transcript", delay=1.0)
        self.channels = REGIONAL_CHANNELS[region]

    def parse(self, limit: int = 20) -> List[Article]:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
        except ImportError:
            raise ImportError("Установи: pip install youtube-transcript-api")

        self._log(f"Начинаем сбор субтитров (лимит={limit})")
        limit_per_channel = max(1, limit // len(self.channels))

        for channel_id, channel_name in self.channels:
            video_ids = self._get_video_ids_rss(channel_id, limit_per_channel)
            self._log(f"Канал '{channel_name}': найдено {len(video_ids)} видео")

            for video_id in video_ids:
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(
                        video_id, languages=["ru"]
                    )
                    text = " ".join(entry["text"] for entry in transcript_list)
                    if len(text) < 100:
                        continue

                    article = Article(
                        text=text,
                        source="youtube",
                        region=self.region,
                        text_type="video",
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        title=channel_name,
                        extra={"channel_id": channel_id, "channel_name": channel_name},
                    )
                    self._results.append(article)
                    self._log(f"  ✓ {video_id} ({len(text)} символов)")

                except (NoTranscriptFound, TranscriptsDisabled):
                    self._log(f"  ✗ {video_id}: субтитры недоступны")
                except Exception as e:
                    self._log(f"  ✗ {video_id}: {e}")

                self._sleep()

        self._log(f"Итого: {len(self._results)} видео с субтитрами")
        return self._results

    def _get_video_ids_rss(self, channel_id: str, limit: int) -> List[str]:
        """Получает ID видео через RSS-фид канала (без API-ключа)."""
        import requests
        from xml.etree import ElementTree as ET

        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            self._log(f"Ошибка RSS для {channel_id}: {e}")
            return []

        ns = {
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "atom": "http://www.w3.org/2005/Atom"
        }
        root = ET.fromstring(resp.text)
        video_ids = []
        for entry in root.findall("atom:entry", ns):
            vid_el = entry.find("yt:videoId", ns)
            if vid_el is not None:
                video_ids.append(vid_el.text)
            if len(video_ids) >= limit:
                break

        return video_ids


class YouTubeSeleniumParser(BaseParser):
    """
    Динамический парсинг YouTube через Selenium.
    Запускать локально (не в Colab) — там нет Chrome.
    """

    def __init__(self, region: str, headless: bool = True):
        if region not in REGIONAL_CHANNELS:
            raise ValueError(f"Регион '{region}' не поддерживается.")
        super().__init__(region=region, source_name="youtube_selenium", delay=2.0)
        self.headless = headless
        self.channels = REGIONAL_CHANNELS[region]
        self._driver = None

    def parse(self, limit: int = 20) -> List[Article]:
        self._start_driver()
        try:
            limit_per_channel = max(1, limit // len(self.channels))
            for channel_id, channel_name in self.channels:
                video_ids = self._scrape_channel_videos(channel_id, limit_per_channel)
                self._log(f"Канал '{channel_name}': найдено {len(video_ids)} ссылок")
                for vid_id in video_ids:
                    article = self._get_transcript(vid_id, channel_name, channel_id)
                    if article:
                        self._results.append(article)
                    self._sleep()
        finally:
            self._stop_driver()

        self._log(f"Итого: {len(self._results)} статей с субтитрами")
        return self._results

    def _start_driver(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except ImportError:
            service = Service()

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--lang=ru-RU")
        self._driver = webdriver.Chrome(service=service, options=options)
        self._driver.set_page_load_timeout(30)
        self._log("Браузер запущен")

    def _stop_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None

    def _scrape_channel_videos(self, channel_id: str, limit: int) -> List[str]:
        from selenium.webdriver.common.by import By

        if channel_id.startswith("UC"):
            url = f"https://www.youtube.com/channel/{channel_id}/videos"
        else:
            url = f"https://www.youtube.com/@{channel_id}/videos"

        self._driver.get(url)
        time.sleep(3)

        video_ids = set()
        scroll_attempts = 0

        while len(video_ids) < limit and scroll_attempts < 5:
            links = self._driver.find_elements(
                By.CSS_SELECTOR, "a#video-title-link, a[href*='/watch?v=']"
            )
            for link in links:
                href = link.get_attribute("href") or ""
                match = re.search(r"v=([A-Za-z0-9_\-]{11})", href)
                if match:
                    video_ids.add(match.group(1))
            if len(video_ids) >= limit:
                break
            self._driver.execute_script(
                "window.scrollTo(0, document.documentElement.scrollHeight);"
            )
            time.sleep(2)
            scroll_attempts += 1

        return list(video_ids)[:limit]

    def _get_transcript(self, video_id: str,
                         channel_name: str, channel_id: str) -> Optional[Article]:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["ru"]
            )
            text = " ".join(entry["text"] for entry in transcript_list)
            if len(text) < 100:
                return None
            return Article(
                text=text,
                source="youtube",
                region=self.region,
                text_type="video",
                url=f"https://www.youtube.com/watch?v={video_id}",
                title=channel_name,
                date=datetime.now(),
                extra={"channel_id": channel_id, "channel_name": channel_name},
            )
        except Exception as e:
            self._log(f"  ✗ {video_id}: {e}")
            return None



try:
    parser = YouTubeTranscriptParser(region="Екатеринбург")

    print("Каналы:", parser.channels)
except Exception as e:
    print(" Ошибка:", e)


import requests

API_KEY = "AIzaSyABQ0BxF3WLOirpVhhUT1WI75QBpwbB5ow"

def get_channel_id(query: str) -> tuple:
    """Находит channel_id и название канала по поисковому запросу."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 1,
        "key": API_KEY,
    }
    resp = requests.get(url, params=params)
    items = resp.json().get("items", [])
    if not items:
        return None, None
    channel_id = items[0]["snippet"]["channelId"]
    channel_name = items[0]["snippet"]["title"]
    return channel_id, channel_name

queries = [
    "E1.ru Екатеринбург новости",
    "НГС Новосибирск",
    "74.ru Челябинск",
    "161.ru Ростов",
    "93.ru Краснодар",
    "Москва 24",
    "Фонтанка Петербург",
    "НГС55 Омск",
]

for query in queries:
    channel_id, name = get_channel_id(query)
    print(f"{query}: {name} → {channel_id}")
