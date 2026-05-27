import tkinter as tk
import tempfile
import os
import sys

from tkinter import ttk, messagebox
from datetime import date

from db.conexion import obtener_todos
from db.reportes_sql import construir_consulta

from control_escolar.datepicker import DatePicker

from tkinter import filedialog
from utils.pdf_reportes import construir_pdf_en_memoria


def mostrar_reportes(parent, ciclo_activo):

    for w in parent.winfo_children():
        w.destroy()

    contenedor = tk.Frame(parent, bg="white")
    contenedor.pack(fill="both", expand=True)

    header = tk.Frame(contenedor, bg="#d0e4f5", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text=f"Reportes – Ciclo {ciclo_activo['nombre']}",
        bg="#d0e4f5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    notebook = ttk.Notebook(contenedor)
    notebook.pack(fill="both", expand=True)

    tabs = {}

    for nombre in ("Inscripción", "Reinscripción", "Alumnos"):
        frame = tk.Frame(notebook, bg="white", padx=15, pady=15)
        notebook.add(frame, text=nombre)

        # ===== FECHA =====
        lf_fecha = tk.LabelFrame(frame, text="Fecha", bg="white")
        lf_fecha.pack(fill="x", pady=5)

        fecha_var = tk.StringVar(value="todos")

        tk.Radiobutton(
            lf_fecha, text="Todos",
            variable=fecha_var, value="todos", bg="white"
        ).pack(anchor="w")

        rango = tk.Frame(lf_fecha, bg="white")
        rango.pack(anchor="w", pady=5)

        tk.Radiobutton(
            rango, text="Rango",
            variable=fecha_var, value="rango", bg="white"
        ).pack(side="left")

        tk.Label(rango, text="Desde:", bg="white").pack(side="left", padx=5)
        dp_desde = DatePicker(rango, initial=date.today())
        dp_desde.pack(side="left")

        tk.Label(rango, text="Hasta:", bg="white").pack(side="left", padx=5)
        dp_hasta = DatePicker(rango, initial=date.today())
        dp_hasta.pack(side="left")

        # ===== ORDEN =====
        lf_orden = tk.LabelFrame(frame, text="Orden", bg="white")
        lf_orden.pack(fill="x", pady=5)

        orden_var = tk.StringVar(value="matricula")

        tk.Radiobutton(
            lf_orden, text="Matrícula",
            variable=orden_var, value="matricula", bg="white"
        ).pack(anchor="w")

        tk.Radiobutton(
            lf_orden, text="Alfabético",
            variable=orden_var, value="alfabetico", bg="white"
        ).pack(anchor="w")

        # ===== AGRUPAR =====
        lf_agrupar = tk.LabelFrame(frame, text="Agrupar por", bg="white")
        lf_agrupar.pack(fill="x", pady=5)

        agrupar_cb = ttk.Combobox(
            lf_agrupar,
            state="readonly",
            values=[
                "Sin agrupar",
                "Fecha inscripción",
                "Grupo",
                "Género",
                "Condición"
            ]
        )
        agrupar_cb.current(0)
        agrupar_cb.pack(anchor="w", pady=5)

        tabs[nombre] = {
            "fecha_tipo": fecha_var,
            "desde": dp_desde,
            "hasta": dp_hasta,
            "orden": orden_var,
            "agrupar": agrupar_cb
        }

    acciones = tk.Frame(contenedor, bg="white")
    acciones.pack(fill="x", pady=(10, 0))

    reporte_actual = {
        "filas": [],
        "columnas": [],
        "titulo": ""
    }


    def generar_reporte():
        pestaña = notebook.tab(notebook.select(), "text")
        cfg = tabs[pestaña]

        fecha_tipo = cfg["fecha_tipo"].get()
        orden = cfg["orden"].get()
        agrupar = cfg["agrupar"].get()

        if fecha_tipo == "rango":
            desde = cfg["desde"].get_text()
            hasta = cfg["hasta"].get_text()
        else:
            desde = hasta = None

        sql, params = construir_consulta(
            tipo=pestaña,
            ciclo_id=ciclo_activo["id"],
            fecha_tipo=fecha_tipo,
            desde=desde,
            hasta=hasta,
            orden=orden,
            agrupar=agrupar
        )

        filas = obtener_todos(sql, params)

        columnas = [
            "Matrícula",
            "Nombre",
            "Fecha Inscripción",
            "Grupo",
            "Género",
            "Condición",
            "Contacto"
        ]

        reporte_actual["filas"] = filas
        reporte_actual["columnas"] = columnas
        reporte_actual["titulo"] = f"Reporte de {pestaña}"

        buffer = construir_pdf_en_memoria(
            titulo=reporte_actual["titulo"],
            columnas=reporte_actual["columnas"],
            filas=reporte_actual["filas"],
            ciclo_nombre=ciclo_activo["nombre"]
        )

        # Crear archivo temporal
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(buffer.read())
        tmp.close()

        ruta_pdf = tmp.name

        # Abrir según sistema operativo
        if sys.platform.startswith("win"):
            os.startfile(ruta_pdf)
        elif sys.platform == "darwin":
            os.system(f"open '{ruta_pdf}'")
        else:
            os.system(f"xdg-open '{ruta_pdf}'")
        


    ttk.Button(acciones, text="Generar", command=generar_reporte).pack(side="right", padx=5)




