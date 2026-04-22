import argparse
import json
import os
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--attempt", default="1")
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    with open(args.context, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    video_key = ctx["video_key"]

    base = Path("audit/videos") / video_key / args.stage / f"run-{args.run_id}-attempt-{args.attempt}"
    base.mkdir(parents=True, exist_ok=True)

    for inp in args.inputs:
        p = Path(inp)
        if p.exists():
            shutil.copy(p, base / p.name)

    # write/update source.json
    source_path = Path("audit/videos") / video_key / "source.json"
    if not source_path.exists():
        source_path.parent.mkdir(parents=True, exist_ok=True)
        with open(source_path, "w", encoding="utf-8") as f:
            json.dump(ctx, f, indent=2, ensure_ascii=False)

    # update latest.json
    latest_path = Path("audit/videos") / video_key / "latest.json"
    latest = {}
    if latest_path.exists():
        latest = json.loads(latest_path.read_text(encoding="utf-8"))

    latest[args.stage] = {
        "run_id": args.run_id,
        "attempt": args.attempt,
        "path": str(base),
    }

    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    # global active run pointer
    active_path = Path("audit/active_run.json")
    active_path.parent.mkdir(parents=True, exist_ok=True)
    with open(active_path, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)

    print("Persisted stage:", args.stage)
    print("Output dir:", base)


if __name__ == "__main__":
    main()
