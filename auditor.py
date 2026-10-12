"""Auditor de workflows de n8n — Fase 1: leer y listar.

Lee los .json exportados de n8n en una carpeta y muestra, por cada
workflow, su nombre, número de nodos y los tipos de nodo que usa.

Uso:
    python auditor.py              # usa la carpeta ejemplos/
    python auditor.py otra_carpeta
"""

import argparse
import json
import sys
from pathlib import Path


def cargar_workflow(ruta):
    """Lee un archivo y regresa (workflow, None) o (None, mensaje_de_error).

    Nunca lanza excepción: los errores se regresan como texto para que
    el programa pueda reportarlos y seguir con el siguiente archivo.
    """
    try:
        texto = ruta.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return None, f"no se pudo leer el archivo ({e})"

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as e:
        return None, f"no es JSON válido (línea {e.lineno}: {e.msg})"

    # Un workflow de n8n es un objeto con una lista "nodes".
    if not isinstance(datos, dict) or not isinstance(datos.get("nodes"), list):
        return None, 'no parece un workflow de n8n (no tiene "nodes")'

    return datos, None


def resumir_workflow(workflow, ruta):
    """Extrae los datos que vamos a imprimir de un workflow ya cargado."""
    nodos = workflow["nodes"]
    # set() quita repetidos; sorted() da un orden estable para leer y comparar.
    tipos = sorted({n.get("type", "(sin tipo)") for n in nodos if isinstance(n, dict)})
    return {
        "nombre": workflow.get("name") or f"(sin nombre: {ruta.name})",
        "archivo": ruta.name,
        "num_nodos": len(nodos),
        "tipos": tipos,
    }


def main():
    # En Windows la consola puede usar cp1252; si un nombre de workflow trae
    # un carácter que no cabe ahí, se reemplaza por "?" en vez de tronar.
    sys.stdout.reconfigure(errors="replace")

    parser = argparse.ArgumentParser(description="Lista los workflows de n8n de una carpeta.")
    parser.add_argument(
        "carpeta",
        nargs="?",
        default="ejemplos",
        help="carpeta con los .json exportados de n8n (por defecto: ejemplos/)",
    )
    args = parser.parse_args()

    carpeta = Path(args.carpeta)
    if not carpeta.is_dir():
        print(f"Error: la carpeta '{carpeta}' no existe.")
        return 1

    resumenes = []
    errores = []
    for ruta in sorted(carpeta.glob("*.json")):
        workflow, error = cargar_workflow(ruta)
        if error:
            errores.append((ruta.name, error))
        else:
            resumenes.append(resumir_workflow(workflow, ruta))

    print(f"Workflows leídos: {len(resumenes)}\n")
    for r in resumenes:
        print(f"- {r['nombre']}  [{r['archivo']}]")
        print(f"  Nodos: {r['num_nodos']}")
        print(f"  Tipos ({len(r['tipos'])}):")
        for tipo in r["tipos"]:
            print(f"    - {tipo}")
        print()

    if errores:
        print(f"Archivos omitidos: {len(errores)}")
        for nombre, error in errores:
            print(f"  x {nombre}: {error}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
