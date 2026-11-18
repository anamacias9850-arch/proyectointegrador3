import csv
import os
from datetime import datetime
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTOS_CSV = os.path.join(BASE_DIR, "productos.csv")
VENTAS_CSV = os.path.join(BASE_DIR, "ventas.csv")

class ProductoNuevo(BaseModel):
    nombre: str
    categoria: str
    precio: float
    stock: int

class CompraRequest(BaseModel):
    cantidad: int

def leer_productos():
    productos = []
    with open(PRODUCTOS_CSV, mode="r", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            productos.append({
                "id": int(fila["id"]),
                "nombre": fila["nombre"],
                "categoria": fila["categoria"],
                "precio": float(fila["precio"]),
                "stock": int(fila["stock"])
            })
    return productos

def guardar_productos(productos):
    campos = ["id", "nombre", "categoria", "precio", "stock"]
    with open(PRODUCTOS_CSV, mode="w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(productos)

@app.get("/productos")
def obtener_productos():
    return leer_productos()

@app.post("/productos")
def crear_producto(item: ProductoNuevo):
    productos = leer_productos()
    nuevo_id = max([p["id"] for p in productos], default=0) + 1
    nuevo = {
        "id": nuevo_id,
        "nombre": item.nombre,
        "categoria": item.categoria,
        "precio": item.precio,
        "stock": item.stock
    }
    productos.append(nuevo)
    guardar_productos(productos)
    return {"mensaje": "Producto agregado", "producto": nuevo}

@app.post("/productos/{producto_id}")
def comprar_producto(producto_id: int, compra: CompraRequest):
    productos = leer_productos()
    encontrado = None

    for p in productos:
        if p["id"] == producto_id:
            if p["stock"] < compra.cantidad:
                raise HTTPException(status_code=400, detail="Stock insuficiente")
            p["stock"] -= compra.cantidad
            encontrado = p
            break

    if not encontrado:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    guardar_productos(productos)

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    total = round(encontrado["precio"] * compra.cantidad, 2)

    with open(VENTAS_CSV, mode="a", newline="", encoding="utf-8") as f:
        campos = ["fecha", "producto", "precio", "cantidad", "total"]
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writerow({
            "fecha": fecha_hoy,
            "producto": encontrado["nombre"],
            "precio": encontrado["precio"],
            "cantidad": compra.cantidad,
            "total": total
        })

    return {"mensaje": "Compra exitosa", "total": total}

@app.delete("/productos/{producto_id}")
def eliminar_producto(producto_id: int):
    productos = leer_productos()
    filtrados = [p for p in productos if p["id"] != producto_id]
    if len(productos) == len(filtrados):
        raise HTTPException(status_code=404, detail="No encontrado")
    guardar_productos(filtrados)
    return {"mensaje": "Eliminado"}

@app.get("/analytics/kpis")
def obtener_kpis():
    df = pd.read_csv(VENTAS_CSV)
    if df.empty:
        return {"ingresos_totales": 0, "total_transacciones": 0, "ticket_promedio": 0, "producto_estrella": "N/A"}
    return {
        "ingresos_totales": round(float(df["total"].sum()), 2),
        "total_transacciones": int(len(df)),
        "ticket_promedio": round(float(df["total"].mean()), 2),
        "producto_estrella": df.groupby("producto")["cantidad"].sum().idxmax()
    }

@app.get("/analytics/ventas-por-producto")
def ventas_por_producto():
    df = pd.read_csv(VENTAS_CSV)
    agrupado = df.groupby("producto", as_index=False)["total"].sum()
    return agrupado.to_dict(orient="records")

@app.get("/analytics/ventas-por-fecha")
def ventas_por_fecha():
    df = pd.read_csv(VENTAS_CSV)
    agrupado = df.groupby("fecha", as_index=False)["total"].sum().sort_values("fecha")
    return agrupado.to_dict(orient="records")
