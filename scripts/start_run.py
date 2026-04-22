import argparse
import hashlib
import json
import re
from urllib.parse import parse_qs, urlparse


def is_comment_or_empty(line: str) -> bool:
    s = line.strip()
    return not s or s.startswith("#")


def detect_source(url: str) -> str:
    parsed = urlparse(url)
    if "drive.google.com" in parsed.netloc or "docs.google.com" in parsed.netloc:
        return "gdrive"
    return "direct"


def normalize_gdrive(url: str) -> str:
    parsed = urlparse(url)
    if "id" in parse_qs(parsed.query):
        return f"https://drive.google.com/uc?id={parse_qs(parsed.query)['id'][0]}"
    match = re.search(r"/file/d/([^/]+)", url)
    if match:
        return f"https://drive.google.com/uc?id={match.group(1)}"
    return url


def build_url_hash(original_url: str) -> str:
    return hashlib.sha256(original_url.encode("utf-8")).hexdigest()[:12]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.queue, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if not is_comment_or_empty(l)]

    if not lines:
        raise SystemExit("No URLs found in queue")

    url = lines[0]
    source = detect_source(url)
    resolved = normalize_gdrive(url) if source == "gdrive" else url
    url_hash = build_url_hash(url)

    context = {
        "original_url": url,
        "resolved_url": resolved,
        "source_type": source,
        "url_hash": url_hash,
        "video_name": None,
        "work_id": f"pending_{url_hash}",
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(context, f, indent=2, ensure_ascii=False)

    print("Selected URL:", url)
    print("Resolved URL:", resolved)
    print("URL hash:", url_hash)


if __name__ == "__main__":
    main()
