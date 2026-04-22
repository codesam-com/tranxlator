import json
import os

import whisperx
from whisperx.diarize import DiarizationPipeline


def main():
    device = "cpu"

    print("Loading audio...")
    audio = whisperx.load_audio("audio.wav")

    print("Loading aligned transcript...")
    with open("transcript_aligned.json", "r", encoding="utf-8") as f:
        aligned = json.load(f)

    print("Running diarization...")
    hf_token = os.environ.get("HF_TOKEN")
    diarize_model = DiarizationPipeline(token=hf_token, device=device)

    diarize_df = diarize_model(audio)

    diarization_rows = diarize_df.to_dict(orient="records")
    with open("diarization.json", "w", encoding="utf-8") as f:
        json.dump(diarization_rows, f, indent=2, ensure_ascii=False)

    print("Assigning speakers...")
    final = whisperx.assign_word_speakers(diarize_df, aligned)

    with open("transcript_speakers.json", "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print("Done diarize")


if __name__ == "__main__":
    main()
