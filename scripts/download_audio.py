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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--output-prefix", default="source_audio")
    args = parser.parse_args()

    with open(args.context, "r", encoding="utf-8") as f:
        context = json.load(f)

    url = context["resolved_url"]
    source_type = context["source_type"]
    print(f"URL: {url}")
    print(f"SOURCE_TYPE: {source_type}")

    output_prefix = Path(args.output_prefix)

    if source_type == "gdrive":
        try:
            run(["gdown", url, "-O", str(output_prefix)])
        except subprocess.CalledProcessError:
            run(["gdown", "--fuzzy", url, "-O", str(output_prefix)])
        candidates = [output_prefix]
    else:
        run([
            "yt-dlp",
            "-x",
            "--audio-format",
            "wav",
            "-o",
            f"{output_prefix}.%(ext)s",
            url,
        ])
        candidates = sorted(Path(".").glob(f"{output_prefix.name}*"))

    existing = [p for p in candidates if p.exists()]
    if not existing:
        raise SystemExit("No downloaded payload found")

    payload = existing[0]
    print(f"Downloaded payload: {payload}")

    if detect_html_payload(payload):
        raise SystemExit(f"Downloaded payload is HTML instead of media: {payload}")


if __name__ == "__main__":
    main()
