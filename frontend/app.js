const API_URL = "http://127.0.0.1:8000";
let chartProductos = null;
let chartFechas = null;

document.addEventListener("DOMContentLoaded", actualizarTodo);

async function actualizarTodo() {
    await cargarProductos();
    await cargarKPIs();
    await cargarGraficas();
}

async function cargarProductos() {
    const res = await fetch(`${API_URL}/productos`);
    const productos = await res.json();
    const tbody = document.getElementById("tabla-productos");
    tbody.innerHTML = "";

    productos.forEach(p => {
        tbody.innerHTML += `
            <tr>
                <td>${p.id}</td>
                <td>${p.nombre}</td>
                <td>${p.categoria}</td>
                <td>$${p.precio.toFixed(2)}</td>
                <td>${p.stock}</td>
                <td>
                    <button class="btn-comprar" onclick="comprarProducto(${p.id})">Comprar</button>
                    <button class="btn-eliminar" onclick="eliminarProducto(${p.id})">Eliminar</button>
                </td>
            </tr>`;
    });
}

document.getElementById("form-producto").addEventListener("submit", async (e) => {
    e.preventDefault();
    const nuevo = {
        nombre: document.getElementById("nombre").value,
        categoria: document.getElementById("categoria").value,
        precio: parseFloat(document.getElementById("precio").value),
        stock: parseInt(document.getElementById("stock").value)
    };
    await fetch(`${API_URL}/productos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(nuevo)
    });
    e.target.reset();
    await cargarProductos();
});

async function comprarProducto(id) {
    const cantidad = parseInt(prompt("¿Cuántas unidades?", "1"));
    if (!cantidad || cantidad <= 0) return;

    const res = await fetch(`${API_URL}/productos/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cantidad })
    });

    if (res.ok) await actualizarTodo();
    else alert("Stock insuficiente");
}

async function eliminarProducto(id) {
    if (!confirm("¿Eliminar producto?")) return;
    await fetch(`${API_URL}/productos/${id}`, { method: "DELETE" });
    await cargarProductos();
}

async function cargarKPIs() {
    const res = await fetch(`${API_URL}/analytics/kpis`);
    const data = await res.json();
    document.getElementById("kpi-ingresos").textContent = `$${data.ingresos_totales.toFixed(2)}`;
    document.getElementById("kpi-estrella").textContent = data.producto_estrella;
    document.getElementById("kpi-transacciones").textContent = data.total_transacciones;
    document.getElementById("kpi-ticket").textContent = `$${data.ticket_promedio.toFixed(2)}`;
}

async function cargarGraficas() {
    const resProd = await fetch(`${API_URL}/analytics/ventas-por-producto`);
    const datosProd = await resProd.json();
    if (chartProductos) chartProductos.destroy();
    chartProductos = new Chart(document.getElementById("graficaProductos"), {
        type: "bar",
        data: {
            labels: datosProd.map(d => d.producto),
            datasets: [{ label: "Ingresos ($)", data: datosProd.map(d => d.total), backgroundColor: "#6d4c41" }]
        }
    });

    const resFechas = await fetch(`${API_URL}/analytics/ventas-por-fecha`);
    const datosFechas = await resFechas.json();
    if (chartFechas) chartFechas.destroy();
    chartFechas = new Chart(document.getElementById("graficaFechas"), {
        type: "line",
        data: {
            labels: datosFechas.map(d => d.fecha),
            datasets: [{ label: "Ventas ($)", data: datosFechas.map(d => d.total), borderColor: "#d4a373" }]
        }
    });
}