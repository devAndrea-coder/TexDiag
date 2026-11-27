import streamlit as st

from motor import (DIAGNOSTICOS, PREGUNTAS, SINTOMAS, TRATAMIENTOS,
                   crear_motor, diagnosticar, leer_reglas)

st.set_page_config(page_title="TexDiag", page_icon="🧵", layout="centered")

ICONOS = {"S1": "🪡", "S2": "🧵", "S3": "🔁", "S4": "〰️",
          "S5": "🧶", "S6": "🛢️", "S7": "🔊", "S8": "📏"}

EJEMPLOS = {
    "Aguja defectuosa": ["S1", "S5"],
    "Tensión y enhebrado": ["S2", "S3", "S8"],
    "Exceso de aceite": ["S6"],
    "Un solo síntoma": ["S1"],
}

REQUIEREN_TECNICO = {"T6"}
OPCIONES = ["No sé", "Sí", "No"]
VALORES = {"Sí": "si", "No": "no"}

st.markdown(
    """
    <style>
    .hero {background: linear-gradient(135deg, #1F4E79 0%, #2E7DA6 100%);
           color: #fff; padding: 1.5rem 1.8rem; border-radius: 18px;
           margin-bottom: 1.2rem;}
    .hero-t {font-size: 2.2rem; font-weight: 800; line-height: 1.1;}
    .hero-s {margin-top: .4rem; opacity: .92; font-size: 1rem;}
    .tarjeta {border-radius: 14px; padding: .9rem 1.2rem; margin: .55rem 0;
              background: #fff; color: #262626; border: 1px solid #E3DACB;
              box-shadow: 0 1px 4px rgba(0,0,0,.07);}
    .diag {border-left: 6px solid #1F7A5C;}
    .accion {border-left: 6px solid #2E7DA6;}
    .alerta {border-left: 6px solid #D9822B; background: #FFF6EA;}
    .titulo {font-weight: 700; font-size: 1.05rem;}
    .detalle {margin-top: .25rem; color: #4A4A4A;}
    .nota {margin-top: .3rem; color: #8A4B0B; font-size: .9rem;}
    .chip {display: inline-block; padding: .08rem .6rem; border-radius: 999px;
           font-size: .75rem; font-weight: 700; background: #EAF2F8;
           color: #1F4E79; margin-right: .4rem;}
    .chip-alerta {background: #FBE3C4; color: #8A4B0B;}
    .chip-top {background: #D8F0E6; color: #145C43;}
    .barra {height: 10px; background: #EDE6DA; border-radius: 999px;
            margin: .55rem 0 .25rem; overflow: hidden;}
    .relleno {height: 100%; border-radius: 999px;}
    .alto {background: #1F7A5C;} .medio {background: #2E7DA6;}
    .bajo {background: #D9822B;}
    .certeza {font-size: .85rem; color: #4A4A4A;}
    .vacio {text-align: center; padding: 1.6rem 1rem; border-radius: 14px;
            border: 2px dashed #CFC3AF; color: #6B6254; background: #fff;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def cargar_reglas():
    """Las reglas no cambian: se leen una vez y se comparten (solo lectura)."""
    return leer_reglas(crear_motor())


REGLAS = cargar_reglas()

# Cada usuario (sesión) tiene su propio motor CLIPS.
if "motor" not in st.session_state:
    st.session_state["motor"] = crear_motor()


def limpiar_respuestas():
    for pid in PREGUNTAS:
        st.session_state[f"resp_{pid}"] = OPCIONES[0]


def cargar_ejemplo(codigos):
    st.session_state["seleccion"] = list(codigos)
    limpiar_respuestas()


def nombre_sintoma(codigo):
    return f"{ICONOS[codigo]} {SINTOMAS[codigo]}"


def nombre_elemento(codigo):
    if codigo in SINTOMAS:
        return f"{codigo} · {SINTOMAS[codigo]}"
    if codigo in DIAGNOSTICOS:
        return f"{codigo} · {DIAGNOSTICOS[codigo]}"
    return f"{codigo} · {TRATAMIENTOS[codigo][0]}"


def nivel(cf):
    if cf >= 0.70:
        return "alto", "Alta"
    if cf >= 0.45:
        return "medio", "Media"
    return "bajo", "Posible"


def barra(cf):
    clase, etiqueta = nivel(cf)
    return (
        f'<div class="barra"><div class="relleno {clase}" '
        f'style="width:{round(cf * 100)}%"></div></div>'
        f'<div class="certeza">Certeza {round(cf * 100)}% · {etiqueta}</div>'
    )


# ---------------------------- Panel lateral ---------------------------------
with st.sidebar:
    st.markdown("### Cómo funciona")
    st.markdown(
        "1. Marca los síntomas que observas.\n"
        "2. El motor de reglas (CLIPS) calcula la **certeza** de cada causa.\n"
        "3. Responde las preguntas para afinar el resultado.\n"
        "4. Consulta **por qué** llegó a esa conclusión."
    )
    st.markdown("### Probar un ejemplo")
    for etiqueta, codigos in EJEMPLOS.items():
        st.button(etiqueta, on_click=cargar_ejemplo, args=(codigos,),
                  width="stretch", key=f"ej_{etiqueta}")
    st.button("Limpiar selección", on_click=cargar_ejemplo, args=([],),
              width="stretch", type="primary", key="limpiar")
    st.divider()
    st.caption("Proyecto del curso de Sistema Inteligente · UNJFSC · 2026. "
               "Los valores de certeza son estimaciones del equipo y las "
               "recomendaciones son didácticas.")

# ------------------------------ Encabezado ----------------------------------
st.markdown(
    """
    <div class="hero">
      <div class="hero-t">🧵 TexDiag</div>
      <div class="hero-s">Diagnóstico inteligente de defectos en máquinas de
      coser rectas industriales</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ------------------------------ Entrada -------------------------------------
st.markdown("#### 1. ¿Qué estás observando?")
st.caption("Toca uno o varios síntomas. El resultado se actualiza al instante.")

seleccion = st.pills(
    "Síntomas observados",
    options=list(SINTOMAS),
    selection_mode="multi",
    format_func=nombre_sintoma,
    key="seleccion",
    on_change=limpiar_respuestas,
    label_visibility="collapsed",
) or []

# ------------------------------ Resultado -----------------------------------
st.markdown("#### 2. Diagnóstico")

if not seleccion:
    st.markdown(
        '<div class="vacio">Elige al menos un síntoma, o prueba un ejemplo '
        "desde el panel lateral.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

respuestas = {}
for pid in PREGUNTAS:
    valor = VALORES.get(st.session_state.get(f"resp_{pid}"))
    if valor:
        respuestas[pid] = valor

resultado = diagnosticar(st.session_state["motor"], seleccion, respuestas)
diagnosticos = resultado["diagnosticos"]
tratamientos = resultado["tratamientos"]

c1, c2, c3 = st.columns(3)
c1.metric("Síntomas", len(seleccion))
c2.metric("Causas probables", len(diagnosticos))
c3.metric("Acciones", len(tratamientos))

st.markdown("##### Causas probables (de mayor a menor certeza)")
for i, d in enumerate(diagnosticos):
    top = '<span class="chip chip-top">Más probable</span>' if i == 0 else ""
    notas = "".join(f'<div class="nota">ℹ️ {n}</div>' for n in d["notas"])
    st.markdown(
        f'<div class="tarjeta diag"><span class="chip">{d["codigo"]}</span>'
        f'{top}<div class="titulo">{d["nombre"]}</div>'
        f'{barra(d["cf"])}{notas}</div>',
        unsafe_allow_html=True,
    )

if resultado["preguntas"]:
    st.markdown("##### Afina el diagnóstico")
    with st.container(border=True):
        st.caption("Responde para ajustar la certeza. Puedes dejar «No sé».")
        for p in resultado["preguntas"]:
            st.radio(p["texto"], OPCIONES, horizontal=True,
                     key=f"resp_{p['id']}")

st.markdown("##### Qué hacer (en orden de prioridad)")
for t in tratamientos:
    if t["codigo"] in REQUIEREN_TECNICO:
        clase, aviso = "alerta", '<span class="chip chip-alerta">Requiere técnico</span>'
    else:
        clase, aviso = "accion", ""
    st.markdown(
        f'<div class="tarjeta {clase}"><span class="chip">{t["codigo"]}</span>'
        f"{aviso}"
        f'<div class="titulo">{t["nombre"]}</div>'
        f'<div class="detalle">{t["accion"]}</div>'
        f'<div class="certeza">Prioridad según certeza: {round(t["cf"] * 100)}%'
        f"</div></div>",
        unsafe_allow_html=True,
    )

# Explicación: qué reglas se usaron y cómo se combinó la certeza.
with st.expander("¿Por qué el sistema llegó a esta conclusión?"):
    st.caption(
        "Encadenamiento hacia adelante: síntomas → causa (con certeza) → acción. "
        "Cuando varias reglas apoyan la misma causa, la certeza se combina con "
        "FC = FC1 + FC2 × (1 − FC1)."
    )
    for d in diagnosticos:
        st.markdown(f"**{nombre_elemento(d['codigo'])}** · certeza "
                    f"**{round(d['cf'] * 100)}%**")
        acumulado = 0.0
        for id_regla in d["reglas"]:
            r = REGLAS[id_regla]
            if r["tipo"] == "sintoma":
                motivo = f"observas {nombre_elemento(r['si'])}"
            else:
                motivo = f"respondiste Sí a «{PREGUNTAS[r['si']]}»"
            acumulado = acumulado + r["cf"] * (1 - acumulado)
            st.markdown(f"- **{id_regla}** · {motivo} → aporta {r['cf']:.2f} "
                        f"(certeza acumulada {acumulado:.2f})")
    for t in tratamientos:
        r = REGLAS[t["regla"]]
        st.markdown(f"**{t['regla']}** · SI {nombre_elemento(r['si'])} → "
                    f"**{nombre_elemento(r['entonces'])}** "
                    f"(hereda certeza {round(t['cf'] * 100)}%)")