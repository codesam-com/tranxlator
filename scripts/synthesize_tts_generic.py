import json
import math
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

from huggingface_hub import hf_hub_download
from pydub import AudioSegment

VOICE_SPECS = [
    ("es/es_ES/davefx/medium/es_ES-davefx-medium.onnx", "es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json"),
    ("es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx", "es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json"),
]
MIN_SEGMENT_MS = 100
FADE_MS = 30


def ensure_voice_files(index: int, cache_dir: Path):
    model_rel, config_rel = VOICE_SPECS[index % len(VOICE_SPECS)]
    model_path = hf_hub_download(repo_id="rhasspy/piper-voices", filename=model_rel, local_dir=str(cache_dir))
    config_path = hf_hub_download(repo_id="rhasspy/piper-voices", filename=config_rel, local_dir=str(cache_dir))
    return Path(model_path), Path(config_path)


def synthesize_with_piper(text: str, model_path: Path, config_path: Path, output_path: Path):
    cmd = ["piper", "--model", str(model_path), "--config", str(config_path), "--output_file", str(output_path)]
    subprocess.run(cmd, input=text, text=True, check=True)


def ffprobe_duration_ms(path: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(float(result.stdout.strip()) * 1000)


def build_atempo_chain(ratio: float) -> str:
    ratio = max(0.25, min(4.0, ratio))
    filters = []
    while ratio < 0.5:
        filters.append("atempo=0.5")
        ratio /= 0.5
    while ratio > 2.0:
        filters.append("atempo=2.0")
        ratio /= 2.0
    filters.append(f"atempo={ratio:.5f}")
    return ",".join(filters)


def fit_clip_to_target(src_wav: Path, target_ms: int, dst_wav: Path):
    current_ms = max(MIN_SEGMENT_MS, ffprobe_duration_ms(src_wav))
    ratio = current_ms / max(MIN_SEGMENT_MS, target_ms)
    atempo = build_atempo_chain(ratio)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src_wav), "-filter:a", atempo, str(dst_wav)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def postprocess_clip(path: Path, target_ms: int) -> AudioSegment:
    clip = AudioSegment.from_file(path)
    if len(clip) > target_ms:
        clip = clip[:target_ms]
    elif len(clip) < target_ms:
        clip = clip + AudioSegment.silent(duration=target_ms - len(clip))
    fade = min(FADE_MS, max(5, len(clip) // 10))
    return clip.fade_in(fade).fade_out(fade)


def synthesize_segments(translated_segments, out_dir: Path):
    by_speaker = defaultdict(list)
    for seg in translated_segments:
        speaker = seg.get('speaker') or 'UNKNOWN'
        if seg.get('text', '').strip():
            by_speaker[speaker].append(seg)

    total_duration_ms = int(max(seg['end'] for seg in translated_segments) * 1000) + 1000
    tracks_dir = out_dir / 'tts_speaker_tracks'
    segs_dir = out_dir / 'tts_segments'
    cache_dir = out_dir / '.voice_cache'
    tracks_dir.mkdir(exist_ok=True)
    segs_dir.mkdir(exist_ok=True)
    cache_dir.mkdir(exist_ok=True)

    manifest = {}
    for speaker_idx, (speaker, segments) in enumerate(by_speaker.items()):
        timeline = AudioSegment.silent(duration=total_duration_ms)
        segment_files = []
        speaker_dir = segs_dir / speaker
        speaker_dir.mkdir(exist_ok=True)
        model_path, config_path = ensure_voice_files(speaker_idx, cache_dir)

        for idx, seg in enumerate(segments, 1):
            target_ms = max(MIN_SEGMENT_MS, int((seg['end'] - seg['start']) * 1000))
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir = Path(tmpdir)
                raw_wav = tmpdir / 'raw.wav'
                stretched_wav = tmpdir / 'stretched.wav'
                synthesize_with_piper(seg['text'], model_path, config_path, raw_wav)
                fit_clip_to_target(raw_wav, target_ms, stretched_wav)
                clip = postprocess_clip(stretched_wav, target_ms)
                out_clip = speaker_dir / f'segment_{idx:03}.wav'
                clip.export(out_clip, format='wav')
                timeline = timeline.overlay(clip, position=int(seg['start'] * 1000))
                segment_files.append(str(out_clip))

        track_path = tracks_dir / f'{speaker}.wav'
        timeline.export(track_path, format='wav')
        manifest[speaker] = {
            'track': str(track_path),
            'segments': segment_files,
            'voice_mode': 'generic_piper_es',
            'voice_model': str(model_path.name),
            'timing_strategy': 'ffmpeg_atempo_plus_fades'
        }

    (out_dir / 'tts_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    translated = json.loads(Path('translated_segments.json').read_text(encoding='utf-8'))
    out_dir = Path('tts_outputs')
    out_dir.mkdir(exist_ok=True)
    synthesize_segments(translated['segments'], out_dir)


if __name__ == '__main__':
    main()
