import time
import pandas as pd
from agent_ia import pregunta_a_sql, ejecutar_sql

def formatear_mensaje(mensaje):
    """Detecta si un mensaje corresponde a una advertencia de seguridad."""
    if isinstance(mensaje, str) and "sin condiciones seguras" in mensaje.lower():
        return "⚠️ Acción bloqueada (seguridad)"
    if isinstance(mensaje, str) and "no se puede" in mensaje.lower():
        return "⚠️ Acción no permitida o datos incompletos"
    return mensaje


def probar_accion(descripcion, texto, tipo_esperado):
    """
    Prueba una acción enviando una instrucción al modelo
    y ejecutando el SQL resultante (si aplica).
    """
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
        print(f"📢 Modelo devolvió mensaje, no SQL:\n{sql}")
        return {"Prueba": descripcion, "Duración (s)": duracion, "Tipo SQL": "Mensaje", "Resultado": formatear_mensaje(sql)}

    if tipo_detectado != tipo_esperado:
        print(f"⚠️ Tipo incorrecto: esperaba {tipo_esperado.upper()}, pero generó {tipo_detectado.upper()}")
    else:
        print(f"✅ Tipo correcto: {tipo_detectado.upper()}")

    resultado = ejecutar_sql(sql)
    if isinstance(resultado, pd.DataFrame):
        tipo_salida = "DataFrame"
        salida = f"{len(resultado)} filas"
    else:
        tipo_salida = "Texto"
        salida = formatear_mensaje(resultado)

    print(f"📊 Resultado: {salida}")
    return {"Prueba": descripcion, "Duración (s)": duracion, "Tipo SQL": tipo_detectado, "Salida": tipo_salida, "Resultado": salida}


# 🧩 --- SECCIÓN DE PRUEBAS CRUD COMPLETAS ---
resultados = []

# 1️⃣ Consulta general
resultados.append(probar_accion("Consulta general de empleados", "Muestra todos los empleados", "select"))

# 2️⃣ Insertar empleado de prueba
resultados.append(probar_accion("Insertar empleado de prueba",
    "Agrega a QA Tester, correo qatest@example.com, como IT_PROG en el departamento 60 con salario 4000.", "insert"))

# 3️⃣ Verificar que el empleado fue agregado
resultados.append(probar_accion("Verificar empleado insertado",
    "Muestra el empleado llamado QA Tester", "select"))

# 4️⃣ Actualizar salario del empleado
resultados.append(probar_accion("Actualizar salario del empleado",
    "Actualiza el salario de QA Tester a 4800.", "update"))

# 5️⃣ Confirmar actualización
resultados.append(probar_accion("Confirmar salario actualizado",
    "Muestra el salario del empleado QA Tester", "select"))

# 6️⃣ Eliminar el empleado
resultados.append(probar_accion("Eliminar empleado de prueba",
    "Elimina al empleado QA Tester", "delete"))

# 7️⃣ Confirmar que fue eliminado
resultados.append(probar_accion("Verificar eliminación",
    "Muestra el empleado QA Tester", "select"))

# 8️⃣ Prueba de seguridad (DELETE sin WHERE)
resultados.append(probar_accion("Intento de eliminación masiva", "Elimina todos los empleados", "delete"))

# 9️⃣ Prueba de seguridad (UPDATE sin WHERE)
resultados.append(probar_accion("Intento de actualización masiva", "Actualiza todos los salarios a 9000", "update"))

# 10️⃣ Intento de usar botón incorrecto
resultados.append(probar_accion("Intento de consulta con acción de agregar", "Agrega ¿Cuántos empleados hay?", "insert"))

# 🧾 Mostrar resultados
df = pd.DataFrame(resultados)
print("\n\n📋 RESULTADOS DE LAS PRUEBAS:")
print(df.to_string(index=False))

# 📁 Guardar el reporte
df.to_csv("reporte_pruebas_full.csv", index=False)
print("\n✅ Reporte guardado en 'reporte_pruebas_full.csv'")
