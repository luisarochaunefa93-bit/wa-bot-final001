import sqlite3
from datetime import datetime

DB_NAME = "apuestas.db"

def init_db():
    """Crea las tablas necesarias si no existen."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabla de saldo
    c.execute('''CREATE TABLE IF NOT EXISTS saldo (
                    id INTEGER PRIMARY KEY,
                    monto REAL,
                    comision_acumulada REAL,
                    ultima_actualizacion TEXT
                )''')
    
    # Tabla de historial de apuestas
    c.execute('''CREATE TABLE IF NOT EXISTS apuestas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    caballo_a TEXT,
                    caballo_b TEXT,
                    monto_a REAL,
                    monto_b REAL,
                    ganancia_bruta REAL,
                    comision REAL,
                    ganancia_neta REAL,
                    saldo_restante REAL,
                    estado TEXT
                )''')
    
    # Insertar saldo inicial si no existe (17.000 Bs.)
    c.execute("SELECT * FROM saldo WHERE id=1")
    if not c.fetchone():
        c.execute("INSERT INTO saldo (id, monto, comision_acumulada, ultima_actualizacion) VALUES (1, 17000, 0, datetime('now'))")
    
    conn.commit()
    conn.close()

def get_saldo():
    """Devuelve el saldo actual y la comisión acumulada."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT monto, comision_acumulada FROM saldo WHERE id=1")
    saldo, comision = c.fetchone()
    conn.close()
    return saldo, comision

def actualizar_saldo(monto, comision=0):
    """Actualiza el saldo y la comisión acumulada."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE saldo SET monto = monto + ?, comision_acumulada = comision_acumulada + ?, ultima_actualizacion = datetime('now') WHERE id=1", (monto, comision))
    conn.commit()
    conn.close()

def registrar_apuesta(caballo_a, caballo_b, monto_a, monto_b, ganancia_bruta, comision, ganancia_neta, saldo_restante, estado="confirmada"):
    """Guarda una apuesta en el historial."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO apuestas 
                 (fecha, caballo_a, caballo_b, monto_a, monto_b, ganancia_bruta, comision, ganancia_neta, saldo_restante, estado) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (datetime.now().isoformat(), caballo_a, caballo_b, monto_a, monto_b, ganancia_bruta, comision, ganancia_neta, saldo_restante, estado))
    conn.commit()
    conn.close()

def obtener_historial(limite=5):
    """Devuelve las últimas 'limite' apuestas."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT fecha, caballo_a, caballo_b, monto_a, monto_b, ganancia_neta, estado FROM apuestas ORDER BY id DESC LIMIT ?", (limite,))
    rows = c.fetchall()
    conn.close()
    return rows

def reset_saldo():
    """Reinicia el saldo a 17.000 Bs. (solo para pruebas)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE saldo SET monto = 17000, comision_acumulada = 0, ultima_actualizacion = datetime('now') WHERE id=1")
    conn.commit()
    conn.close()
