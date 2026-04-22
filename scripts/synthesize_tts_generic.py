import json
import tempfile
from collections import defaultdict
from pathlib import Path

from pydub import AudioSegment
from melo.api import TTS


def synthesize_segments(translated_segments, out_dir: Path):
    device = 'cpu'
    model = TTS(language='ES', device=device)
    speaker_ids = model.hps.data.spk2id
    base_speaker = speaker_ids['ES'] if 'ES' in speaker_ids else list(speaker_ids.values())[0]

    by_speaker = defaultdict(list)
    for seg in translated_segments:
        speaker = seg.get('speaker') or 'UNKNOWN'
        if seg.get('text', '').strip():
            by_speaker[speaker].append(seg)

    total_duration_ms = int(max(seg['end'] for seg in translated_segments) * 1000) + 1000
    tracks_dir = out_dir / 'tts_speaker_tracks'
    segs_dir = out_dir / 'tts_segments'
    tracks_dir.mkdir(exist_ok=True)
    segs_dir.mkdir(exist_ok=True)

    manifest = {}
    for speaker, segments in by_speaker.items():
        timeline = AudioSegment.silent(duration=total_duration_ms)
        segment_files = []
        speaker_dir = segs_dir / speaker
        speaker_dir.mkdir(exist_ok=True)
        for idx, seg in enumerate(segments, 1):
            target_ms = max(100, int((seg['end'] - seg['start']) * 1000))
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_wav = Path(tmpdir) / 'seg.wav'
                model.tts_to_file(seg['text'], base_speaker, str(tmp_wav), speed=1.0)
                clip = AudioSegment.from_file(tmp_wav)
                if len(clip) > target_ms:
                    clip = clip[:target_ms]
                elif len(clip) < target_ms:
                    clip = clip + AudioSegment.silent(duration=target_ms - len(clip))
                out_clip = speaker_dir / f'segment_{idx:03}.wav'
                clip.export(out_clip, format='wav')
                timeline = timeline.overlay(clip, position=int(seg['start'] * 1000))
                segment_files.append(str(out_clip))
        track_path = tracks_dir / f'{speaker}.wav'
        timeline.export(track_path, format='wav')
        manifest[speaker] = {
            'track': str(track_path),
            'segments': segment_files,
            'voice_mode': 'generic_melotts_es'
        }

    (out_dir / 'tts_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    translated = json.loads(Path('translated_segments.json').read_text(encoding='utf-8'))
    out_dir = Path('tts_outputs')
    out_dir.mkdir(exist_ok=True)
    synthesize_segments(translated['segments'], out_dir)


if __name__ == '__main__':
    main()
