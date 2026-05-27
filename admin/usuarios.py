import tkinter as tk
from tkinter import ttk
import hashlib

from db.conexion import obtener_todos, ejecutar_consulta


# =====================================================
# UTILIDAD HASH PASSWORD
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =====================================================
# UTILIDADES UI
# =====================================================
def centrar_ventana(win, parent):
    win.update_idletasks()
    w = win.winfo_width()
    h = win.winfo_height()

    x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
    y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)

    win.geometry(f"{w}x{h}+{x}+{y}")


def show_error(parent, titulo, mensaje):
    root = parent.winfo_toplevel()

    win = tk.Toplevel(root)
    win.title(titulo)
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(
        win,
        text=mensaje,
        wraplength=300,
        padx=20,
        pady=20
    ).pack()

    ttk.Button(win, text="Aceptar", command=win.destroy).pack(pady=(0, 15))

    win.update_idletasks()
    centrar_ventana(win, root)
    win.wait_window()


def ask_yes_no(parent, titulo, mensaje):
    root = parent.winfo_toplevel()
    respuesta = {"valor": False}

    win = tk.Toplevel(root)
    win.title(titulo)
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(
        win,
        text=mensaje,
        wraplength=300,
        padx=20,
        pady=20
    ).pack()

    frame = tk.Frame(win)
    frame.pack(pady=(0, 15))

    

    ttk.Button(
        frame,
        text="No",
        command=win.destroy
    ).pack(side="left", padx=10)

    ttk.Button(
        frame,
        text="Sí",
        command=lambda: (respuesta.update(valor=True), win.destroy())
    ).pack(side="left", padx=10)

    win.update_idletasks()
    centrar_ventana(win, root)
    win.wait_window()

    return respuesta["valor"]


# =====================================================
# PANTALLA PRINCIPAL
# =====================================================
def mostrar_usuarios(parent):
    for w in parent.winfo_children():
        w.destroy()

    contenedor = tk.Frame(parent, bg="white")
    contenedor.pack(fill="both", expand=True)

    header = tk.Frame(contenedor, bg="#d0e4f5", height=60)
    header.pack(fill="x")

    tk.Label(
        header,
        text="ADMINISTRACIÓN DE USUARIOS",
        bg="#d0e4f5",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    toolbar = tk.Frame(contenedor, bg="white")
    toolbar.pack(fill="x", padx=20, pady=5)

    ttk.Button(
        toolbar,
        text="Agregar",
        command=lambda: ventana_usuario(parent, tree)
    ).pack(side="left", padx=5)

    ttk.Button(
        toolbar,
        text="Modificar",
        command=lambda: modificar_usuario(parent, tree)
    ).pack(side="left", padx=5)

    ttk.Button(
        toolbar,
        text="Borrar",
        command=lambda: borrar_usuario(parent, tree)
    ).pack(side="left", padx=5)

    tree = ttk.Treeview(
        contenedor,
        columns=("usuario", "nombre", "roles", "activo"),
        show="headings",
        height=12
    )

    tree.heading("usuario", text="Usuario")
    tree.heading("nombre", text="Nombre")
    tree.heading("roles", text="Roles")
    tree.heading("activo", text="Activo")

    tree.column("usuario", width=140)
    tree.column("nombre", width=260)
    tree.column("roles", width=260)
    tree.column("activo", width=80, anchor="center")

    tree.pack(fill="both", expand=True, padx=20, pady=10)
    tree.bind("<Double-1>", lambda e: modificar_usuario(parent, tree))

    cargar_usuarios(tree)


# =====================================================
# CARGAR USUARIOS
# =====================================================
def cargar_usuarios(tree):
    tree.delete(*tree.get_children())

    filas = obtener_todos("""
        SELECT 
            u.id,
            u.usuario,
            u.nombre,
            COALESCE(GROUP_CONCAT(r.nombre, ', '), '') AS roles,
            CASE u.activo WHEN 1 THEN 'Sí' ELSE 'No' END
        FROM usuarios u
        LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
        LEFT JOIN roles r ON r.id = ur.rol_id
        GROUP BY u.id
        ORDER BY u.usuario
    """)

    for f in filas:
        tree.insert("", "end", iid=f[0], values=f[1:])


# =====================================================
# VENTANA AGREGAR / MODIFICAR
# =====================================================
def ventana_usuario(parent, tree, datos=None):
    top = tk.Toplevel(parent)
    top.title("Usuario")
    top.geometry("290x450")
    top.minsize(280, 450)
    top.transient(parent.winfo_toplevel())
    top.grab_set()
    top.resizable(False, False)

    top.grid_rowconfigure(0, weight=1)
    top.grid_rowconfigure(1, weight=0)
    top.grid_columnconfigure(0, weight=1)

    cont = tk.Frame(top, padx=15, pady=10)
    cont.grid(row=0, column=0, sticky="nsew")

    buttons = tk.Frame(top)
    buttons.grid(row=1, column=0, sticky="ew", pady=8)


    centrar_ventana(top, parent)

    cont = tk.Frame(top, padx=25, pady=15)
    cont.grid(row=0, column=0, sticky="nsew")
    
    main = tk.Frame(cont)
    main.pack(fill="both", expand=True)


    content_frame = tk.Frame(cont)
    content_frame.pack(fill="both", expand=True)

    buttons_frame = tk.Frame(cont)
    buttons_frame.pack(fill="x", pady=(10, 0))
    form_frame = tk.Frame(main)
    form_frame.pack(anchor="center")


    # =========================
    # USUARIO Y NOMBRE
    # =========================
    tk.Label(form_frame, text="Usuario:").pack(anchor="w")

    usuario_var = tk.StringVar()

    entry_usuario = tk.Entry(form_frame, width=30, textvariable=usuario_var)
    entry_usuario.pack(pady=4)

    def usuario_mayusculas(*args):
        valor = usuario_var.get()
        if valor != valor.upper():
            usuario_var.set(valor.upper())

    usuario_var.trace_add("write", usuario_mayusculas)

    tk.Label(form_frame, text="Nombre del usuario:").pack(anchor="w")

    nombre_var = tk.StringVar()

    entry_nombre = tk.Entry(form_frame, width=30, textvariable=nombre_var)
    entry_nombre.pack(pady=(0, 10))

    def nombre_mayusculas(*args):
        valor = nombre_var.get()
        if valor != valor.upper():
            nombre_var.set(valor.upper())

    nombre_var.trace_add("write", nombre_mayusculas)


    # =========================
    # PESTAÑAS
    # =========================
    notebook = ttk.Notebook(main)
    notebook.pack(fill="both", expand=False, pady=10)

    tab_acceso = tk.Frame(notebook, padx=15, pady=15)
    tab_perfil = tk.Frame(notebook, padx=15, pady=15)

    notebook.add(tab_acceso, text="Acceso")
    notebook.add(tab_perfil, text="Perfil")

    # =========================
    # ACCESO
    # =========================
    tk.Label(tab_acceso, text="Contraseña:").pack(anchor="w")
    entry_password = tk.Entry(tab_acceso, width=32, show="*")
    entry_password.pack(anchor="w", pady=5)

    tk.Label(tab_acceso, text="Tipo de usuario:").pack(anchor="w", pady=(10, 0))

    roles_frame = tk.Frame(tab_acceso)
    roles_frame.pack(anchor="w", pady=5)

    rol_var = tk.IntVar()

    roles = obtener_todos("SELECT id, nombre FROM roles ORDER BY nombre")
    for rol_id, nombre in roles:
        tk.Radiobutton(
            roles_frame,
            text=nombre,
            variable=rol_var,
            value=rol_id
        ).pack(side="left", padx=15)

    activo_var = tk.BooleanVar(value=True)
    tk.Checkbutton(
        tab_acceso,
        text="Usuario activo",
        variable=activo_var
    ).pack(anchor="w", pady=10)

    # =========================
    # PERFIL (expandible correcto + scroll)
    # =========================
    canvas = tk.Canvas(tab_perfil, highlightthickness=0)
    scrollbar = ttk.Scrollbar(tab_perfil, orient="vertical", command=canvas.yview)

    perfil_frame = tk.Frame(canvas)

    perfil_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=perfil_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    canvas = tk.Canvas(tab_perfil, highlightthickness=0, height=200)

    permisos = {
        "Control Escolar": [
            "Inscripciones",
            "Reinscripciones",
            "Alumnos",
            "Reportes"
        ],
        "Caja": [
            "Pagos - Alumnos",
            "Pagos - Recibos",
            "Pagos - Pagados",
            "Pagos - Cargos",
            "Reportes"
        ],
        "Admin": [
            "Escuela",
            "Ciclos",
            "Grupos",
            "Usuarios"
        ]
    }

    perm_vars = {}

    for modulo, opciones in permisos.items():
        # CONTENEDOR DEL MÓDULO
        modulo_frame = tk.Frame(perfil_frame)
        modulo_frame.pack(fill="x", pady=(6, 0))

        # HEADER
        header = tk.Frame(modulo_frame)
        header.pack(fill="x")

        expanded = tk.BooleanVar(value=False)

        btn = tk.Button(
            header,
            text="+",
            width=2
        )
        btn.pack(side="left")

        tk.Label(
            header,
            text=modulo,
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=6)

        # CONTENIDO EXPANDIBLE
        contenido = tk.Frame(modulo_frame, padx=30)

        def toggle(frame=contenido, var=expanded, b=btn):
            if var.get():
                frame.pack_forget()
                b.config(text="+")
                var.set(False)
            else:
                frame.pack(fill="x")
                b.config(text="−")
                var.set(True)

        btn.config(command=toggle)

        # OPCIONES
        for opcion in opciones:
            var = tk.BooleanVar()
            perm_vars[f"{modulo}:{opcion}"] = var

            tk.Checkbutton(
                contenido,
                text=opcion,
                variable=var
            ).pack(anchor="w")


    # =========================
    # CARGAR DATOS
    # =========================
    if datos:
        entry_usuario.insert(0, datos["usuario"])
        entry_usuario.config(state="disabled")

        entry_nombre.insert(0, datos["nombre"])
        activo_var.set(datos["activo"])

        rol_actual = obtener_todos(
            "SELECT rol_id FROM usuarios_roles WHERE usuario_id=?",
            (datos["id"],)
        )
        if rol_actual:
            rol_var.set(rol_actual[0][0])
        
        permisos_bd = obtener_todos(
            """
            SELECT modulo, permiso
            FROM usuarios_permisos
            WHERE usuario_id=?
            """,
            (datos["id"],)
        )

        for modulo, permiso in permisos_bd:
            clave = f"{modulo}:{permiso}"
            if clave in perm_vars:
                perm_vars[clave].set(True)


    # =========================
    # BOTONES
    # =========================
    acciones = tk.Frame(content_frame)
    acciones.pack(pady=20)

    def guardar():
        usuario = entry_usuario.get().strip().upper()
        nombre = entry_nombre.get().strip().upper()
        password = entry_password.get()
        activo = 1 if activo_var.get() else 0
        rol_id = rol_var.get()

        if not usuario or not nombre:
            show_error(top, "Error", "Usuario y nombre son obligatorios.")
            return

        if not datos and not password:
            show_error(top, "Error", "La contraseña es obligatoria.")
            return

        if not rol_id:
            show_error(top, "Error", "Seleccione un tipo de usuario.")
            return

        if datos:
            ejecutar_consulta(
                "UPDATE usuarios SET nombre=?, activo=? WHERE id=?",
                (nombre, activo, datos["id"])
            )

            if password:
                ejecutar_consulta(
                    "UPDATE usuarios SET password=? WHERE id=?",
                    (hash_password(password), datos["id"])
                )

            usuario_id = datos["id"]
        else:
            ejecutar_consulta(
                "INSERT INTO usuarios (usuario, nombre, password, activo) VALUES (?, ?, ?, ?)",
                (usuario, nombre, hash_password(password), activo)
            )

            usuario_id = obtener_todos(
                "SELECT id FROM usuarios WHERE usuario=?",
                (usuario,)
            )[0][0]

        ejecutar_consulta(
            "DELETE FROM usuarios_roles WHERE usuario_id=?",
            (usuario_id,)
        )

        ejecutar_consulta(
            "INSERT INTO usuarios_roles (usuario_id, rol_id) VALUES (?, ?)",
            (usuario_id, rol_id)
        )

        ejecutar_consulta(
            "DELETE FROM usuarios_permisos WHERE usuario_id=?",
            (usuario_id,)
        )

        for clave, var in perm_vars.items():
            if ":" not in clave:
                continue

            if var.get():
                modulo, permiso = clave.split(":")

                ejecutar_consulta(
                    """
                    INSERT INTO usuarios_permisos (usuario_id, modulo, permiso)
                    VALUES (?, ?, ?)
                    """,
                    (usuario_id, modulo, permiso)
                )



        cargar_usuarios(tree)
        top.destroy()


    ttk.Button(buttons, text="Guardar", command=guardar).pack(side="right", padx=16)
    ttk.Button(buttons, text="Cancelar", command=top.destroy).pack(side="right")

    top.bind("<Return>", lambda e: guardar())
    top.bind("<Escape>", lambda e: top.destroy())


# =====================================================
# MODIFICAR
# =====================================================
def modificar_usuario(parent, tree):
    sel = tree.selection()
    if not sel:
        show_error(parent, "Aviso", "Seleccione un usuario.")
        return

    usuario_id = sel[0]

    fila = obtener_todos(
        "SELECT usuario, nombre, activo FROM usuarios WHERE id=?",
        (usuario_id,)
    )

    if not fila:
        return

    datos = {
        "id": usuario_id,
        "usuario": fila[0][0],
        "nombre": fila[0][1],
        "activo": bool(fila[0][2])
    }

    ventana_usuario(parent, tree, datos)


# =====================================================
# BORRAR
# =====================================================
def borrar_usuario(parent, tree):
    sel = tree.selection()
    if not sel:
        show_error(parent, "Aviso", "Seleccione un usuario.")
        return

    usuario_id = sel[0]
    usuario = tree.item(usuario_id, "values")[0]

    if not ask_yes_no(
        parent,
        "Confirmar",
        f"¿Eliminar el usuario '{usuario}'?"
    ):
        return

    ejecutar_consulta("DELETE FROM usuarios_roles WHERE usuario_id=?", (usuario_id,))
    ejecutar_consulta("DELETE FROM usuarios WHERE id=?", (usuario_id,))
    cargar_usuarios(tree)
