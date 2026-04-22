import json
import shutil
from pathlib import Path


STAGES = ["start", "transcribe", "diarize", "translate", "summarize", "tts"]


def main():
    ctx = json.loads(Path("run_context.json").read_text(encoding="utf-8"))
    work_id = ctx["work_id"]
    work_dir = Path("works") / work_id

    package_root = Path("package_build") / work_id
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    included = []
    for stage in STAGES:
        stage_dir = work_dir / stage
        if stage_dir.exists():
            shutil.copytree(stage_dir, package_root / stage)
            included.append(stage)

    manifest = {
        "work_id": work_id,
        "included_stages": included,
        "artifact_name": f"package-{work_id}",
        "zip_name": f"{work_id}.zip",
    }
    (package_root / "package_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    archive_base = Path(work_id)
    archive_path = shutil.make_archive(str(archive_base), "zip", root_dir=str(package_root.parent), base_dir=work_id)

    Path("package_artifact.json").write_text(
        json.dumps({
            "artifact_name": manifest["artifact_name"],
            "zip_path": archive_path,
            "work_id": work_id,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
