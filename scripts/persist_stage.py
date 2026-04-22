import argparse
import json
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    ctx = json.load(open(args.context, encoding="utf-8"))
    work_id = ctx["work_id"]

    base = Path("works") / work_id
    stage_dir = base / args.stage

    # clean previous stage folder (retry behavior)
    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)

    for inp in args.inputs:
        p = Path(inp)
        if p.exists():
            shutil.copy(p, stage_dir / p.name)

    # status file
    status_path = base / "status.json"
    status = {}
    if status_path.exists():
        status = json.loads(status_path.read_text(encoding="utf-8"))

    status["last_completed"] = args.stage
    status["last_failed"] = None

    base.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    # active pointer
    Path("works/active_run.json").write_text(json.dumps(ctx, indent=2), encoding="utf-8")

    print("Persisted stage:", args.stage)


if __name__ == "__main__":
    main()
