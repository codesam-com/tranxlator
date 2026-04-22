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
- ASR base: WhisperX como orquestador de transcripción alineada.
- Backend ASR: faster-whisper con checkpoint Whisper large-v3 para maximizar fidelidad sin depender de API de pago.
- Diarización: pyannote `speaker-diarization-community-1` ejecutado localmente.
- Traducción: modelos open-source tipo M2M100/NLLB.
- TTS / voice cloning: Coqui XTTS v2.

## Decisión fijada para el siguiente ciclo
### Transcripción
Se usará `WhisperX + faster-whisper + Whisper large-v3` como baseline principal.

Motivos:
- WhisperX aporta timestamps a nivel palabra, alineación forzada, VAD y asignación posterior de hablante.
- faster-whisper reduce coste de inferencia y memoria frente a OpenAI Whisper manteniendo la misma familia de modelos.
- large-v3 prioriza precisión frente a variantes turbo o checkpoints más pequeños.

### Diarización
Se usará `pyannote/speaker-diarization-community-1` como baseline principal.

Motivos:
- Es local/offline y no exige servicio de pago.
- Mejora el conteo/asignación de hablantes respecto a 3.1.
- Su salida `exclusive speaker diarization` facilita reconciliar diarización y timestamps de transcripción.

### Modelo descartado por ahora
`pyannote/speaker-diarization-precision-2` no se fija como baseline porque, aunque su propia documentación lo sitúa por encima de `community-1`, se ejecuta en servidores pyannoteAI y depende de clave/API externa. No es la opción más robusta para un pipeline reproducible sin billing.

## Requisitos clave
- Alineación temporal real.
- Diarización robusta.
- Segmentos limpios para clonación de voz.
- Sincronía en audio final.

## Estrategia de desarrollo
Iteraciones incrementales con ejecución real y análisis de logs.
