import json
import os

import whisperx
from whisperx.diarize import DiarizationPipeline


def main():
    device = "cpu"

    print("Loading audio...")
    audio = whisperx.load_audio("audio.wav")

    print("Loading raw transcript...")
    with open("transcript_raw.json", "r", encoding="utf-8") as f:
        result = json.load(f)

    print("Aligning transcript...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    aligned = whisperx.align(result["segments"], model_a, metadata, audio, device)

    with open("transcript_aligned.json", "w", encoding="utf-8") as f:
        json.dump(aligned, f, indent=2, ensure_ascii=False)

    print("Running diarization...")
    hf_token = os.environ.get("HF_TOKEN")
    diarize_model = DiarizationPipeline(use_auth_token=hf_token, device=device)
    diarize_segments = diarize_model(audio)

    diarization_rows = diarize_segments.to_dict(orient="records")
    with open("diarization.json", "w", encoding="utf-8") as f:
        json.dump(diarization_rows, f, indent=2, ensure_ascii=False)

    print("Assigning speakers...")
    final = whisperx.assign_word_speakers(diarize_segments, aligned)

    with open("transcript_speakers.json", "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print("Done align + diarize")


if __name__ == "__main__":
    main()
