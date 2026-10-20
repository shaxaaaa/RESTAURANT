# Final quality check

| Check | Result |
|---|---|
| Duration | **180.00 s** (ffprobe). 4,500 frames at 25 fps. |
| Format | H.264 High, **1920×1080**, 16:9, yuv420p; AAC stereo 48 kHz |
| Structure | 6 scenes on the requested timeline (0:00 / 0:15 / 0:40 / 1:15 / 1:50 / 2:25 / 3:00), see `STORYBOARD.md` |
| Opening title | “ASMO BINTI ABU BAKR” + “Jasorat, sadoqat va ilm timsoli” (0:02–0:13.6) ✔ |
| Final text | “Ilm — omonat. Uni asrash va yetkazish — mas’uliyat.” (2:55.6–3:00, slow fade) ✔ |
| Closing duʼo | Exact wording requested, segment 25 (2:46–2:55.5) ✔ |
| Subtitles vs narration | Subtitles are generated from the same `narration.json` used by the voice-over script, so the words match exactly. 25 segments, 47 subtitle cues, one line each, highest reading speed 14.4 characters/s. |
| Key terms highlighted | Zotun-nitoqayn, Hijrat, hadis, ellik sakkizta, Sahihi Buxoriy (gold, bold) and on-screen key-term cards ✔ |
| Honorifics | “roziyallohu anho / anhu” after every Companion’s name in the narration; “sollallohu alayhi vasallam” after Rasululloh ✔ |
| Uzbek spelling | Official Latin script, using ʻ (U+02BB) for oʻ/gʻ and ’/ʼ for the tutuq belgisi ✔ |
| Religious guidelines | The Prophet ﷺ and the Companions are never depicted. Only landscapes, architecture, objects and manuscripts are shown. No invented quotations or events. The one quotation, “Ha, onang bilan silai rahm qil”, appears only as Arabic manuscript text from Bukhari 2620 ✔ |
| Arabic text | Only verified phrases (see `SOURCES.md` §5), rendered with correct shaping ✔ |
| Historical accuracy | Checked against Bukhari 2979/3907/2620/227 and al-Dhahabi’s *Siyar*. **“110 narrations” replaced by the verifiable “58 (al-Dhahabi), 13 agreed upon by Bukhari & Muslim”**, with a note that counts differ between sources and that each narration has its own chain and grade ✔ |
| Sound | Vocal-free ambient soundscape: wind, low drone, crickets, quill, pages, cloth. No sudden loud sounds. Integrated loudness **−25.1 LUFS**, quiet enough to sit under narration (ducked a further −8 dB by `add_voiceover.py`) ✔ |
| Uzbek voice-over | ⚠ **Not included in the MP4.** This environment had no Uzbek TTS engine and no network access to TTS services. The voice is added with `add_voiceover.py`, using neural uz-UZ TTS or a human narrator; see README. The script was tested end to end with placeholder recordings: all 25 segments fit their slots, with at most ×1.02 speed-up. |
| Not achieved literally | “A manuscript closing gently” is shown as a slow fade over the arcade rather than an animated closing book. There are no people (teacher and students) in scene 5; it is represented symbolically by the study circle and the transmission diagram. |
