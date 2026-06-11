from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI()

# Permitir que nuestra página HTML se comunique con Python sin problemas de permisos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos adaptados a los nuevos requerimientos académica
class RegistroEntrada(BaseModel):
    carnet_universitario: str
    nombre: str
    materia: str

class RegistroSalida(BaseModel):
    carnet_universitario: str

# Configuración de Base de Datos
def init_db():
    conn = sqlite3.connect('asistencia_exposicion.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            carnet_universitario TEXT,
            nombre TEXT,
            materia TEXT,
            hora_entrada TEXT,
            hora_salida TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.post("/entrada")
def registrar_entrada(data: RegistroEntrada):
    hora_actual = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect('asistencia_exposicion.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO registros (carnet_universitario, nombre, materia, hora_entrada) VALUES (?, ?, ?, ?)",
        (data.carnet_universitario, data.nombre, data.materia, hora_actual)
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "mensaje": f"Entrada registrada a las {hora_actual}"}

@app.post("/salida")
def registrar_salida(data: RegistroSalida):
    hora_actual = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect('asistencia_exposicion.db')
    cursor = conn.cursor()
    
    # Buscar última entrada sin salida para este carnet
    cursor.execute(
        "SELECT id, nombre FROM registros WHERE carnet_universitario = ? AND hora_salida IS NULL ORDER BY id DESC LIMIT 1",
        (data.carnet_universitario,)
    )
    res = cursor.fetchone()
    
    if not res:
        conn.close()
        raise HTTPException(status_code=400, detail="No se encontro una entrada activa para este carnet.")
    
    id_reg, nombre = res
    cursor.execute("UPDATE registros SET hora_salida = ? WHERE id = ?", (hora_actual, id_reg))
    conn.commit()
    conn.close()
    return {"status": "ok", "mensaje": f"Salida registrada para {nombre} a las {hora_actual}"}

@app.get("/historial")
def obtener_historial():
    conn = sqlite3.connect('asistencia_exposicion.db')
    cursor = conn.cursor()
    cursor.execute("SELECT carnet_universitario, nombre, materia, hora_entrada, hora_salida FROM registros ORDER BY id DESC")
    filas = cursor.fetchall()
    conn.close()
    
    return [
        {
            "carnet_universitario": f[0], 
            "nombre": f[1], 
            "materia": f[2], 
            "entrada": f[3], 
            "salida": f[4] or "Dentro del evento"
        } 
        for f in filas
    ]