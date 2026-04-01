# SOP — Sistema Editorial ContentOps Toolkit

Este sistema está diseñado para producir contenidos SEO de forma controlada, escalable y con mínimo riesgo de canibalización.

## 1. Objetivo del sistema
Convertir una oportunidad editorial validada en:
1. Brief SEO detallado en `examples/briefs/`.
2. Calendario editorial enriquecido en `SEO_Master_Strategy.xlsx`.
3. Draft redactado en `examples/drafts/`.
4. HTML limpio en `examples/html/`.

## 2. Archivos principales del sistema
- `templates/SEO_Master_Strategy.xlsx` — Fuente principal de estrategia y control.
- `templates/Commerce_Catalog.xlsx` — Fuente para enlazado interno (productos y categorías).
- `scripts/` — Scripts en Python para lectura, conexión de datos y enlazado.

## 3. Flujo maestro (Fases)
1. **Fase 1 — Lectura de Contenido:** Validar el estado actual contra URLs publicadas (03_MASTER).
2. **Fase 2 — Enlazado Interno:** Cruzar backlog contra catálogo buscando match semántico.
3. **Fase 3 — Generación de Briefs:** Crear documentación técnica para redactores.
4. **Fase 4 — Producción Editorial:** Redactar, revisar y convertir a HTML.

## 4. Reglas de Calidad
- **Anti-Canibalización:** Es obligatorio revisar `03_MASTER` antes de iniciar cualquier pieza nueva.
- **Jerarquía de Enlazado:** Siempre priorizar categorías sobre productos individuales.
- **Semántica:** Evitar el keyword stuffing; enfocar el contenido en resolver la intención de búsqueda real del usuario.

*Nota: Este sistema ha sido anonimizado para su distribución pública.*
