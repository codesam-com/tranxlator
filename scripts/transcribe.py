import json
import whisperx


def main():
    print("Loading WhisperX model large-v3 on CPU (int8)...")
    model = whisperx.load_model("large-v3", device="cpu", compute_type="int8")

    result = model.transcribe("audio.wav")

    with open("transcript_raw.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("Detected language:", result.get("language"))
    print("Segments:", len(result.get("segments", [])))


if __name__ == "__main__":
    main()
