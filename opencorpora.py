import requests


url = "http://opencorpora.org/files/export/annot/annot.opcorpora.xml.bz2"
resp = requests.head(url, timeout=10)
print(f"Статус: {resp.status_code}")
print(f"Размер: {resp.headers.get('content-length', 'неизвестно')} байт")




opencorpora_articles = []

for text_el in root.findall("text")[:500]:  # берём первые 500
    try:
        name = text_el.attrib.get("name", "")

        words = []
        paragraphs = text_el.find("paragraphs")
        if paragraphs is None:
            continue

        for sent in paragraphs.findall(".//sentence"):
            for token in sent.findall(".//token"):
                word = token.attrib.get("text", "")
                if word and re.match(r'[а-яёА-ЯЁ]', word):
                    words.append(word)

        text = " ".join(words)
        if len(text) < 100:
            continue

        opencorpora_articles.append({
            "text":      text,
            "title":     name,
            "url":       "",
            "source":    "opencorpora",
            "region":    "не определён",
            "text_type": "corpus",
            "word_count": len(words),
        })
    except Exception as e:
        pass

print(f" Извлечено: {len(opencorpora_articles)} текстов")
if opencorpora_articles:
    print(f"Пример: {opencorpora_articles[0]['text'][:200]}")
    print(f"Источник: {opencorpora_articles[0]['title']}")


df_corpus = pd.DataFrame(opencorpora_articles)
df_all_extended = pd.concat([df_all, df_corpus], ignore_index=True)

print(f"Итоговый датасет:")
print(df_all_extended.groupby("text_type")["word_count"].agg(count="count", mean_words="mean").round(0))
print(f"\nВсего текстов: {len(df_all_extended)}")


print("\nЛексический анализ корпуса OpenCorpora...")
corpus_lex = []
for idx, row in tqdm(df_corpus.iterrows(), total=len(df_corpus)):
    try:
        metrics = analyze_lexics(row["text"])
        if metrics:
            corpus_lex.append({
                "region":       row["region"],
                "text_type":    row["text_type"],
                "source":       row["source"],
                "ttr":          metrics["ttr"],
                "unique_ratio": metrics["unique_ratio"],
                "hapax_ratio":  metrics["hapax_ratio"],
                "avg_freq":     metrics["avg_freq"],
                "n_words":      metrics["n_words"],
                "n_unique":     metrics["n_unique"],
            })
    except:
        pass

df_lex_full = pd.concat([df_lex, pd.DataFrame(corpus_lex)], ignore_index=True)
print(f"\n Всего проанализировано: {len(df_lex_full)} текстов")
print(f"\nСредние значения по типу текста:")
print(df_lex_full.groupby("text_type")[
    ["ttr", "unique_ratio", "hapax_ratio", "avg_freq"]
].mean().round(3))


