# Sixcrep Full-Stack

Sistema completo de auditoría contable ambiental SEEA + ESG + ODS para Chile.

**Características:**
- Backend FastAPI real (conexión a baseapi.cl)
- Panel interactivo con mapa satelital de Antofagasta
- Enrolamiento real con pendrive
- Cálculos regionales reales de CO₂, ODS y ESG
- Generación de informe PDF completo de 20 páginas al hacer clic en un nodo

## Uso rápido

1. Abre `panel_antofagasta.html` en el navegador
2. Haz clic en cualquier nodo para descargar el informe completo con datos reales
3. Ejecuta `backend/run.sh` para iniciar el backend

## Estructura
- `panel_antofagasta.html` - Dashboard principal (Antofagasta)
- `backend/` - FastAPI real
- `scripts/enroll_pendrive.py` - Enrolamiento real con baseapi.cl

**RUT de prueba:** 77.231.540-6