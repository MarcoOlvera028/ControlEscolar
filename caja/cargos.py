import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from db.conexion import obtener_todos, ejecutar_consulta
from control_escolar.datepicker import DatePicker


# =====================================================
# VISTA PRINCIPAL
# =====================================================
def mostrar_cargos(parent, ciclo_activo):
    for w in parent.winfo_children():
        w.destroy()

    contenedor = tk.Frame(parent, bg="white")
    contenedor.pack(fill="both", expand=True)

    header = tk.Frame(contenedor, bg="#d0e4f5", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text=f"Cargos – Ciclo {ciclo_activo['nombre']}",
        bg="#d0e4f5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)


    # ===== BOTONES =====
    toolbar = tk.Frame(contenedor, bg="white")
    toolbar.pack(fill="x", padx=20, pady=5)

    ttk.Button(
        toolbar,
        text="Agregar",
        command=lambda: ventana_cargo(contenedor, tree, ciclo_activo)
    ).pack(side="left", padx=5)

    ttk.Button(
        toolbar,
        text="Modificar",
        command=lambda: modificar_cargo(contenedor, tree, ciclo_activo)
    ).pack(side="left", padx=5)

    ttk.Button(
        toolbar,
        text="Borrar",
        command=lambda: borrar_cargo(tree)
    ).pack(side="left", padx=5)

    # ===== TABLA CON SCROLL =====
    tabla_frame = tk.Frame(contenedor, bg="white")
    tabla_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # Scroll horizontal
    scroll_x = ttk.Scrollbar(tabla_frame, orient="horizontal")
    scroll_x.pack(side="bottom", fill="x")

    # Scroll vertical (opcional pero recomendado)
    scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical")
    scroll_y.pack(side="right", fill="y")

    columnas = (
        "id", "concepto", "tipo", "fecha_inicio",
        "monto", "fecha_inicio_recargo",
        "recargo", "activo"
    )

    tree = ttk.Treeview(
        tabla_frame,
        columns=columnas,
        show="headings",
        height=12,
        xscrollcommand=scroll_x.set,
        yscrollcommand=scroll_y.set
    )

    tree.pack(fill="both", expand=True)

    scroll_x.config(command=tree.xview)
    scroll_y.config(command=tree.yview)

    tree.heading("id", text="ID")
    tree.heading("concepto", text="Concepto")
    tree.heading("tipo", text="Tipo")
    tree.heading("fecha_inicio", text="Inicio cobro")
    tree.heading("monto", text="Monto del concepto")
    tree.heading("fecha_inicio_recargo", text="Fecha límite de pago")
    tree.heading("recargo", text="Recargo")
    tree.heading("activo", text="Activo")

    tree.column("id", width=50, anchor="center")
    tree.column("concepto", width=220)
    tree.column("tipo", width=110)
    tree.column("fecha_inicio", width=110, anchor="center")
    tree.column("monto", width=90, anchor="center")
    tree.column("fecha_inicio_recargo", width=110, anchor="center")
    tree.column("recargo", width=70, anchor="center")
    tree.column("activo", width=70, anchor="center")

    tree.pack(fill="both", expand=True, padx=20, pady=10)

    tree.bind("<Double-1>", lambda e: modificar_cargo(contenedor, tree, ciclo_activo))

    cargar_cargos(tree, ciclo_activo["id"])


# =====================================================
def cargar_cargos(tree, ciclo_id):
    tree.delete(*tree.get_children())

    filas = obtener_todos(
        """
        SELECT
            id,
            concepto,
            tipo,
            fecha_inicio,
            monto,
            fecha_inicio_recargos,
            recargo_diario,
            CASE activo WHEN 1 THEN 'Sí' ELSE 'No' END
        FROM Cargos
        WHERE ciclo_id = ?
        ORDER BY orden ASC
        """,
        (ciclo_id,)
    )

    for f in filas:
        tree.insert("", "end", values=f)


# =====================================================
# VENTANA AGREGAR / MODIFICAR
# =====================================================
def ventana_cargo(parent, tree, ciclo_activo, datos=None):
    top = tk.Toplevel(parent)
    top.title("Cargo")
    top.geometry("350x350")
    top.transient(parent.winfo_toplevel())
    top.grab_set()
    top.resizable(False, False)

    centrar_ventana(top, parent)

    cont = tk.Frame(top, padx=20, pady=20)
    cont.pack(fill="both", expand=True)

    # ===== CAMPOS =====
    tk.Label(cont, text="Concepto:").grid(row=0, column=0, sticky="w", pady=6)
    entry_concepto = tk.Entry(cont, width=30)
    entry_concepto.grid(row=0, column=1, pady=6)

    def convertir_mayusculas(event=None):
        texto = entry_concepto.get()
        entry_concepto.delete(0, tk.END)
        entry_concepto.insert(0, texto.upper())

    entry_concepto.bind("<KeyRelease>", convertir_mayusculas)

    tk.Label(cont, text="Tipo:").grid(row=1, column=0, sticky="w", pady=6)
    tipo_cb = ttk.Combobox(
        cont,
        state="readonly",
        values=["Inscripción", "Colegiatura"]
    )
    tipo_cb.grid(row=1, column=1, pady=6)
    tipo_cb.current(0)

    if datos:
        # ===== INICIO DE COBRO =====
        tk.Label(cont, text="Inicio:").grid(row=2, column=0, sticky="w", pady=6)
        dp_inicio = DatePicker(cont)
        dp_inicio.grid(row=2, column=1, pady=6)

        # ===== INICIO DE COBRO RECARGO=====
        tk.Label(cont, text="Fecha límite del pago:").grid(row=4, column=0, sticky="w", pady=6)
        dp_inicio_recargo = DatePicker(cont)
        dp_inicio_recargo.grid(row=4, column=1, pady=6)
    else:
        # ===== INICIO DE COBRO =====
        tk.Label(cont, text="Inicio:").grid(row=2, column=0, sticky="w", pady=6)
        dp_inicio = DatePicker(cont, initial=date.today())
        dp_inicio.grid(row=2, column=1, pady=6)

        # ===== INICIO DE COBRO RECARGO=====
        tk.Label(cont, text="Fecha límite de pago:").grid(row=4, column=0, sticky="w", pady=6)
        dp_inicio_recargo = DatePicker(cont, initial=date.today())
        dp_inicio_recargo.grid(row=4, column=1, pady=6)

    # ===== MONTO =====
    tk.Label(cont, text="Monto del concepto:").grid(row=3, column=0, sticky="w", pady=6)
    entry_monto = tk.Entry(cont)
    entry_monto.grid(row=3, column=1, pady=6)

    # ===== RECARGO (DINÁMICO) =====
    lbl_recargo = tk.Label(cont)
    lbl_recargo.grid(row=5, column=0, sticky="w", pady=6)

    entry_recargo = tk.Entry(cont)
    entry_recargo.grid(row=5, column=1, pady=6)
    entry_recargo.insert(0, "0.00")

    def actualizar_tipo(event=None):
        if tipo_cb.get() == "Colegiatura":
            lbl_recargo.config(text="Recargo diario:")
        else:
            lbl_recargo.config(text="Recargo:")

    tipo_cb.bind("<<ComboboxSelected>>", actualizar_tipo)
    actualizar_tipo()  # estado inicial
    
    activo_var = tk.IntVar(value=1)
    tk.Checkbutton(
        cont,
        text="Activo",
        variable=activo_var
    ).grid(row=6, column=1, sticky="w", pady=6)

    # ===== CARGAR DATOS =====
    if datos:
        entry_concepto.insert(0, datos["concepto"])
        tipo_cb.set(datos["tipo"])
        dp_inicio.entry.insert(0, datos["fecha_inicio"])
        entry_monto.insert(0, datos["monto"])
        dp_inicio_recargo.entry.insert(0, datos["fecha_inicio_recargo"])
        entry_recargo.insert(0, datos.get("recargo_diario", 0))
        activo_var.set(1 if datos["activo"] == "Sí" else 0)
        entry_recargo.delete(0, tk.END)

    # ===== GUARDAR =====
    def guardar():
        concepto = entry_concepto.get().strip().upper()
        tipo = tipo_cb.get()
        fecha_inicio = dp_inicio.get_text()
        fecha_inicio_recargo = dp_inicio_recargo.get_text()
        monto = entry_monto.get().strip()
        orden = 1

        activo = activo_var.get()

        try:
            recargo_diario = float(entry_recargo.get())
        except ValueError:
            messagebox.showerror(
                "Error",
                "El recargo diario debe ser un número.",
                parent=top
            )
            return

        if not concepto or not fecha_inicio or not monto or not orden:
            messagebox.showerror(
                "Error",
                "Todos los campos son obligatorios.",
                parent=top
            )
            return

        if datos:
            ejecutar_consulta(
                """
                UPDATE Cargos
                SET concepto=?, tipo=?, fecha_inicio=?, fecha_inicio_recargos=?, monto=?, orden=?,
                    recargo_diario=?, activo=?
                WHERE id=?
                """,
                (concepto, tipo, fecha_inicio, fecha_inicio_recargo, monto, orden, recargo_diario, activo, datos["id"])
            )
        else:
            ejecutar_consulta(
                """
                INSERT INTO Cargos (
                    ciclo_id, concepto, tipo, fecha_inicio, fecha_inicio_recargos,
                    monto, orden, recargo_diario, activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ciclo_activo["id"],
                    concepto,
                    tipo,
                    fecha_inicio,
                    fecha_inicio_recargo,
                    monto,
                    orden,
                    recargo_diario,
                    activo
                )
            )

        cargar_cargos(tree, ciclo_activo["id"])
        top.destroy()

    acciones = tk.Frame(cont)
    acciones.grid(row=7, column=0, columnspan=2, pady=20)

    top.bind("<Return>", lambda e: guardar())

    
    ttk.Button(acciones, text="Guardar", command=guardar).pack(side="right", padx=7)
    ttk.Button(acciones, text="Cancelar", command=top.destroy).pack(side="right")


# =====================================================
def modificar_cargo(parent, tree, ciclo_activo):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Aviso", "Seleccione un cargo.")
        return

    v = tree.item(sel[0], "values")

    datos = {
        "id": v[0],
        "concepto": v[1],
        "tipo": v[2],
        "fecha_inicio": v[3],
        "monto": v[4],
        "fecha_inicio_recargo": v[5],
        "recargo_diario": v[6],
        "activo": v[7]
    }

    ventana_cargo(parent, tree, ciclo_activo, datos)


# =====================================================
def borrar_cargo(tree):
    sel = tree.selection()
    if not sel:
        messagebox.showwarning("Aviso", "Seleccione un cargo.")
        return

    cargo_id = tree.item(sel[0], "values")[0]

    if not messagebox.askyesno("Confirmar", "¿Eliminar este cargo?"):
        return

    ejecutar_consulta("DELETE FROM Cargos WHERE id=?", (cargo_id,))
    tree.delete(sel[0])


# =====================================================
def centrar_ventana(win, parent):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()
    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
