import os
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from control_escolar.datepicker import DatePicker

from db.conexion import obtener_conexion

from utils.pdf_reportes_cargos import generar_pdf_cargos_en_memoria, generar_pdf_estado_cuenta_en_memoria, generar_pdf_programa_ingresos_en_memoria, generar_pdf_descuentos_en_memoria, generar_pdf_condonaciones_en_memoria, generar_pdf_pagos_en_memoria


def mostrar_reportes_caja(parent, ciclo_activo):


    # ===============================
    # LIMPIAR CONTENEDOR
    # ===============================
    for w in parent.winfo_children():
        w.destroy()

    # ===============================
    # HEADER
    # ===============================
    header = tk.Frame(parent, bg="#d0e4f5", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text="Reportes - Caja",
        bg="#d0e4f5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=12)

    # ===============================
    # CONTENEDOR CENTRAL (CLAVE)
    # ===============================
    contenido = tk.Frame(parent)
    contenido.pack(fill="both", expand=True)

    # ===============================
    # NOTEBOOK
    # ===============================
    notebook = ttk.Notebook(contenido)
    notebook.pack(fill="both", expand=True, padx=15, pady=(1))

    tab_pagos = tk.Frame(notebook)
    tab_cargos = tk.Frame(notebook)
    tab_estado = tk.Frame(notebook)
    tab_programa = tk.Frame(notebook)
    tab_descuentos = tk.Frame(notebook)
    tab_condonaciones = tk.Frame(notebook)

    notebook.add(tab_pagos, text="Pagos")
    notebook.add(tab_cargos, text="Cargos")
    notebook.add(tab_estado, text="Estado de cuenta")
    notebook.add(tab_programa, text="Programa de ingresos")
    notebook.add(tab_descuentos, text="Descuentos")
    notebook.add(tab_condonaciones, text="Condonaciones")

    
    # ===============================
    # PESTAÑA PAGOS
    # ===============================
    cont_pagos = tk.Frame(tab_pagos)
    cont_pagos.pack(fill="both", expand=True, padx=20, pady=20)

    # ===============================
    # RANGO DE FECHAS
    # ===============================
    fechas_frame = tk.LabelFrame(
        cont_pagos,
        text="Rango de fechas",
        font=("Segoe UI", 11, "bold")
    )
    fechas_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)

    tk.Label(fechas_frame, text="Fecha inicial:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    dp_inicio_pagos = DatePicker(fechas_frame, initial=date.today())
    dp_inicio_pagos.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(fechas_frame, text="Fecha final:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    dp_fin_pagos = DatePicker(fechas_frame, initial=date.today())
    dp_fin_pagos.grid(row=1, column=1, padx=5, pady=5)

    # ===============================
    # DETALLE
    # ===============================
    detalle_frame = tk.LabelFrame(
        cont_pagos,
        text="Detalle",
        font=("Segoe UI", 11, "bold")
    )
    detalle_frame.grid(row=1, column=0, sticky="w", padx=10, pady=10)

    detalle_var1 = tk.StringVar(value="Usuario")

    cb_detalle = ttk.Combobox(
        detalle_frame,
        textvariable=detalle_var1,
        state="readonly",
        width=40,
        values=[
            "Usuario",
            "Usuario + Alumnos",
            "Usuario + Alumnos + Concepto"
        ]
    )
    cb_detalle.pack(padx=10, pady=8)
    cb_detalle.current(0)

    # ===============================
    # CICLO
    # ===============================
    ciclo_frame = tk.LabelFrame(
        cont_pagos,
        text="Ciclo",
        font=("Segoe UI", 11, "bold")
    )
    ciclo_frame.grid(row=2, column=0, sticky="w", padx=10, pady=10)

    ciclo_var_pagos = tk.StringVar(value="Ciclo actual")

    cb_ciclo_pagos = ttk.Combobox(
        ciclo_frame,
        textvariable=ciclo_var_pagos,
        state="readonly",
        width=25,
        values=[
            "Ciclo actual",
            "Todos los ciclos"
        ]
    )
    cb_ciclo_pagos.pack(padx=10, pady=6)
    cb_ciclo_pagos.current(0)

    # ===============================
    # GRADOS Y GRUPOS
    # ===============================
    grupos_frame = tk.LabelFrame(
        cont_pagos,
        text="Grados y grupos",
        font=("Segoe UI", 11, "bold")
    )
    grupos_frame.grid(row=0, column=1, rowspan=4, sticky="nsew", padx=20, pady=10)

    columnas = ("sel", "nombre")

    tree_pagos = ttk.Treeview(
        grupos_frame,
        columns=columnas,
        show="tree headings",
        height=14
    )

    tree_pagos.heading("#0", text="")
    tree_pagos.heading("sel", text="")
    tree_pagos.heading("nombre", text="Grado / Grupo")

    tree_pagos.column("#0", width=30, stretch=False)
    tree_pagos.column("sel", width=40, anchor="center", stretch=False)
    tree_pagos.column("nombre", width=260)

    tree_pagos.pack(side="left", fill="both", expand=True)

    vsb = ttk.Scrollbar(grupos_frame, orient="vertical", command=tree_pagos.yview)
    vsb.pack(side="right", fill="y")
    tree_pagos.configure(yscrollcommand=vsb.set)

    # ===============================
    # OBTENER GRADOS Y GRUPOS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.id,
            g.nombre,
            gr.id,
            gr.grupo
        FROM Grados g
        JOIN Grupos gr ON gr.grado_id = g.id
        ORDER BY g.orden, gr.grupo
    """)

    rows = cur.fetchall()
    conn.close()

    seleccionar_todo = {"valor": False}
    seleccionados_pagos = {}
    estructura = {}

    for grado_id, grado_nombre, grupo_id, grupo_num in rows:
        estructura.setdefault(grado_id, {
            "nombre": grado_nombre,
            "grupos": []
        })["grupos"].append((grupo_id, grupo_num))

    for grado_id, data in estructura.items():
        iid_grado = f"grado_{grado_id}"

        tree_pagos.insert(
            "",
            "end",
            iid=iid_grado,
            values=("☐", data["nombre"]),
            open=False
        )
        seleccionados_pagos[iid_grado] = False

        for grupo_id, grupo_num in data["grupos"]:
            grupo_texto = f"{data['nombre']}/{grupo_num}"

            tree_pagos.insert(
                iid_grado,
                "end",
                iid=grupo_texto,
                values=("☐", grupo_texto)
            )
            seleccionados_pagos[grupo_texto] = False

    # ===============================
    # CHECKBOX CLICK
    # ===============================
    def toggle_checkbox_pagos(event):
        region = tree_pagos.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tree_pagos.identify_column(event.x)
        if col != "#1":
            return

        item = tree_pagos.identify_row(event.y)
        if not item:
            return

        nuevo = not seleccionados_pagos[item]
        seleccionados_pagos[item] = nuevo
        tree_pagos.set(item, "sel", "☑" if nuevo else "☐")

        if item.startswith("grado_"):
            for hijo in tree_pagos.get_children(item):
                seleccionados_pagos[hijo] = nuevo
                tree_pagos.set(hijo, "sel", "☑" if nuevo else "☐")

        elif "/" in item:
            padre = tree_pagos.parent(item)
            hijos = tree_pagos.get_children(padre)

            if all(seleccionados_pagos[h] for h in hijos):
                seleccionados_pagos[padre] = True
                tree_pagos.set(padre, "sel", "☑")
            else:
                seleccionados_pagos[padre] = False
                tree_pagos.set(padre, "sel", "☐")

    def toggle_seleccionar_todo(event):
        region = tree_pagos.identify_region(event.x, event.y)
        if region != "heading":
            return

        col = tree_pagos.identify_column(event.x)
        if col != "#1":  # columna "nombre" (Grado / Grupo)
            return

        nuevo = not seleccionar_todo["valor"]
        seleccionar_todo["valor"] = nuevo

        for item in seleccionados_pagos:
            seleccionados_pagos[item] = nuevo
            tree_pagos.set(item, "sel", "☑" if nuevo else "☐")


    tree_pagos.bind("<Button-1>", toggle_checkbox_pagos)
    tree_pagos.bind("<ButtonRelease-1>", toggle_seleccionar_todo)

    # ===============================
    # BOTÓN GENERAR PDF
    # ===============================
    acciones_pagos = tk.Frame(tab_pagos)
    acciones_pagos.pack(fill="x", side="bottom", padx=20, pady=15)

    def generar_pagos_pdf():
        fecha_inicio = dp_inicio_pagos.get_text()
        fecha_fin = dp_fin_pagos.get_text()

        if not fecha_inicio or not fecha_fin:
            messagebox.showwarning(
                "Aviso",
                "Seleccione una fecha inicial y una fecha final."
            )
            return

        grupos = [
            i for i, v in seleccionados_pagos.items()
            if v and "/" in i
        ]

        if not grupos:
            messagebox.showwarning(
                "Aviso",
                "Seleccione al menos un grupo."
            )
            return

        detalle = detalle_var1.get()
        ciclo_modo = ciclo_var_pagos.get()

        pdf_buffer4 = generar_pdf_pagos_en_memoria(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            grupos=grupos,
            ciclo_modo=ciclo_modo,
            ciclo_activo=ciclo_activo,
            detalle=detalle,
            obtener_conexion=obtener_conexion
        )

        if pdf_buffer4 is None:
            messagebox.showinfo(
                "PDF vacío",
                "No existen pagos para los filtros seleccionados."
            )
            return

        # Vista previa temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_buffer4.read())
            ruta = f.name

        os.startfile(ruta)

    ttk.Button(
        acciones_pagos,
        text="Generar PDF",
        command=generar_pagos_pdf
    ).pack(side="right")










    # ===============================
    # PESTAÑA CARGOS
    # ===============================
    columnas = ("sel", "nombre")

    cont = tk.Frame(tab_cargos)
    cont.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(
        cont,
        columns=columnas,
        show="tree headings",
        height=16
    )

    tree.heading("#0", text="")
    tree.heading("sel", text="")
    tree.heading("nombre", text="Grado / Grupo")

    tree.column("#0", width=30, stretch=False)
    tree.column("sel", width=40, anchor="center", stretch=False)
    tree.column("nombre", width=260)

    tree.pack(side="left", fill="both", expand=True)

    vsb = ttk.Scrollbar(cont, orient="vertical", command=tree.yview)
    vsb.pack(side="left", fill="y")
    tree.configure(yscrollcommand=vsb.set)
    tree.configure(cursor="hand2")
    # ===============================
    # OBTENER GRADOS Y GRUPOS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.id,
            g.nombre,
            gr.id,
            gr.grupo
        FROM Grados g
        JOIN Grupos gr ON gr.grado_id = g.id
        ORDER BY g.orden, gr.grupo
    """)

    rows = cur.fetchall()
    conn.close()

    # ===============================
    # ESTRUCTURA
    # ===============================
    seleccionados = {}

    grados = {}
    for grado_id, grado_nombre, grupo_id, grupo_num in rows:
        grados.setdefault(grado_id, {
            "nombre": grado_nombre,
            "grupos": []
        })["grupos"].append((grupo_id, grupo_num))

    # ===============================
    # LLENAR TREEVIEW
    # ===============================
    for grado_id, data in grados.items():
        iid_grado = f"grado_{grado_id}"

        tree.insert(
            "",
            "end",
            iid=iid_grado,
            text="",
            values=("☐", data["nombre"]),
            open=False
        )
        seleccionados[iid_grado] = False

        for grupo_id, grupo_num in data["grupos"]:
            iid_grupo = f"grupo_{grupo_id}"

            tree.insert(
                iid_grado,
                "end",
                iid=iid_grupo,
                text="",
                values=("☐", str(grupo_num))
            )
            seleccionados[iid_grupo] = False

    # ===============================
    # TOGGLE CHECKBOX
    # ===============================
    def toggle_checkbox(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tree.identify_column(event.x)
        if col != "#1":  # columna sel
            return
        
        item = tree.identify_row(event.y)
        if not item:
            return

        nuevo = not seleccionados[item]
        seleccionados[item] = nuevo
        tree.set(item, "sel", "☑" if nuevo else "☐")

        # Si es grado → aplicar a hijos
        if item.startswith("grado_"):
            for hijo in tree.get_children(item):
                seleccionados[hijo] = nuevo
                tree.set(hijo, "sel", "☑" if nuevo else "☐")

        # Si es grupo → verificar padre
        elif item.startswith("grupo_"):
            padre = tree.parent(item)
            hijos = tree.get_children(padre)

            if all(seleccionados[h] for h in hijos):
                seleccionados[padre] = True
                tree.set(padre, "sel", "☑")
            else:
                seleccionados[padre] = False
                tree.set(padre, "sel", "☐")



    tree.bind("<Button-1>", toggle_checkbox)

    # ===============================
    # BOTONES
    # ===============================
    acciones = tk.Frame(tab_cargos, bg="white")
    acciones.pack(fill="x", side="bottom", padx=15, pady=15)

    def generar_pdf():
        grupos = [
            int(i.replace("grupo_", ""))
            for i, v in seleccionados.items()
            if v and i.startswith("grupo_")
        ]

        if not grupos:
            messagebox.showwarning("Aviso", "Seleccione al menos un grupo.")
            return

        pdf_buffer = generar_pdf_cargos_en_memoria(
            ciclo_activo=ciclo_activo,
            grupos_seleccionados=grupos,
            obtener_conexion=obtener_conexion
        )

        # ===============================
        # GUARDAR TEMPORAL Y ABRIR
        # ===============================
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_buffer.read())
            ruta = tmp.name

        os.startfile(ruta)


    ttk.Button(acciones, text="Generar PDF", command=generar_pdf).pack(side="right")








    # ===============================
    # PESTAÑA ESTADO DE CUENTA
    # ===============================
    cont_estado = tk.Frame(tab_estado)
    cont_estado.pack(fill="both", expand=True, padx=20, pady=20)

    # ===============================
    # FECHA DE CORTE
    # ===============================
    tk.Label(
        cont_estado,
        text="Fecha de corte:",
        font=("Segoe UI", 11, "bold")
    ).grid(row=0, column=0, sticky="w", pady=8)

    dp_corte = DatePicker(cont_estado, initial=date.today())
    dp_corte.grid(row=0, column=1, sticky="w", pady=8)

    # ===============================
    # FORMATO
    # ===============================
    tk.Label(
        cont_estado,
        text="Formato:",
        font=("Segoe UI", 11, "bold")
    ).grid(row=1, column=0, sticky="w", pady=8)

    formato_var = tk.StringVar(value="ciclo")

    tk.Radiobutton(
        cont_estado,
        text="Sólo ciclo actual",
        variable=formato_var,
        value="ciclo"
    ).grid(row=1, column=1, sticky="w")

    tk.Radiobutton(
        cont_estado,
        text="Todos los ciclos",
        variable=formato_var,
        value="todos"
    ).grid(row=1, column=2, sticky="w")

    # ===============================
    # ALUMNO
    # ===============================
    tk.Label(
        cont_estado,
        text="Alumno:",
        font=("Segoe UI", 11, "bold")
    ).grid(row=2, column=0, sticky="w", pady=8)

    alumno_var = tk.StringVar()
    cb_alumnos = ttk.Combobox(
        cont_estado,
        textvariable=alumno_var,
        state="readonly",
        width=45
    )
    cb_alumnos.grid(row=2, column=1, columnspan=2, sticky="w", pady=8)

    # ===============================
    # CARGAR ALUMNOS
    # ===============================
    def cargar_alumnos():
        conn = obtener_conexion()
        cur = conn.cursor()

        if formato_var.get() == "ciclo":
            cur.execute("""
                SELECT e.id, e.nombre, e.apellido_paterno, e.apellido_materno
                FROM Estudiantes e
                JOIN DatosEscolares d ON d.estudiante_id = e.matricula
                WHERE d.ciclo_id = ?
                ORDER BY e.apellido_paterno, e.apellido_materno, e.nombre
            """, (ciclo_activo["id"],))
        else:
            cur.execute("""
                SELECT id, nombre, apellido_paterno, apellido_materno
                FROM Estudiantes
                ORDER BY apellido_paterno, apellido_materno, nombre
            """)

        rows = cur.fetchall()
        conn.close()

        alumnos = []
        mapa = {}

        for r in rows:
            nombre = f"{r[1]} {r[2]} {r[3]}"
            alumnos.append(nombre)
            mapa[nombre] = r[0]

        cb_alumnos["values"] = alumnos
        cb_alumnos.mapa_ids = mapa

        if alumnos:
            cb_alumnos.current(0)

    cargar_alumnos()

    def on_cambio_formato(*_):
        cargar_alumnos()

    formato_var.trace_add("write", on_cambio_formato)

    # ===============================
    # BOTONES
    # ===============================
    acciones_estado = tk.Frame(tab_estado)
    acciones_estado.pack(fill="x", side="bottom", padx=20, pady=15)

    def generar_estado_cuenta():
        fecha_corte = dp_corte.get_text()
        alumno_nombre = alumno_var.get()

        if not fecha_corte:
            messagebox.showwarning("Aviso", "Se debe seleccionar una fecha")
            return

        if not alumno_nombre:
            messagebox.showwarning("Aviso", "Seleccione un alumno.")
            return

        alumno_id = cb_alumnos.mapa_ids.get(alumno_nombre)
        formato = "todos" if formato_var.get() == "todos" else "ciclo"

        pdf_buffer = generar_pdf_estado_cuenta_en_memoria(
            alumno_id=alumno_id,
            fecha_corte=fecha_corte,
            formato=formato,
            ciclo_activo=ciclo_activo,
            obtener_conexion=obtener_conexion
        )

        if pdf_buffer is None:
            messagebox.showinfo(
                "PDF vacío",
                "No existen registros para la fecha seleccionada."
            )
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_buffer.read())
            ruta = f.name

        os.startfile(ruta)

    ttk.Button(
        acciones_estado,
        text="Generar PDF",
        command=generar_estado_cuenta
    ).pack(side="right")





    # ===============================
    # PESTAÑA PROGRAMA DE INGRESOS
    # ===============================
    cont_programa = tk.Frame(tab_programa)
    cont_programa.pack(fill="both", expand=True, padx=20, pady=20)

    # ===============================
    # PAGOS
    # ===============================
    pagos_frame = tk.LabelFrame(
        cont_programa,
        text="Pagos",
        font=("Segoe UI", 11, "bold")
    )
    pagos_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)

    incluir_pagos_var = tk.IntVar(value=1)

    tk.Checkbutton(
        pagos_frame,
        text="Incluir pagos",
        variable=incluir_pagos_var
    ).pack(anchor="w", padx=10, pady=5)

    # ===============================
    # DETALLE
    # ===============================
    detalle_frame = tk.LabelFrame(
        cont_programa,
        text="Detalle",
        font=("Segoe UI", 11, "bold")
    )
    detalle_frame.grid(row=1, column=0, sticky="w", padx=10, pady=10)

    detalle_var = tk.StringVar(value="Meses")

    cb_detalle = ttk.Combobox(
        detalle_frame,
        textvariable=detalle_var,
        state="readonly",
        width=40,
        values=[
            "Meses",
            "Meses + concepto",
            "Meses + concepto + grado",
            "Meses + concepto + grado + alumno"
        ]
    )
    cb_detalle.pack(padx=10, pady=8)

    # ===============================
    # CICLO
    # ===============================
    ciclo_frame = tk.LabelFrame(
        cont_programa,
        text="Ciclo",
        font=("Segoe UI", 11, "bold")
    )
    ciclo_frame.grid(row=2, column=0, sticky="w", padx=10, pady=10)

    ciclo_var = tk.StringVar(value="actual")

    cb_ciclo = ttk.Combobox(
        ciclo_frame,
        textvariable=ciclo_var,
        state="readonly",
        width=25,
        values=[
            "Ciclo actual",
            "Todos los ciclos"
        ]
    )
    cb_ciclo.pack(padx=10, pady=6)
    cb_ciclo.current(0)

    # ===============================
    # GRADOS Y GRUPOS
    # ===============================
    grupos_frame = tk.LabelFrame(
        cont_programa,
        text="Grados y grupos",
        font=("Segoe UI", 11, "bold")
    )
    grupos_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=20, pady=10)

    columnas = ("sel", "nombre")

    tree_grupos = ttk.Treeview(
        grupos_frame,
        columns=columnas,
        show="tree headings",
        height=14
    )

    tree_grupos.heading("#0", text="")
    tree_grupos.heading("sel", text="")
    tree_grupos.heading("nombre", text="Grado / Grupo")

    tree_grupos.column("#0", width=30, stretch=False)
    tree_grupos.column("sel", width=40, anchor="center", stretch=False)
    tree_grupos.column("nombre", width=260)

    tree_grupos.pack(side="left", fill="both", expand=True)

    vsb = ttk.Scrollbar(grupos_frame, orient="vertical", command=tree_grupos.yview)
    vsb.pack(side="right", fill="y")
    tree_grupos.configure(yscrollcommand=vsb.set)

    # ===============================
    # OBTENER GRADOS Y GRUPOS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.id,
            g.nombre,
            gr.id,
            gr.grupo
        FROM Grados g
        JOIN Grupos gr ON gr.grado_id = g.id
        ORDER BY g.orden, gr.grupo
    """)

    rows = cur.fetchall()
    conn.close()

    
    seleccionar_todo = {"valor": False}
    seleccionados = {}
    estructura = {}

    for grado_id, grado_nombre, grupo_id, grupo_num in rows:
        estructura.setdefault(grado_id, {
            "nombre": grado_nombre,
            "grupos": []
        })["grupos"].append((grupo_id, grupo_num))

    # ===============================
    # LLENAR TREEVIEW
    # ===============================
    for grado_id, data in estructura.items():
        iid_grado = f"grado_{grado_id}"

        tree_grupos.insert(
            "",
            "end",
            iid=iid_grado,
            text="",
            values=("☐", data["nombre"]),
            open=False
        )
        seleccionados[iid_grado] = False

        for grupo_id, grupo_num in data["grupos"]:
            grupo_texto = f"{data['nombre']}/{grupo_num}"

            tree_grupos.insert(
                iid_grado,
                "end",
                iid=grupo_texto,          # ← CLAVE
                text="",
                values=("☐", grupo_texto)
            )
            seleccionados[grupo_texto] = False

    # ===============================
    # CHECKBOX CLICK (SOLO EN CUADRO)
    # ===============================
    def toggle_checkbox(event):
        region = tree_grupos.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tree_grupos.identify_column(event.x)
        if col != "#1":  # solo columna checkbox
            return

        item = tree_grupos.identify_row(event.y)
        if not item:
            return

        nuevo = not seleccionados[item]
        seleccionados[item] = nuevo
        tree_grupos.set(item, "sel", "☑" if nuevo else "☐")

        # Grado → propagar a hijos
        if item.startswith("grado_"):
            for hijo in tree_grupos.get_children(item):
                seleccionados[hijo] = nuevo
                tree_grupos.set(hijo, "sel", "☑" if nuevo else "☐")

        # Grupo → verificar padre
        elif item.startswith("grupo_"):
            padre = tree_grupos.parent(item)
            hijos = tree_grupos.get_children(padre)

            if all(seleccionados[h] for h in hijos):
                seleccionados[padre] = True
                tree_grupos.set(padre, "sel", "☑")
            else:
                seleccionados[padre] = False
                tree_grupos.set(padre, "sel", "☐")

    def toggle_seleccionar_todo(event):
        region = tree_grupos.identify_region(event.x, event.y)
        if region != "heading":
            return

        col = tree_grupos.identify_column(event.x)
        if col != "#1":  # columna "nombre" (Grado / Grupo)
            return

        nuevo = not seleccionar_todo["valor"]
        seleccionar_todo["valor"] = nuevo

        for item in seleccionados:
            seleccionados[item] = nuevo
            tree_grupos.set(item, "sel", "☑" if nuevo else "☐")


    tree_grupos.bind("<Button-1>", toggle_checkbox)
    tree_grupos.bind("<ButtonRelease-1>", toggle_seleccionar_todo)

    # ===============================
    # BOTÓN GENERAR PDF (ABAJO)
    # ===============================
    acciones_programa = tk.Frame(tab_programa)
    acciones_programa.pack(fill="x", side="bottom", padx=20, pady=15)

    def generar_programa_ingresos():
        grupos = [
            i
            for i, v in seleccionados.items()
            if v and "/" in i
        ]

        if not grupos:
            messagebox.showwarning("Aviso", "Seleccione al menos un grupo.")
            return

        incluir_pagos = incluir_pagos_var.get()
        detalle = detalle_var.get()

        # Aquí después conectamos el PDF
        pdf = generar_pdf_programa_ingresos_en_memoria(
            ciclo_activo=ciclo_activo,
            grupos=grupos,
            incluir_pagos=incluir_pagos,
            detalle=detalle,
            ciclo_modo=ciclo_var,
            obtener_conexion=obtener_conexion
        )

        if pdf is None:
            messagebox.showinfo(
                "PDF vacío",
                "No existen registros para los grupos seleccionados."
            )
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf.read())
            ruta = f.name

        os.startfile(ruta)

    ttk.Button(
        acciones_programa,
        text="Generar PDF",
        command=generar_programa_ingresos
    ).pack(side="right")





    # ===============================
    # PESTAÑA DESCUENTOS
    # ===============================
    cont_descuentos = tk.Frame(tab_descuentos)
    cont_descuentos.pack(fill="both", expand=True, padx=20, pady=20)

    # ===============================
    # RANGO DE FECHAS
    # ===============================
    fechas_frame = tk.LabelFrame(
        cont_descuentos,
        text="Rango de fechas",
        font=("Segoe UI", 11, "bold")
    )
    fechas_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)

    tk.Label(fechas_frame, text="Fecha inicial:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    dp_inicio = DatePicker(fechas_frame, initial=date.today())
    dp_inicio.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(fechas_frame, text="Fecha final:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    dp_fin = DatePicker(fechas_frame, initial=date.today())
    dp_fin.grid(row=1, column=1, padx=5, pady=5)

    # ===============================
    # CICLO
    # ===============================
    ciclo_frame = tk.LabelFrame(
        cont_descuentos,
        text="Ciclo",
        font=("Segoe UI", 11, "bold")
    )
    ciclo_frame.grid(row=1, column=0, sticky="w", padx=10, pady=10)

    ciclo_var = tk.StringVar(value="Ciclo actual")

    cb_ciclo = ttk.Combobox(
        ciclo_frame,
        textvariable=ciclo_var,
        state="readonly",
        width=30,
        values=["Ciclo actual", "Todos los ciclos"]
    )
    cb_ciclo.pack(padx=10, pady=8)

    # ===============================
    # GRADOS Y GRUPOS
    # ===============================
    grupos_frame = tk.LabelFrame(
        cont_descuentos,
        text="Grados y grupos",
        font=("Segoe UI", 11, "bold")
    )
    grupos_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=20, pady=10)

    columnas = ("sel", "nombre")

    tree_desc = ttk.Treeview(
        grupos_frame,
        columns=columnas,
        show="tree headings",
        height=14
    )

    tree_desc.heading("#0", text="")
    tree_desc.heading("sel", text="")
    tree_desc.heading("nombre", text="Grado / Grupo")

    tree_desc.column("#0", width=30, stretch=False)
    tree_desc.column("sel", width=40, anchor="center", stretch=False)
    tree_desc.column("nombre", width=260)

    tree_desc.pack(side="left", fill="both", expand=True)

    vsb = ttk.Scrollbar(grupos_frame, orient="vertical", command=tree_desc.yview)
    vsb.pack(side="right", fill="y")
    tree_desc.configure(yscrollcommand=vsb.set)
    tree_desc.configure(cursor="hand2")

    # ===============================
    # OBTENER GRADOS Y GRUPOS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.id,
            g.nombre,
            gr.id,
            gr.grupo
        FROM Grados g
        JOIN Grupos gr ON gr.grado_id = g.id
        ORDER BY g.orden, gr.grupo
    """)

    rows = cur.fetchall()
    conn.close()

    seleccionar_todo = {"valor": False}
    seleccionados = {}
    estructura = {}

    for grado_id, grado_nombre, grupo_id, grupo_num in rows:
        estructura.setdefault(grado_id, {
            "nombre": grado_nombre,
            "grupos": []
        })["grupos"].append((grupo_id, grupo_num))

    # ===============================
    # LLENAR TREEVIEW
    # ===============================
    for grado_id, data in estructura.items():
        iid_grado = f"grado_{grado_id}"

        tree_desc.insert(
            "",
            "end",
            iid=iid_grado,
            values=("☐", data["nombre"]),
            open=False
        )
        seleccionados[iid_grado] = False

        for grupo_id, grupo_num in data["grupos"]:
            grupo_texto = f"{data['nombre']}/{grupo_num}"

            tree_desc.insert(
                iid_grado,
                "end",
                iid=grupo_texto,
                values=("☐", grupo_texto)
            )
            seleccionados[grupo_texto] = False
        

    # ===============================
    # CHECKBOX (SOLO EN RECUADRO)
    # ===============================
    def toggle_checkbox_desc(event):
        region = tree_desc.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tree_desc.identify_column(event.x)
        if col != "#1":
            return

        item = tree_desc.identify_row(event.y)
        if not item:
            return

        nuevo = not seleccionados[item]
        seleccionados[item] = nuevo
        tree_desc.set(item, "sel", "☑" if nuevo else "☐")

        # Grado → hijos
        if item.startswith("grado_"):
            for hijo in tree_desc.get_children(item):
                seleccionados[hijo] = nuevo
                tree_desc.set(hijo, "sel", "☑" if nuevo else "☐")

        # Grupo → padre
        elif "/" in item:
            padre = tree_desc.parent(item)
            hijos = tree_desc.get_children(padre)

            if all(seleccionados[h] for h in hijos):
                seleccionados[padre] = True
                tree_desc.set(padre, "sel", "☑")
            else:
                seleccionados[padre] = False
                tree_desc.set(padre, "sel", "☐")

    def toggle_seleccionar_todo(event):
        region = tree_desc.identify_region(event.x, event.y)
        if region != "heading":
            return

        col = tree_desc.identify_column(event.x)
        if col != "#1":  # columna "nombre" (Grado / Grupo)
            return

        nuevo = not seleccionar_todo["valor"]
        seleccionar_todo["valor"] = nuevo

        for item in seleccionados:
            seleccionados[item] = nuevo
            tree_desc.set(item, "sel", "☑" if nuevo else "☐")


    tree_desc.bind("<Button-1>", toggle_checkbox_desc)
    tree_desc.bind("<ButtonRelease-1>", toggle_seleccionar_todo)
    # ===============================
    # BOTÓN GENERAR PDF
    # ===============================
    acciones_desc = tk.Frame(tab_descuentos)
    acciones_desc.pack(fill="x", side="bottom", padx=20, pady=15)

    def generar_descuentos_pdf():
        fecha_inicio = dp_inicio.get_text()
        fecha_fin = dp_fin.get_text()

        if not fecha_inicio or not fecha_fin:
            messagebox.showwarning(
                "Aviso",
                "Se debe seleccionar una fecha inicial y una fecha final."
            )
            return

        grupos = [
            i
            for i, v in seleccionados.items()
            if v and "/" in i
        ]

        if not grupos:
            messagebox.showwarning(
                "Aviso",
                "Seleccione al menos un grado/grupo."
            )
            return

        ciclo_modo = ciclo_var.get()  # "Ciclo actual" | "Todos los ciclos"

        pdf_buffer2 = generar_pdf_descuentos_en_memoria(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            grupos_seleccionados=grupos,
            ciclo_modo=ciclo_modo,
            ciclo_activo=ciclo_activo,
            obtener_conexion=obtener_conexion
        )

        if pdf_buffer2 is None:
            messagebox.showinfo(
                "PDF vacío",
                "No existen descuentos para los filtros seleccionados."
            )
            return

        # Vista previa temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_buffer2.read())
            ruta = f.name

        os.startfile(ruta)

    ttk.Button(
        acciones_desc,
        text="Generar PDF",
        command=generar_descuentos_pdf
    ).pack(side="right")





    # ===============================
    # PESTAÑA CONDONACIONES
    # ===============================
    cont_cond = tk.Frame(tab_condonaciones)
    cont_cond.pack(fill="both", expand=True, padx=20, pady=20)

    # ===============================
    # RANGO DE FECHAS
    # ===============================
    fechas_cond_frame = tk.LabelFrame(
        cont_cond,
        text="Rango de fechas",
        font=("Segoe UI", 11, "bold")
    )
    fechas_cond_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)

    tk.Label(fechas_cond_frame, text="Fecha inicial:")\
        .grid(row=0, column=0, sticky="w", padx=5, pady=5)

    dp_inicio_cond = DatePicker(fechas_cond_frame, initial=date.today())
    dp_inicio_cond.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(fechas_cond_frame, text="Fecha final:")\
        .grid(row=1, column=0, sticky="w", padx=5, pady=5)

    dp_fin_cond = DatePicker(fechas_cond_frame, initial=date.today())
    dp_fin_cond.grid(row=1, column=1, padx=5, pady=5)

    # ===============================
    # CICLO
    # ===============================
    ciclo_cond_frame = tk.LabelFrame(
        cont_cond,
        text="Ciclo",
        font=("Segoe UI", 11, "bold")
    )
    ciclo_cond_frame.grid(row=1, column=0, sticky="w", padx=10, pady=10)

    ciclo_var = tk.StringVar(value="Ciclo actual")

    cb_ciclo = ttk.Combobox(
        ciclo_cond_frame,
        textvariable=ciclo_var,
        state="readonly",
        width=30,
        values=["Ciclo actual", "Todos los ciclos"]
    )
    cb_ciclo.pack(padx=10, pady=8)

    # ===============================
    # GRADOS Y GRUPOS
    # ===============================
    grupos_cond_frame = tk.LabelFrame(
        cont_cond,
        text="Grados y grupos",
        font=("Segoe UI", 11, "bold")
    )
    grupos_cond_frame.grid(
        row=0, column=1, rowspan=2,
        sticky="nsew", padx=20, pady=10
    )

    columnas = ("sel", "nombre")

    tree_cond = ttk.Treeview(
        grupos_cond_frame,
        columns=columnas,
        show="tree headings",
        height=14
    )

    tree_cond.heading("#0", text="")
    tree_cond.heading("sel", text="")
    tree_cond.heading("nombre", text="Grado / Grupo")

    tree_cond.column("#0", width=30, stretch=False)
    tree_cond.column("sel", width=40, anchor="center", stretch=False)
    tree_cond.column("nombre", width=260)

    tree_cond.pack(side="left", fill="both", expand=True)

    vsb_cond = ttk.Scrollbar(
        grupos_cond_frame,
        orient="vertical",
        command=tree_cond.yview
    )
    vsb_cond.pack(side="right", fill="y")

    tree_cond.configure(yscrollcommand=vsb_cond.set)
    tree_cond.configure(cursor="hand2")

    # ===============================
    # OBTENER GRADOS Y GRUPOS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            g.id,
            g.nombre,
            gr.id,
            gr.grupo
        FROM Grados g
        JOIN Grupos gr ON gr.grado_id = g.id
        ORDER BY g.orden, gr.grupo
    """)

    rows = cur.fetchall()
    conn.close()

    seleccionar_todo = {"valor": False}
    estructura = {}
    seleccionados_cond = {}

    for grado_id, grado_nombre, grupo_id, grupo_num in rows:
        estructura.setdefault(grado_id, {
            "nombre": grado_nombre,
            "grupos": []
        })["grupos"].append((grupo_id, grupo_num))

    # ===============================
    # LLENAR TREEVIEW
    # ===============================
    for grado_id, data in estructura.items():
        iid_grado = f"grado_{grado_id}"

        tree_cond.insert(
            "",
            "end",
            iid=iid_grado,
            values=("☐", data["nombre"]),
            open=False
        )
        seleccionados_cond[iid_grado] = False

        for grupo_id, grupo_num in data["grupos"]:
            iid_grupo = f"{data['nombre']}/{grupo_num}"

            tree_cond.insert(
                iid_grado,
                "end",
                iid=iid_grupo,
                values=("☐", iid_grupo)
            )
            seleccionados_cond[iid_grupo] = False

    # ===============================
    # CHECKBOX SOLO EN EL CUADRO
    # ===============================
    def toggle_checkbox_cond(event):
        region = tree_cond.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tree_cond.identify_column(event.x)
        if col != "#1":
            return

        item = tree_cond.identify_row(event.y)
        if not item:
            return

        nuevo = not seleccionados_cond[item]
        seleccionados_cond[item] = nuevo
        tree_cond.set(item, "sel", "☑" if nuevo else "☐")

        # Grado → propagar a hijos
        if item.startswith("grado_"):
            for hijo in tree_cond.get_children(item):
                seleccionados_cond[hijo] = nuevo
                tree_cond.set(hijo, "sel", "☑" if nuevo else "☐")

        # Grupo → validar padre
        elif item.startswith("grupo_"):
            padre = tree_cond.parent(item)
            hijos = tree_cond.get_children(padre)

            if all(seleccionados_cond[h] for h in hijos):
                seleccionados_cond[padre] = True
                tree_cond.set(padre, "sel", "☑")
            else:
                seleccionados_cond[padre] = False
                tree_cond.set(padre, "sel", "☐")

    def toggle_seleccionar_todo(event):
        region = tree_cond.identify_region(event.x, event.y)
        if region != "heading":
            return

        col = tree_cond.identify_column(event.x)
        if col != "#1":  # columna "nombre" (Grado / Grupo)
            return

        nuevo = not seleccionar_todo["valor"]
        seleccionar_todo["valor"] = nuevo

        for item in seleccionados_cond:
            seleccionados_cond[item] = nuevo
            tree_cond.set(item, "sel", "☑" if nuevo else "☐")


    tree_cond.bind("<Button-1>", toggle_checkbox_cond)
    tree_cond.bind("<ButtonRelease-1>", toggle_seleccionar_todo)

    # ===============================
    # BOTÓN GENERAR PDF (ABAJO)
    # ===============================
    acciones_cond = tk.Frame(tab_condonaciones)
    acciones_cond.pack(fill="x", side="bottom", padx=20, pady=15)

    def generar_condonaciones_pdf():
        fecha_inicio = dp_inicio_cond.get_text()
        fecha_fin = dp_fin_cond.get_text()

        if not fecha_inicio or not fecha_fin:
            messagebox.showwarning(
                "Aviso",
                "Debe seleccionar fecha inicial y final."
            )
            return

        grupos = [
            i
            for i, v in seleccionados_cond.items()
            if v and "/" in i
        ]

        if not grupos:
            messagebox.showwarning(
                "Aviso",
                "Seleccione al menos un grupo."
            )
            return
        
        ciclo_modo = ciclo_var.get()  # "Ciclo actual" | "Todos los ciclos"



        pdf_buffer3 = generar_pdf_condonaciones_en_memoria(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            grupos=grupos,
            ciclo_modo=ciclo_modo,
            ciclo_activo=ciclo_activo,
            obtener_conexion=obtener_conexion
        )

        if pdf_buffer3 is None:
            messagebox.showinfo(
                "PDF vacío",
                "No existen condonaciones para los filtros seleccionados."
            )
            return

        # Vista previa temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(pdf_buffer3.read())
            ruta = f.name

        os.startfile(ruta)
        


    ttk.Button(
        acciones_cond,
        text="Generar PDF",
        command=generar_condonaciones_pdf
    ).pack(side="right")
