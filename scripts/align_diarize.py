import json
import os

import whisperx


def main():
    device = "cpu"

    print("Loading audio...")
    audio = whisperx.load_audio("audio.wav")

    print("Loading raw transcript...")
    result = json.load(open("transcript_raw.json", "r", encoding="utf-8"))

    print("Aligning transcript...")
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    aligned = whisperx.align(result["segments"], model_a, metadata, audio, device)

    with open("transcript_aligned.json", "w", encoding="utf-8") as f:
        json.dump(aligned, f, indent=2, ensure_ascii=False)

    print("Running diarization...")
    hf_token = os.environ.get("HF_TOKEN")
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
    diarize_segments = diarize_model(audio)

    with open("diarization.json", "w", encoding="utf-8") as f:
        json.dump([str(x) for x in diarize_segments], f, indent=2)

    print("Assigning speakers...")
    final = whisperx.assign_word_speakers(diarize_segments, aligned)

    with open("transcript_speakers.json", "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print("Done align + diarize")


if __name__ == "__main__":
    main()
