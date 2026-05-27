ytt_api = YouTubeTranscriptApi()


candidate_channels = {
    "Екатеринбург": [
        ("UCW-EN3hRb9hQwhkMcGzhJUQ", "Новости Шеремета"),
        ("UCSY2vJyiTZv10npi8qr0tBw", "Новости Екатеринбург"),
        ("UC98dclLj-kHjPVUwXSRMbeQ", "Телекомпания ОТВ"),
    ],
    "Новосибирск": [
        ("UCGMo28dimZs6UpYYM0kFuSw", "VN Новости Новосибирска"),
        ("UC7jNKSiGVTz7j8eIMyntNlg", "Эпиграф.инфо"),
    ],
    "Челябинск": [
        ("UCoRsJDVTeld1BOyFmk7Iydg", "74RU Челябинск"),
        ("UCtnkW27rQNLQ7EjQiwQxF_g", "EA74 Челябинск"),
    ],
    "Краснодар": [
        ("UCeVPB5QarTM1IW7GmZghWfA", "Блог новости Краснодар"),
        ("UCKm4X_1-1MLoN967z0cm9YA", "Новости Krasnodar 23"),
    ],
    "Омск": [
        ("UCtMmba_7RNbEwkKUXoT3xZA", "НГС55 Омск"),
    ],
}

def check_channel_subtitles(channel_id: str, channel_name: str, n_videos: int = 3) -> int:

    video_ids = YouTubeTranscriptParser(region="Ростов")._get_video_ids_rss(channel_id, n_videos)
    if not video_ids:
        return 0
    found = 0
    for vid_id in video_ids:
        try:
            ytt_api.fetch(vid_id, languages=["ru"])
            found += 1
        except:
            pass
    return found

print("Проверяем субтитры...\n")
working_channels = {}

for region, channels in candidate_channels.items():
    print(f"=== {region} ===")
    working_channels[region] = []
    for channel_id, name in channels:
        found = check_channel_subtitles(channel_id, name)
        status = "j" if found > 0 else "7"
        print(f"  {status} {name}: {found} видео с субтитрами")
        if found > 0:
            working_channels[region].append((channel_id, name))
    print()
