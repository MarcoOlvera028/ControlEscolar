# control_escolar/caja/pago_alumno.py

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta

from db.conexion import obtener_todos
from db.conexion import obtener_conexion

from utils.tickets import imprimir_ticket_pago, previsualizar_ticket


def to_float(valor):
    try:
        return float(str(valor).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


# =====================================================
# VISTA PRINCIPAL – PAGOS POR ALUMNO
# =====================================================
def mostrar_pagos_del_alumno(parent, alumno_id, ciclo_activo, usuario_id):
    # ===============================
    # LIMPIAR VISTA ANTERIOR
    # ===============================
    for w in parent.winfo_children():
        w.destroy()

    def safe(v):
        return "" if v is None else str(v)

    # ===============================
    # OBTENER DATOS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    cur.execute(
        "SELECT matricula, nombre, apellido_paterno, apellido_materno "
        "FROM Estudiantes WHERE id=?",
        (alumno_id,)
    )
    alumno = cur.fetchone() or (alumno_id, "", "", "")

    cur.execute("""
        SELECT fecha_inscripcion, grupo
        FROM DatosEscolares
        WHERE estudiante_id=? AND ciclo_id=?
    """, (alumno_id, ciclo_activo["id"]))
    escolares = cur.fetchone()

    conn.close()

    # ===============================
    # HEADER
    # ===============================
    header = tk.Frame(parent, bg="#d0e4f5", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text="Pagos del Alumno",
        bg="#d0e4f5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    # ===============================
    # BODY
    # ===============================
    body = tk.Frame(parent, bg="white")
    body.pack(fill="both", expand=True, padx=20, pady=15)

    # ===============================
    # DATOS ALUMNO
    # ===============================
    datos = tk.Frame(body, bg="white")
    datos.pack(fill="x")

    tk.Label(
        datos,
        text=f"Matrícula: {alumno[0]}   "
             f"Nombre: {alumno[1]} {alumno[2]} {alumno[3]}   "
             f"Grupo: {safe(escolares[1])}",
        bg="white",
        font=("Segoe UI", 11, "bold")
    ).pack(anchor="w")

    tk.Frame(body, height=2, bg="#e0e0e0").pack(fill="x", pady=12)

    # ===============================
    # TABLA DE CARGOS
    # ===============================
    columnas = ("sel", "concepto", "fecha", "monto", "estado")

    tabla_frame = tk.Frame(body, bg="white")
    tabla_frame.pack(fill="both", expand=True)

    # Scrollbars
    vsb = ttk.Scrollbar(tabla_frame, orient="vertical")
    hsb = ttk.Scrollbar(tabla_frame, orient="horizontal")

    tabla = ttk.Treeview(
        tabla_frame,
        columns=columnas,
        show="headings",
        height=12,
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set
    )

    vsb.config(command=tabla.yview)
    hsb.config(command=tabla.xview)

    # Layout con grid (NO pack aquí)
    tabla.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    tabla_frame.rowconfigure(0, weight=1)
    tabla_frame.columnconfigure(0, weight=1)

    tabla.heading("sel", text="")
    tabla.heading("concepto", text="Concepto")
    tabla.heading("fecha", text="Fecha")
    tabla.heading("monto", text="Monto total")
    tabla.heading("estado", text="Estado")


    
    tabla.column("sel", width=40, anchor="center", stretch=False)
    tabla.column("concepto", width=220)
    tabla.column("fecha", width=120, anchor="center")
    tabla.column("monto", width=120, anchor="e")
    tabla.column("estado", width=160, anchor="center")

    # Colores
    tabla.tag_configure("pagado", foreground="#0D47A1")
    tabla.tag_configure("siguiente", foreground="#64B5F6")
    tabla.tag_configure("nopagado", foreground="#D32F2F")

    # ===============================
    # PAGOS
    # ===============================
    pagos = obtener_todos("""
        SELECT
            p.id,
            c.concepto,
            p.fecha_pago,
            p.monto_pagado,
            p.recargos,
            p.status
        FROM Pagos p
        JOIN Cargos c ON c.id = p.cargo_id
        WHERE p.estudiante_id = ?
        AND p.ciclo_id = ?
        AND p.status = 'Pagado'
        ORDER BY p.fecha_pago DESC
    """, (alumno_id, ciclo_activo["id"]))

    seleccionados = {}

    for pago_id, concepto, fecha_pago, monto_pagado, recargos, status in pagos:

        if status == "Pagado":
            tag = "pagado"
        elif status == "Parcial":
            tag = "siguiente"
        else:
            tag = "nopagado"

        monto_pagado += recargos

        tabla.insert(
            "",
            "end",
            iid=str(pago_id),
            values=(
                "☐",
                concepto,
                fecha_pago or "",
                f"${monto_pagado:,.2f}",
                status
            ),
            tags=(tag,)
        )
        seleccionados[str(pago_id)] = False

    
    # ===============================
    # CLICK PARA SELECCIONAR
    # ===============================
    def toggle(event):
        region = tabla.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tabla.identify_column(event.x)
        if col != "#1":
            return

        item = tabla.identify_row(event.y)
        if not item:
            return

        seleccionados[item] = not seleccionados[item]
        tabla.set(item, "sel", "☑" if seleccionados[item] else "☐")

    tabla.bind("<Button-1>", toggle)

    # ===============================
    # BOTONES
    # ===============================
    acciones = tk.Frame(body, bg="white")
    acciones.pack(fill="x", pady=15)

    def salir():
        from caja.recibos import mostrar_recibos
        mostrar_recibos(parent, ciclo_activo, usuario_id)

    def continuar():
        pagos_ids = [int(pid) for pid, v in seleccionados.items() if v]

        if not pagos_ids:
            messagebox.showwarning(
                "Aviso",
                "Debe seleccionar al menos un pago."
            )
            return
        imprimir_ticket_pago(pagos_ids, usuario_id)
        #previsualizar_ticket(parent, pagos_ids, usuario_id)
        #return
    

    
    ttk.Button(acciones, text="Continuar", command=continuar).pack(side="right")
    ttk.Button(acciones, text="Salir", command=salir).pack(side="right", padx=6)

