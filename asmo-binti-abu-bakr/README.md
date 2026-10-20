# Asmo binti Abu Bakr — 3-minute Islamic educational documentary (Uzbek)

| File | What it is |
|---|---|
| `asmo_binti_abu_bakr.mp4` | Finished 180 s video, 1920×1080, 25 fps. Burned-in Uzbek subtitles, titles, transitions, ambient sound design. **No voice yet**: see below. |
| `asmo_binti_abu_bakr.uz.srt` | The same subtitles as a separate SRT file (YouTube / players). |
| `NARRATION_SCRIPT.md` | Timestamped Uzbek narration script with pronunciation notes, for a narrator or TTS. |
| `STORYBOARD.md` | Scene-by-scene storyboard: shots, on-screen text and sound. |
| `SOURCES.md` | Historical sources, fact-check notes and the corrections made, e.g. why the video says 58 narrations, not 110. |
| `QUALITY_CHECK.md` | Final QA checklist with measured values. |
| `narration.json` | Single source of truth for narration text and timing. Subtitles, SRT and voice-over are all built from it. |

## Adding the Uzbek voice-over

The production environment had no Uzbek speech engine and no internet access to TTS services. The video therefore ships with the ambient soundtrack only, and the narration is timed and subtitled so a voice can be dropped in without re-editing.

**Option A: neural Uzbek TTS (free, about 2 minutes, needs internet)**

```bash
pip install edge-tts numpy          # ffmpeg must also be installed
python3 add_voiceover.py --video asmo_binti_abu_bakr.mp4 --voice uz-UZ-SardorNeural
# female voice:  --voice uz-UZ-MadinaNeural      slower:  --rate=-12%
```

The script does the following:
1. Synthesizes each of the 25 narration segments.
2. Fits each segment into its subtitle slot, speeding it up by at most ×1.2 when a phrase runs long.
3. Lowers the ambience under the voice (ducking).
4. Writes `asmo_binti_abu_bakr_ovozli.mp4`.

At the end it prints a table showing how well each segment fit its slot.

**Option B: a human narrator (best quality)**

1. Record each numbered segment from `NARRATION_SCRIPT.md` as `seg_01.wav` … `seg_25.wav`.
2. Run:

   ```bash
   python3 add_voiceover.py --video asmo_binti_abu_bakr.mp4 --recordings ./takes
   ```

Without a computer, you can run Option A in Google Colab. Upload the MP4, `narration.json` and `add_voiceover.py`, then run the commands in a cell with a leading `!`.

## Rebuilding the video from source

```bash
node render_plates.js build/plates 1            # 3D scenes (WebGL shaders, headless Chromium)
node render_film.js build/plates build/frames 25 # 4500 composited frames (titles, subtitles, motion)
python3 soundscape.py build/soundscape.wav      # vocal-free ambience
ffmpeg -framerate 25 -i build/frames/f_%05d.jpg -i build/soundscape.wav \
  -c:v libx264 -crf 20 -preset slow -pix_fmt yuv420p -c:a aac -b:a 160k -shortest asmo_binti_abu_bakr.mp4
python3 make_srt.py
```

All visuals are procedural. Nothing comes from stock footage or AI image generators. The Prophet ﷺ and the Companions are never depicted. Only landscapes, architecture, objects and manuscripts are shown.
