import os

REQUIRED_PATHS = [
    "inputs/video_urls.txt",
    "scripts/start_run.py",
    ".github/workflows/00_manual_start.yml",
    ".github/workflows/10_transcribe.yml",
]


def main():
    missing = [p for p in REQUIRED_PATHS if not os.path.exists(p)]
    if missing:
        raise SystemExit(f"Missing required paths: {missing}")

    with open(".github/workflows/00_manual_start.yml", "r", encoding="utf-8") as f:
        content = f.read()
        if "workflow_dispatch" not in content:
            raise SystemExit("00_manual_start.yml must have workflow_dispatch")

    with open(".github/workflows/10_transcribe.yml", "r", encoding="utf-8") as f:
        content = f.read()
        if "workflow_run" not in content:
            raise SystemExit("10_transcribe.yml must have workflow_run")

    print("Repo validation OK")


if __name__ == "__main__":
    main()
