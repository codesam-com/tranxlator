# Arquitectura objetivo

Pipeline encadenado por workflows:

00_manual_start
→ 10_transcribe
→ 20_diarize
→ 30_translate
→ 40_summarize
→ 50_tts
→ 60_package
→ 70_cleanup

## Contrato entre etapas
Cada etapa produce un artefacto JSON + artefactos binarios.

Ejemplo:
- run_context.json
- transcript.json
- diarization.json
- translation.json

## Decisiones técnicas
- ASR: WhisperX (alineación + diarización) + faster-whisper backend.
- Diarización: pyannote community-1.
- Traducción: modelos open-source tipo M2M100/NLLB.
- TTS / voice cloning: Coqui XTTS v2.

## Requisitos clave
- Alineación temporal real.
- Diarización robusta.
- Segmentos limpios para clonación de voz.
- Sincronía en audio final.

## Estrategia de desarrollo
Iteraciones incrementales con ejecución real y análisis de logs.
