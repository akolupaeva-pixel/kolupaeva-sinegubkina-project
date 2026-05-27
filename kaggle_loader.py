df_kaggle = pd.read_csv(
    "sentiment_dataset.csv",
    encoding="utf-8",
    encoding_errors="ignore",
    on_bad_lines="skip",
    engine="python",
    quotechar='"'
)
rint(df_kaggle["src"].value_counts())

for src in df_kaggle["src"].unique():
    examples = df_kaggle[df_kaggle["src"] == src]["text"].dropna()
    if len(examples) > 0:
        print(f"\n[{src}]: {examples.iloc[0][:150]}")

  
df_reviews = df_kaggle[df_kaggle["src"].isin(["rureviews", "kinopoisk"])].copy()
df_reviews = df_reviews[df_reviews["text"].notna()]
df_reviews = df_reviews[df_reviews["text"].str.len() > 50]

df_reviews_formatted = pd.DataFrame({
    "source": "kaggle_reviews",
    "region": "не определён",
    "text_type": "review",
    "title": "",
    "url": "",
    "date": "",
    "text": df_reviews["text"],
    "word_count": df_reviews["text"].str.split().str.len(),
})

print(f"Отзывов отобрано: {len(df_reviews_formatted)}")
print(f"Средняя длина: {df_reviews_formatted['word_count'].mean():.0f} слов")
print(f"\nПример:\n{df_reviews_formatted['text'].iloc[0][:300]}")
