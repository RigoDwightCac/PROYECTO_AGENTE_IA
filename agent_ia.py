# agent_ia.py
import os
import mysql.connector
import requests
from dotenv import load_dotenv
import gradio as gr
import sqlparse
import pandas as pd

# 1️⃣ Cargar variables del entorno (.env)
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASS = os.getenv("MYSQL_PASS")
MYSQL_DB   = os.getenv("MYSQL_DB")
GROK_KEY   = os.getenv("GROK_API_KEY")

# 2️⃣ Función para conectarse a la base de datos
def connect_db():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASS,
        database=MYSQL_DB,
        charset="utf8mb4"
    )

# 3️⃣ Función que envía la pregunta a Grok para traducir a SQL
# IMPORTS al inicio del archivo
from groq import Groq

# Inicializa el cliente (fuera de la función, una vez)
groq_client = Groq(api_key=os.getenv("tu_api_key_aqui")) # Reemplaza con tu clave real

def extraer_texto_de_resp(resp):
    """
    Intenta extraer texto de un objeto de respuesta de Groq,
    sea cual sea su formato (objeto, dict o estructura OpenAI).
    """
    # Caso típico estilo OpenAI
    try:
        if hasattr(resp, "choices"):
            ch = resp.choices
            if isinstance(ch, (list, tuple)) and len(ch) > 0:
                m = getattr(ch[0], "message", None)
                if m and hasattr(m, "content"):
                    return m.content
                if isinstance(ch[0], dict):
                    return ch[0].get("message", {}).get("content", "")
    except Exception:
        pass

    # Si tiene output/output_text
    try:
        if hasattr(resp, "output"):
            out = resp.output
            if isinstance(out, (list, tuple)) and len(out) > 0:
                if hasattr(out[0], "content"):
                    return out[0].content
                if isinstance(out[0], dict):
                    return out[0].get("content", "")
    except Exception:
        pass

    # Si es un diccionario
    try:
        data = resp if isinstance(resp, dict) else getattr(resp, "__dict__", None)
        if isinstance(data, dict):
            if "choices" in data:
                c = data["choices"]
                if isinstance(c, list) and len(c) > 0:
                    return c[0].get("message", {}).get("content", "") or c[0].get("text", "")
            if "output" in data:
                o = data["output"]
                if isinstance(o, list) and len(o) > 0:
                    return o[0].get("content", "") or o[0].get("text", "")
            return data.get("text") or data.get("content")
    except Exception:
        pass

    # Último recurso
    return str(resp)

def pregunta_a_sql(pregunta):
    system = (
    "Eres un asistente que traduce preguntas en español a consultas SQL válidas "
    "para una base de datos llamada Human_Resources con tablas y vistas: countries, departments, emp_details_view, employees, job_history, jobs, locations y regions. "
    "IMPORTANTE: Los nombres de las columnas y tablas están en minúsculas y con guiones bajos si corresponde: employee_id, job_id, manager_id, department_id, location_id, country_id, first_name, last_name, salary, commission_pct, department_name, job_title, city, state_province, country_name, region_name, emp_details_view. "
    "No uses nombres como firstname, lastname, empdetailsview, ni emplees mayúsculas o guiones. "
    "Responde SOLO con la consulta SQL, sin explicaciones ni texto adicional fuera del código. "

    "Cuando el usuario pida nombres, empleados o personas, "
    "ordena el resultado alfabéticamente por el apellido (last_name). "

    "Si el usuario desea agregar (INSERT) un empleado, usa SIEMPRE esta estructura: "
    "INSERT INTO employees (first_name, last_name, email, hire_date, job_id, salary, department_id) VALUES (...); "
    "No incluyas el campo employee_id, ya que es AUTO_INCREMENT en MySQL. Usa NOW() como valor para hire_date si no se especifica. "

    "Si el usuario desea actualizar (UPDATE) empleados, "
    "usa condiciones seguras en la cláusula WHERE (ejemplo: WHERE first_name='Ana' AND last_name='García'). "

    "Si el usuario menciona un nombre completo como 'QA Tester', 'Ana García' o 'John Doe', interpreta siempre la primera palabra como first_name y la segunda como last_name. "
    "Cuando el usuario diga 'QA Tester', NO lo interpretes como un job_title (puesto de trabajo), sino como el nombre de un empleado. "
    "Usa condiciones como WHERE first_name='QA' AND last_name='Tester' en lugar de usar job_title. "

    "Si el usuario desea eliminar (DELETE) empleados, "
    "usa condiciones seguras con nombre y apellido para evitar borrar todos los registros. "

    "Para consultas que involucren empleados, departamentos, cargos o ubicaciones, "
    "usa la vista emp_details_view directamente sin joins adicionales. "

    "IMPORTANTE: Si el usuario menciona nombres de puestos, cargos, departamentos o ciudades en español, traduce esos términos al inglés según existen en la base antes de generar la consulta SQL. Ejemplo: programador → Programmer, contador → Accountant, gerente de ventas → Sales Manager, recursos humanos → Human Resources, ventas → Sales, etc. "
    
    "Si el usuario solicita comparar registros entre employees y emp_details_view, "
    "usa employee_id para la comparación, nunca uses (first_name, last_name), "
    "y genera la consulta usando NOT IN (SELECT employee_id FROM emp_details_view). "

    "CONTROL DE SEGURIDAD Y ERRORES AVANZADOS: "
    "Nunca permitas eliminar todos los empleados ni modificar masivamente los salarios sin condiciones seguras. "
    "Si el usuario solicita eliminar o actualizar todos de forma insegura, responde SOLO con este mensaje profesional, sin saltos de línea ni mostrar ningún SQL: "
    "Si intentas insertar un empleado sin apellido, nombre, correo u otro campo obligatorio, responde: 'Error: No se puede agregar el empleado porque falta campo obligatorio (first_name, last_name, email, hire_date, job_id, salary, department_id).' "
    "Si el correo ya existe, responde: 'Error: correo duplicado, ya existe un empleado con ese email.' "
    "Si el usuario consulta una columna inexistente, responde: 'Error: Columna no válida, no existe en la base Human_Resources.' "
    "Siempre notifica cuáles son los campos obligatorios: first_name, last_name, email, hire_date, job_id, salary, department_id."
)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": pregunta}
    ]

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.0,
            max_tokens=512
        )

        # 🧠 Intentar extraer el texto SQL desde la respuesta
        texto = extraer_texto_de_resp(resp)
        print("DEBUG Texto extraído de Groq:", texto)  # Para depuración

        # 🧹 Limpiar formato Markdown (```sql ... ```)
        if "```" in texto:
            texto = texto.replace("```sql", "").replace("```", "").strip()

        # 🧽 Limpieza extra
        texto = texto.replace("\n", " ").replace("\r", " ").strip()

        # 🧾 Formatear SQL para mostrarlo bonito
        sql_pretty = sqlparse.format(texto, reindent=True, keyword_case='upper')

        return sql_pretty

    except TypeError as te:
        print("❌ TypeError en pregunta_a_sql:", te)
        raise
    except Exception as e:
        print("❌ Error general en pregunta_a_sql:", e)
        raise

# 4️⃣ Ejecutar la consulta SQL en la base
def ejecutar_sql(sql):
    import pandas as pd
    import mysql.connector

    conn = None
    cursor = None

    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)

        sql_lower = sql.strip().lower()
        es_modificacion = sql_lower.startswith(("insert", "update", "delete"))

        # 🚫 Protección adicional contra DELETE o UPDATE sin WHERE
        if (sql_lower.startswith("delete") or sql_lower.startswith("update")) and "where" not in sql_lower:
            return "⚠️ Operación bloqueada: No puedes eliminar o actualizar todos los registros sin condición WHERE."

        # Solo usa un preview_cursor si verdaderamente lo vas a necesitar
        empleados_afectados = []
        if ("from employees" in sql_lower or "update employees" in sql_lower) and "where" in sql_lower:
            pre_sql = "SELECT employee_id, first_name, last_name FROM employees " + sql[sql_lower.index("where"):]
            with conn.cursor(dictionary=True) as preview_cursor:
                preview_cursor.execute(pre_sql)
                empleados_afectados = preview_cursor.fetchall()

        # Ejecutar consulta principal (ningún preview_cursor abierto)
        cursor.execute(sql)

        # Si es modificación (INSERT/UPDATE/DELETE)
        if es_modificacion:
            conn.commit()
            filas = cursor.rowcount
            if filas == 0:
                msg = "⚠️ No se encontró ningún empleado con ese criterio."
            else:
                if empleados_afectados:
                    detalles = ", ".join(
                        f"{e['first_name']} {e['last_name']} (ID {e['employee_id']})"
                        for e in empleados_afectados
                    )
                    if sql_lower.startswith("delete"):
                        msg = f"✅ Se eliminó correctamente al empleado {detalles}."
                    elif sql_lower.startswith("update"):
                        msg = f"✅ Se actualizó correctamente al empleado {detalles}."
                    else:
                        msg = f"✅ Operación exitosa. {filas} fila(s) afectada(s)."
                else:
                    msg = f"✅ Operación exitosa. {filas} fila(s) afectada(s)."
            return msg

        # Si es SELECT -> obtener filas
        rows = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
        if not rows:
            return "⚠️ No se encontraron resultados para esa consulta."
        df = pd.DataFrame(rows, columns=columnas)
        return df

    except mysql.connector.Error as err:
        # mismos errores que tienes (sin cambios)
        if err.errno == 1062:
            return "⚠️ Ya existe un empleado con ese correo electrónico."
        elif err.errno == 1452:
            return "⚠️ No se puede insertar o actualizar: clave foránea inexistente."
        elif err.errno == 1048:
            return "⚠️ Uno de los campos obligatorios está vacío."
        elif err.errno == 1054:
            return "⚠️ Alguna columna en la consulta no existe o está mal escrita."
        elif err.errno == 1146:
            return "⚠️ La tabla especificada no existe en la base de datos."
        elif err.errno == 2014:
            return "⚠️ Comando fuera de sincronización. Intenta nuevamente."
        else:
            return f"❌ Error SQL ({err.errno}): {err.msg}"
    except Exception as e:
        return f"❌ Error general al ejecutar SQL:\n{e}"

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()
    
# 5️⃣ --- Funciones para el agente y la interfaz ---

import gradio as gr
import pandas as pd

# 🧹 Función para limpiar interfaz
def limpiar():
    """
    Limpia el cuadro de texto, el mensaje SQL y la tabla de resultados.
    Además, devuelve el foco al cuadro de texto.
    """
    mensaje_inicial = "🕹️ Escribe una pregunta y presiona un botón."
    return gr.update(value="", interactive=True, autofocus=True), mensaje_inicial, gr.update(value=None, visible=False)


# ⚙️ Función genérica de procesamiento
def procesar_consulta(preg, tipo_accion):
    if not preg or not preg.strip():
        return "⚠️ Debes escribir una instrucción.", gr.update(value=None, visible=False)

    # 🧩 Ajustar el texto según el botón usado
    if tipo_accion == "consultar":
        prompt = preg
    elif tipo_accion == "agregar":
        prompt = f"Agrega {preg}"
    elif tipo_accion == "actualizar":
        prompt = f"Actualiza {preg}"
    elif tipo_accion == "eliminar":
        prompt = f"Elimina {preg}"
    else:
        prompt = preg

    try:
        # 🔍 Generar SQL con Groq
        sql_generado = pregunta_a_sql(prompt)

        # 🧠 Verificar si la respuesta realmente parece un SQL válido
        sql_generado_lower = sql_generado.lower()
        if not any(sql_generado_lower.startswith(cmd) for cmd in ["select", "insert", "update", "delete"]):
            # No es SQL, sino una advertencia o explicación del modelo
            md = f"📢 {sql_generado}"
            return md, gr.update(value=None, visible=False)

        # 🚫 Validar que el SQL coincida con la acción del botón
        if tipo_accion == "consultar" and not sql_generado_lower.startswith("select"):
            return "⚠️ Solo puedes realizar consultas (SELECT) con este botón.", gr.update(value=None, visible=False)
        if tipo_accion == "agregar" and not sql_generado_lower.startswith("insert"):
            return "⚠️ Solo puedes agregar (INSERT) con este botón.", gr.update(value=None, visible=False)
        if tipo_accion == "actualizar" and not sql_generado_lower.startswith("update"):
            return "⚠️ Solo puedes actualizar (UPDATE) con este botón.", gr.update(value=None, visible=False)
        if tipo_accion == "eliminar" and not sql_generado_lower.startswith("delete"):
            return "⚠️ Solo puedes eliminar (DELETE) con este botón.", gr.update(value=None, visible=False)

        # ✅ Ejecutar consulta SQL
        resultado = ejecutar_sql(sql_generado)

        # Si resultado es DataFrame (solo SELECT)
        if isinstance(resultado, pd.DataFrame):
            df = resultado.copy()
            if "No." not in df.columns:
                df.insert(0, "No.", range(1, len(df) + 1))
            md = f"**Consulta generada:**\n```sql\n{sql_generado}\n```"
            return md, gr.update(value=df, visible=True)

        # Si resultado es texto (INSERT, UPDATE o DELETE)
        md = f"**Consulta generada:**\n```sql\n{sql_generado}\n```\n\n📊 **Resultado:**\n{resultado}"
        return md, gr.update(value=None, visible=False)

    except Exception as e:
        md = f"❌ Error general: {e}"
        return md, gr.update(value=None, visible=False)

# 🔘 Funciones específicas para cada botón
def solo_consultar(preg, salida_sql, salida_tabla):
    return procesar_consulta(preg, "consultar")

def solo_agregar(preg, salida_sql, salida_tabla):
    return procesar_consulta(preg, "agregar")

def solo_actualizar(preg, salida_sql, salida_tabla):
    return procesar_consulta(preg, "actualizar")

def solo_eliminar(preg, salida_sql, salida_tabla):
    return procesar_consulta(preg, "eliminar")


# 6️⃣ --- Interfaz principal con logo personalizado ---
with gr.Blocks(
    title="AGENTE IA con Groq + MySQL",
    css="""
        body {
            background: linear-gradient(135deg, #002b70, #004aad, #0a69c2);
            color: white;
            font-family: 'Segoe UI', sans-serif;
        }
        .gradio-container {
            background: transparent !important;
        }
        h1 {
            text-align: center;
            font-size: 3em !important;
            font-weight: 900 !important;
            color: #00b0ff !important;  /* Azul brillante */
            margin-top: 0.3em;
            text-shadow: 2px 2px 12px rgba(0, 0, 0, 0.5);
        }
        .logo {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 120px;
            height: 120px;
            border-radius: 50%;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
        }
        .gr-button {
            border-radius: 10px !important;
            font-weight: bold !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.25);
            transition: 0.3s;
        }
        .gr-button.primary {
            background-color: #1a9cfc !important;
            color: white !important;
        }
        .gr-button:hover {
            transform: scale(1.05);
            filter: brightness(1.1);
        }
        textarea {
            border-radius: 10px !important;
            border: 2px solid #1976d2 !important;
            background-color: #f0f8ff !important;
            color: #000 !important;
        }
        .gr-markdown {
            background-color: rgba(255,255,255,0.1) !important;
            border-radius: 10px !important;
            padding: 12px;
        }
        .gr-dataframe {
            background-color: white !important;
            border-radius: 10px !important;
            color: black !important;
        }
    """
) as iface:
    # 🔹 Mostrar logo centrado y título debajo
    gr.HTML(
    """
    <div style="display:flex; justify-content:center; align-items:center; 
                background:linear-gradient(135deg, #e6f0ff, #f8fbff); 
                padding:25px; border-radius:20px; box-shadow:0 4px 8px rgba(0,0,0,0.1);">
        
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Escudo_de_la_universidad_Mariano_G%C3%A1lvez_Guatemala.svg/2048px-Escudo_de_la_universidad_Mariano_G%C3%A1lvez_Guatemala.svg.png"
             alt="Logo Agente IA"
             width="100"
             style="margin-right:20px;">
        
        <h1 style="color:#007BFF; font-size:50px; font-weight:bold; 
                   text-shadow:2px 2px 5px rgba(0,0,0,0.2); margin:0;">
            AGENTE IA
        </h1>
    </div>
    """
)

    with gr.Row():
        pregunta = gr.Textbox(
            label="💭 Escribe tu pregunta o acción:",
            placeholder="Ejemplo: ¿Cuántos empleados hay en total?",
            autofocus=True,
            lines=2
        )

    with gr.Row():
        btn_consultar = gr.Button("🚀 Consultar", variant="primary")
        btn_agregar = gr.Button("🟢 Agregar")
        btn_actualizar = gr.Button("🟡 Actualizar")
        btn_eliminar = gr.Button("🔴 Eliminar")
        btn_limpiar = gr.Button("🧹 Limpiar")

    salida_sql = gr.Markdown("🕹️ Escribe una pregunta y presiona un botón.")
    salida_tabla = gr.Dataframe(label="📊 Resultados", interactive=False, visible=False)

    # 🔗 Conectar botones con sus funciones
    btn_consultar.click(solo_consultar, inputs=[pregunta, salida_sql, salida_tabla], outputs=[salida_sql, salida_tabla])
    btn_agregar.click(solo_agregar, inputs=[pregunta, salida_sql, salida_tabla], outputs=[salida_sql, salida_tabla])
    btn_actualizar.click(solo_actualizar, inputs=[pregunta, salida_sql, salida_tabla], outputs=[salida_sql, salida_tabla])
    btn_eliminar.click(solo_eliminar, inputs=[pregunta, salida_sql, salida_tabla], outputs=[salida_sql, salida_tabla])
    btn_limpiar.click(limpiar, outputs=[pregunta, salida_sql, salida_tabla])

# 🚀 Lanzar la app
if __name__ == "__main__":
    iface.launch()
