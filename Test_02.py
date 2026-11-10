import random
import heapq
import numpy as np
import networkx as nx
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ================= LÓGICA MATEMÁTICA Y ALGORITMO =================

def generar_matriz_automatica(n, dirigido=True):
    """
    Genera una matriz de adyacencia ponderada limpia y conexa.
    Evita saturar el grafo cuando n es grande (10 a 15 nodos),
    garantizando entre 2 y 3 salidas por vértice más una ruta base.
    """
    matriz = np.zeros((n, n), dtype=int)

    # 1. Garantizar al menos un flujo base conectado para que siempre sea resoluble
    nodos = list(range(n))
    for i in range(n - 1):
        peso = random.randint(5, 35)
        matriz[nodos[i]][nodos[i + 1]] = peso
        if not dirigido:
            matriz[nodos[i + 1]][nodos[i]] = peso

    # 2. Agregar conexiones adicionales controladas (2 a 3 aristas por nodo)
    max_extra = 2 if n >= 11 else 3
    for i in range(n):
        posibles = [j for j in range(n) if j != i and matriz[i][j] == 0]
        # Preferir conectar con nodos cercanos en índice para evitar cruces largos
        posibles.sort(key=lambda x: abs(x - i))
        candidatos = posibles[:min(len(posibles), 5)]
        if candidatos:
            elegidos = random.sample(candidatos, k=min(len(candidatos), random.randint(1, max_extra)))
            for j in elegidos:
                peso = random.randint(1, 50)
                matriz[i][j] = peso
                if not dirigido:
                    matriz[j][i] = peso

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
        self.root.geometry("1280x760")
        self.root.configure(bg="#f4f6f9")

        self.n = 10
        self.matriz = np.zeros((self.n, self.n), dtype=int)
        self.celdas_matriz = []
        self.pos = {}
        self.nodo_arrastrado = None
        self.ultimo_camino = None
        self.ultimo_titulo = "Grafo Ponderado Orientado"

        self._construir_caratula_superior()
        self._construir_paneles_principales()
        self.accion_generar_automatica()

    def _construir_caratula_superior(self):
        header = tk.Frame(self.root, bg="#1e293b", pady=7)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="PRIMER ENTREGABLE: APLICACIÓN DEL ALGORITMO DE DIJKSTRA EN LA SOLUCIÓN DEL PROBLEMA DE CAMINO MÍNIMO",
            fg="white", bg="#1e293b", font=("sans-serif", 10, "bold")
        ).pack()

        tk.Label(
            header,
            text="Curso: MATEMÁTICA COMPUTACIONAL   |   Profesor: Antonio Marcos Medina Martinez   |   Sección: 3215",
            fg="#cbd5e1", bg="#1e293b", font=("sans-serif", 9)
        ).pack()

    def _construir_paneles_principales(self):
        contenedor = tk.Frame(self.root, bg="#f4f6f9")
        contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Panel Izquierdo
        panel_izq = tk.Frame(contenedor, bg="#ffffff", bd=1, relief=tk.SOLID, padx=10, pady=8)
        panel_izq.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 1. Configuración de N y Orientación
        lbl_paso1 = tk.LabelFrame(panel_izq, text=" 1. Configuración del Grafo (5 - 15) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso1.pack(fill=tk.X, pady=(0, 6))

        fila_top = tk.Frame(lbl_paso1, bg="#ffffff")
        fila_top.pack(fill=tk.X, pady=(0, 4))

        tk.Label(fila_top, text="Vértices (n):", bg="#ffffff").pack(side=tk.LEFT)
        self.var_n = tk.StringVar(value="10")
        spin_n = tk.Spinbox(fila_top, from_=5, to=15, textvariable=self.var_n, width=4, font=("sans-serif", 10))
        spin_n.pack(side=tk.LEFT, padx=6)

        tk.Button(
            fila_top, text="Generar Automática", bg="#2563eb", fg="white",
            relief=tk.FLAT, padx=8, command=self.accion_generar_automatica
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            fila_top, text="Matriz Manual (En 0)", bg="#475569", fg="white",
            relief=tk.FLAT, padx=8, command=self.accion_preparar_manual
        ).pack(side=tk.LEFT, padx=3)

        fila_opciones = tk.Frame(lbl_paso1, bg="#ffffff")
        fila_opciones.pack(fill=tk.X, pady=(4, 0))

        self.var_dirigido = tk.BooleanVar(value=True)
        tk.Checkbutton(
            fila_opciones, text="Grafo Orientado (Flechas)", variable=self.var_dirigido,
            bg="#ffffff", command=self.accion_cambiar_diseno
        ).pack(side=tk.LEFT)

        tk.Label(fila_opciones, text="  Diseño:", bg="#ffffff").pack(side=tk.LEFT, padx=(8, 2))
        self.combo_layout = ttk.Combobox(
            fila_opciones,
            values=["Capas (Izq -> Der)", "Circular (Anillo)", "Kamada-Kawai", "Fuerzas (Spring)"],
            state="readonly", width=16
        )
        self.combo_layout.set("Capas (Izq -> Der)")
        self.combo_layout.pack(side=tk.LEFT)
        self.combo_layout.bind("<<ComboboxSelected>>", lambda e: self.accion_recalcular_posiciones())

        # 2. Tabla interactiva de la Matriz
        lbl_paso2 = tk.LabelFrame(panel_izq, text=" 2. Matriz de Adyacencia (Editable) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso2.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        tk.Label(
            lbl_paso2,
            text="Filas = Origen, Columnas = Destino. Edita pesos (>= 0):",
            bg="#ffffff", fg="#475569", font=("sans-serif", 8)
        ).pack(anchor="w")

        self.frame_tabla = tk.Frame(lbl_paso2, bg="#ffffff")
        self.frame_tabla.pack(pady=4)

        tk.Button(
            lbl_paso2, text="Aplicar cambios de matriz al Grafo", bg="#0d9488", fg="white",
            relief=tk.FLAT, pady=4, command=self.accion_leer_matriz_manual
        ).pack(fill=tk.X, pady=(4, 0))

        # 3. Selección de Origen y Destino (Dijkstra)
        lbl_paso3 = tk.LabelFrame(panel_izq, text=" 3. Cálculo de Camino Mínimo (Dijkstra) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso3.pack(fill=tk.X, pady=(0, 6))

        fila_nodos = tk.Frame(lbl_paso3, bg="#ffffff")
        fila_nodos.pack(fill=tk.X, pady=2)

        tk.Label(fila_nodos, text="Origen:", bg="#ffffff").pack(side=tk.LEFT)
        self.combo_origen = ttk.Combobox(fila_nodos, width=4, state="readonly")
        self.combo_origen.pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(fila_nodos, text="Destino:", bg="#ffffff").pack(side=tk.LEFT)
        self.combo_destino = ttk.Combobox(fila_nodos, width=4, state="readonly")
        self.combo_destino.pack(side=tk.LEFT, padx=(4, 10))

        tk.Button(
            fila_nodos, text="Calcular Camino Mínimo", bg="#16a34a", fg="white",
            font=("sans-serif", 9, "bold"), relief=tk.FLAT, padx=8,
            command=self.accion_calcular_dijkstra
        ).pack(side=tk.RIGHT)

        # 4. Cuadro de Resultados
        lbl_paso4 = tk.LabelFrame(panel_izq, text=" 4. Resultado del Recorrido ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso4.pack(fill=tk.X)

        self.lbl_resultado = tk.Label(
            lbl_paso4, text="Seleccione origen y destino para calcular.",
            bg="#f8fafc", fg="#0f172a", font=("monospace", 9),
            justify=tk.LEFT, anchor="w", padx=8, pady=6, relief=tk.SUNKEN
        )
        self.lbl_resultado.pack(fill=tk.X)

        # Panel Derecho: Grafo interactivo
        panel_der = tk.Frame(contenedor, bg="#ffffff", bd=1, relief=tk.SOLID)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        barra_ayuda = tk.Frame(panel_der, bg="#e2e8f0", pady=4, padx=10)
        barra_ayuda.pack(fill=tk.X)
        tk.Label(
            barra_ayuda,
            text="TIP INTERACTIVO: Puedes hacer clic sobre cualquier nodo azul/verde y arrastrarlo con el mouse para acomodar las flechas.",
            bg="#e2e8f0", fg="#1e293b", font=("sans-serif", 8, "bold")
        ).pack(side=tk.LEFT)

        tk.Button(
            barra_ayuda, text="Ver Grafo Completo (Quitar filtro)", bg="#64748b", fg="white",
            font=("sans-serif", 8), relief=tk.FLAT, padx=6,
            command=lambda: self._dibujar_grafo_en_ventana(camino=None, titulo="Grafo Ponderado Orientado")
        ).pack(side=tk.RIGHT)

        self.fig = Figure(figsize=(7.5, 6.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=panel_der)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Eventos para arrastrar nodos con el mouse
        self.canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self._on_mouse_release)

    # ================= CÁLCULO DE POSICIONES LIMPIAS (LAYOUTS) =================

    def _calcular_layout(self, G):
        modo = self.combo_layout.get()
        if modo == "Capas (Izq -> Der)":
            # Distribuye los nodos en columnas ordenadas de izquierda a derecha
            columnas = 4 if self.n <= 10 else 5
            for i in range(self.n):
                G.nodes[i]["layer"] = i // int(np.ceil(self.n / columnas))
            pos = nx.multipartite_layout(G, subset_key="layer", align="vertical")
            # Pequeño desfase vertical alternado para que flechas horizontales no se tapen
            for nodo, coord in pos.items():
                desfase_y = 0.08 * ((nodo % 3) - 1)
                pos[nodo] = np.array([coord[0], coord[1] + desfase_y])
            return pos
        elif modo == "Circular (Anillo)":
            return nx.circular_layout(G)
        elif modo == "Kamada-Kawai":
            return nx.kamada_kawai_layout(G)
        else:
            return nx.spring_layout(G, seed=42, k=1.6 / np.sqrt(self.n), iterations=100)

    def _crear_objeto_grafo(self):
        G = nx.DiGraph() if self.var_dirigido.get() else nx.Graph()
        for i in range(self.n):
            G.add_node(i)
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.matriz[i][j] > 0:
                    G.add_edge(i, j, weight=int(self.matriz[i][j]))
        return G

    # ================= INTERACCIÓN CON EL MOUSE (DRAG & DROP) =================

    def _on_mouse_press(self, event):
        if event.inaxes != self.ax or not self.pos:
            return
        # Buscar el nodo más cercano al clic
        dist_min = 0.12
        seleccionado = None
        for nodo, (x, y) in self.pos.items():
            dist = np.hypot(event.xdata - x, event.ydata - y)
            if dist < dist_min:
                dist_min = dist
                seleccionado = nodo
        self.nodo_arrastrado = seleccionado

    def _on_mouse_move(self, event):
        if self.nodo_arrastrado is None or event.inaxes != self.ax:
            return
        if event.xdata is not None and event.ydata is not None:
            self.pos[self.nodo_arrastrado] = np.array([event.xdata, event.ydata])
            self._dibujar_grafo_en_ventana(
                camino=self.ultimo_camino, titulo=self.ultimo_titulo, recalcular_pos=False
            )

    def _on_mouse_release(self, event):
        self.nodo_arrastrado = None

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
        for j in range(self.n):
            tk.Label(self.frame_tabla, text=str(j), bg="#e2e8f0", width=3, font=("sans-serif", 8, "bold")).grid(row=0, column=j + 1, padx=1, pady=1)

        for i in range(self.n):
            tk.Label(self.frame_tabla, text=str(i), bg="#e2e8f0", width=3, font=("sans-serif", 8, "bold")).grid(row=i + 1, column=0, padx=1, pady=1)
            fila_entries = []
            for j in range(self.n):
                e = tk.Entry(self.frame_tabla, width=3, justify="center", font=("sans-serif", 8))
                e.grid(row=i + 1, column=j + 1, padx=1, pady=1)
                e.insert(0, str(self.matriz[i][j]))
                if i == j:
                    e.config(state="disabled", disabledbackground="#cbd5e1")
                else:
                    e.bind("<KeyRelease>", lambda event, r=i, c=j: self._sincronizar_si_no_dirigido(r, c))
                fila_entries.append(e)
            self.celdas_matriz.append(fila_entries)

        opciones = [str(i) for i in range(self.n)]
        self.combo_origen["values"] = opciones
        self.combo_destino["values"] = opciones
        self.combo_origen.set("0")
        self.combo_destino.set(str(self.n - 1))

    def _sincronizar_si_no_dirigido(self, i, j):
        if not self.var_dirigido.get():
            valor = self.celdas_matriz[i][j].get()
            self.celdas_matriz[j][i].delete(0, tk.END)
            self.celdas_matriz[j][i].insert(0, valor)

    def accion_generar_automatica(self):
        n_val = self._validar_n_interfaz()
        if n_val is None:
            return
        self.n = n_val
        self.matriz = generar_matriz_automatica(self.n, dirigido=self.var_dirigido.get())
        self._reconstruir_tabla_matriz()
        self.lbl_resultado.config(text="Matriz generada con densidad limpia.\nElija origen y destino y pulse 'Calcular Camino Mínimo'.")
        self._dibujar_grafo_en_ventana(camino=None, titulo="Grafo Ponderado Orientado", recalcular_pos=True)

    def accion_preparar_manual(self):
        n_val = self._validar_n_interfaz()
        if n_val is None:
            return
        self.n = n_val
        self.matriz = np.zeros((self.n, self.n), dtype=int)
        self._reconstruir_tabla_matriz()
        self.lbl_resultado.config(text="Matriz reiniciada en 0.\nIngrese los pesos en la tabla y pulse 'Aplicar cambios'.")
        self._dibujar_grafo_en_ventana(camino=None, titulo="Grafo Ponderado (Ingreso Manual)", recalcular_pos=True)

    def accion_cambiar_diseno(self):
        self._dibujar_grafo_en_ventana(
            camino=self.ultimo_camino, titulo=self.ultimo_titulo, recalcular_pos=False
        )

    def accion_recalcular_posiciones(self):
        self._dibujar_grafo_en_ventana(
            camino=self.ultimo_camino, titulo=self.ultimo_titulo, recalcular_pos=True
        )

    def accion_leer_matriz_manual(self):
        nueva_matriz = np.zeros((self.n, self.n), dtype=int)
        try:
            for i in range(self.n):
                for j in range(self.n):
                    if i == j:
                        continue
                    texto = self.celdas_matriz[i][j].get().strip()
                    peso = int(texto) if texto != "" else 0
                    if peso < 0:
                        messagebox.showerror("Error", f"El peso en ({i}, {j}) no puede ser negativo.")
                        return False
                    nueva_matriz[i][j] = peso
            self.matriz = nueva_matriz
            self._dibujar_grafo_en_ventana(camino=None, titulo="Grafo Ponderado Actualizado", recalcular_pos=False)
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
                text=f"Secuencia: {camino}\nRuta orientada: {secuencia_str}\nCosto total del recorrido: S/{costo}"
            )
            self._dibujar_grafo_en_ventana(
                camino=camino,
                titulo=f"Camino mínimo {origen} --> {destino}  |  Costo: S/{costo}",
                recalcular_pos=False
            )
        else:
            self.lbl_resultado.config(
                text=f"No existe un camino orientado posible entre {origen} y {destino}."
            )
            self._dibujar_grafo_en_ventana(
                camino=None, titulo="Grafo Ponderado (Sin camino disponible)", recalcular_pos=False
            )

    def _dibujar_grafo_en_ventana(self, camino=None, titulo="Grafo Ponderado", recalcular_pos=True):
        self.ax.clear()
        self.ultimo_camino = camino
        self.ultimo_titulo = titulo

        G = self._crear_objeto_grafo()
        if recalcular_pos or len(self.pos) != self.n:
            self.pos = self._calcular_layout(G)

        es_dirigido = self.var_dirigido.get()
        estilo_arco = "arc3,rad=0.12" if es_dirigido else "arc3,rad=0.0"

        edges_camino = []
        if camino and len(camino) > 1:
            edges_camino = [(camino[i], camino[i + 1]) for i in range(len(camino) - 1)]

        # Si hay un camino activo, atenuamos el resto de aristas para que no estorben visualmente
        aristas_secundarias = [e for e in G.edges() if e not in edges_camino and (es_dirigido or (e[1], e[0]) not in edges_camino)]
        opacidad_base = 0.22 if edges_camino else 0.75

        # 1. Dibujar aristas base orientadas con flecha
        nx.draw_networkx_edges(
            G, self.pos, edgelist=aristas_secundarias, ax=self.ax,
            edge_color="#64748b", width=1.3, alpha=opacidad_base,
            arrows=es_dirigido, arrowstyle="-|>", arrowsize=14,
            connectionstyle=estilo_arco, node_size=600
        )

        # 2. Dibujar nodos base y nodos del camino mínimo
        nodos_normales = [n for n in G.nodes() if not camino or n not in camino]
        nx.draw_networkx_nodes(
            G, self.pos, nodelist=nodos_normales, ax=self.ax,
            node_color="lightblue", edgecolors="#334155", linewidths=1.2,
            node_size=580, alpha=0.55 if edges_camino else 1.0
        )

        if camino:
            nx.draw_networkx_nodes(
                G, self.pos, nodelist=camino, ax=self.ax,
                node_color="#4ade80", edgecolors="#14532d", linewidths=2.0, node_size=680
            )
            if edges_camino:
                nx.draw_networkx_edges(
                    G, self.pos, edgelist=edges_camino, ax=self.ax,
                    edge_color="#dc2626", width=2.8,
                    arrows=es_dirigido, arrowstyle="-|>", arrowsize=20,
                    connectionstyle=estilo_arco, node_size=680
                )

        nx.draw_networkx_labels(G, self.pos, ax=self.ax, font_weight="bold", font_size=9)

        # 3. Etiquetas de pesos desplazadas (label_pos=0.32) con caja blanca para no superponerse
        all_weights = nx.get_edge_attributes(G, "weight")
        if edges_camino:
            # Mostrar nítidos los pesos del camino mínimo y tenues los demás
            pesos_camino = {
                e: all_weights[e] for e in G.edges()
                if e in edges_camino or (not es_dirigido and (e[1], e[0]) in edges_camino)
            }
            nx.draw_networkx_edge_labels(
                G, self.pos, edge_labels=pesos_camino, ax=self.ax,
                label_pos=0.35, font_size=9, font_color="#b91c1c", font_weight="bold",
                 rotate=False, bbox=dict(boxstyle="round,pad=0.2", fc="#fef2f2", ec="#dc2626", alpha=0.95)
            )
        else:
            nx.draw_networkx_edge_labels(
                G, self.pos, edge_labels=all_weights, ax=self.ax,
                label_pos=0.33, font_size=8, font_color="#0f172a",
                rotate=False, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8)
            )

        self.ax.set_title(titulo, fontsize=12, fontweight="bold", pad=10)
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw_idle()


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaCaminoMinimoApp(root)
    root.mainloop()