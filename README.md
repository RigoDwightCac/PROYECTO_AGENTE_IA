# 🤖 Agente de Inteligencia Artificial — Consultor SQL (Proyecto Académico)

Este proyecto implementa un **Agente de Inteligencia Artificial (IA)** capaz de interpretar preguntas en lenguaje natural y traducirlas automáticamente a **consultas SQL**, que se ejecutan sobre una base de datos **MySQL** llamada **Human Resources**.

El sistema combina **procesamiento de lenguaje natural (NLP)** mediante la API de **Groq (modelo LLaMA 3.3)** con consultas SQL dinámicas, integradas en una interfaz visual desarrollada con **Gradio**.

---

## 🎯 Objetivo del Proyecto
El propósito de este agente es actuar como un **consultor inteligente de base de datos**, capaz de:

- Comprender el lenguaje humano
- Traducirlo a una instrucción SQL válida
- Ejecutarla directamente en MySQL
- Mostrar los resultados de forma clara y amigable

Este proyecto fue desarrollado como parte del curso **Base de Datos I**.

---

## 🧩 Estructura del Proyecto
```
Agente_IA_Entrega/
├── agent_ia.py                    # Código principal del agente IA
├── test_connection.py             # Prueba de conexión a la base de datos
├── test_agente_ia_full.py         # Pruebas CRUD y de seguridad
├── human_resources.sql            # Script de creación de la base de datos
├── reporte_pruebas_full.csv       # Resultados de las pruebas
├── requirements.txt               # Librerías necesarias para ejecutar el proyecto
├── .env.example                   # Variables de entorno (modelo sin datos reales)
├── .gitignore                     # Exclusión de archivos sensibles
├── README.md                      # Documento de descripción general
└── docs/
    └── PROYECTO BASE DE DATOS I.pdf  # Documentación y evidencias del proyecto
```

---

## ⚙️ Instrucciones Rápidas

### 1️⃣ Instalar dependencias  
Ejecuta en tu terminal:
```bash
pip install -r requirements.txt
```

### 2️⃣ Configurar variables de entorno

Copia el archivo `.env.example` y renómbralo como `.env`.  
Luego edítalo con tus credenciales de conexión:
```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASS=tu_contraseña
MYSQL_DB=human_resources
GROQ_API_KEY=tu_api_key
```

### 🔐 Nota sobre la clave Groq

Este proyecto utiliza la API de Groq para interpretar lenguaje natural. Por motivos de seguridad, la clave no está incluida directamente en el repositorio. 

Para ejecutar el sistema, crea un archivo `.env` a partir de `.env.example` y agrega tu propia `GROQ_API_KEY`.

**¿Cómo obtener tu clave API de Groq?**

1. Visita: [https://console.groq.com/keys](https://console.groq.com/keys)
2. Inicia sesión o crea una cuenta gratuita
3. Haz clic en **"Create API Key"**
4. Copia la clave generada y agrégala a tu archivo `.env`

### 3️⃣ Importar la base de datos

Ejecuta este comando en la consola de MySQL o desde MySQL Workbench:
```bash
mysql -u root -p < human_resources.sql
```

### 4️⃣ Ejecutar el agente IA

Para iniciar la interfaz visual (Gradio):
```bash
python agent_ia.py
```

Una vez ejecutado, se abrirá una ventana local donde podrás escribir preguntas como:

- "Muestra los empleados del departamento de TI."
- "Agrega a Ana García como Programmer con salario 4000."
- "Actualiza el salario de Ana García a 5000."
- "Elimina a Ana García."

---

## 🧠 Tecnologías Utilizadas

- **Python 3.10+**
- **MySQL**
- **Groq API (LLaMA 3.3)**
- **Gradio**
- **Pandas**
- **SQLParse**
- **Dotenv**