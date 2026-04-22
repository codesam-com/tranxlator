import json
import time
from pathlib import Path

import whisperx


def main():
    started = time.time()
    device = "cpu"
    print("Loading WhisperX model large-v3 on CPU (int8)...")
    model = whisperx.load_model("large-v3", device=device, compute_type="int8")
    audio = whisperx.load_audio("audio.wav")
    result = model.transcribe(audio)

    Path("transcript_raw.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Aligning transcript...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    aligned = whisperx.align(result["segments"], model_a, metadata, audio, device)
    Path("transcript_aligned.json").write_text(
        json.dumps(aligned, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    plain_text = "\n\n".join(seg.get("text", "").strip() for seg in aligned.get("segments", []))
    Path("transcript_raw.txt").write_text(plain_text, encoding="utf-8")

    metrics = {
        "language": result.get("language"),
        "raw_segment_count": len(result.get("segments", [])),
        "aligned_segment_count": len(aligned.get("segments", [])),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    Path("metrics_transcribe.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Detected language:", result.get("language"))
    print("Aligned segments:", len(aligned.get("segments", [])))
    print("Elapsed seconds:", metrics["elapsed_seconds"])


if __name__ == "__main__":
    main()
