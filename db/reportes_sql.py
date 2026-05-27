# control_escolar/reportes_sql.py

# ==============================
# COLUMNAS DE ORDEN
# ==============================
COLUMNAS_ORDEN = {
    "matricula": "e.matricula",
    "alfabetico": "e.apellido_paterno, e.apellido_materno, e.nombre",
    "fecha_inscripcion": "de.fecha_inscripcion"
}

# ==============================
# COLUMNAS DE AGRUPACIÓN
# ==============================
COLUMNAS_AGRUPAR = {
    "Sin agrupar": None,
    "Fecha inscripción": "DATE(de.fecha_inscripcion)",
    "Grupo": "de.grupo",
    "Género": "dg.genero",
    "Condición": "de.condicion"
}


# ==============================
# SELECT BASE
# ==============================
def obtener_select_base():
    return """
    SELECT
        e.matricula AS matricula,
        e.nombre,
        e.apellido_paterno,
        e.apellido_materno,
        de.fecha_inscripcion,
        de.grupo,
        dg.genero,
        de.condicion
    """


# ==============================
# FROM BASE
# ==============================
def obtener_from_base():
    return """
    FROM Estudiantes e
    INNER JOIN DatosEscolares de
        ON de.estudiante_id = e.id
    LEFT JOIN DatosGenerales dg
        ON dg.estudiante_id = e.id
    """


# ==============================
# WHERE BASE (ciclo + fecha)
# ==============================
def obtener_where_base(ciclo_id, fecha_tipo, desde, hasta):
    where = ["de.ciclo_id = ?"]
    params = [ciclo_id]

    if fecha_tipo == "rango" and desde and hasta:
        where.append("de.fecha_inscripcion BETWEEN ? AND ?")
        params.extend([desde, hasta])

    return "WHERE " + " AND ".join(where), params


# ==============================
# GROUP BY
# ==============================
def obtener_group_by(agrupar):
    col = COLUMNAS_AGRUPAR.get(agrupar)
    if not col:
        return ""
    return f"GROUP BY {col}"


# ==============================
# ORDER BY
# ==============================
def obtener_order_by(orden):
    col = COLUMNAS_ORDEN.get(orden)
    if not col:
        return ""
    return f"ORDER BY {col}"


# ==============================
# CONSTRUCTOR PRINCIPAL
# ==============================
def construir_consulta(
    tipo,
    ciclo_id,
    fecha_tipo,
    desde,
    hasta,
    orden,
    agrupar
):
    params = [ciclo_id]

    select_sql = """
        SELECT
            e.matricula AS matricula,

            -- Nombre completo
            TRIM(
                e.nombre || ' ' ||
                e.apellido_paterno || ' ' ||
                e.apellido_materno
            ) AS nombre,

            de.fecha_inscripcion,
            de.grupo,
            dg.genero,
            de.condicion,

            -- Contacto (familiar)
            TRIM(
                IFNULL(df.nombre, '') ||
                CASE
                    WHEN df.celular IS NOT NULL AND df.celular != ''
                    THEN ' - ' || df.celular
                    ELSE ''
                END
            ) AS contacto
    """

    from_sql = """
        FROM Estudiantes e
        JOIN DatosEscolares de
            ON de.estudiante_id = e.id
        JOIN DatosGenerales dg
            ON dg.estudiante_id = e.id
        LEFT JOIN DatosFamiliares df
            ON df.estudiante_id = e.id
    """

    where_sql = "WHERE de.ciclo_id = ?"

    # ===== FILTRO POR TIPO =====
    if tipo == "Inscripción":
        where_sql += " AND de.condicion = 'nuevo ingreso'"

    elif tipo == "Reinscripción":
        where_sql += " AND de.condicion = 'reingreso'"

    # ===== FILTRO POR FECHA =====
    if fecha_tipo == "rango":
        where_sql += " AND de.fecha_inscripcion BETWEEN ? AND ?"
        params.extend([desde, hasta])

    # ===== AGRUPAR =====
    group_sql = ""
    col_group = COLUMNAS_AGRUPAR.get(agrupar)
    if col_group:
        group_sql = f"GROUP BY {col_group}"

    # ===== ORDEN =====
    order_sql = ""
    col_order = COLUMNAS_ORDEN.get(orden)
    if col_order:
        order_sql = f"ORDER BY {col_order}"

    sql = f"""
        {select_sql}
        {from_sql}
        {where_sql}
        {group_sql}
        {order_sql}
    """

    return sql.strip(), params
