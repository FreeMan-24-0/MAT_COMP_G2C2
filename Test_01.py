import random
import heapq
import numpy as np
import networkx as nx
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ================= LÓGICA MATEMÁTICA Y ALGORITMO =================

def generar_matriz_automatica(n):
    """Genera aleatoriamente una matriz de adyacencia ponderada"""
    matriz = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            # 30% de probabilidad de no haber conexión
            if random.random() > 0.3:
                peso = random.randint(1, 50)
                matriz[i][j] = peso
                matriz[j][i] = peso  # Grafo no dirigido
    return matriz


def dijkstra(matriz, origen, destino, n):
    """Encuentra el camino mínimo y su costo."""
    distancias = {i: float('inf') for i in range(n)}
    distancias[origen] = 0
    padres = {i: None for i in range(n)}
    cola_prioridad = [(0, origen)]

    while cola_prioridad:
        distancia_actual, nodo_actual = heapq.heappop(cola_prioridad)

        if nodo_actual == destino:
            break

        if distancia_actual > distancias[nodo_actual]:
            continue

        for vecino in range(n):
            peso = int(matriz[nodo_actual][vecino])
            if peso > 0:
                nueva_distancia = distancia_actual + peso
                if nueva_distancia < distancias[vecino]:
                    distancias[vecino] = nueva_distancia
                    padres[vecino] = nodo_actual
                    heapq.heappush(cola_prioridad, (nueva_distancia, vecino))

    camino = []
    nodo_paso = destino
    if distancias[destino] != float('inf'):
        while nodo_paso is not None:
            camino.insert(0, nodo_paso)
            nodo_paso = padres[nodo_paso]

    return camino, distancias[destino]


# ================= INTERFAZ GRÁFICA INTEGRADA =================

class SistemaCaminoMinimoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Camino Mínimo - Matemática Computacional (Sección 3215)")
        self.root.geometry("1220x740")
        self.root.configure(bg="#f4f6f9")

        self.n = 6
        self.matriz = np.zeros((self.n, self.n), dtype=int)
        self.celdas_matriz = []

        self._construir_caratula_superior()
        self._construir_paneles_principales()
        self.accion_generar_automatica()

    def _construir_caratula_superior(self):
        """Encabezado fijo con los datos de la carátula del curso"""
        header = tk.Frame(self.root, bg="#1e293b", pady=8)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="PRIMER ENTREGABLE: APLICACIÓN DEL ALGORITMO DE DIJKSTRA EN LA SOLUCIÓN DEL PROBLEMA DE CAMINO MÍNIMO",
            fg="white", bg="#1e293b", font=("sans-serif", 11, "bold")
        ).pack()

        tk.Label(
            header,
            text="Curso: MATEMÁTICA COMPUTACIONAL   |   Profesor: Antonio Marcos Medina Martinez   |   Sección: 3215",
            fg="#cbd5e1", bg="#1e293b", font=("sans-serif", 9)
        ).pack()

    def _construir_paneles_principales(self):
        contenedor = tk.Frame(self.root, bg="#f4f6f9")
        contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel Izquierdo: Controles, Matriz y Resultados
        panel_izq = tk.Frame(contenedor, bg="#ffffff", bd=1, relief=tk.SOLID, padx=12, pady=10)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 1. Configuración de N
        lbl_paso1 = tk.LabelFrame(panel_izq, text=" 1. Número de Vértices (5 - 15) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso1.pack(fill=tk.X, pady=(0, 8))

        tk.Label(lbl_paso1, text="Vértices (n):", bg="#ffffff").pack(side=tk.LEFT)
        self.var_n = tk.StringVar(value="6")
        spin_n = tk.Spinbox(lbl_paso1, from_=5, to=15, textvariable=self.var_n, width=5, font=("sans-serif", 10))
        spin_n.pack(side=tk.LEFT, padx=8)

        tk.Button(
            lbl_paso1, text="Generar Automática", bg="#2563eb", fg="white",
            relief=tk.FLAT, padx=8, command=self.accion_generar_automatica
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            lbl_paso1, text="Matriz Manual (En 0)", bg="#475569", fg="white",
            relief=tk.FLAT, padx=8, command=self.accion_preparar_manual
        ).pack(side=tk.LEFT, padx=4)

        # 2. Tabla interactiva de la Matriz de Adyacencia
        lbl_paso2 = tk.LabelFrame(panel_izq, text=" 2. Matriz de Adyacencia (Editable) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso2.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        tk.Label(
            lbl_paso2,
            text="Puedes editar los pesos (>= 0) y pulsar 'Aplicar cambios de matriz':",
            bg="#ffffff", fg="#475569", font=("sans-serif", 8)
        ).pack(anchor="w")

        self.frame_tabla = tk.Frame(lbl_paso2, bg="#ffffff")
        self.frame_tabla.pack(pady=6)

        tk.Button(
            lbl_paso2, text="Aplicar cambios de matriz al Grafo", bg="#0d9488", fg="white",
            relief=tk.FLAT, pady=4, command=self.accion_leer_matriz_manual
        ).pack(fill=tk.X, pady=(4, 0))

        # 3. Selección de Origen y Destino (Dijkstra)
        lbl_paso3 = tk.LabelFrame(panel_izq, text=" 3. Cálculo de Camino Mínimo (Dijkstra) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso3.pack(fill=tk.X, pady=(0, 8))

        fila_nodos = tk.Frame(lbl_paso3, bg="#ffffff")
        fila_nodos.pack(fill=tk.X, pady=4)

        tk.Label(fila_nodos, text="Origen:", bg="#ffffff").pack(side=tk.LEFT)
        self.combo_origen = ttk.Combobox(fila_nodos, width=5, state="readonly")
        self.combo_origen.pack(side=tk.LEFT, padx=(4, 15))

        tk.Label(fila_nodos, text="Destino:", bg="#ffffff").pack(side=tk.LEFT)
        self.combo_destino = ttk.Combobox(fila_nodos, width=5, state="readonly")
        self.combo_destino.pack(side=tk.LEFT, padx=4)

        tk.Button(
             fila_nodos, text="Calcular Camino Mínimo", bg="#16a34a", fg="white",
             font=("sans-serif", 9, "bold"), relief=tk.FLAT, padx=10,
             command=self.accion_calcular_dijkstra
        ).pack(side=tk.RIGHT)

        # 4. Cuadro de Resultados
        lbl_paso4 = tk.LabelFrame(panel_izq, text=" 4. Resultado del Recorrido ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso4.pack(fill=tk.X)

        self.lbl_resultado = tk.Label(
            lbl_paso4, text="Seleccione origen y destino para calcular.",
            bg="#f8fafc", fg="#0f172a", font=("monospace", 9),
            justify=tk.LEFT, anchor="w", padx=8, pady=8, relief=tk.SUNKEN
        )
        self.lbl_resultado.pack(fill=tk.X)

        # Panel Derecho: Grafo integrado en la misma ventana
        panel_der = tk.Frame(contenedor, bg="#ffffff", bd=1, relief=tk.SOLID)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(7, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=panel_der)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ================= MÉTODOS DE CONTROL =================

    def _validar_n_interfaz(self):
        try:
            n = int(self.var_n.get())
            if 5 <= n <= 15:
                return n
            messagebox.showerror("Error de validación", "El valor de n debe estar estrictamente entre 5 y 15.")
            return None
        except ValueError:
            messagebox.showerror("Error de validación", "Por favor, ingrese un número entero válido para n.")
            return None

    def _reconstruir_tabla_matriz(self):
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()

        self.celdas_matriz = []
        # Encabezados de columna
        for j in range(self.n):
            tk.Label(self.frame_tabla, text=str(j), bg="#e2e8f0", width=3, font=("sans-serif", 8, "bold")).grid(row=0, column=j+1, padx=1, pady=1)

        for i in range(self.n):
            # Encabezado de fila
            tk.Label(self.frame_tabla, text=str(i), bg="#e2e8f0", width=3, font=("sans-serif", 8, "bold")).grid(row=i+1, column=0, padx=1, pady=1)
            fila_entries = []
            for j in range(self.n):
                e = tk.Entry(self.frame_tabla, width=3, justify="center", font=("sans-serif", 8))
                e.grid(row=i+1, column=j+1, padx=1, pady=1)
                e.insert(0, str(self.matriz[i][j]))
                if i == j:
                    e.config(state="disabled", disabledbackground="#cbd5e1")
                else:
                    # Sincronizar automáticamente (i, j) con (j, i) al escribir
                    e.bind("<KeyRelease>", lambda event, r=i, c=j: self._sincronizar_simetria(r, c))
                fila_entries.append(e)
            self.celdas_matriz.append(fila_entries)

        # Actualizar selectores de origen y destino
        opciones = [str(i) for i in range(self.n)]
        self.combo_origen["values"] = opciones
        self.combo_destino["values"] = opciones
        self.combo_origen.set("0")
        self.combo_destino.set(str(self.n - 1))

    def _sincronizar_simetria(self, i, j):
        valor = self.celdas_matriz[i][j].get()
        self.celdas_matriz[j][i].delete(0, tk.END)
        self.celdas_matriz[j][i].insert(0, valor)

    def accion_generar_automatica(self):
        n_val = self._validar_n_interfaz()
        if n_val is None:
            return
        self.n = n_val
        self.matriz = generar_matriz_automatica(self.n)
        self._reconstruir_tabla_matriz()
        self.lbl_resultado.config(text="Matriz automática generada.\nElija origen y destino y pulse 'Calcular Camino Mínimo'.")
        self._dibujar_grafo_en_ventana(titulo="Grafo Ponderado")

    def accion_preparar_manual(self):
        n_val = self._validar_n_interfaz()
        if n_val is None:
            return
        self.n = n_val
        self.matriz = np.zeros((self.n, self.n), dtype=int)
        self._reconstruir_tabla_matriz()
        self.lbl_resultado.config(text="Matriz reiniciada en 0.\nIngrese los pesos en la tabla y pulse 'Aplicar cambios'.")
        self._dibujar_grafo_en_ventana(titulo="Grafo Ponderado (Ingreso Manual)")

    def accion_leer_matriz_manual(self):
        nueva_matriz = np.zeros((self.n, self.n), dtype=int)
        try:
            for i in range(self.n):
                for j in range(i + 1, self.n):
                    texto = self.celdas_matriz[i][j].get().strip()
                    peso = int(texto) if texto != "" else 0
                    if peso < 0:
                        messagebox.showerror("Error", f"El peso entre ({i}, {j}) no puede ser negativo.")
                        return False
                    nueva_matriz[i][j] = peso
                    nueva_matriz[j][i] = peso
            self.matriz = nueva_matriz
            self._reconstruir_tabla_matriz()
            self._dibujar_grafo_en_ventana(titulo="Grafo Ponderado Actualizado")
            return True
        except ValueError:
            messagebox.showerror("Error", "Todos los pesos de la matriz deben ser números enteros.")
            return False

    def accion_calcular_dijkstra(self):
        if not self.accion_leer_matriz_manual():
            return

        origen = int(self.combo_origen.get())
        destino = int(self.combo_destino.get())

        camino, costo = dijkstra(self.matriz, origen, destino, self.n)

        if camino:
            secuencia_str = " -> ".join(map(str, camino))
            self.lbl_resultado.config(
                text=f"Secuencia de vértices: {camino}\nRuta: {secuencia_str}\nCosto total del recorrido: S/{costo}"
            )
            self._dibujar_grafo_en_ventana(
                camino=camino,
                titulo=f"Camino mínimo {origen} --> {destino}  |  Costo: S/{costo}"
            )
        else:
            self.lbl_resultado.config(
                text=f"No existe un camino posible entre los vértices {origen} y {destino}."
            )
            self._dibujar_grafo_en_ventana(titulo="Grafo Ponderado (Sin camino disponible)")

    def _dibujar_grafo_en_ventana(self, camino=None, titulo="Grafo Ponderado"):
        """Dibuja el grafo directamente en el lienzo derecho sin abrir otra ventana"""
        self.ax.clear()

        G = nx.Graph()
        for i in range(self.n):
            G.add_node(i)
            for j in range(i + 1, self.n):
                if self.matriz[i][j] > 0:
                    G.add_edge(i, j, weight=int(self.matriz[i][j]))

        pos = nx.spring_layout(G, seed=42)

        # Dibujar nodos y aristas base
        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color='lightblue', node_size=650)
        nx.draw_networkx_edges(G, pos, ax=self.ax, edge_color='#64748b', width=1.5)
        nx.draw_networkx_labels(G, pos, ax=self.ax, font_weight='bold', font_size=10)

        edge_labels = nx.get_edge_attributes(G, 'weight')
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=self.ax, font_size=9)

        # Resaltar el camino mínimo si existe
        if camino and len(camino) >= 1:
            if len(camino) > 1:
                edges_camino = [(camino[i], camino[i + 1]) for i in range(len(camino) - 1)]
                nx.draw_networkx_edges(G, pos, edgelist=edges_camino, ax=self.ax, edge_color='red', width=2.8)
            nx.draw_networkx_nodes(G, pos, nodelist=camino, ax=self.ax, node_color='lightgreen', node_size=650)

        self.ax.set_title(titulo, fontsize=13, fontweight='bold', pad=12)
        self.ax.axis('off')
        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaCaminoMinimoApp(root)
    root.mainloop()