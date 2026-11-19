# vistas/alumnos.py
import tkinter as tk
from tkinter import ttk

from db.conexion import obtener_conexion

from tkinter import ttk, messagebox

from caja.pagos_del_alumno import mostrar_pagos_del_alumno

# =====================================================
# MOSTRAR INSCRIPCIONES
# =====================================================
def mostrar_recibos(contenido, ciclo_activo, usuario_id):
    # Validar ciclo activo
    if not ciclo_activo["id"]:
        messagebox.showwarning(
            "Ciclo no seleccionado",
            "Debe seleccionar un ciclo escolar para ver alumnos."
        )
        return
    """Renderiza la vista de lista de alumnos dentro del frame 'contenido'."""
    
    # limpiar vista previa
    for w in contenido.winfo_children():
        w.destroy()

    # --- TÍTULO RECIBOS ---
    
    header = tk.Frame(contenido, bg="#d0e4f5", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text="RECIBOS - ALUMNOS",
        bg="#d0e4f5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)


    # --- BUSCADOR ---
    top = tk.Frame(contenido, bg="white")
    top.pack(fill="x", padx=20, pady=(20, 0))

    tk.Label(top, text="Buscar:", bg="white").pack(side="left", padx=(0,8))
    entry_buscar = tk.Entry(top, bd=1, relief="solid")
    entry_buscar.pack(side="left", padx=(0,8))

    btn_buscar = tk.Button(top, text="Buscar")
    btn_buscar.pack(side="left")

    btn_limpiar = tk.Button(top, text="Mostrar todos")
    btn_limpiar.pack(side="left", padx=(8,0))

    # --- TABLA ---
    table_frame = tk.Frame(contenido, bg="white")
    table_frame.pack(fill="both", expand=True, padx=20, pady=20)

    columnas = ("id", "nombre", "apellido_paterno", "apellido_materno",
                "grupo", "condicion")

    tabla = ttk.Treeview(
        table_frame,
        columns=columnas,
        show="headings"
    )

    # Encabezados
    tabla.heading("id", text="Matrícula")
    tabla.heading("nombre", text="Nombre")
    tabla.heading("apellido_paterno", text="Apellido Paterno")
    tabla.heading("apellido_materno", text="Apellido Materno")
    tabla.heading("grupo", text="Grupo")
    tabla.heading("condicion", text="Condición")

    # Tamaños iniciales
    tabla.column("id", width=100, anchor="center")
    tabla.column("nombre", width=160)
    tabla.column("apellido_paterno", width=140)
    tabla.column("apellido_materno", width=140)
    tabla.column("grupo", width=100)
    tabla.column("condicion", width=120)

    # SCROLLBARS VERTICAL + HORIZONTAL
    vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tabla.yview)
    hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tabla.xview)
    tabla.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tabla.pack(side="left", fill="both", expand=True)

    # FUNCIÓN: AJUSTAR ANCHO DE COLUMNA (como Excel)
    def ajustar_ancho_columnas():
        font = ("Segoe UI", 10)

        for col in columnas:
            max_width = tk.font.Font(font=font).measure(col) + 20  # ancho del encabezado

            for row in tabla.get_children():
                texto = str(tabla.set(row, col))
                width = tk.font.Font(font=font).measure(texto) + 20
                if width > max_width:
                    max_width = width

            tabla.column(col, width=max_width)

    # FUNCIÓN: CARGAR DATOS
    def cargar(filtro=""):
        conn = obtener_conexion()
        cur = conn.cursor()
        tabla.delete(*tabla.get_children())

        if filtro.strip():
            like = f"%{filtro}%"
            cur.execute("""
                SELECT E.matricula,
                    E.nombre,
                    E.apellido_paterno,
                    E.apellido_materno,
                    D.grupo,
                    D.condicion,
                    E.id
                FROM Estudiantes E
                INNER JOIN DatosEscolares D
                        ON D.estudiante_id = E.id
                    AND D.ciclo_id = ?
                WHERE E.nombre LIKE ?
                OR E.apellido_paterno LIKE ?
                OR E.apellido_materno LIKE ?
                ORDER BY E.id
            """, (ciclo_activo["id"], like, like, like))
        else:
            cur.execute("""
                SELECT E.matricula,
                    E.nombre,
                    E.apellido_paterno,
                    E.apellido_materno,
                    D.grupo,
                    D.condicion,
                    E.id
                FROM Estudiantes E
                INNER JOIN DatosEscolares D
                        ON D.estudiante_id = E.id
                    AND D.ciclo_id = ?
                ORDER BY E.id
            """, (ciclo_activo["id"],))


        filas = cur.fetchall()
        conn.close()

        # Insertar filas con valores NULL convertidos a ""
        for row in filas:
            tabla.insert("", "end", values=[v if v is not None else "" for v in row])

        ajustar_ancho_columnas()

    # EVENTOS DE BÚSQUEDA
    btn_buscar.config(command=lambda: cargar(entry_buscar.get()))
    entry_buscar.bind("<Return>", lambda e: cargar(entry_buscar.get()))
    btn_limpiar.config(command=lambda: (entry_buscar.delete(0, tk.END), cargar("")))

    # EVENTO: DOBLE CLIC / SELECCIÓN
    def on_select(event):
        sel = tabla.focus()
        if not sel:
            return

        vals = tabla.item(sel, "values")
        if not vals:
            return

        id = vals[6]

        # ⚠️ ORDEN CORRECTO DE PARÁMETROS
        mostrar_pagos_del_alumno(contenido, id, ciclo_activo, usuario_id)

    # Usar doble clic
    tabla.bind("<Double-1>", on_select)
    # Cargar datos iniciales
    cargar("")