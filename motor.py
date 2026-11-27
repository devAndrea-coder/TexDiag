"""Motor de TexDiag v2: conecta Python con las reglas de CLIPS (texdiag.clp).

CLIPS decide los diagnosticos, sus factores de certeza (FC) y los tratamientos.
Este modulo prepara los hechos, ejecuta el motor y ordena el resultado.
"""
import re
import unicodedata
from pathlib import Path

import clips

ARCHIVO_REGLAS = Path(__file__).parent / "texdiag_v2.clp"

# --- Textos para mostrar en pantalla (con tildes) ---------------------------
SINTOMAS = {
    "S1": "Puntada saltada",
    "S2": "Hilo superior roto",
    "S3": "Lazadas en el revés de la tela",
    "S4": "Tela fruncida",
    "S5": "Hilo deshilachado",
    "S6": "Manchas de aceite",
    "S7": "Ruido anormal",
    "S8": "Puntada irregular",
}

DIAGNOSTICOS = {
    "D1": "Aguja defectuosa o mal colocada",
    "D2": "Tensión del hilo incorrecta",
    "D3": "Enhebrado erróneo",
    "D4": "Exceso de aceite",
    "D5": "Presión del prensatelas o avance mal regulado",
    "D6": "Mecanismo desajustado (garfio o sincronización)",
}

TRATAMIENTOS = {
    "T1": ("Cambiar la aguja",
           "Usar el calibre adecuado al grosor de la tela y verificar que quede bien insertada."),
    "T2": ("Ajustar la tensión",
           "Regular el disco de tensión del hilo superior y revisar la tensión de la bobina."),
    "T3": ("Reenhebrar el hilo",
           "Subir el prensatelas y seguir la ruta completa de guías hasta la aguja."),
    "T4": ("Limpiar el aceite",
           "Retirar el exceso, limpiar la zona y reducir la cantidad de lubricante."),
    "T5": ("Regular el prensatelas",
           "Ajustar la presión y la altura de los dientes de arrastre según la tela."),
    "T6": ("Llamar a mantenimiento",
           "La sincronización del garfio requiere personal técnico."),
}

NOTAS = {
    "Tela elastica: usar aguja de punta bola.": "Tela elástica: usar aguja de punta bola.",
}

PREGUNTAS = {
    "P1": "¿La aguja lleva más de una semana de uso?",
    "P2": "¿La tela es elástica?",
    "P3": "¿El ruido continúa al girar la máquina sin tela?",
    "P4": "¿Se enhebró la máquina hace poco?",
}


def _sin_tildes(texto):
    """CLIPS trabaja mejor con texto ASCII (igual que en texdiag.clp)."""
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


def _numero_regla(id_regla):
    return int(id_regla[1:])


def crear_motor():
    """Crea un motor CLIPS nuevo con las reglas cargadas (uno por usuario)."""
    env = clips.Environment()
    env.load(str(ARCHIVO_REGLAS))
    return env


def diagnosticar(env, codigos, respuestas=None):
    """Ejecuta el motor.

    codigos:    lista de sintomas, por ejemplo ["S1", "S5"].
    respuestas: diccionario opcional {"P1": "si", "P2": "no"} con las
                respuestas a las preguntas de seguimiento.
    Devuelve diagnosticos y tratamientos (ordenados de mayor a menor
    certeza) y las preguntas de seguimiento pertinentes.
    """
    respuestas = respuestas or {}
    desconocidos = [c for c in codigos if c not in SINTOMAS]
    if desconocidos:
        raise ValueError(f"Síntomas desconocidos: {desconocidos}")
    for pregunta, valor in respuestas.items():
        if pregunta not in PREGUNTAS or valor not in ("si", "no"):
            raise ValueError(f"Respuesta no válida: {pregunta}={valor}")

    env.reset()  # vacia la memoria de trabajo de este usuario
    for codigo in codigos:
        nombre = _sin_tildes(SINTOMAS[codigo])
        env.assert_string(f'(sintoma (codigo {codigo}) (nombre "{nombre}"))')
    for pregunta, valor in respuestas.items():
        env.assert_string(f"(respuesta (pregunta {pregunta}) (valor {valor}))")
    env.run()

    diagnosticos, tratamientos, catalogo = [], [], {}
    for hecho in env.facts():
        plantilla = hecho.template.name
        if plantilla == "diagnostico":
            codigo = str(hecho["codigo"])
            diagnosticos.append({
                "codigo": codigo,
                "nombre": DIAGNOSTICOS[codigo],
                "cf": round(float(hecho["cf"]), 2),
                "reglas": sorted((str(r) for r in hecho["reglas"]), key=_numero_regla),
                "notas": [NOTAS.get(str(n), str(n)) for n in hecho["notas"]],
            })
        elif plantilla == "tratamiento":
            codigo = str(hecho["codigo"])
            nombre, accion = TRATAMIENTOS[codigo]
            tratamientos.append({
                "codigo": codigo,
                "nombre": nombre,
                "accion": accion,
                "regla": str(hecho["regla"]),
                "cf": round(float(hecho["cf"]), 2),
            })
        elif plantilla == "pregunta":
            catalogo[str(hecho["id"])] = str(hecho["diagnostico"])

    diagnosticos.sort(key=lambda d: (-d["cf"], d["codigo"]))
    tratamientos.sort(key=lambda t: (-t["cf"], t["codigo"]))

    # Solo se pregunta lo que ayuda a afinar un diagnostico ya presente.
    presentes = {d["codigo"] for d in diagnosticos}
    preguntas = [
        {"id": pid, "texto": PREGUNTAS[pid], "diagnostico": diag}
        for pid, diag in sorted(catalogo.items()) if diag in presentes
    ]
    return {
        "sintomas": [{"codigo": c, "nombre": SINTOMAS[c]} for c in codigos],
        "diagnosticos": diagnosticos,
        "tratamientos": tratamientos,
        "preguntas": preguntas,
    }


# --- Explicación: se lee directamente de las reglas de CLIPS ----------------
def leer_reglas(env):
    """Lee las reglas desde CLIPS y las convierte en un diccionario.

    Asi la explicacion sale de texdiag.clp (unica fuente de conocimiento).
    Tipos: "sintoma" (sintoma -> evidencia), "refuerzo" (respuesta ->
    evidencia) y "tratamiento" (diagnostico -> tratamiento).
    """
    reglas = {}
    for regla in env.rules():
        if not re.match(r"R\d+-", regla.name):
            continue  # reglas de control, como consolidar-evidencia
        id_regla = regla.name.split("-")[0]
        izquierda, _, derecha = str(regla).partition("=>")
        evidencia = re.search(
            r"\(assert \(evidencia \(diagnostico (\w+)\) \(regla \w+\) \(cf ([\d.]+)\)",
            derecha)
        if evidencia:
            diag, cf = evidencia.group(1), float(evidencia.group(2))
            sintoma = re.search(r"\(sintoma \(codigo (\w+)\)", izquierda)
            if sintoma:
                reglas[id_regla] = {"tipo": "sintoma", "si": sintoma.group(1),
                                    "entonces": diag, "cf": cf}
            else:
                pregunta = re.search(r"\(respuesta \(pregunta (\w+)\)", izquierda)
                reglas[id_regla] = {"tipo": "refuerzo", "si": pregunta.group(1),
                                    "entonces": diag, "cf": cf}
        else:
            origen = re.search(r"\(diagnostico \(codigo (\w+)\)", izquierda)
            trat = re.search(r"\(assert \(tratamiento \(codigo (\w+)\)", derecha)
            reglas[id_regla] = {"tipo": "tratamiento", "si": origen.group(1),
                                "entonces": trat.group(1)}
    return dict(sorted(reglas.items(), key=lambda kv: _numero_regla(kv[0])))