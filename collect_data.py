import pandas as pd

all_articles = []


smi_regions = ["Екатеринбург", "Новосибирск", "Челябинск", "Ростов", "Омск", "Краснодар"]
smi = MultiRegionSMIParser(regions=smi_regions)
smi_articles = smi.parse_all(limit_per_region=30)
all_articles.extend(smi_articles)
print(f"СМИ: собрано {len(smi_articles)} статей")


REGIONAL_CHANNELS.update({
    "Ростов":         [("UC3nfFfCATQsJ744jJRvcK5w", "161.ru")],
    "Санкт-Петербург":[("UC_lH9Fu7wo3u-sYblbTe0RA", "Фонтанка СПб")],
})

yt_regions = ["Ростов", "Санкт-Петербург"]
yt_articles = []
seen_texts = set()

for region in yt_regions:
    parser = YouTubeTranscriptParser(region=region)
    raw = parser.parse(limit=20)
    for art in raw:
        cleaned = clean_transcript(art.text)
        key = cleaned[:100]
        if key not in seen_texts and is_good_text(art.text):
            seen_texts.add(key)
            art.text = cleaned
            yt_articles.append(art)

all_articles.extend(yt_articles)
print(f"YouTube: собрано {len(yt_articles)} видео")



df = pd.DataFrame([{
    "source":    art.source,
    "region":    art.region,
    "text_type": art.text_type,
    "title":     art.title,
    "url":       art.url,
    "date":      art.date.isoformat() if art.date else "",
    "text":      art.text,
    "word_count": art.word_count(),
} for art in all_articles])

print(df.groupby(["region", "text_type"])["word_count"].agg(["count", "mean"]).round(0))
print(f"\nВсего статей: {len(df)}")
print(f"Всего слов: {df['word_count'].sum():,}")
