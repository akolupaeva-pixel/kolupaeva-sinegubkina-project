import time
import re
from datetime import datetime
from typing import List, Optional

from base_parser import BaseParser, Article


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
    def __init__(self, region: str):
        if region not in REGIONAL_CHANNELS:
            raise ValueError(f"'{region}' не поддерживается.")
        super().__init__(region=region, source_name="youtube_transcript", delay=1.0)
        self.channels = REGIONAL_CHANNELS[region]

    

        self._log(f"сбор субтитров (лимит={limit})")
        limit_per_channel = max(1, limit // len(self.channels))

        for channel_id, channel_name in self.channels:
            video_ids = self._get_video_ids_simple(channel_id, limit_per_channel)
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

        self._log(f"{len(self._results)} видео с субтитрами")
        return self._results

    def _get_video_ids_simple(self, channel_id: str, limit: int) -> List[str]:

        import requests
        from xml.etree import ElementTree as ET

        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            self._log(f"ошибка RSS для {channel_id}: {e}")
            return []

        ns = {"yt": "http://www.youtube.com/xml/schemas/2015",
              "atom": "http://www.w3.org/2005/Atom"}
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

    def __init__(self, region: str, headless: bool = True):
        if region not in REGIONAL_CHANNELS:
            raise ValueError(f"Регион '{region}' не поддерживается.")
        super().__init__(region=region, source_name="youtube_selenium", delay=2.0)
        self.headless = headless
        self.channels = REGIONAL_CHANNELS[region]
        self._driver = None

    def _start_driver(self):
        """Инициализирует Selenium WebDriver."""
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except ImportError:
            # webdriver-manager не установлен — используем chromedriver из PATH
            service = Service()

        options = Options()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=ru-RU")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/124.0.0 Safari/537.36"
        )
        self._driver = webdriver.Chrome(service=service, options=options)
        self._driver.set_page_load_timeout(30)
        self._log("Браузер запущен")

    def _stop_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None
            self._log("Браузер закрыт")

    def parse(self, limit: int = 20) -> List[Article]:
        self._start_driver()
        try:
            limit_per_channel = max(1, limit // len(self.channels))
            for channel_id, channel_name in self.channels:
                video_ids = self._scrape_channel_videos(channel_id, channel_name,
                                                         limit_per_channel)
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


    def _scrape_channel_videos(self, channel_id: str,
                                channel_name: str, limit: int) -> List[str]:

        from selenium.webdriver.common.by import By

        url = f"https://www.youtube.com/@{channel_id}/videos"
        
        if channel_id.startswith("UC"):
            url = f"https://www.youtube.com/channel/{channel_id}/videos"

        self._log(f"Открываем: {url}")
        self._driver.get(url)
        time.sleep(3)  # Ждём загрузки JS

        
        video_ids = set()
        scroll_attempts = 0
        max_scrolls = 5

        while len(video_ids) < limit and scroll_attempts < max_scrolls:
            
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
            from youtube_transcript_api import (YouTubeTranscriptApi,
                                                NoTranscriptFound,
                                                TranscriptsDisabled)
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id, languages=["ru"]
            )
            text = " ".join(entry["text"] for entry in transcript_list)
            if len(text) < 100:
                return None

            self._log(f"  ✓ {video_id}: {len(text)} символов")
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


if __name__ == "__main__":
    
    print("=== Тест YouTubeTranscriptParser (без Selenium) ===")
    parser = YouTubeTranscriptParser(region="Екатеринбург")
    articles = parser.parse(limit=3)
    for art in articles:
        print(art)
        print("Начало текста:", art.text[:300])
        print("---")

    
    print("\n=== Тест YouTubeSeleniumParser (Selenium) ===")
    parser_sel = YouTubeSeleniumParser(region="Екатеринбург", headless=True)
    articles_sel = parser_sel.parse(limit=5)
    for art in articles_sel:
        print(art)
