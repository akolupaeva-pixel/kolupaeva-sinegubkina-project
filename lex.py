import pymorphy2
from collections import Counter
import re

morph = pymorphy2.MorphAnalyzer()

def lemmatize_text(text: str) -> list:
    """Приводит слова к начальной форме"""
    words = re.findall(r'[а-яё]+', text.lower())
    lemmas = []
    for word in words:
        parsed = morph.parse(word)[0]
        lemmas.append(parsed.normal_form)
    return lemmas

def get_pos(word: str) -> str:
    """Возвращает часть речи слова."""
    parsed = morph.parse(word)[0]
    return parsed.tag.POS

def analyze_lexics(text: str) -> dict:
    """
    Лексический анализ текста.
    Возвращает метрики разнообразия и частотности.
    """
    text = text[:3000]
    words = re.findall(r'[а-яё]+', text.lower())
    if len(words) < 10:
        return None

    lemmas = [morph.parse(w)[0].normal_form for w in words]

    # Стоп-слова (служебные части речи)
    stopwords = {"и", "в", "на", "с", "по", "для", "от", "до", "из",
                 "что", "как", "это", "но", "а", "же", "ли", "бы",
                 "он", "она", "они", "мы", "вы", "я", "его", "её",
                 "не", "ни", "или", "так", "уже", "ещё", "то", "за"}

    content_lemmas = [l for l in lemmas if l not in stopwords and len(l) > 2]

    # 1. TTR — разнообразие словаря (type-token ratio)
    ttr = len(set(lemmas)) / len(lemmas) if lemmas else 0

    # 2. Топ-10 значимых слов
    top_words = Counter(content_lemmas).most_common(10)

    # 3. Доля уникальных слов
    unique_ratio = len(set(content_lemmas)) / len(content_lemmas) if content_lemmas else 0

    # 4. Средняя частота слова (обратная мера богатства словаря)
    word_counts = Counter(content_lemmas)
    avg_freq = sum(word_counts.values()) / len(word_counts) if word_counts else 0

    # 5. Доля редких слов (встречаются 1 раз)
    hapax_ratio = sum(1 for c in word_counts.values() if c == 1) / len(word_counts) if word_counts else 0

    return {
        "ttr":          round(ttr, 3),
        "unique_ratio": round(unique_ratio, 3),
        "avg_freq":     round(avg_freq, 2),
        "hapax_ratio":  round(hapax_ratio, 3),
        "top_words":    top_words,
        "n_words":      len(words),
        "n_unique":     len(set(lemmas)),
    }


sample = df_all[df_all["text_type"] == "smi"]["text"].iloc[0]
print("Текст:", sample[:200])
print("\nЛексический анализ:")
result = analyze_lexics(sample)
for k, v in result.items():
    print(f"  {k}: {v}")



lex_results = []
for idx, row in tqdm(df_all.iterrows(), total=len(df_all)):
    try:
        metrics = analyze_lexics(row["text"])
        if metrics:
            lex_results.append({
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
    except Exception as e:
        pass

df_lex = pd.DataFrame(lex_results)
print(f"\n✅ Проанализировано: {len(df_lex)} текстов")
print(f"\nСредние значения по типу текста:")
print(df_lex.groupby("text_type")[
    ["ttr", "unique_ratio", "hapax_ratio", "avg_freq"]
].mean().round(3))
