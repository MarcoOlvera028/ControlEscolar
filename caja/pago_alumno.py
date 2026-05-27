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

def calcular_recargo(fecha_inicio_recargo, recargo_diario, recargo_hasta, status, tipo_cargo):
    if tipo_cargo == 'Colegiatura':
        if recargo_diario <= 0:
            return 0.0
        

        corte = datetime.strptime(fecha_inicio_recargo, "%Y-%m-%d").date()
        hoy = date.today()

        if corte > hoy:
            return 0.0
        # Antes del corte no hay recargo
        if hoy <= corte:
            return 0.0

        # Desde dónde contar
        if recargo_hasta:
            inicio = datetime.strptime(recargo_hasta, "%Y-%m-%d").date()
            fecha_limite = corte + timedelta(days=10)
            if hoy < fecha_limite:
                hoy = date.today()
            else:
                hoy = fecha_limite
        else:
            inicio = corte

        if hoy <= inicio:
            return 0.0
        
        if status in ("Pagado"):
            return 0.0
        
        if status in ("Condonado", "Descontado"):
            return 0.0

        # SOLO días nuevos, máximo 10 en total
        dias_nuevos = min((hoy - inicio).days, 10)
            

        return round(dias_nuevos * recargo_diario, 2)
    else:
        if recargo_diario <= 0:
            return 0.0

        corte = datetime.strptime(fecha_inicio_recargo, "%Y-%m-%d").date()
        hoy = date.today()

        if corte > hoy:
            return 0.0
        
        if hoy <= corte:
            return 0.0
        
        if status in ("Pagado", "Condonado"):
            return 0.0
        
        if recargo_hasta:
            return 0.0

        return recargo_diario

def calcular_recargo_pagado(fecha_inicio_recargo, recargo_diario, recargo_hasta, status, tipo_cargo):
    if tipo_cargo == 'Colegiatura':
        if status in ("Pagado", "Condonado", "Descontado"):
            inicio = datetime.strptime(fecha_inicio_recargo, "%Y-%m-%d").date()
            fin = datetime.strptime(recargo_hasta, "%Y-%m-%d").date()

            dias_nuevos = min((fin - inicio).days, 10)
            
            return round(dias_nuevos * recargo_diario, 2)
        else:
            if recargo_diario <= 0:
                return 0.0
            

            corte = datetime.strptime(fecha_inicio_recargo, "%Y-%m-%d").date()
            hoy = date.today()

            if corte > hoy:
                return 0.0
            # Antes del corte no hay recargo
            if hoy <= corte:
                return 0.0

            # Desde dónde contar
            if recargo_hasta:
                inicio = datetime.strptime(recargo_hasta, "%Y-%m-%d").date()
                fecha_limite = corte + timedelta(days=10)
                if hoy < fecha_limite:
                    hoy = date.today()
                else:
                    hoy = fecha_limite
            else:
                inicio = corte

            if hoy <= inicio:
                return 0.0
            
            if status in ("Pagado"):
                return 0.0
            
            if status in ("Condonado", "Descontado"):
                return 0.0

            # SOLO días nuevos, máximo 10 en total
            dias_nuevos = min((hoy - inicio).days, 10)
                

            return round(dias_nuevos * recargo_diario, 2)
    else:
        return recargo_diario

def calcular_recargo2(fecha_inicio_recargo, recargo_diario, recargo_hasta, status, tipo_cargo):
    if tipo_cargo == 'Colegiatura':
        if recargo_diario <= 0:
            return 0.0
        

        corte = datetime.strptime(fecha_inicio_recargo, "%Y-%m-%d").date()
        hoy = date.today()

        if corte > hoy:
            return 0.0
        # Antes del corte no hay recargo
        if hoy <= corte:
            return 0.0

        # Desde dónde contar
        if recargo_hasta:
            inicio = datetime.strptime(recargo_hasta, "%Y-%m-%d").date()
            fecha_limite = corte + timedelta(days=10)
            if hoy < fecha_limite:
                hoy = date.today()
            else:
                hoy = fecha_limite
        else:
            inicio = corte

        if hoy <= inicio:
            return 0.0

        # SOLO días nuevos, máximo 10 en total
        dias_nuevos = min((hoy - inicio).days, 10)
            

        return round(dias_nuevos * recargo_diario, 2)
    else:
        if recargo_diario <= 0:
            return 0.0

        corte = datetime.strptime(fecha_inicio_recargo, "%Y-%m-%d").date()
        hoy = date.today()

        if corte > hoy:
            return 0.0
        
        if hoy <= corte:
            return 0.0
        
        if recargo_hasta:
            return 0.0

        return recargo_diario

       

# =====================================================
# VISTA PRINCIPAL – PAGOS POR ALUMNO
# =====================================================
def mostrar_pago_alumno(parent, alumno_id, ciclo_activo, usuario_id):
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
        text="Ventana de pagos",
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
    columnas = ("sel", "concepto", "tipo", "fecha", "monto_total", "abonado", "restante", "estado")

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
    tabla.heading("tipo", text="Tipo")
    tabla.heading("fecha", text="Fecha")
    tabla.heading("monto_total", text="Monto total")
    tabla.heading("abonado", text="Abonado")
    tabla.heading("restante", text="Restante")
    tabla.heading("estado", text="Estado")


    
    tabla.column("sel", width=40, anchor="center", stretch=False)
    tabla.column("concepto", width=220)
    tabla.column("tipo", width=120, anchor="center")
    tabla.column("fecha", width=120, anchor="center")
    tabla.column("monto_total", width=120, anchor="e")
    tabla.column("abonado", width=120, anchor="e")
    tabla.column("restante", width=120, anchor="e")
    tabla.column("estado", width=160, anchor="center")

    # Colores
    tabla.tag_configure("pagado", foreground="#0D47A1")
    tabla.tag_configure("siguiente", foreground="#64B5F6")
    tabla.tag_configure("nopagado", foreground="#D32F2F")

    # ===============================
    # CARGOS Y PAGOS
    # ===============================
    cargos = obtener_todos("""
        SELECT
            c.id,
            c.concepto,
            c.tipo,
            c.fecha_inicio,
            c.fecha_inicio_recargos,
            IFNULL(p.monto, c.monto) AS monto,
            c.recargo_diario,
            c.tipo,
            IFNULL(p.monto_pagado, 0),
            IFNULL(p.condonacion, 0),
            IFNULL(p.descuento, 0),
            IFNULL(p.recargos, NULL),
            IFNULL(p.recargo_hasta, NULL),
            IFNULL(p.status, 'No pagado'),
            IFNULL(p.tipo_pago, '')
        FROM Cargos c
        LEFT JOIN Pagos p
            ON p.cargo_id = c.id
        AND p.estudiante_id = ?
        AND p.ciclo_id = ?
        WHERE c.ciclo_id = ?
        AND c.activo = 1
        ORDER BY c.orden;
    """, (alumno_id, ciclo_activo["id"], ciclo_activo["id"]))

    # diccionario: { cargo_id: tipo_pago }
    seleccionados = {}
    siguiente_asignado = False

    for c in cargos:
        (
            cargo_id,
            concepto,
            tipo,
            fecha,
            fecha_inicio_recargo,
            monto,
            recargo_diario,
            tipo_cargo,
            monto_pagado,
            condonacion,
            descuento,
            recargo_bd,
            recargo_hasta,
            status,
            tipo_pago
        ) = c

        if recargo_bd is None:
            recargo_bd = 0.0

        recargo_calc = calcular_recargo(fecha_inicio_recargo=fecha_inicio_recargo, recargo_diario=recargo_diario, recargo_hasta=recargo_hasta, status=status, tipo_cargo=tipo_cargo)
        

        pagado = monto_pagado + condonacion + descuento + recargo_bd
        
        recargo_total = recargo_calc

        monto_total = monto + recargo_calc
        
        restante = max((monto + recargo_total) - pagado, 0)

        if recargo_bd == 0 and recargo_hasta is not None:
            recargo_pagado_hasta = calcular_recargo_pagado(fecha_inicio_recargo=fecha_inicio_recargo, recargo_diario=recargo_diario, recargo_hasta=recargo_hasta, status=status, tipo_cargo=tipo_cargo)
            monto_total = monto + recargo_pagado_hasta
        
        if status in ("Pagado", "Condonado", "Descontado") and recargo_calc == 0:
            recargo_pagado_hasta = calcular_recargo2(fecha_inicio_recargo=fecha_inicio_recargo, recargo_diario=recargo_diario, recargo_hasta=recargo_hasta, status=status, tipo_cargo=tipo_cargo)
            monto_total = monto + recargo_pagado_hasta + recargo_bd

        if recargo_calc == 0 and status in ("Parcial"):
            monto_total = monto + recargo_bd
            restante = max((monto + recargo_total + recargo_bd) - pagado, 0)
        
        if recargo_calc != 0 and status in ("Parcial"):
            monto_total += recargo_bd
            restante = max((monto + recargo_total + recargo_bd) - pagado, 0)
        
        if status in ("Pagado", "Condonado", "Descontado") and recargo_calc == 0 and monto_total > pagado:
            monto_total = monto + recargo_bd

        # =========================
        # ESTADO
        # =========================
        if restante <= 0:
            if status == "Condonado":
                estado = "Condonado"

            elif status == "Pagado":
                if tipo_pago:
                    estado = f"Pagado ({tipo_pago})"
                else:
                    estado = "Pagado"

            else:
                estado = status  # fallback por si hay otro valor

            tag = "pagado"

        elif pagado > 0:
            if not siguiente_asignado:
                estado = "Siguiente"
                tag = "siguiente"
                siguiente_asignado = True
            else:
                estado = "Pendiente"
                tag = "nopagado"

        else:
            if not siguiente_asignado:
                estado = "Siguiente"
                tag = "siguiente"
                siguiente_asignado = True
            else:
                estado = "No pagado"
                tag = "nopagado"


        tabla.insert(
            "",
            "end",
            iid=str(cargo_id),
            values=(
                "☐",
                concepto,
                tipo,
                fecha,
                f"${monto_total:,.2f}",
                f"${pagado:,.2f}",
                f"${restante:,.2f}",
                estado
            ),
            tags=(tag,)
        )
        seleccionados[str(cargo_id)] = False
    # ===============================
    # CLICK PARA SELECCIONAR
    # ===============================
    def toggle(event):
        region = tabla.identify("region", event.x, event.y)
        if region != "cell":
            return

        col = tabla.identify_column(event.x)
        if col != "#1":   # columna "sel" (primera)
            return

        item = tabla.identify_row(event.y)
        if not item:
            return

        seleccionado = seleccionados.get(item, False)
        seleccionado = not seleccionado
        seleccionados[item] = seleccionado

        tabla.set(item, "sel", "☑" if seleccionado else "☐")

    tabla.bind("<Button-1>", toggle)

    # ===============================
    # BOTONES
    # ===============================
    acciones = tk.Frame(body, bg="white")
    acciones.pack(fill="x", pady=15)

    def salir():
        from caja.caja_alumnos import mostrar_alumnos_caja
        mostrar_alumnos_caja(parent, ciclo_activo, usuario_id)

    def continuar():
        cargos_sel = [
            int(i)          # ← i es el iid = cargo_id
            for i, v in seleccionados.items() if v
        ]

        if not cargos_sel:
            messagebox.showwarning(
                "Aviso",
                "Al menos un monto debe de ser seleccionado."
            )
            return

        ventana_registro_pago(parent, cargos_sel, ciclo_activo, usuario_id)

    def reiniciar():
        cargos_sel = [
            int(i)          # iid = cargo_id
            for i, v in seleccionados.items() if v
        ]

        if not cargos_sel:
            messagebox.showwarning(
                "Aviso",
                "Al menos un cargo debe de ser seleccionado."
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar reinicio",
            "Esto eliminará TODOS los pagos, descuentos y condonaciones\n"
            "de los cargos seleccionados.\n\n"
            "¿Desea continuar?"
        )

        if not confirmar:
            return

        conn = obtener_conexion()
        cur = conn.cursor()

        for cargo_id in cargos_sel:
            cur.execute("""
                UPDATE Pagos
                SET
                    monto_pagado = 0,
                    descuento = 0,
                    condonacion = 0,
                    fecha_pago = NULL,
                    tipo_pago = NULL,
                    status = 'Pendiente',
                    usuario_id = NULL,
                    recargo_hasta = NULL,
                    recargos = 0
                WHERE estudiante_id = ?
                AND ciclo_id = ?
                AND cargo_id = ?
            """, (
                alumno_id,
                ciclo_activo["id"],
                cargo_id
            ))

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Reinicio completado",
            "Los pagos seleccionados fueron reiniciados correctamente."
        )

        # Refrescar la vista
        mostrar_pago_alumno(parent, alumno_id, ciclo_activo, usuario_id)

    ttk.Button(acciones, text="Continuar", command=continuar).pack(side="right")
    ttk.Button(acciones, text="Salir", command=salir).pack(side="right", padx=6)
    ttk.Button(acciones, text="Cancelar", command=reiniciar).pack(side="left", padx=6)














    # ===============================
    # VENTANA REGISTRO DE PAGO
    # ===============================
    def ventana_registro_pago(parent, cargos_sel, ciclo_activo, usuario_id):
        from datetime import datetime
        import tkinter as tk
        from tkinter import ttk, messagebox

        # ===============================
        # VENTANA
        # ===============================
        top = tk.Toplevel(parent)
        top.title("Registro de pago")
        top.resizable(False, False)

        ancho, alto = 900, 450
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (ancho // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (alto // 2)
        top.geometry(f"{ancho}x{alto}+{x}+{y}")

        top.transient(parent)
        top.grab_set()

        # ===============================
        # CONTENEDOR PRINCIPAL
        # ===============================
        cont = tk.Frame(top, padx=20, pady=15)
        cont.pack(fill="both", expand=True)

        # ===============================
        # HEADER
        # ===============================
        fecha = datetime.now().strftime("%d/%m/%Y")
        conn = obtener_conexion()
        cur = conn.cursor()

        base_datos = {}

        total_inicial = 0.0
        for cargo_id in cargos_sel:
            cur.execute(
                "SELECT monto FROM Cargos WHERE id=?",
                (cargo_id,)
            )
            row = cur.fetchone()
            if row:
                total_inicial += row[0]

        conn.close()

        header = tk.Frame(cont)
        header.grid(row=0, column=0, sticky="we")

        tk.Label(
            header,
            text=f"Fecha: {fecha}",
            font=("Segoe UI", 11)
        ).grid(row=0, column=0, sticky="w")

        lbl_total = tk.Label(
            header,
            text=f"TOTAL: ${total_inicial:,.2f}",
            font=("Segoe UI", 16, "bold"),
            fg="#0D47A1"
        )
        lbl_total.grid(row=0, column=1, sticky="e")

        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=1)

        ttk.Separator(cont, orient="horizontal")\
            .grid(row=1, column=0, sticky="we", pady=10)

        # ===============================
        # TIPO DE PAGO
        # ===============================
        tipo_frame = tk.Frame(cont)
        tipo_frame.grid(row=2, column=0, sticky="w", pady=(0, 10))

        tk.Label(
            tipo_frame,
            text="Tipo de pago:",
            font=("Segoe UI", 11)
        ).pack(side="left", padx=(0, 8))

        # 🔹 VARIABLE (ESTA FALTABA)
        tipo_pago_var = tk.StringVar(value="Pago total")
        extemporaneo_var = tk.IntVar(value=0)

        cb_tipo = ttk.Combobox(
            tipo_frame,
            textvariable=tipo_pago_var,
            state="readonly",
            values=[
                "Pago total",
                "Pago parcial",
                "Condonación de cargos",
                "Descuento extra"
            ],
            width=24
        )
        cb_tipo.pack(side="left")

        # ===============================
        # PANEL DESCUENTO (HORIZONTAL)
        # ===============================
        panel_descuento = tk.Frame(tipo_frame, bg="#f5f5f5", padx=10, pady=6)

        tk.Label(
            panel_descuento,
            text="Monto:",
            bg="#f5f5f5"
        ).pack(side="left", padx=(0, 5))

        entry_monto_desc = tk.Entry(panel_descuento, width=12)
        entry_monto_desc.pack(side="left", padx=5)

        btn_aplicar = ttk.Button(panel_descuento, text="Aplicar")
        btn_aplicar.pack(side="left")

        panel_descuento.pack_forget()


        # ===============================
        # TABLA
        # ===============================
        columnas = (
            "ciclo",
            "aplica",
            "concepto",
            "monto_total",
            "pagado",
            "pago_parcial",
            "condonacion",
            "descuento",
            "restante",
            "total"
        )

        tabla_frame = tk.Frame(cont)
        tabla_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=10)

        tabla = ttk.Treeview(
            tabla_frame,
            columns=columnas,
            show="headings",
            height=8
        )

        vsb = ttk.Scrollbar(tabla_frame, orient="vertical", command=tabla.yview)
        hsb = ttk.Scrollbar(tabla_frame, orient="horizontal", command=tabla.xview)

        tabla.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tabla.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        tabla_frame.rowconfigure(0, weight=1)
        tabla_frame.columnconfigure(0, weight=1)

        encabezados = {
            "ciclo": "Ciclo",
            "aplica": "Aplica",
            "concepto": "Concepto",
            "monto_total": "Monto total",
            "pagado": "Abonado",
            "pago_parcial": "Pago parcial",
            "condonacion": "Condonación",
            "descuento": "Descuento",
            "restante": "Restante",
            "total": "Total Operación"
        }

        for c in columnas:
            if c == "sel":
                tabla.heading("sel", text="✓")
                tabla.column("sel", width=40, anchor="center")
                continue

            tabla.heading(c, text=encabezados[c])
            tabla.column(c, anchor="center", width=120)

        tabla.column("concepto", width=200)

        # ===============================
        # LLENAR TABLA
        # ===============================
        conn = obtener_conexion()
        cur = conn.cursor()

        for cargo_id in cargos_sel:
            cur.execute("""
                SELECT c.concepto, c.fecha_inicio, c.tipo, c.fecha_inicio_recargos,
                    IFNULL(p.monto, c.monto),
                    IFNULL(p.monto_pagado, 0),
                    IFNULL(p.descuento, 0),
                    IFNULL(p.condonacion, 0),
                    IFNULL(p.recargos, 0),
                    IFNULL(c.recargo_diario, 0),
                    IFNULL(p.recargo_hasta, NULL),
                    IFNULL(p.status, 'No pagado')                    
                FROM Cargos c
                LEFT JOIN Pagos p
                    ON p.cargo_id = c.id
                AND p.estudiante_id = ?
                AND p.ciclo_id = ?
                WHERE c.id = ?
            """, (alumno_id, ciclo_activo["id"], cargo_id))

            row = cur.fetchone()
            if not row:
                continue
            
            
            
            concepto, fecha_aplica, tipo_cargo, fecha_inicio_recargo, monto_total, pagado_bd, descuento_bd, condonacion_bd, recargos_bd, recargo_diario, recargo_hasta, status = row

            recargo_calc2 = calcular_recargo(fecha_inicio_recargo=fecha_inicio_recargo, recargo_diario=recargo_diario, recargo_hasta=recargo_hasta, status=status, tipo_cargo=tipo_cargo)
            
            pagado_real = pagado_bd + descuento_bd + condonacion_bd + recargos_bd
            
            restante = monto_total + recargo_calc2 - pagado_real

            monto_total_real = monto_total + recargo_calc2

            if recargo_calc2 == 0 and status in ("Parcial"):
                monto_total_real = monto_total + recargos_bd

            if recargos_bd is None:
                recargos_bd = 0.0

            if recargo_calc2 != 0 and status in ("Parcial"):
                monto_total_real += recargos_bd
            
            
            tabla.insert(
                "",
                "end",
                iid=str(cargo_id),
                values=(
                    ciclo_activo["nombre"],
                    fecha_aplica,
                    concepto,
                    f"{monto_total_real:.2f}",
                    f"{pagado_real:.2f}",
                    "0.00",
                    "0.00",
                    "0.00",
                    f"{restante:.2f}",
                    "0.00"
                )
            )

            base_datos[cargo_id] = {
                "monto_total": monto_total,
                "recargos_bd": recargos_bd,
                "recargo_nuevo": recargo_calc2,
                "recargo_diario": recargo_diario,
                "fecha_inicio": fecha_aplica,
                "pagado_bd": pagado_bd,
                "descuento_bd": descuento_bd,
                "condonacion_bd": condonacion_bd,
                "recargo_hasta": recargo_hasta,
                "status": status,
                "tipo_cargo": tipo_cargo
            }
            

        conn.close()

        # ===============================
        # ¿HAY INSCRIPCIÓN?
        # ===============================
        hay_inscripcion = any(
            base["tipo_cargo"] == "Inscripción"
            for base in base_datos.values()
        )

        # ===============================
        # CHECKBOX EXTEMPORÁNEO
        # ===============================
        if hay_inscripcion:
            chk_extemporaneo = tk.Checkbutton(
                tipo_frame,
                text="Extemporáneo",
                variable=extemporaneo_var,
                font=("Segoe UI", 10),
                command=lambda: aplicar_extemporaneo()
            )
            chk_extemporaneo.pack(side="right", padx=(10, 0))

        def recalcular_total_general():
            total = 0.0
            for item in tabla.get_children():
                total += float(tabla.item(item, "values")[9])
            lbl_total.config(text=f"TOTAL OPERACIÓN: ${total:,.2f}")

        recalcular_total_general()

        # ===============================
        # BOTONES
        # =============================== 

        def aplicar_extemporaneo():
            es_extemporaneo = extemporaneo_var.get() == 1

            for item in tabla.get_children():
                cargo_id = int(item)
                base = base_datos[cargo_id]

                v = list(tabla.item(item, "values"))

                if es_extemporaneo:
                    # 🔹 FORZAR SIN RECARGO
                    base["recargo_nuevo"] = 0.00
                    base["pago_recargo"] = 0.00
                else:
                    # 🔹 RECALCULAR NORMAL
                    recargo_real = calcular_recargo(
                        fecha_inicio_recargo=base["fecha_inicio"],
                        recargo_diario=base["recargo_diario"],
                        recargo_hasta=base["recargo_hasta"],
                        status=base["status"],
                        tipo_cargo=base["tipo_cargo"]
                    )
                    base["recargo_nuevo"] = recargo_real

                # 🔹 Recalcular restante y total
                monto_total = base["monto_total"]
                pagado_bd = base["pagado_bd"]
                descuento_bd = base["descuento_bd"]
                condonacion_bd = base["condonacion_bd"]

                restante = max(
                    monto_total + base["recargo_nuevo"]
                    - pagado_bd - descuento_bd - condonacion_bd,
                    0.0
                )

                v[3] = f"{restante:.2f}"
                v[5] = f"{restante:.2f}"
                v[8] = f"{restante:.2f}"  # restante
                v[9] = f"{restante:.2f}"            # total hoy (se recalcula luego)

                tabla.item(item, values=v)

            recalcular_total_general()
        

        def aplicar(event=None):
            try:
                monto_input = float(entry_monto_desc.get())
            except ValueError:
                messagebox.showerror("Error", "Ingrese un monto válido")
                return

            if monto_input <= 0:
                messagebox.showerror("Error", "El monto debe ser mayor a 0")
                return

            tipo = tipo_pago_var.get()

            for item in tabla.get_children():
                cargo_id = int(item)
                base = base_datos[cargo_id]

                monto_total = base["monto_total"]
                pagado_bd = base["pagado_bd"]
                descuento_bd = base["descuento_bd"]
                restante = max(monto_total + base["recargo_nuevo"] - pagado_bd - descuento_bd - condonacion_bd, 0.0)
           

                pago_parcial = 0.00
                condonacion = 0.00
                descuento = 0.00
                total_hoy = 0.00
                nuevo_restante = restante
                recargo_pendiente = base["recargo_nuevo"]
                base.setdefault("dias_pagados", 0)

                if tipo == "Pago parcial":
                    pago = monto_input

                    # 1. Primero se paga recargo
                    pago_a_recargo = min(pago, recargo_pendiente)
                    pago -= pago_a_recargo
                    base["pago_recargo"] = pago_a_recargo
                    if recargo_diario > 0:
                        base["dias_pagados"] = int(pago_a_recargo / recargo_diario)
                    else:
                        base["dias_pagados"] = 0

                    # 2. Luego se paga al monto base
                    pago_a_monto = min(pago, restante)
                
                

                    pago_parcial = pago_a_monto + pago_a_recargo
                    total_hoy = pago_a_recargo + pago_a_monto
                    nuevo_restante = restante - pago_a_monto - pago_a_recargo


                elif tipo == "Condonación de cargos":
                    pago = monto_input
                    pago_a_recargo = min(pago, recargo_pendiente)
                    
                    condonacion = min(monto_input, restante) 
                    total_hoy = 0.00
                    nuevo_restante = restante - condonacion

                elif tipo == "Descuento extra":
                    pago = monto_input
                    pago_a_recargo = min(pago, recargo_pendiente)
                    
                    descuento = min(monto_input, restante)
                    total_hoy = 0.00
                    nuevo_restante = restante - descuento 

                
                v = list(tabla.item(item, "values"))
                v[5] = f"{pago_parcial:.2f}"
                v[6] = f"{condonacion:.2f}"
                v[7] = f"{descuento:.2f}"
                v[8] = f"{nuevo_restante:.2f}"
                v[9] = f"{total_hoy:.2f}"

                tabla.item(item, values=v)

            recalcular_total_general()


        def on_tipo_pago(event=None):
            entry_monto_desc.delete(0, "end")
            tipo = tipo_pago_var.get()

            for item in tabla.get_children():
                cargo_id = int(item)
                base = base_datos[cargo_id]

                monto_total = base["monto_total"]
                pagado_bd = base["pagado_bd"]
                descuento_bd = base["descuento_bd"]
                condonacion_bd = base["condonacion_bd"]
                recargos_bd = base["recargos_bd"]

                
                recargo_pendiente = base["recargo_nuevo"]
                restante = max((monto_total + recargo_pendiente) - pagado_bd - descuento_bd - condonacion_bd, 0)

                if recargo_pendiente == 0 and status in ("Parcial"):
                    restante += recargos_bd
                
                if recargo_pendiente != 0 and status in ("Parcial"):
                    restante += recargos_bd

                v = list(tabla.item(item, "values"))

                # 🔹 Reset SIEMPRE
                v[6] = "0.00"  # condonacion
                v[7] = "0.00"  # descuento
                v[8] = "0.00"  # restante
                v[9] = f"{restante:.2f}"  # restante

                # 🔹 SOLO pago total afecta automáticamente
                if tipo == "Pago total":
                    pago = restante

                    recargo_pendiente = base["recargo_nuevo"]
                    recargo_diario = base["recargo_diario"]

                    # 1. Pagar recargo completo
                    pago_a_recargo = min(pago, recargo_pendiente)
                    pago -= pago_a_recargo

                    base["pago_recargo"] = pago_a_recargo
                    if recargo_diario > 0:
                        base["dias_pagados"] = int(pago_a_recargo / recargo_diario)
                    else:
                        base["dias_pagados"] = 0

                    # 2. Resto al monto
                    pago_a_monto = pago


                    # 3. Actualizar tabla
                    v[5] = f"{(pago_a_recargo + pago_a_monto - recargos_bd):.2f}" 
                    v[8] = f"{(pago_a_recargo + pago_a_monto - recargos_bd):.2f}"
                    v[9] = f"{(pago_a_recargo + pago_a_monto - recargos_bd):.2f}"
                else:
                    v[5] = "0.00"
                    v[9] = "0.00"

                tabla.item(item, values=v)

            recalcular_total_general()
            

            # Mostrar u ocultar panel
            if tipo in ("Pago parcial", "Condonación de cargos", "Descuento extra"):
                panel_descuento.pack(side="left", padx=10)
            else:
                panel_descuento.pack_forget()

        
        cb_tipo.bind("<<ComboboxSelected>>", on_tipo_pago)
        btn_aplicar.config(command=aplicar)
        entry_monto_desc.bind("<Return>", aplicar)

        on_tipo_pago()

        acciones = tk.Frame(cont)
        acciones.grid(row=4, column=0, columnspan=2, sticky="e", pady=10)


        def obtener_cargos_calculados():
            cargos = []

            for item in tabla.get_children():
                cargo_id = int(item)
                v = tabla.item(item, "values")

                cargos.append({
                    "cargo_id": cargo_id,
                    "monto_total": float(v[3]),
                    "pagado_bd": float(v[4]),
                    "pago_parcial": float(v[5]),
                    "condonacion": float(v[6]),
                    "descuento": float(v[7]),
                    "restante": float(v[8]),
                    "total_hoy": float(v[9]),

                    "pago_recargo": base_datos[cargo_id].get("pago_recargo", 0.0),
                    "dias_pagados": base_datos[cargo_id].get("dias_pagados", 0),
                    "recargo_diario": base_datos[cargo_id]["recargo_diario"],
                    "fecha_inicio": base_datos[cargo_id]["fecha_inicio"]
                })
 

            return cargos

        ttk.Button(acciones, text="Continuar", command=lambda: ventana_confirmar_pago(
                parent=top,
                total_pagar=sum(c["total_hoy"] for c in obtener_cargos_calculados()),
                alumno_id=alumno_id,
                ciclo_activo=ciclo_activo,
                cargos_finales=obtener_cargos_calculados(),
                usuario_id=usuario_id,
                on_pago_registrado=lambda: mostrar_pago_alumno(parent, alumno_id, ciclo_activo, usuario_id)
            )
        ).pack(side="right", padx=6)

        ttk.Button(acciones, text="Regresar", command=top.destroy).pack(side="right", padx=6)

        

        cont.columnconfigure(0, weight=1)



    # ===============================
    # VENTANA CONFIRMAR PAGO
    # ===============================
    def ventana_confirmar_pago(parent, total_pagar, alumno_id, ciclo_activo, cargos_finales, usuario_id, on_pago_registrado):
        from datetime import date
        from db.conexion import obtener_conexion
        import tkinter as tk
        from tkinter import ttk

        # ===============================
        # VENTANA
        # ===============================
        top = tk.Toplevel(parent)
        top.title("Confirmar pago")
        top.resizable(False, False)

        ancho, alto = 430, 360
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (ancho // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (alto // 2)
        top.geometry(f"{ancho}x{alto}+{x}+{y}")

        top.transient(parent)
        top.grab_set()

        cont = tk.Frame(top, padx=20, pady=20)
        cont.pack(fill="both", expand=True)

        # ===============================
        # HEADER
        # ===============================
        fecha = date.today().strftime("%d/%m/%Y")

        tk.Label(cont, text=fecha, font=("Segoe UI", 11)).pack()
        tk.Label(cont, text="TOTAL A PAGAR", font=("Segoe UI", 11, "bold"), pady=6).pack()
        tk.Label(
            cont,
            text=f"${total_pagar:,.2f}",
            font=("Segoe UI", 18, "bold"),
            fg="#0D47A1"
        ).pack()

        ttk.Separator(cont, orient="horizontal").pack(fill="x", pady=15)

        # ===============================
        # FORMA DE PAGO
        # ===============================
        form = tk.Frame(cont)
        form.pack(fill="x", pady=10)

        tk.Label(form, text="Método:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        tk.Label(
            form,
            text="Pago en una sola exhibición",
            font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=1, sticky="w")

        tk.Label(form, text="Forma:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w")
        forma_var = tk.StringVar(value="Efectivo")

        ttk.Combobox(
            form,
            textvariable=forma_var,
            state="readonly",
            values=["Efectivo", "Transferencia"],
            width=25
        ).grid(row=1, column=1, pady=6)

        # ===============================
        # BOTONES
        # ===============================
        imprimir_var = tk.BooleanVar(value=False)
        chk_imprimir = ttk.Checkbutton(
            cont,
            text="Imprimir ticket",
            variable=imprimir_var
        )
        chk_imprimir.pack()

        acciones = tk.Frame(cont)
        acciones.pack(fill="x", pady=20)

        def registrar_pago():
            conn = obtener_conexion()
            cur = conn.cursor()
            fecha_pago = date.today().isoformat()
            pagos_ids = []

            for c in cargos_finales:
                cargo_id = c["cargo_id"]
                monto_total = c["monto_total"]

                pago_parcial_ui = c["pago_parcial"]
                condonacion_ui = c["condonacion"]
                descuento_ui = c["descuento"]
                recargo_pagado = c["pago_recargo"]

                fecha_inicio_cargo = c["fecha_inicio"]
                dias_pagados = c["dias_pagados"]

                # ===============================
                # DATOS ACTUALES BD
                # ===============================
                cur.execute("""
                    SELECT monto_pagado, condonacion, descuento, recargo_hasta, recargos
                    FROM Pagos
                    WHERE estudiante_id=? AND ciclo_id=? AND cargo_id=?
                """, (alumno_id, ciclo_activo["id"], cargo_id))

                row = cur.fetchone()
                if row:
                    monto_pagado_bd, condonacion_bd, descuento_bd, recargo_hasta_bd, recargos_bd = row
                else:
                    monto_pagado_bd = 0.0
                    condonacion_bd = 0.0
                    descuento_bd = 0.0
                    recargos_bd = 0.0
                    recargo_hasta_bd = None
                
                cur.execute("""
                    SELECT monto
                        FROM Cargos
                        WHERE id=?
                """, (cargo_id,))
                row2 = cur.fetchone()
                if row2:
                    monto_total2 = row2[0]

                # ===============================
                # ACUMULAR VALORES
                # ===============================
                recargos_pagados = recargos_bd + recargo_pagado

                
                if pago_parcial_ui <= 0:
                    monto_pagado_nuevo = monto_pagado_bd
                else:
                    monto_pagado_nuevo = monto_pagado_bd + pago_parcial_ui - recargo_pagado

                descuento_nuevo = descuento_bd + descuento_ui
                condonacion_nueva = condonacion_bd + condonacion_ui


                if condonacion_ui:
                    if condonacion_nueva <= monto_total and recargos_bd == 0:
                        recargos_pagados = recargos_bd
                        dias_pagados = 0
                        recargo_hasta = None
                    elif condonacion_nueva <= monto_total and recargos_bd != 0:
                        recargos_pagados = recargos_bd
                        dias_pagados = 0

                if descuento_ui:
                    if descuento_nuevo <= monto_total and recargos_bd == 0:
                        recargos_pagados = recargos_bd
                        dias_pagados = 0
                        recargo_hasta = None
                    elif descuento_nuevo <= monto_total and recargos_bd != 0:
                        recargos_pagados = recargos_bd
                        dias_pagados = 0

                # ===============================
                # CALCULAR DÍAS DE RECARGO PAGADOS
                # ===============================


                fi = datetime.strptime(fecha_inicio_cargo, "%Y-%m-%d").date()
                corte = fi.replace(day=15)

                if dias_pagados > 0:
                    base_fecha = (
                        datetime.strptime(recargo_hasta_bd, "%Y-%m-%d").date()
                        if recargo_hasta_bd
                        else corte
                    )
                    recargo_hasta = base_fecha + timedelta(days=dias_pagados)
                else:
                    recargo_hasta = recargo_hasta_bd

                pagado_total = (monto_pagado_nuevo + condonacion_nueva + descuento_nuevo + recargos_pagados)
                condonacion_mas_descuento = condonacion_nueva + descuento_nuevo
                
                # ===============================
                # STATUS
                # ===============================
                if pagado_total >= monto_total:
                    status = "Pagado"
                elif pagado_total < monto_total:
                    status = "Parcial"
                    
                if condonacion_nueva >= monto_total:
                    status = "Condonado"
                    recargos_pagados = recargos_bd

                if descuento_nuevo >= monto_total:
                    status = "Descontado"
                    recargos_pagados = recargos_bd        
                
                if condonacion_mas_descuento >= monto_total:
                    status = "Condonado"
                    recargos_pagados = recargos_bd

                # ===============================
                # INSERT / UPDATE
                # ===============================
                cur.execute("""
                    INSERT INTO Pagos (
                        estudiante_id,
                        ciclo_id,
                        cargo_id,
                        monto,
                        monto_pagado,
                        condonacion,
                        descuento,
                        fecha_pago,
                        tipo_pago,
                        status,
                        usuario_id,
                        recargos,
                        recargo_hasta
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(estudiante_id, ciclo_id, cargo_id)
                    DO UPDATE SET
                        monto_pagado = excluded.monto_pagado,
                        condonacion = excluded.condonacion,
                        descuento = excluded.descuento,
                        fecha_pago = excluded.fecha_pago,
                        tipo_pago = excluded.tipo_pago,
                        status = excluded.status,
                        usuario_id = excluded.usuario_id,
                        recargos = excluded.recargos,
                        recargo_hasta = excluded.recargo_hasta
                """, (
                    alumno_id,
                    ciclo_activo["id"],
                    cargo_id,
                    monto_total2,
                    monto_pagado_nuevo,
                    condonacion_nueva,
                    descuento_nuevo,
                    fecha_pago,
                    forma_var.get(),
                    status,
                    usuario_id,
                    recargos_pagados,
                    recargo_hasta
                ))


                # Obtener ID del pago recién registrado
                cur.execute("""
                    SELECT id
                    FROM Pagos
                    WHERE estudiante_id=? AND ciclo_id=? AND cargo_id=?
                """, (alumno_id, ciclo_activo["id"], cargo_id))

                pago_id = cur.fetchone()[0]
                pagos_ids.append(pago_id)

            conn.commit()
            conn.close()

            if imprimir_var.get() and pagos_ids:
                imprimir_ticket_pago(pagos_ids, usuario_id)
                #previsualizar_ticket(parent, pagos_ids, usuario_id)
                #return   # ⬅️ NO cierres aún la ventana

            top.destroy()
            on_pago_registrado()
            



        ttk.Button(acciones, text="Registrar pago", command=registrar_pago).pack(side="right")
        ttk.Button(acciones, text="Regresar", command=top.destroy).pack(side="right", padx=6)


