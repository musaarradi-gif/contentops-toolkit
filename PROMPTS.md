# PROMPTS MASTER — Librería maestra de prompts del sistema editorial SEO

Este archivo contiene los prompts base para cada fase del sistema ContentOps Toolkit.

## 1. Regla general de uso
Todos los prompts de este sistema deben respetar estas reglas base:
- Revisar siempre canibalización contra `SEO_Master_Strategy.xlsx` → `03_MASTER`.
- Priorizar categorías frente a productos en enlazado interno.
- Seguir fielmente la estructura de directorios: `examples/briefs`, `examples/drafts`, `examples/html`.

---

## 2. Prompt — Enlazado Interno
**Objetivo:** Cruzar backlog editorial con catálogo comercial para proponer enlazado interno.

```text
Trabaja con DOS archivos Excel:
1. Archivo editorial: templates/SEO_Master_Strategy.xlsx
2. Archivo comercial: templates/Commerce_Catalog.xlsx

Objetivo:
Generar propuestas de enlazado interno SEO desde las oportunidades del backlog (Hoja 07_BACKLOG_NUEVO) hacia categorías (Hoja 10_CATEGORIAS_MASTER) y productos (Hoja 09_PRODUCTOS_MASTER).

Reglas:
- Prioriza categorías como destino principal.
- Sugiere productos solo si el match semántico es muy alto.
- Formatea la salida en la hoja 08_ENLAZADO_INTERNO.
```

---

## 3. Prompt — Generación de Brief SEO
**Objetivo:** Convertir una oportunidad del backlog en un brief detallado para redactores.

```text
Entrada: templates/SEO_Master_Strategy.xlsx (Hojas 07_BACKLOG_NUEVO y 08_ENLAZADO_INTERNO)

Objetivo:
Generar briefs SEO en formato Markdown guardados en examples/briefs/.

Estructura del brief:
1. Keyword principal y volumen.
2. Intención de búsqueda y perfil de usuario.
3. Estructura H2/H3 recomendada.
4. Enlazado interno (extraído de 08_ENLAZADO_INTERNO).
5. Checklist de calidad.
```

---

## 4. Prompt — Redacción de Borrador (Draft)
**Objetivo:** Redactar el artículo completo basándose en el brief aprobado.

```text
Entrada: examples/briefs/[nombre_del_brief].md

Instrucciones:
- Redactar siguiendo el brief de forma estricta.
- Tono profesional, natural y orientado a la intención de búsqueda.
- Guardar el resultado en examples/drafts/[nombre]_articulo.md.
```

---

*Nota: Este archivo ha sido anonimizado para su distribución pública.*
