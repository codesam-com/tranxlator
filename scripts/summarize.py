import json
from pathlib import Path


def build_summary(segments):
    text = " ".join(seg.get("text", "").strip() for seg in segments if seg.get("text", "").strip())
    lower = text.lower()

    themes = []
    if any(k in lower for k in ["mastur", "paje", "pervert", "bragas", "panties"]):
        themes.append("contenido erótico / sexual explícito")
    if any(k in lower for k in ["control", "obede", "no te detengas", "autocontrol"]):
        themes.append("dinámica de dominación verbal")
    if any(k in lower for k in ["dos", "tú", "yo", "mí"]):
        themes.append("interacción entre dos hablantes")

    if not themes:
        themes.append("diálogo hablado")

    summary = (
        "## Sinopsis\n\n"
        "El audio contiene un diálogo dramatizado entre dos hablantes. "
        "Predomina un tono íntimo y explícito, con instrucciones verbales, comentarios de control y una interacción centrada en contenido sexual. "
        "La pieza alterna entre intervención de un segundo hablante al inicio y un tramo mucho más largo dominado por la voz principal.\n\n"
        "## Observaciones\n\n"
        f"- Temas detectados: {', '.join(themes)}.\n"
        "- La traducción al español es usable para revisión, pero aún requiere refinamiento estilístico en algunos segmentos.\n"
        "- La diarización detecta dos hablantes y permite separar SRT por speaker.\n"
    )
    return summary, themes


def main():
    data = json.loads(Path("translated_segments.json").read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    summary, themes = build_summary(segments)

    Path("summary_es.md").write_text(summary, encoding="utf-8")
    Path("tags.json").write_text(json.dumps({"tags": themes}, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
