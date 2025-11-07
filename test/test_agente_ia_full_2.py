import time
import pandas as pd
from agent_ia import pregunta_a_sql, ejecutar_sql

# -------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------

def formatear_mensaje(mensaje):
    """Detecta si un mensaje corresponde a un error o advertencia."""
    if isinstance(mensaje, str):
        if "no existe" in mensaje.lower():
            return "⚠️ Tabla o columna inexistente"
        if "duplicado" in mensaje.lower() or "ya existe" in mensaje.lower():
            return "⚠️ Dato duplicado"
        if "foránea" in mensaje.lower():
            return "⚠️ Error de clave foránea"
        if "sin condiciones seguras" in mensaje.lower() or "sin where" in mensaje.lower():
            return "⚠️ Operación masiva bloqueada"
        if "no se encontró" in mensaje.lower():
            return "⚠️ Registro no encontrado"
        if "éxito" in mensaje.lower() or "correctamente" in mensaje.lower():
            return "✅ Ejecución correcta"
    return mensaje


def probar_accion(descripcion, texto, tipo_esperado):
    """Ejecuta una consulta o instrucción usando el agente IA."""
    print(f"\n🧪 {descripcion}")
    inicio = time.time()
    sql = pregunta_a_sql(texto).strip()
    duracion = round(time.time() - inicio, 3)

    sql_lower = sql.lower()
    tipo_detectado = None
    for tipo in ["select", "insert", "update", "delete"]:
        if sql_lower.startswith(tipo):
            tipo_detectado = tipo
            break

    if not tipo_detectado:
        print(f"📢 Mensaje en lugar de SQL:\n{sql}")
        return {"Prueba": descripcion, "Duración (s)": duracion, "Tipo SQL": "Mensaje", "Resultado": formatear_mensaje(sql)}

    if tipo_detectado != tipo_esperado:
        print(f"⚠️ Tipo incorrecto: esperaba {tipo_esperado.upper()}, pero generó {tipo_detectado.upper()}")
    else:
        print(f"✅ Tipo correcto: {tipo_detectado.upper()}")

    resultado = ejecutar_sql(sql)
    if isinstance(resultado, pd.DataFrame):
        salida = f"{len(resultado)} filas"
    else:
        salida = formatear_mensaje(resultado)

    print(f"📊 Resultado: {salida}")
    return {"Prueba": descripcion, "Tipo SQL": tipo_detectado, "Duración (s)": duracion, "Resultado": salida}


# -------------------------------------------
# BLOQUES DE PRUEBAS
# -------------------------------------------

pruebas = [
    # PRUEBAS BÁSICAS
    ("¿Cuántos empleados hay en total?", "consultar"),
    ("Muestra todos los nombres y apellidos de los empleados", "consultar"),
    ("Muestra los empleados contratados después del año 2005", "consultar"),
    ("Muestra los empleados que trabajan en el departamento de Marketing", "consultar"),
    ("¿Cuáles son los trabajos disponibles en la empresa?", "consultar"),
    ("Muestra los departamentos existentes", "consultar"),

    # INTERMEDIAS
    ("Muestra los empleados junto con el nombre de su departamento", "consultar"),
    ("¿Cuántos empleados hay en cada departamento?", "consultar"),
    ("Muestra el nombre del empleado y su puesto de trabajo", "consultar"),
    ("Muestra los empleados cuyo salario es mayor a 10000", "consultar"),
    ("Muestra los empleados que reportan a un gerente", "consultar"),

    # INSERCIÓN
    ("Agrega un nuevo empleado llamado Juan Pérez con correo jperez@example.com, salario 4000, puesto ST_CLERK y departamento 50.", "insert"),
    ("Inserta a Ana Gómez con salario 5500 en el departamento 60.", "insert"),
    ("Agrega a otro empleado con el mismo correo que Ana Gómez.", "insert"),
    ("Inserta un empleado sin especificar job_id o department_id.", "insert"),

    # ACTUALIZACIÓN
    ("Actualiza el salario del empleado Juan Pérez a 7000.", "update"),
    ("Cambia el correo electrónico de Ana Gómez a agomez2@example.com.", "update"),
    ("Actualiza el salario de un empleado inexistente.", "update"),
    ("Actualiza el salario de todos los empleados.", "update"),

    # ELIMINACIÓN
    ("Elimina al empleado Ana Gómez.", "delete"),
    ("Elimina al empleado con ID 9999.", "delete"),
    ("Elimina todos los empleados.", "delete"),

    # VALIDACIÓN DE ERRORES
    ("SELECT * FROM employyes;", "consultar"),
    ("SELECT firsst_name FROM employees;", "consultar"),
    ("INSERT INTO employees (first_name) VALUES ('Test');", "insert"),
    ("SELECT * FROM employees; SELECT * FROM departments;", "consultar"),

    # BONUS
    ("Muéstrame los empleados y sus gerentes.", "consultar"),
    ("Elimina todos los empleados contratados antes del 2000.", "delete"),
    ("Actualiza el salario de todos los empleados del departamento 50 en un 10%.", "update"),
    ("Agrega un nuevo empleado con los mismos datos de Juan Pérez.", "insert"),
    ("Dame a los empleados que trabajan como programadores", "consultar"),
    ("Muestra los empleados que viven en la ciudad de Seattle", "consultar")
]

# -------------------------------------------
# EJECUCIÓN DE TODAS LAS PRUEBAS
# -------------------------------------------
resultados = []

for descripcion, tipo in pruebas:
    resultados.append(probar_accion(descripcion, descripcion, tipo))

# Crear DataFrame y guardar reporte
df = pd.DataFrame(resultados)
print("\n\n📋 RESULTADOS DE LAS PRUEBAS:")
print(df.to_string(index=False))
df.to_csv("reporte_pruebas_detallado.csv", index=False)
print("\n✅ Reporte guardado como 'reporte_pruebas_detallado.csv'")
