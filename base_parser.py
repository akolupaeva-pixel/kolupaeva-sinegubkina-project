import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Article:
    text: str
    source: str
    region: str
    text_type: str
    url: str = ""
    title: str = ""
    date: Optional[datetime] = None
    extra: dict = field(default_factory=dict)
    def word_count(self) -> int:
        return len(self.text.split())

    def __repr__(self):
        return f"Article(source={self.source!r}, region={self.region!r}, words={self.word_count()})"


class BaseParser(ABC):

    def __init__(self, region: str, source_name: str, delay: float = 1.5):
        self.region = region
        self.source_name = source_name
        self.delay = delay
        self._results: List[Article] = []

    @abstractmethod
    def parse(self, limit: int = 50) -> List[Article]:
        ...

    def _sleep(self):
        time.sleep(self.delay)

    def _log(self, msg: str):
        logger.info(f"[{self.source_name} / {self.region}] {msg}")

    def get_results(self) -> List[Article]:
        return self._results

    def save_to_csv(self, filepath: str):
        import csv
        if not self._results:
            self._log("нет данных")
            return
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["source", "region", "text_type",
                                                    "title", "url", "date", "text"])
            writer.writeheader()
            for art in self._results:
                writer.writerow({
                    "source": art.source,
                    "region": art.region,
                    "text_type": art.text_type,
                    "title": art.title,
                    "url": art.url,
                    "date": art.date.isoformat() if art.date else "",
                    "text": art.text,
                })
        self._log(f"сохранено {len(self._results)} статей: {filepath}")
