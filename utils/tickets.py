import tkinter as tk

from tkinter import ttk
from escpos.printer import Win32Raw
from datetime import datetime
from PIL import Image, ImageTk

from db.conexion import obtener_conexion

NOMBRE_IMPRESORA = "EPSON TM-T88V Receipt"  # AJUSTA EXACTAMENTE

def imprimir_logo(p, ruta_logo):
    if not ruta_logo:
        return

    img = Image.open(ruta_logo)
    img = img.convert("1")

    ancho_px = 150  # 80mm
    ratio = ancho_px / img.width
    alto = int(img.height * ratio)

    img = img.resize((ancho_px, alto))
    p.image(img)

    
# =====================================================
# OBTENER DATOS DEL PAGO
# =====================================================
def obtener_datos_pagos(pagos_ids, usuario_id):
    conn = obtener_conexion()
    cur = conn.cursor()

    placeholders = ",".join("?" * len(pagos_ids))

    cur.execute(f"""
        SELECT
            p.id,
            p.monto_pagado,
            c.concepto,
            p.tipo_pago,
            e.matricula AS matricula,
            e.nombre || ' ' || e.apellido_paterno || ' ' || e.apellido_materno AS alumno,
            d.grupo AS grado_grupo,
            es.nombre AS escuela,
            es.RFC,
            es.logo,
            u.usuario
        FROM Pagos p
        JOIN Estudiantes e ON e.id = p.estudiante_id
        JOIN DatosEscolares d
            ON d.estudiante_id = e.id
            AND d.ciclo_id = p.ciclo_id
        JOIN Cargos c ON c.id = p.cargo_id
        JOIN usuarios u ON u.id = ?
        JOIN Escuela es ON es.id = (
            SELECT valor FROM configuracion WHERE clave = 'ultima_escuela'
        )
        WHERE p.id IN ({placeholders})
        ORDER BY p.id
    """, (usuario_id, *pagos_ids))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise ValueError("Pagos no encontrados")

    return rows


# =====================================================
# GENERAR TEXTO DEL TICKET
# =====================================================
def generar_texto_ticket_pago(pagos_ids, usuario_id):
    rows = obtener_datos_pagos(pagos_ids, usuario_id)

    (
        pago_id,
        _,
        _,
        tipo_pago,
        matricula,
        alumno,
        grado_grupo,
        escuela,
        rfc,
        logo,
        usuario
    ) = rows[0]

    fecha_impresion = datetime.now().strftime("%d/%m/%Y %H:%M")
    ancho = 32

    ticket = [
        escuela.center(ancho),
        rfc.center(ancho),
        fecha_impresion.center(ancho),
        f"N° {pago_id:<8} Usuario: {usuario}",
        "",
        "",
        "",
        f"Alumno: {alumno}",
        f"Grado: {grado_grupo}",
        f"Matrícula: {matricula}",
        f"Forma: {tipo_pago}",
        "",
        "",
        "",
        "Ct  Concepto                    Total"
    ]

    total = 0.0
    for i, (_, monto, concepto, *_rest) in enumerate(rows, start=1):
        total += monto
        ticket.append(f"{i:<3} {concepto[:24]:24}   ${monto:,.2f}")

    ticket.extend([
        "",
        f"TOTAL: ${total:,.2f}",
        "",
        "",
        "",
        "Recibo de pago simplificado."
    ])

    return "\n".join(ticket)

# =====================================================
# IMPRIMIR TICKET
# =====================================================
def imprimir_ticket_pago(pagos_ids, usuario_id):
    rows = obtener_datos_pagos(pagos_ids, usuario_id)
    logo = rows[0][9]  # es.logo

    p = Win32Raw(NOMBRE_IMPRESORA)

    # ===== LOGO =====
    if logo:
        imprimir_logo(p, logo)
        p.text("\n")  # separación

    # ===== TEXTO =====
    texto = generar_texto_ticket_pago(pagos_ids, usuario_id)

    p.set(align="center", bold=True)
    for linea in texto.split("\n")[:2]:
        p.text(linea + "\n")

    p.set(bold=False)
    for linea in texto.split("\n")[2:]:
        p.text(linea + "\n")

    p.text("\n\n\n\n\n")
    p.text("\x1d\x56\x00")
    p.close()


# =====================================================
# PREVISUALIZACIÓN
# =====================================================
def construir_ticket_modelo(pagos_ids, usuario_id):
    rows = obtener_datos_pagos(pagos_ids, usuario_id)

    (
        pago_id,
        _,
        _,
        tipo_pago,
        matricula,
        alumno,
        grado_grupo,
        escuela,
        rfc,
        logo,
        usuario
    ) = rows[0]

    fecha_impresion = datetime.now().strftime("%d/%m/%Y %H:%M")
    ancho = 32

    bloques = []

    # ===== LOGO =====
    if logo:
        bloques.append({
            "tipo": "logo",
            "ruta": logo
        })

    # ===== ENCABEZADO =====
    encabezado = [
        escuela.center(ancho),
        rfc.center(ancho),
        fecha_impresion.center(ancho),
        f"N° {pago_id:<8} Usuario: {usuario}"
    ]

    bloques.append({
        "tipo": "texto",
        "alineacion": "center",
        "lineas": encabezado
    })

    bloques.append({"tipo": "espacio", "lineas": 2})

    cuerpo = [
        f"Alumno: {alumno}",
        f"Grado: {grado_grupo}",
        f"Matrícula: {matricula}",
        f"Forma: {tipo_pago}",
        "",
        "Ct  Concepto                    Total"
    ]

    total = 0.0
    for i, (_, monto, concepto, *_rest) in enumerate(rows, start=1):
        total += monto
        cuerpo.append(f"{i:<3} {concepto[:24]:24}   ${monto:,.2f}")

    cuerpo.extend([
        "",
        f"TOTAL: ${total:,.2f}",
        "",
        "Recibo de pago simplificado."
    ])

    bloques.append({
        "tipo": "texto",
        "alineacion": "left",
        "lineas": cuerpo
    })

    return bloques

def previsualizar_ticket(parent, pagos_ids, usuario_id):
    bloques = construir_ticket_modelo(pagos_ids, usuario_id)

    root = parent.winfo_toplevel()
    top = tk.Toplevel(root)
    top.title("Vista previa del ticket")
    top.geometry("420x650")
    top.transient(root)
    top.grab_set()

    canvas = tk.Canvas(top, bg="white")
    canvas.pack(fill="both", expand=True)

    y = 10
    ancho_px = 150

    for b in bloques:
        if b["tipo"] == "logo":
            img = Image.open(b["ruta"])
            img = img.convert("1")
            ratio = ancho_px / img.width
            img = img.resize((ancho_px, int(img.height * ratio)))
            img_tk = ImageTk.PhotoImage(img)

            canvas.create_image(210, y, image=img_tk, anchor="n")
            canvas.image = img_tk
            y += img.height + 10

        elif b["tipo"] == "texto":
            font = ("Courier New", 10)
            for l in b["lineas"]:
                anchor = "n"
                canvas.create_text(
                    210 if b["alineacion"] == "center" else 10,
                    y,
                    text=l,
                    font=font,
                    anchor="n" if b["alineacion"] == "center" else "nw"
                )
                y += 14

        elif b["tipo"] == "espacio":
            y += b["lineas"] * 14

    ttk.Button(top, text="Cerrar", command=top.destroy).pack(pady=8)

