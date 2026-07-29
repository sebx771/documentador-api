# Plan: Implementación Multifile → .zip

> **CHECKLIST Meta 2** — La AI genera **N documentos markdown** (uno por chunk) empaquetados en un .zip, en vez de uno solo consolidado.

---

## Concepto

El sistema actual ya divide el código en **chunks** (grupos de archivos relacionados, default ~2 archivos por chunk). Cada chunk se documenta por separado y luego **todo se consolida en un solo documento**.

El cambio: en vez de consolidar, cada chunk → su propio .md, y todos se empaquetan en un .zip.

- Proyecto de 50 archivos → ~25 chunks → ~25 archivos .md en el .zip
- Cada .md cubre un grupo lógico de archivos (los que caben juntos en un chunk)
- No necesitamos cambiar los prompts ni el parser: el flujo por chunk ya funciona

---

## Fases

### Fase 1 — Nombrar chunks con nombres significativos

**Archivo:** `api/services/documentation_orchestrator.py`

Cada chunk ya tiene `chunk["files"]` (lista de nombres de archivo). Para nombrar el .md de salida:
- Si el chunk tiene 1 archivo: `<nombre_sin_ext>.md`
- Si tiene 2+: `<primer_archivo>_<segundo_archivo>_etc.md`
- Alternativa: usar el nombre del directorio común

Modificar `_process_chunks()` para que el `result` incluya un `filename` derivado de `chunk["files"]`.

### Fase 2 — Implementar `ZipService.crear_zip()`

**Archivo:** `api/services/zip_services.py`

```python
def crear_zip(files: dict[str, str]) -> bytes
```

- Recibe `{"nombre_chunk.md": "contenido...", ...}`
- Crea un `.zip` en memoria con `zipfile.ZipFile` modo `w`
- Preserva nombres de archivo (sin estructura de directorios compleja, o con subdirectorios si aplica)
- Retorna `bytes` del `.zip`

### Fase 3 — Modificar `DocumentationOrchestrator`

**Archivo:** `api/services/documentation_orchestrator.py`

- `process_zip()` acepta `multifile=False`
- Cuando `multifile=True`:
  - **Sáltate la consolidación AI** (no llamar a `_consolidate_documentation()`)
  - Cada chunk result ya tiene su `documentation` individual
  - Asignar un `filename` a cada chunk basado en los archivos que contiene
  - Retornar `{"files": {"chunk_1.md": "...", ...}, "consolidated": None, "metadata": {...}}`
- Cuando `multifile=False`: comportamiento actual sin cambios (consolidación + doc único)

### Fase 4 — Modificar `ZipController`

**Archivo:** `api/controllers/zip_controller.py`

- Nuevo método `_generar_zip_multifile(files_dict, cache_stats, elapsed)`:
  - Llama `ZipService.crear_zip(files_dict)` → bytes
  - Retorna `{"type": "file", "content": bytes, "mimetype": "application/zip", "filename": "docs_...zip"}`
- `upload_zip()`: cuando `doc_type == "multifile"`, llama al orquestador con `multifile=True` y luego a `_generar_zip_multifile()`

### Fase 5 — Ruta `/api/upload-zip`

**Archivo:** `api/routes/zip.py`

- Aceptar `doc_type="multifile"` como valor válido (junto a markdown/pdf/word)
- El `send_file` existente ya maneja `result["type"] == "file"` — sin cambios

## Lo que NO cambia

- ❌ No se modifican los prompts de la AI (siguen generando markdown normal por chunk)
- ❌ No se crea `MultifileParser` (no hay formato nuevo que parsear)
- ❌ No se toca `DocumentadorIA.generar()` (sigue igual)
- ❌ No se tocan los exportadores PDF/DOCX (siguen igual para sus formatos)
- ✅ Los chunks se procesan exactamente igual, solo se omite la consolidación

---

## Árbol de archivos afectados

| Archivo | Cambio |
|---|---|
| `api/services/zip_services.py` | Implementar `crear_zip(files_dict) → bytes` |
| `api/services/documentation_orchestrator.py` | `process_zip()` con flag `multifile`, saltar consolidación, generar `files` dict |
| `api/controllers/zip_controller.py` | + `_generar_zip_multifile()`, modificar `upload_zip()` |
| `api/routes/zip.py` | Sin cambios (ya maneja `doc_type` dinámico) |

---

## Criterio de éxito

1. Subir ZIP con `doc_type=multifile` → descargar un `.zip` con N archivos `.md` (uno por chunk)
2. Cada `.md` contiene la documentación de su grupo de archivos (coherente, como hoy)
3. PDF/DOCX siguen generando documento único consolidado (sin regresión)
4. El nombre de cada `.md` refleja los archivos que contiene (ej. `auth_service_db.md`)
5. Proyecto real de ~50 archivos produce ~25 .md (no 50)
