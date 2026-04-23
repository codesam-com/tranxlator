import json
import subprocess
import tempfile
from pathlib import Path

from huggingface_hub import snapshot_download

FADE_MS = 50


def run(cmd):
    subprocess.run(cmd, check=True)


def ensure_openvoice_assets(cache_dir: Path):
    repo_dir = Path(snapshot_download(
        repo_id="myshell-ai/OpenVoiceV2",
        local_dir=str(cache_dir / "OpenVoiceV2"),
        allow_patterns=["converter/*"],
    ))
    return repo_dir / "converter"


def postprocess_track(src_track: Path, out_track: Path):
    fade_seconds = FADE_MS / 1000.0
    filter_chain = (
        f"loudnorm=I=-16:LRA=7:TP=-1.5,"
        f"afade=t=in:ss=0:d={fade_seconds},"
        f"afade=t=out:st=0:d={fade_seconds}:curve=tri"
    )
    run(["ffmpeg", "-y", "-i", str(src_track), "-af", filter_chain, str(out_track)])


def main():
    tts_manifest = json.loads(Path("tts_outputs/tts_manifest.json").read_text(encoding="utf-8"))
    refs_manifest = json.loads(Path("tts_refs_manifest.json").read_text(encoding="utf-8"))

    cache_dir = Path(".ov_cache")
    converter_dir = ensure_openvoice_assets(cache_dir)
    out_dir = Path("tts_outputs/openvoice_cloned_tracks")
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        helper = td / "clone_helper.py"
        helper.write_text(
            "import sys\n"
            "from pathlib import Path\n"
            "import torch\n"
            "from openvoice import se_extractor\n"
            "from openvoice.api import ToneColorConverter\n"
            "_orig_load = torch.hub.load\n"
            "def _trusted_load(repo_or_dir, model, *args, **kwargs):\n"
            "    kwargs.setdefault('trust_repo', True)\n"
            "    return _orig_load(repo_or_dir, model, *args, **kwargs)\n"
            "torch.hub.load = _trusted_load\n"
            "converter_dir, source_audio, target_audio, output_audio = sys.argv[1:5]\n"
            "device='cpu'\n"
            "converter = ToneColorConverter(str(Path(converter_dir)/'config.json'), device=device)\n"
            "converter.load_ckpt(str(Path(converter_dir)/'checkpoint.pth'))\n"
            "src_se, _ = se_extractor.get_se(source_audio, converter, target_dir='processed_src', vad=True)\n"
            "tgt_se, _ = se_extractor.get_se(target_audio, converter, target_dir='processed_tgt', vad=True)\n"
            "converter.convert(audio_src_path=source_audio, src_se=src_se, tgt_se=tgt_se, output_path=output_audio, message='@Tranxlator')\n",
            encoding="utf-8",
        )

        cloned_manifest = {}
        for speaker, meta in tts_manifest.items():
            if speaker not in refs_manifest:
                continue
            ref_mix = td / f"{speaker}_ref.wav"
            list_file = td / f"{speaker}_refs.txt"
            list_file.write_text("\n".join([f"file '{Path(c).resolve()}'" for c in refs_manifest[speaker]["clips"]]), encoding="utf-8")
            run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-ac", "1", "-ar", "22050", str(ref_mix)])

            src_track = Path(meta["track"])
            raw_clone = out_dir / f"{speaker}.raw.wav"
            final_clone = out_dir / f"{speaker}.wav"
            run(["python", str(helper), str(converter_dir), str(src_track), str(ref_mix), str(raw_clone)])
            postprocess_track(raw_clone, final_clone)
            cloned_manifest[speaker] = {
                "source_track": str(src_track),
                "cloned_track": str(final_clone),
                "raw_cloned_track": str(raw_clone),
                "clone_mode": "openvoice_v2_tone_color",
                "postprocess": {
                    "loudnorm": {"I": -16, "LRA": 7, "TP": -1.5},
                    "fade_ms": FADE_MS,
                },
            }

    (out_dir / "openvoice_manifest.json").write_text(json.dumps(cloned_manifest, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
