# Tranxlator

Estado actual: bootstrap funcional del pipeline en GitHub Actions.

## Objetivo
Procesar una URL de vídeo por ejecución manual y producir, de forma encadenada y depurable:

1. SRT general en idioma original.
2. SRT general traducido al español.
3. SRT por hablante en idioma original.
4. SRT por hablante traducido al español.
5. Resumen/sinopsis en español.
6. Tags temáticos.
7. Audios finales en español separados por hablante.

## Principios de diseño
- Orquestación en cadena mediante varios workflows.
- Inicio manual y continuación automática entre fases.
- Reanudación desde la última parte sana cuando sea posible.
- Una sola URL por ejecución.
- Cola persistente de entradas en `inputs/video_urls.txt`.
- Logs y artefactos explícitos en cada etapa.
- Validación continua del repo para evitar romper la cadena.

## Estado de este ciclo
Este ciclo deja preparado el esqueleto operativo mínimo:
- Cola de URLs en repositorio.
- Normalización y selección de la siguiente URL por un workflow manual.
- Detección básica de enlaces de Google Drive compartidos frente a URL directa.
- Generación de un manifiesto (`run_context.json`) como contrato entre workflows.
- Encadenado automático del siguiente workflow mediante `workflow_run`.
- Validación automática del repositorio en cada push y de forma programada.

## Estructura
- `inputs/video_urls.txt`: cola de URLs, una por línea.
- `scripts/start_run.py`: selecciona y normaliza la siguiente URL.
- `scripts/validate_repo.py`: comprobaciones de coherencia mínimas.
- `.github/workflows/00_manual_start.yml`: punto de entrada manual.
- `.github/workflows/10_transcribe.yml`: siguiente fase encadenada.
- `.github/workflows/ci.yml`: validación continua.
- `docs/architecture.md`: arquitectura objetivo y contratos.

## Restricciones ya asumidas
- No se usa OpenAI API.
- Se prioriza software y modelos gratuitos.
- El repo es la fuente de verdad.
- No se elimina la URL de la cola hasta que exista una fase final fiable que marque éxito real de extremo a extremo.

## Próximos ciclos
1. Descargar/resolver entrada a audio reproducible.
2. Transcripción alineada y refinada.
3. Diarización robusta y SRT por hablante.
4. Traducción contextual al español.
5. Resumen y tags.
6. Selección de muestras limpias y síntesis/clonación por hablante.
7. Empaquetado final y limpieza.
