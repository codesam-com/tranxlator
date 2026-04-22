import argparse
import json
import shlex
import subprocess
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(shlex.quote(part) for part in cmd))
    subprocess.run(cmd, check=True)


def detect_html_payload(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    with path.open("rb") as f:
        head = f.read(512).lower()
    return b"<html" in head or b"<!doctype html" in head


def sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in ("-","_"," ")).strip().replace(" ","_")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    args = parser.parse_args()

    context = json.load(open(args.context, encoding="utf-8"))
    url = context["resolved_url"]
    source_type = context["source_type"]

    if source_type == "gdrive":
        run(["gdown", url])
        files = list(Path(".").glob("*"))
    else:
        run(["yt-dlp","-x","--audio-format","wav","-o","%(title)s.%(ext)s",url])
        files = list(Path(".").glob("*.wav"))

    media = max(files, key=lambda p: p.stat().st_mtime)

    if detect_html_payload(media):
        raise SystemExit("Downloaded HTML instead of media")

    name = sanitize(media.stem)
    context["video_name"] = name
    context["work_id"] = f"{name}_{context['url_hash']}"

    with open(args.context, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

    print("Detected video name:", name)


if __name__ == "__main__":
    main()
