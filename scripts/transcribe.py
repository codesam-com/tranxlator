import json
import time
from pathlib import Path

import whisperx


def main():
    started = time.time()
    print("Loading WhisperX model large-v3 on CPU (int8)...")
    model = whisperx.load_model("large-v3", device="cpu", compute_type="int8")
    result = model.transcribe("audio.wav")

    Path("transcript_raw.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    plain_text = "\n\n".join(seg.get("text", "").strip() for seg in result.get("segments", []))
    Path("transcript_raw.txt").write_text(plain_text, encoding="utf-8")

    metrics = {
        "language": result.get("language"),
        "segment_count": len(result.get("segments", [])),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    Path("metrics_transcribe.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Detected language:", result.get("language"))
    print("Segments:", len(result.get("segments", [])))
    print("Elapsed seconds:", metrics["elapsed_seconds"])


if __name__ == "__main__":
    main()
