import argparse
import json
from pathlib import Path

ORDER = ["start","transcribe","diarize","translate","summarize","tts","package","cleanup"]


def should_run(stage, ctx):
    status_path = Path("works") / ctx["work_id"] / "status.json"
    if not status_path.exists():
        return True
    status = json.loads(status_path.read_text())
    failed = status.get("last_failed")
    if not failed:
        return True
    return ORDER.index(stage) >= ORDER.index(failed)


def mark_failed(stage, ctx):
    base = Path("works") / ctx["work_id"]
    base.mkdir(parents=True, exist_ok=True)
    status_path = base / "status.json"
    status = {}
    if status_path.exists():
        status = json.loads(status_path.read_text())
    status["last_failed"] = stage
    status_path.write_text(json.dumps(status, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context")
    parser.add_argument("--stage")
    parser.add_argument("--mode", choices=["check","fail"])
    args = parser.parse_args()

    ctx = json.load(open(args.context))

    if args.mode == "check":
        if should_run(args.stage, ctx):
            print("RUN")
        else:
            print("SKIP")
    else:
        mark_failed(args.stage, ctx)


if __name__ == "__main__":
    main()
