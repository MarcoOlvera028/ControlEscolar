from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from datetime import datetime
from io import BytesIO

from db.conexion import obtener_conexion

def obtener_escuela_activa(conn):
    cur = conn.cursor()

    # 1. Obtener id desde configuracion
    cur.execute("""
        SELECT valor
        FROM configuracion
        WHERE clave = 'ultima_escuela'
        LIMIT 1
    """)
    row = cur.fetchone()

    if not row or not row[0]:
        return "Escuela no definida"

    escuela_id = row[0]

    # 2. Obtener nombre de la escuela
    cur.execute("""
        SELECT nombre
        FROM Escuela
        WHERE id = ?
    """, (escuela_id,))

    row = cur.fetchone()
    return row[0] if row else "Escuela no definida"




def generar_pdf_cargos_en_memoria(ciclo_activo, grupos_seleccionados, obtener_conexion):
    buffer = BytesIO()
    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=4 * cm,
        bottomMargin=2 * cm
    )

    elementos = []

    # ===============================
    # CONSULTAS
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    # Grados y grupos seleccionados
    placeholders = ",".join("?" * len(grupos_seleccionados))
    cur.execute(f"""
        SELECT
            g.nombre AS grado,
            gr.grupo
        FROM Grupos gr
        JOIN Grados g ON g.id = gr.grado_id
        WHERE gr.id IN ({placeholders})
        ORDER BY g.orden, gr.grupo
    """, grupos_seleccionados)

    grupos = cur.fetchall()

    # Cargos (los mismos para todos)
    cur.execute("""
        SELECT
            fecha_inicio,
            concepto,
            monto
        FROM Cargos
        WHERE ciclo_id = ?
        AND activo = 1
        ORDER BY orden
    """, (ciclo_activo["id"],))

    cargos = cur.fetchall()
    conn.close()

    # ===============================
    # CONTENIDO
    # ===============================
    grado_actual = None

    for grado, grupo in grupos:

        if grado != grado_actual:
            elementos.append(Spacer(1, 12))
            elementos.append(
                Paragraph(
                    f"<b>GRADO: {grado.upper()}</b>",
                    styles["Heading2"]
                )
            )
            grado_actual = grado

        elementos.append(
            Paragraph(
                f"<b>Grupo {grupo}</b>",
                styles["Heading3"]
            )
        )
        elementos.append(Spacer(1, 8))

        # Tabla
        data = [["Fecha", "Concepto", "Importe"]]

        for fecha, concepto, monto in cargos:
            data.append([
                fecha,
                concepto.upper(),
                f"${monto:,.2f}"
            ])

        tabla = Table(
            data,
            colWidths=[5 * cm, 16 * cm, 5 * cm],
            repeatRows=1
        )

        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
        ]))

        elementos.append(tabla)
        elementos.append(PageBreak())

    # ===============================
    # CONSTRUIR PDF
    # ===============================
    conn = obtener_conexion()
    cur = conn.cursor()

    nombre_escuela = obtener_escuela_activa(conn)
    def encabezado(canvas, doc):
        ancho, alto = landscape(A4)
        fecha = datetime.now().strftime("%d/%m/%Y")

        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(
            ancho / 2,
            alto - 2 * cm,
            nombre_escuela
        )

        canvas.setFont("Helvetica", 11)
        canvas.drawCentredString(
            ancho / 2,
            alto - 2.8 * cm,
            "Reporte de Cargos – Caja"
        )

        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(
            ancho - 2 * cm,
            alto - 2 * cm,
            f"Fecha: {fecha}"
        )

        canvas.line(
            2 * cm,
            alto - 3.3 * cm,
            ancho - 2 * cm,
            alto - 3.3 * cm
        )

    doc.build(
        elementos,
        onFirstPage=encabezado,
        onLaterPages=encabezado
    )

    buffer.seek(0)
    return buffer


def encabezado_pdf(canvas, doc, titulo):
    conn = obtener_conexion()
    cur = conn.cursor()

    nombre_escuela = obtener_escuela_activa(conn)
    ancho, alto = landscape(A4)
    fecha = datetime.now().strftime("%d/%m/%Y")

    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawCentredString(
        ancho / 2, alto - 2 * cm,
        nombre_escuela
    )

    canvas.setFont("Helvetica", 11)
    canvas.drawCentredString(
        ancho / 2, alto - 2.8 * cm,
        titulo
    )

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(
        ancho - 2 * cm, alto - 2 * cm,
        f"Fecha: {fecha}"
    )

    canvas.line(
        2 * cm, alto - 3.3 * cm,
        ancho - 2 * cm, alto - 3.3 * cm
    )


def generar_pdf_estado_cuenta_en_memoria(alumno_id, fecha_corte, formato, ciclo_activo, obtener_conexion):
    conn = obtener_conexion()
    cur = conn.cursor()

    styles = getSampleStyleSheet()
    elementos = []

    # ===============================
    # OBTENER NOMBRE DEL ALUMNO
    # ===============================
    cur.execute("""
        SELECT nombre || ' ' || apellido_paterno || ' ' || apellido_materno
        FROM Estudiantes
        WHERE id = ?
    """, (alumno_id,))
    nombre_alumno = cur.fetchone()[0]

    # ===============================
    # OBTENER CICLOS DEL ALUMNO
    # ===============================
    if formato == "ciclo":
        ciclos = [(ciclo_activo["id"], ciclo_activo["nombre"])]
    else:
        cur.execute("""
            SELECT DISTINCT c.id, c.ciclo
            FROM DatosEscolares d
            JOIN ciclos c ON c.id = d.ciclo_id
            WHERE d.estudiante_id = ?
            ORDER BY c.id
        """, (alumno_id,))
        ciclos = cur.fetchall()

    hay_datos = False

    for ciclo_id, ciclo_nombre in ciclos:
        cur.execute("""
            SELECT
                p.id,
                c.fecha_inicio,
                p.fecha_pago,
                c.concepto,
                (c.monto + IFNULL(p.recargos, 0)),
                IFNULL(p.descuento, 0),
                IFNULL(p.condonacion, 0),
                (c.monto + IFNULL(p.recargos, 0) - IFNULL(p.descuento, 0) - IFNULL(p.condonacion, 0)),
                (IFNULL(p.monto_pagado, 0) + IFNULL(p.recargos, 0))
            FROM Cargos c
            LEFT JOIN Pagos p
                ON p.cargo_id = c.id
                AND p.estudiante_id = ?
            WHERE c.ciclo_id = ?
              AND c.fecha_inicio <= ?
              AND (p.fecha_pago IS NULL OR p.fecha_pago <= ?)
            ORDER BY c.fecha_inicio
        """, (alumno_id, ciclo_id, fecha_corte, fecha_corte))

        rows = cur.fetchall()
        if not rows:
            continue

        hay_datos = True

        # ===== ENCABEZADO POR CICLO =====
        elementos.append(Spacer(1, 12))
        elementos.append(Paragraph(
            f"<b>Alumno:</b> {nombre_alumno} &nbsp;&nbsp;&nbsp; "
            f"<b>Ciclo:</b> {ciclo_nombre}",
            styles["Normal"]
        ))
        elementos.append(Spacer(1, 10))

        columnas = [
            "Folio",
            "Fecha cargo",
            "Fecha pago",
            "Concepto",
            "Total cargo",
            "Descuento",
            "Condonación",
            "Pagos",
            "Total"
        ]

        filas = []
        for r in rows:
            pagos = r[8]
            filas.append([
                r[0],
                r[1],
                r[2] or "",
                r[3],
                f"${r[4]:,.2f}",
                f"${r[5]:,.2f}",
                f"${r[6]:,.2f}",
                f"${r[7]:,.2f}",
                f"${pagos:,.2f}"
            ])

        tabla = Table([columnas] + filas, repeatRows=1)
        tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))

        elementos.append(tabla)

    conn.close()

    if not hay_datos:
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=4 * cm,
        bottomMargin=2 * cm
    )

    doc.build(
        elementos,
        onFirstPage=lambda c, d: encabezado_pdf(c, d, "Estado de Cuenta"),
        onLaterPages=lambda c, d: encabezado_pdf(c, d, "Estado de Cuenta")
    )

    buffer.seek(0)
    return buffer


def generar_pdf_programa_ingresos_en_memoria(ciclo_activo, grupos, incluir_pagos, detalle, ciclo_modo, obtener_conexion):
    conn = obtener_conexion()
    cur = conn.cursor()

    # ===============================
    # CONSULTA BASE
    # ===============================
    params = []
    where_ciclo = ""

    if ciclo_modo == "Ciclo actual":
        where_ciclo = "AND p.ciclo_id = ?"
        params.append(ciclo_activo["id"])

    sql = f"""
        SELECT
            strftime('%Y-%m', c.fecha_inicio) AS mes,
            c.concepto,

            -- grado
            substr(d.grupo, 1, instr(d.grupo, '/') - 1) AS grado,

            -- grupo
            substr(d.grupo, instr(d.grupo, '/') + 1) AS grupo,

            e.nombre || ' ' || e.apellido_paterno || ' ' || e.apellido_materno AS alumno,

            c.monto AS importe,

            (
                IFNULL(p.monto_pagado, 0) +
                IFNULL(p.descuento, 0) +
                IFNULL(p.condonacion, 0)
            ) AS pagos

        FROM Pagos p
        JOIN Cargos c
            ON c.id = p.cargo_id
        JOIN Estudiantes e
            ON e.id = p.estudiante_id
        JOIN DatosEscolares d
            ON d.estudiante_id = e.id
            AND d.ciclo_id = p.ciclo_id

        WHERE d.grupo IN ({",".join("?" * len(grupos))})
        {where_ciclo}

        ORDER BY
            mes,
            c.concepto,
            grado,
            grupo,
            alumno
    """

    cur.execute(sql, [*grupos, *params])
    rows = cur.fetchall()

    if not rows:
        return None
    

    # ===============================
    # AGRUPACIÓN
    # ===============================
    data = {}

    for mes, concepto, grado, grupo, alumno, monto, pagos in rows:
        data.setdefault(mes, {
            "importe": 0,
            "pagos": 0,
            "saldo": 0,
            "total": 0,
            "conceptos": {}
        })

        mes_ref = data[mes]

        mes_ref["conceptos"].setdefault(concepto, {
            "importe": 0,
            "pagos": 0,
            "saldo": 0,
            "total": 0,
            "grupos": {}
        })

        concepto_ref = mes_ref["conceptos"][concepto]

        grupo_key = f"{grado} - {grupo}"
        concepto_ref["grupos"].setdefault(grupo_key, {
            "importe": 0,
            "pagos": 0,
            "saldo": 0,
            "total": 0,
            "alumnos": []
        })

        grupo_ref = concepto_ref["grupos"][grupo_key]

        # ===============================
        # NIVEL ALUMNO (único cálculo directo)
        # ===============================
        importe = monto
        pagos_realizados = pagos if incluir_pagos else 0
        saldo = importe - pagos_realizados
        total = pagos_realizados

        alumno_data = {
            "nombre": alumno,
            "importe": importe,
            "pagos": pagos_realizados,
            "saldo": saldo,
            "total": total
        }

        grupo_ref["alumnos"].append(alumno_data)

        # ===============================
        # ACUMULAR HACIA ARRIBA
        # ===============================
        for ref in (grupo_ref, concepto_ref, mes_ref):
            ref["importe"] += importe
            ref["pagos"] += pagos_realizados
            ref["saldo"] += saldo
            ref["total"] += total

    # ===============================
    # CONSTRUIR FILAS
    # ===============================
    detalle = detalle.lower()

    mostrar_concepto = "concepto" in detalle
    mostrar_grado = "grado" in detalle
    mostrar_alumno = "alumno" in detalle
    filas = []

    def agregar_fila(texto, importe=0, pagos=0, nivel=0):
        saldo = importe - pagos
        filas.append([
            "   " * nivel + texto,
            f"${importe:,.2f}" if importe else "",
            f"${pagos:,.2f}" if pagos else "",
            f"${saldo:,.2f}" if importe else "",
            f"${pagos:,.2f}" if pagos else ""
        ])

    total_general_importe = 0
    total_general_pagos = 0

    for mes, mes_data in data.items():
        agregar_fila(
            datetime.strptime(mes, "%Y-%m").strftime("%B %Y"),
            mes_data["importe"],
            mes_data["pagos"],
            nivel=0
        )

        total_general_importe += mes_data["importe"]
        total_general_pagos += mes_data["pagos"]

        # ===============================
        # CONCEPTO
        # ===============================
        if not mostrar_concepto:
            continue

        for concepto, c_data in mes_data["conceptos"].items():
            agregar_fila(
                concepto,
                c_data["importe"],
                c_data["pagos"],
                nivel=1
            )

            # ===============================
            # GRADO / GRUPO
            # ===============================
            if not mostrar_grado:
                continue

            for grupo, g_data in c_data["grupos"].items():
                agregar_fila(
                    grupo,
                    g_data["importe"],
                    g_data["pagos"],
                    nivel=2
                )

                # ===============================
                # ALUMNO
                # ===============================
                if not mostrar_alumno:
                    continue

                for alumno in g_data["alumnos"]:
                    agregar_fila(
                        alumno["nombre"],
                        alumno["importe"],
                        alumno["pagos"],
                        nivel=3
                    )
    
    # ===============================
    # TOTAL GENERAL
    # ===============================
    agregar_fila(
        "TOTAL GENERAL",
        total_general_importe,
        total_general_pagos,
        nivel=0
    )

    # ===============================
    # PDF
    # ===============================
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=4 * cm,
        bottomMargin=2 * cm
    )

    tabla = Table(
        [["Concepto", "Importe", "Pagos", "Saldo", "Total"]] + filas,
        repeatRows=1
    )

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))

    doc.build(
        [tabla],
        onFirstPage=lambda c, d: encabezado_pdf(c, d, "Programa de Ingresos"),
        onLaterPages=lambda c, d: encabezado_pdf(c, d, "Programa de Ingresos")
    )

    buffer.seek(0)
    return buffer


def generar_pdf_descuentos_en_memoria(fecha_inicio, fecha_fin, grupos_seleccionados, ciclo_modo, ciclo_activo, obtener_conexion):
    conn = obtener_conexion()
    cur = conn.cursor()

    params = [fecha_inicio, fecha_fin]
    where_ciclo = ""

    if ciclo_modo == "Ciclo actual":
        where_ciclo = "AND p.ciclo_id = ?"
        params.append(ciclo_activo["id"])

    placeholders = ",".join("?" * len(grupos_seleccionados))
    params.extend(grupos_seleccionados)

    cur.execute(f"""
        SELECT
            c.tipo AS concepto,
            e.id AS matricula,
            e.nombre || ' ' || e.apellido_paterno || ' ' || e.apellido_materno AS alumno,
            d.grupo,
            c.monto,
            IFNULL(p.descuento, 0) AS descuento,
            IFNULL(p.condonacion, 0) AS condonacion,
            p.recargos
        FROM Pagos p
        JOIN Cargos c ON c.id = p.cargo_id
        JOIN Estudiantes e ON e.id = p.estudiante_id
        JOIN DatosEscolares d
            ON d.estudiante_id = e.id
            AND d.ciclo_id = p.ciclo_id
        WHERE p.fecha_pago BETWEEN ? AND ?
        {where_ciclo}
        AND d.grupo IN ({placeholders})
        AND IFNULL(p.descuento, 0) > 0
        ORDER BY c.tipo, d.grupo, alumno
    """, params)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    # ===============================
    # AGRUPAR POR CONCEPTO
    # ===============================
    data = {}
    total_importe = 0.0
    total_descuento = 0.0
    total_total_pagado = 0

    for concepto, matricula, alumno, grupo, monto, descuento, condonacion, recargos in rows:
        data.setdefault(concepto, []).append(
            (matricula, alumno, grupo, monto, descuento, condonacion, recargos)
        )
        total_importe += monto + recargos
        total_descuento += descuento

    # ===============================
    # CONSTRUIR FILAS
    # ===============================
    filas = []

    def fila(texto, matricula="", grado="", importe="", descuento="", total_pagado=""):
        filas.append([texto, matricula, grado, importe, descuento, total_pagado])

    for concepto, items in data.items():
        fila(concepto.upper())
        

        for matricula, alumno, grupo, monto, descuento, condonacion, recargos in items:
            total_importe1 = monto + recargos
            total_pagado1 = total_importe1 - descuento - condonacion
            total_total_pagado += total_pagado1
            fila(
                f"    {alumno}",
                str(matricula),
                grupo,
                f"${total_importe1:,.2f}",
                f"${descuento:,.2f}",
                f"${total_pagado1:,.2f}"
            )

    # Fila TOTAL
    filas.append([
        "TOTAL",
        "",
        "",
        f"${total_importe:,.2f}",
        f"${total_descuento:,.2f}",
        f"${total_total_pagado:,.2f}"
    ])

    # ===============================
    # PDF EN MEMORIA
    # ===============================
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=4 * cm,
        bottomMargin=2 * cm
    )

    tabla = Table(
        [["Concepto", "Matrícula", "Grado", "Importe", "Descuento", "Total Pagado"]] + filas,
        repeatRows=1,
        colWidths=[9 * cm, 3 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm]
    )

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]))

    doc.build(
        [tabla],
        onFirstPage=lambda c, d: encabezado_pdf(c, d, "Reporte de Descuentos"),
        onLaterPages=lambda c, d: encabezado_pdf(c, d, "Reporte de Descuentos")
    )

    buffer.seek(0)
    return buffer


def generar_pdf_condonaciones_en_memoria(fecha_inicio, fecha_fin, grupos, ciclo_modo, ciclo_activo, obtener_conexion):
    conn = obtener_conexion()
    cur = conn.cursor()

    params = [fecha_inicio, fecha_fin]
    where_ciclo = ""

    if ciclo_modo == "actual":
        where_ciclo = "AND p.ciclo_id = ?"
        params.append(ciclo_activo["id"])

    # ===============================
    # CONSULTA
    # ===============================
    cur.execute(f"""
        SELECT
            c.tipo,
            e.id AS matricula,
            d.grupo,
            e.nombre || ' ' || e.apellido_paterno || ' ' || e.apellido_materno AS alumno,
            c.monto,
            IFNULL(p.condonacion, 0),
            IFNULL(p.descuento, 0),
            p.recargos
        FROM Pagos p
        JOIN Cargos c ON c.id = p.cargo_id
        JOIN Estudiantes e ON e.id = p.estudiante_id
        JOIN DatosEscolares d
            ON d.estudiante_id = e.id
            AND d.ciclo_id = p.ciclo_id
        WHERE p.fecha_pago BETWEEN ? AND ?
        {where_ciclo}
        AND d.grupo IN ({",".join("?" * len(grupos))})
        AND IFNULL(p.condonacion, 0) > 0
        ORDER BY c.tipo, d.grupo, alumno
    """, params + grupos)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    # ===============================
    # AGRUPAR POR CONCEPTO
    # ===============================
    data = {}
    total_importe = 0.0
    total_condonacion = 0.0
    total_total_pagado = 0.0

    for tipo, matricula, grupo, alumno, monto, condonacion, descuento, recargos in rows:
        data.setdefault(tipo, [])
        data[tipo].append(
            (matricula, grupo, alumno, monto, condonacion, descuento, recargos)
        )
        total_importe += monto + recargos
        total_condonacion += condonacion

    # ===============================
    # CONSTRUIR FILAS
    # ===============================
    filas = []

    for tipo, registros in data.items():
        filas.append([
            tipo.upper(),
            "",
            "",
            "",
            ""
        ])

        for matricula, grupo, alumno, monto, condonacion, descuento, recargos in registros:
            total_importe1 = monto + recargos
            total_pagado1 = total_importe1 - descuento - condonacion
            total_total_pagado += total_pagado1
            filas.append([
                "   " + alumno,
                matricula,
                grupo,
                f"${total_importe1:,.2f}",
                f"${condonacion:,.2f}",
                f"${total_pagado1:,.2f}"
            ])

    filas.append([
        "TOTAL",
        "",
        "",
        f"${total_importe:,.2f}",
        f"${total_condonacion:,.2f}",
        f"${total_total_pagado:,.2f}"
    ])

    # ===============================
    # PDF EN MEMORIA
    # ===============================
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=4 * cm,
        bottomMargin=2 * cm
    )

    tabla = Table(
        [["Concepto", "Matrícula", "Grado", "Importe", "Condonación", "Total Pagado"]] + filas,
        repeatRows=1,
        colWidths=[9 * cm, 3 * cm, 4 * cm, 3 * cm, 3 * cm, 3 * cm]
    )

    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]))

    doc.build(
        [tabla],
        onFirstPage=lambda c, d: encabezado_pdf(c, d, "Reporte de Condonaciones"),
        onLaterPages=lambda c, d: encabezado_pdf(c, d, "Reporte de Condonaciones")
    )

    buffer.seek(0)
    return buffer


def generar_pdf_pagos_en_memoria(fecha_inicio, fecha_fin, grupos, ciclo_modo, ciclo_activo, detalle, obtener_conexion):
    from io import BytesIO
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    conn = obtener_conexion()
    cur = conn.cursor()

    params = [fecha_inicio, fecha_fin]
    where_ciclo = ""

    if ciclo_modo == "Ciclo actual":
        where_ciclo = "AND p.ciclo_id = ?"
        params.append(ciclo_activo["id"])

    placeholders = ",".join("?" * len(grupos))
    params.extend(grupos)

    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontSize = 7
    cell_style.leading = 8
    def P(text):
        return Paragraph(str(text), cell_style)

    # ===============================
    # CONSULTA BASE
    # ===============================
    cur.execute(f"""
        SELECT
            p.id,
            u.usuario AS usuario,
            e.nombre || ' ' || e.apellido_paterno || ' ' || e.apellido_materno AS alumno,
            d.grupo,
            c.concepto,
            p.fecha_pago,
            p.monto_pagado,
            IFNULL(p.descuento, 0),
            IFNULL(p.condonacion, 0),
            IFNULL(p.recargos, 0)
        FROM Pagos p
        JOIN usuarios u ON u.id = p.usuario_id
        JOIN Estudiantes e ON e.id = p.estudiante_id
        JOIN DatosEscolares d
            ON d.estudiante_id = e.id
            AND d.ciclo_id = p.ciclo_id
        JOIN Cargos c ON c.id = p.cargo_id
        WHERE p.fecha_pago BETWEEN ? AND ?
        {where_ciclo}
        AND d.grupo IN ({placeholders})
        ORDER BY u.usuario, alumno, c.concepto, p.fecha_pago
    """, params)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    # ===============================
    # AGRUPAR DATOS POR USUARIO
    # ===============================
    data = {}

    for id, usuario, alumno, grupo, concepto, fecha, imp, desc, cond, rec in rows:
        total = imp + rec

        data.setdefault(usuario, []).append({
            "folio": id,
            "alumno": alumno,
            "grupo": grupo,
            "concepto": concepto,
            "fecha": fecha,
            "importe": imp,
            "descuento": desc,
            "condonacion": cond,
            "recargos": rec,
            "total": total
        })

    # ===============================
    # CONSTRUIR FILAS
    # ===============================
    filas = []
    subtotales_idx = []
    total_idx = None

    detalle = detalle.strip().lower()

    def money(v):
        return f"${v:,.2f}"

    total_importe = total_desc = total_cond = total_rec = total_gen = 0

    # ---------- DETALLE: USUARIO ----------
    if detalle == "usuario":
        encabezado = [
            "Usuario", "Importe", "Descuentos",
            "Condonación", "Recargos", "Total"
        ]

        for usuario, items in data.items():
            sub_imp = sum(i["importe"] for i in items)
            sub_des = sum(i["descuento"] for i in items)
            sub_con = sum(i["condonacion"] for i in items)
            sub_rec = sum(i["recargos"] for i in items)
            sub_tot = sum(i["total"] for i in items)

            filas.append([
                usuario,
                money(sub_imp),
                money(sub_des),
                money(sub_con),
                money(sub_rec),
                money(sub_tot)
            ])

            total_importe += sub_imp
            total_desc += sub_des
            total_cond += sub_con
            total_rec += sub_rec
            total_gen += sub_tot

    # ---------- DETALLE: USUARIO + ALUMNOS ----------
    elif detalle == "usuario + alumnos":
        encabezado = [
            "Usuario", "Alumno", "Grupo",
            "Importe", "Descuentos",
            "Condonación", "Recargos", "Total"
        ]

        for usuario, items in data.items():
            filas.append([usuario] + [""] * (len(encabezado) - 1))

            sub_imp = sub_des = sub_con = sub_rec = sub_tot = 0

            for i in items:
                filas.append([
                    "",
                    i["alumno"],
                    i["grupo"],
                    money(i["importe"]),
                    money(i["descuento"]),
                    money(i["condonacion"]),
                    money(i["recargos"]),
                    money(i["total"])
                ])

                sub_imp += i["importe"]
                sub_des += i["descuento"]
                sub_con += i["condonacion"]
                sub_rec += i["recargos"]
                sub_tot += i["total"]

            subtotales_idx.append(len(filas) + 1)

            filas.append([
                "",
                "SUBTOTAL",
                "",
                money(sub_imp),
                money(sub_des),
                money(sub_con),
                money(sub_rec),
                money(sub_tot)
            ])

            total_importe += sub_imp
            total_desc += sub_des
            total_cond += sub_con
            total_rec += sub_rec
            total_gen += sub_tot

    # ---------- DETALLE: USUARIO + ALUMNOS + CONCEPTO ----------
    elif detalle == "usuario + alumnos + concepto":
        encabezado = [
            "Usuario", "Folio", "Concepto", 
            "Fecha", "Alumno", "Grupo",
            "Importe", "Dto.",
            "Condonación", "Recargos", "Total"
        ]

        for usuario, items in data.items():
            filas.append([usuario] + [""] * (len(encabezado) - 1))

            sub_imp = sub_des = sub_con = sub_rec = sub_tot = 0

            for i in items:
                filas.append([
                    "",
                    i["folio"],
                    P(i["concepto"]),
                    i["fecha"],
                    P(i["alumno"]),
                    i["grupo"],
                    money(i["importe"]),
                    money(i["descuento"]),
                    money(i["condonacion"]),
                    money(i["recargos"]),
                    money(i["total"])
                ])

                sub_imp += i["importe"]
                sub_des += i["descuento"]
                sub_con += i["condonacion"]
                sub_rec += i["recargos"]
                sub_tot += i["total"]

            subtotales_idx.append(len(filas) + 1)

            filas.append([
                "",
                "SUBTOTAL",
                "",
                "",
                "",
                "",
                money(sub_imp),
                money(sub_des),
                money(sub_con),
                money(sub_rec),
                money(sub_tot)
            ])

            total_importe += sub_imp
            total_desc += sub_des
            total_cond += sub_con
            total_rec += sub_rec
            total_gen += sub_tot

    # ===============================
    # TOTAL GENERAL (alineado correcto)
    # ===============================
    total_idx = len(filas) + 1

    total_row = [""] * len(encabezado)

    total_row[0] = "TOTAL GENERAL"

    # Dependiendo del detalle, los números empiezan en distinta columna
    if detalle == "usuario":
        total_row[1:] = [
            money(total_importe),
            money(total_desc),
            money(total_cond),
            money(total_rec),
            money(total_gen),
        ]

    elif detalle == "usuario + alumnos":
        total_row[3:] = [
            money(total_importe),
            money(total_desc),
            money(total_cond),
            money(total_rec),
            money(total_gen),
        ]

    elif detalle == "usuario + alumnos + concepto":
        total_row[6:] = [
            money(total_importe),
            money(total_desc),
            money(total_cond),
            money(total_rec),
            money(total_gen),
        ]

    filas.append(total_row)

    # ===============================
    # PDF
    # ===============================
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=4 * cm,
        bottomMargin=2 * cm
    )

    tabla = Table(
        [encabezado] + filas,
        repeatRows=1,
        colWidths = [
            2.5*cm,   # Usuario
            1.7*cm,   # Folio
            4.5*cm,   # Concepto
            1.7*cm, # Fecha
            3*cm,   # Alumno
            1.7*cm,   # Grupo
            1.7*cm,   # Importe
            1.7*cm,   # Dto
            1.9*cm,   # Condonación
            1.7*cm,   # Recargos
            2*cm  # Total
        ]
    )

    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e0e0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
    ])

    for idx in subtotales_idx:
        style.add("FONTNAME", (0, idx), (-1, idx), "Helvetica-Bold")
        style.add("BACKGROUND", (0, idx), (-1, idx), colors.whitesmoke)

    style.add("FONTNAME", (0, total_idx), (-1, total_idx), "Helvetica-Bold")
    style.add("BACKGROUND", (0, total_idx), (-1, total_idx), colors.lightgrey)
    style.add("LINEABOVE", (0, total_idx), (-1, total_idx), 1.5, colors.black)

    tabla.setStyle(style)

    doc.build(
        [tabla],
        onFirstPage=lambda c, d: encabezado_pdf(c, d, "Reporte de Pagos"),
        onLaterPages=lambda c, d: encabezado_pdf(c, d, "Reporte de Pagos")
    )

    buffer.seek(0)
    return buffer

