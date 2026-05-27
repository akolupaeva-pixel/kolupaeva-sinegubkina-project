!pip install natasha -q

from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, NewsSyntaxParser, Doc

segmenter = Segmenter()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)
syntax_parser = NewsSyntaxParser(emb)
morph_vocab = MorphVocab()

def analyze_syntax(text: str) -> dict:
    
    text = text[:3000]

    doc = Doc(text)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    doc.parse_syntax(syntax_parser)

    sentences = doc.sents
    if not sentences:
        return None

    # 1. Средняя длина предложения (в словах)
    sent_lengths = [len(list(s.tokens)) for s in sentences]
    avg_sent_length = sum(sent_lengths) / len(sent_lengths)

    # 2. Доля сложных предложений (содержат союзы)
    conjunctions = {"что", "который", "если", "когда", "чтобы",
                    "потому", "хотя", "пока", "как", "и", "но", "а"}
    complex_sents = 0
    for sent in sentences:
        words = {t.text.lower() for t in sent.tokens}
        if words & conjunctions:
            complex_sents += 1
    complex_ratio = complex_sents / len(sentences)

    # 3. Доля глаголов (активность текста)
    all_tokens = [t for s in sentences for t in s.tokens]
    verbs = [t for t in all_tokens if t.pos == "VERB"]
    verb_ratio = len(verbs) / len(all_tokens) if all_tokens else 0

    # 4. Доля существительных (номинализация)
    nouns = [t for t in all_tokens if t.pos == "NOUN"]
    noun_ratio = len(nouns) / len(all_tokens) if all_tokens else 0

    # 5. Средняя длина слова (сложность лексики)
    avg_word_length = sum(len(t.text) for t in all_tokens) / len(all_tokens) if all_tokens else 0

    return {
        "n_sentences":    len(sentences),
        "avg_sent_length": round(avg_sent_length, 2),
        "complex_ratio":  round(complex_ratio, 2),
        "verb_ratio":     round(verb_ratio, 2),
        "noun_ratio":     round(noun_ratio, 2),
        "avg_word_length": round(avg_word_length, 2),
    }


results = []
for idx, row in tqdm(df_all.iterrows(), total=len(df_all)):
    try:
        metrics = analyze_syntax(row["text"])
        if metrics:
            metrics["text_type"] = row["text_type"]
            metrics["region"] = row["region"]
            metrics["source"] = row["source"]
            results.append(metrics)
    except Exception as e:
        pass

df_syntax = pd.DataFrame(results)
print(f"\n Проанализировано: {len(df_syntax)} текстов")
print(f"\nСредние значения по типу текста:")
print(df_syntax.groupby("text_type")[
    ["avg_sent_length", "complex_ratio", "verb_ratio", "noun_ratio", "avg_word_length"]
].mean().round(2))
