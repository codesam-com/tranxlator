import argparse
import json
import shutil
from pathlib import Path


def copy_input(src: Path, dst_dir: Path) -> None:
    dst = dst_dir / src.name
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--inputs", nargs="+", required=True)
    args = parser.parse_args()

    with open(args.context, encoding="utf-8") as f:
        ctx = json.load(f)
    work_id = ctx["work_id"]

    base = Path("works") / work_id
    stage_dir = base / args.stage

    if stage_dir.exists():
        shutil.rmtree(stage_dir)
    stage_dir.mkdir(parents=True, exist_ok=True)

    for inp in args.inputs:
        p = Path(inp)
        if p.exists():
            copy_input(p, stage_dir)

    status_path = base / "status.json"
    status = {}
    if status_path.exists():
        status = json.loads(status_path.read_text(encoding="utf-8"))

    status["last_completed"] = args.stage
    status["last_failed"] = None

    base.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    Path("works/active_run.json").write_text(json.dumps(ctx, indent=2), encoding="utf-8")

    print("Persisted stage:", args.stage)


if __name__ == "__main__":
    main()
