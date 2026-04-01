import pandas as pd
import sys
import unicodedata
import re

sys.stdout.reconfigure(encoding='utf-8')

from config import EXCEL_FILE_PATH, COMMERCE_CATALOG_PATH
editorial_file  = EXCEL_FILE_PATH
commercial_file = COMMERCE_CATALOG_PATH
output_sheet    = "08_ENLAZADO_INTERNO"

# ── helpers ──────────────────────────────────────────────────────────────────
def norm(text):
    t = str(text).lower()
    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t

def tokens(text, min_len=3):
    return set(w for w in re.findall(r'\w+', norm(text)) if len(w) >= min_len
               and w not in {'con','los','las','del','que','para','por','una','uno','mas','muy','sus','sin',
                             'entre','como','sobre','este','esta','todo','todos','hay','bien','ser'})

def score(query_tokens, target_ctx):
    tgt = tokens(target_ctx)
    if not tgt or not query_tokens: return 0
    inter = query_tokens & tgt
    return len(inter) / max(len(query_tokens), len(tgt))

# ── load data ─────────────────────────────────────────────────────────────────
df_back  = pd.read_excel(editorial_file,  sheet_name='07_BACKLOG_NUEVO',   engine='openpyxl')
df_prods = pd.read_excel(commercial_file, sheet_name='09_PRODUCTOS_MASTER', engine='openpyxl')
df_cats  = pd.read_excel(commercial_file, sheet_name='10_CATEGORIAS_MASTER', engine='openpyxl')

# Filter approved backlog rows
approved = df_back[df_back['decision'].astype(str).str.lower().str.contains('crear|aprobad', na=False)]
if approved.empty:
    approved = df_back[df_back['keyword_principal'].notna()]

rows = []

for _, ed in approved.iterrows():
    kw        = str(ed.get('keyword_principal', ''))
    cluster   = str(ed.get('cluster', ''))
    titulo    = str(ed.get('titulo_sugerido', ''))
    angulo    = str(ed.get('angulo_editorial', ''))
    intencion = str(ed.get('intencion_estimada', ''))

    # Build query signal
    query_raw = f"{kw} {cluster} {angulo}"
    q_tokens  = tokens(query_raw)

    # ── Score categories ──────────────────────────────────────────────────────
    df_cats['_score'] = df_cats['contexto_seo'].apply(lambda x: score(q_tokens, x))
    top_cats = df_cats.sort_values('_score', ascending=False).head(25)
    top_cats = top_cats[top_cats['_score'] >= 0.07]   # min threshold

    # ── Score products ────────────────────────────────────────────────────────
    df_prods['_score'] = df_prods['contexto_seo'].apply(lambda x: score(q_tokens, x))
    top_prods = df_prods.sort_values('_score', ascending=False).head(5)
    top_prods = top_prods[top_prods['_score'] >= 0.12]  # stricter threshold for products

    # ── Build suggestions per piece ───────────────────────────────────────────
    suggestions = []

    # Categories → top 2
    for _, cat in top_cats.head(2).iterrows():
        s = cat['_score']
        prio = 'alta' if s >= 0.25 else ('media' if s >= 0.12 else 'baja')
        anchor = cat['nombre'].lower()
        ubicacion = 'intro' if prio == 'alta' else 'cuerpo'
        motivo = f"Categoría comercial directa: '{cat['contexto_seo']}' coincide con la señal semántica del artículo sobre '{kw}'."
        suggestions.append({
            'keyword_principal': kw, 'cluster': cluster, 'titulo_sugerido': titulo,
            'tipo_origen': 'blog', 'hoja_origen': '07_BACKLOG_NUEVO',
            'url_destino': cat['url'], 'nombre_destino': cat['nombre'],
            'tipo_destino': 'categoria',
            'anchor_sugerido': anchor,
            'tipo_anchor': 'exacto' if s >= 0.3 else 'parcial',
            'prioridad': prio,
            'motivo_semantico': motivo,
            'ubicacion_recomendada': ubicacion,
            'observaciones': f"Score semántico: {s:.2f}"
        })

    # Products → top 3 (only if strong match)
    prod_count = 0
    for _, prod in top_prods.iterrows():
        if prod_count >= 3: break
        s = prod['_score']
        prio = 'alta' if s >= 0.35 else 'media'
        anchor = norm(prod['nombre'])[:60]
        motivo = f"Producto específico con match claro: slug contiene '{prod['contexto_seo'][:50]}' alineado con '{kw}'."
        suggestions.append({
            'keyword_principal': kw, 'cluster': cluster, 'titulo_sugerido': titulo,
            'tipo_origen': 'blog', 'hoja_origen': '07_BACKLOG_NUEVO',
            'url_destino': prod['url'], 'nombre_destino': prod['nombre'],
            'tipo_destino': 'producto',
            'anchor_sugerido': anchor,
            'tipo_anchor': 'contextual',
            'prioridad': prio,
            'motivo_semantico': motivo,
            'ubicacion_recomendada': 'bloque recomendacion',
            'observaciones': f"Score semántico: {s:.2f}"
        })
        prod_count += 1

    # Ensure minimum 3 suggestions: add more cats if needed
    if len(suggestions) < 3:
        extra_cats = top_cats.iloc[len(suggestions):]
        for _, cat in extra_cats.iterrows():
            if len(suggestions) >= 3: break
            s = cat['_score']
            anchor = cat['nombre'].lower()
            suggestions.append({
                'keyword_principal': kw, 'cluster': cluster, 'titulo_sugerido': titulo,
                'tipo_origen': 'blog', 'hoja_origen': '07_BACKLOG_NUEVO',
                'url_destino': cat['url'], 'nombre_destino': cat['nombre'],
                'tipo_destino': 'categoria',
                'anchor_sugerido': anchor,
                'tipo_anchor': 'parcial',
                'prioridad': 'baja',
                'motivo_semantico': f"Categoría de apoyo: '{cat['contexto_seo']}' relacionada con el tema del artículo.",
                'ubicacion_recomendada': 'FAQ',
                'observaciones': f"Score semántico: {s:.2f}"
            })

    rows.extend(suggestions)

# ── assemble output dataframe ─────────────────────────────────────────────────
cols = ['keyword_principal','cluster','titulo_sugerido','tipo_origen','hoja_origen',
        'url_destino','nombre_destino','tipo_destino','anchor_sugerido','tipo_anchor',
        'prioridad','motivo_semantico','ubicacion_recomendada','observaciones']

df_out = pd.DataFrame(rows)[cols]

# ── write to editorial file ───────────────────────────────────────────────────
with pd.ExcelWriter(editorial_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
    df_out.to_excel(writer, sheet_name=output_sheet, index=False)

# ── summary ───────────────────────────────────────────────────────────────────
n_piezas = len(approved)
n_total  = len(df_out)
n_cats   = len(df_out[df_out['tipo_destino'] == 'categoria'])
n_prods  = len(df_out[df_out['tipo_destino'] == 'producto'])

print(f"Piezas editoriales procesadas: {n_piezas}")
print(f"Total sugerencias generadas:   {n_total}")
print(f"  → Categorías:  {n_cats}")
print(f"  → Productos:   {n_prods}")
print(f"\nMuestra (primeras 5 filas):")
print(df_out[['keyword_principal','tipo_destino','nombre_destino','anchor_sugerido','prioridad']].head(5).to_string(index=False))
