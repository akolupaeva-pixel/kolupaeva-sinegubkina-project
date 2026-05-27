fig = plt.figure(figsize=(24, 38))
fig.patch.set_facecolor('#F8F9FA')

fig.text(0.5, 0.99, 'Синтаксический анализ русскоязычных текстов',
         ha='center', va='top', fontsize=24, fontweight='bold', color='#1A1A2E')
fig.text(0.5, 0.977,
         'Источники: региональные СМИ (6 городов) · YouTube-субтитры (Ростов, СПб) · Отзывы покупателей (Kaggle)',
         ha='center', va='top', fontsize=13, color='#666666')

metrics = [
    ("avg_sent_length", "Средняя длина предложения (слов)",    "Длинные предложения → книжный, сложный стиль"),
    ("complex_ratio",   "Доля сложных предложений",            "Больше союзов → разветвлённые конструкции"),
    ("noun_ratio",      "Доля существительных",                "Высокая номинализация → официальный стиль"),
    ("avg_word_length", "Средняя длина слова (символов)",      "Длинные слова → профессиональная лексика"),
]

type_colors   = {"smi": "#1E88E5", "video": "#FF9800", "review": "#43A047"}
type_labels   = {"smi": "СМИ", "video": "YouTube", "review": "Отзывы"}
region_colors = {
    "Екатеринбург":    "#E53935",
    "Челябинск":       "#8E24AA",
    "Новосибирск":     "#1E88E5",
    "Омск":            "#00897B",
    "Ростов":          "#F4511E",
    "Краснодар":       "#FFB300",
    "Санкт-Петербург": "#00ACC1",
    "не определён":    "#90A4AE",
}

from matplotlib.gridspec import GridSpec
gs = GridSpec(14, 2, figure=fig,
              hspace=0.9, wspace=0.35,
              top=0.968, bottom=0.02,
              left=0.12, right=0.95)


block_positions = {
    "① СМИ vs YouTube vs Отзывы":           0.958,
    "② Региональные СМИ: сравнение городов": 0.638,
    "③ Ростов и СПб: СМИ vs YouTube":        0.318,
}
for label, y in block_positions.items():
    fig.text(0.03, y, label, fontsize=16, fontweight='bold', color='#1A1A2E')


for i, (metric, title, desc) in enumerate(metrics):
    ax = fig.add_subplot(gs[i, 0])
    ax.set_facecolor('#FFFFFF')
    data = df_syntax.groupby("text_type")[metric].mean()
    mean_val = data.mean()

    bars = ax.barh([type_labels[t] for t in data.index], data.values,
                   color=[type_colors[t] for t in data.index],
                   edgecolor='white', height=0.5)
    ax.axvline(mean_val, color='#333', linestyle='--', linewidth=1.5,
               label=f'Среднее: {mean_val:.2f}')
    for bar, val in zip(bars, data.values):
        ax.text(val + data.max()*0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.2f}', va='center', ha='left', fontsize=11, fontweight='bold')
    ax.set_title(f'{title}\n{desc}', fontsize=11, fontweight='bold',
                 loc='left', color='#1A1A2E', pad=6)
    ax.legend(fontsize=9, loc='lower right')
    ax.set_xlim(0, data.max() * 1.2)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle=':')


df_smi = df_syntax[df_syntax["text_type"] == "smi"]

for i, (metric, title, desc) in enumerate(metrics):
    ax = fig.add_subplot(gs[i+5, 0])
    ax.set_facecolor('#FFFFFF')
    data = df_smi.groupby("region")[metric].mean().sort_values(ascending=True)
    mean_val = data.mean()

    bars = ax.barh(data.index, data.values,
                   color=[region_colors[r] for r in data.index],
                   edgecolor='white', height=0.55)
    ax.axvline(mean_val, color='#333', linestyle='--', linewidth=1.5,
               label=f'Среднее: {mean_val:.2f}')
    for bar, (region, val) in zip(bars, data.items()):
        ax.text(val + data.max()*0.01, bar.get_y() + bar.get_height()/2,
                f'{val:.2f}', va='center', ha='left', fontsize=11,
                fontweight='bold', color=region_colors[region])
        if region == data.idxmax():
            ax.text(data.max()*1.1, bar.get_y() + bar.get_height()/2,
                    '▲ МАКС', va='center', fontsize=9,
                    color='#E53935', fontweight='bold')
        elif region == data.idxmin():
            ax.text(data.max()*1.1, bar.get_y() + bar.get_height()/2,
                    '▼ МИН', va='center', fontsize=9,
                    color='#1E88E5', fontweight='bold')
    ax.set_title(f'{title}\n{desc}', fontsize=11, fontweight='bold',
                 loc='left', color='#1A1A2E', pad=6)
    ax.legend(fontsize=9, loc='lower right')
    ax.set_xlim(0, data.max() * 1.25)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.grid(axis='x', alpha=0.3, linestyle=':')


df_compare = df_syntax[df_syntax["region"].isin(["Ростов", "Санкт-Петербург"])]

for i, (metric, title, desc) in enumerate(metrics):
    ax = fig.add_subplot(gs[i+10, 0])
    ax.set_facecolor('#FFFFFF')
    data = df_compare.groupby(["region", "text_type"])[metric].mean().reset_index()

    regions = ["Ростов", "Санкт-Петербург"]
    x = np.arange(len(regions))
    width = 0.35

    for j, text_type in enumerate(["smi", "video"]):
        vals = []
        for region in regions:
            row = data[(data["region"] == region) & (data["text_type"] == text_type)]
            vals.append(row[metric].values[0] if len(row) > 0 else 0)
        bars = ax.bar(x + (j - 0.5) * width, vals, width,
                      label=type_labels[text_type],
                      color=type_colors[text_type], edgecolor='white')
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + max(vals)*0.01,
                        f'{val:.2f}', ha='center', va='bottom',
                        fontsize=10, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(regions, fontsize=11)
    ax.set_title(f'{title}\n{desc}', fontsize=11, fontweight='bold',
                 loc='left', color='#1A1A2E', pad=6)
    ax.legend(fontsize=9)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    ax.grid(axis='y', alpha=0.3, linestyle=':')

plt.savefig("syntax_final_v2.png", dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.show()
