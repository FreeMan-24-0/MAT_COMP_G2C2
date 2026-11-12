import random
import heapq
import numpy as np
import networkx as nx
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ================= LÓGICA DE RED VIAL (CALLES Y ROTONDA) =================

def grado_total_nodo(matriz, nodo, dirigido=True):
    """
    Cuenta cuántos caminos (aristas) tocan a un nodo en total.
    En grafo orientado: suma de calles que entran + calles que salen.
    """
    n = len(matriz)
    if dirigido:
        salidas = sum(1 for j in range(n) if j != nodo and matriz[nodo][j] > 0)
        entradas = sum(1 for i in range(n) if i != nodo and matriz[i][nodo] > 0)
        return salidas + entradas
    else:
        return sum(1 for j in range(n) if j != nodo and matriz[nodo][j] > 0)


def generar_matriz_calles_y_rotonda(n, dirigido=True):
    """
    Genera una red vial donde:
    - Cada intersección normal tiene como MÁXIMO 4 caminos en total.
    - Exactamente 1 nodo central actúa como ROTONDA con 5 o 6 caminos.
    - Los pesos representan distancias en metros (A -> B).
    """
    matriz = np.zeros((n, n), dtype=int)
    rotonda = n // 2
    meta_rotonda = random.choice([5, 6])

    limites = {i: 4 for i in range(n)}
    limites[rotonda] = meta_rotonda

    def puede_conectar(u, v, permitir_doble_via=False):
        if u == v or matriz[u][v] > 0:
            return False
        if not permitir_doble_via and matriz[v][u] > 0:
            return False
        if grado_total_nodo(matriz, u, dirigido) >= limites[u]:
            return False
        if grado_total_nodo(matriz, v, dirigido) >= limites[v]:
            return False
        return True

    def agregar_calle(u, v):
        metros = random.randint(5, 50)
        matriz[u][v] = metros
        if not dirigido:
            matriz[v][u] = metros

    # 1. Crear ruta arterial base (0 -> 1 -> 2 -> ... -> n-1) para asegurar conectividad
    for i in range(n - 1):
        agregar_calle(i, i + 1)

    # 2. Conectar la ROTONDA hasta que alcance 5 o 6 caminos
    vecinos_ordenados = sorted(
        [i for i in range(n) if i != rotonda],
        key=lambda x: abs(x - rotonda)
    )
    for vecino in vecinos_ordenados:
        if grado_total_nodo(matriz, rotonda, dirigido) >= meta_rotonda:
            break
        u, v = (vecino, rotonda) if vecino < rotonda else (rotonda, vecino)
        if puede_conectar(u, v, permitir_doble_via=False):
            agregar_calle(u, v)
        elif puede_conectar(v, u, permitir_doble_via=False):
            agregar_calle(v, u)

    if dirigido and grado_total_nodo(matriz, rotonda, dirigido) < 5:
        for vecino in vecinos_ordenados:
            if grado_total_nodo(matriz, rotonda, dirigido) >= 5:
                break
            if puede_conectar(rotonda, vecino, permitir_doble_via=True):
                agregar_calle(rotonda, vecino)
            elif puede_conectar(vecino, rotonda, permitir_doble_via=True):
                agregar_calle(vecino, rotonda)

    # 3. Completar intersecciones normales hasta un máximo estricto de 3 o 4 calles
    for i in range(n):
        if i == rotonda:
            continue
        tope_local = random.choice([3, 4])
        candidatos = [j for j in range(n) if j != i and 1 <= abs(j - i) <= 4]
        random.shuffle(candidatos)
        for j in candidatos:
            if grado_total_nodo(matriz, i, dirigido) >= min(tope_local, limites[i]):
                break
            u, v = (i, j) if i < j or random.random() < 0.7 else (j, i)
            if puede_conectar(u, v, permitir_doble_via=False):
                agregar_calle(u, v)

    return matriz, rotonda


def dijkstra(matriz, origen, destino, n):
    """Encuentra el camino de menor distancia (en metros) usando cola de prioridad."""
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


# ================= INTERFAZ GRÁFICA EN UNA SOLA VENTANA =================

class SistemaCaminoMinimoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Red Vial y Camino Mínimo (Dijkstra) - Matemática Computacional (Sección 3215)")
        self.root.geometry("1280x780")
        self.root.configure(bg="#f4f6f9")

        self.n = 10
        self.rotonda = self.n // 2
        self.matriz = np.zeros((self.n, self.n), dtype=int)
        self.celdas_matriz = []
        self.pos = {}
        self.nodo_arrastrado = None
        self.ultimo_camino = None
        self.ultimo_titulo = "Mapa Vial Ponderado (Distancia en metros)"

        self._construir_caratula_superior()
        self._construir_paneles_principales()
        self.accion_generar_automatica()

    def _construir_caratula_superior(self):
        header = tk.Frame(self.root, bg="#1e293b", pady=7)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="PRIMER ENTREGABLE: APLICACIÓN DEL ALGORITMO DE DIJKSTRA EN RUTAS VIALES (DISTANCIA EN METROS)",
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

        # 1. Configuración
        lbl_paso1 = tk.LabelFrame(panel_izq, text=" 1. Configuración de Intersecciones (5 - 15) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso1.pack(fill=tk.X, pady=(0, 6))

        fila_top = tk.Frame(lbl_paso1, bg="#ffffff")
        fila_top.pack(fill=tk.X, pady=(0, 4))

        tk.Label(fila_top, text="Nodos (n):", bg="#ffffff").pack(side=tk.LEFT)
        self.var_n = tk.StringVar(value="10")
        spin_n = tk.Spinbox(fila_top, from_=5, to=15, textvariable=self.var_n, width=4, font=("sans-serif", 10))
        spin_n.pack(side=tk.LEFT, padx=6)

        tk.Button(
            fila_top, text="Generar Red Vial", bg="#2563eb", fg="white",
            relief=tk.FLAT, padx=8, command=self.accion_generar_automatica
        ).pack(side=tk.LEFT, padx=3)

        tk.Button(
            fila_top, text="Matriz en 0 (Manual)", bg="#475569", fg="white",
            relief=tk.FLAT, padx=8, command=self.accion_preparar_manual
        ).pack(side=tk.LEFT, padx=3)

        fila_opciones = tk.Frame(lbl_paso1, bg="#ffffff")
        fila_opciones.pack(fill=tk.X, pady=(4, 0))

        self.var_dirigido = tk.BooleanVar(value=True)
        tk.Checkbutton(
            fila_opciones, text="Calles Orientadas (A -> B)", variable=self.var_dirigido,
            bg="#ffffff", command=self.accion_cambiar_diseno
        ).pack(side=tk.LEFT)

        tk.Label(fila_opciones, text="  Diseño:", bg="#ffffff").pack(side=tk.LEFT, padx=(6, 2))
        self.combo_layout = ttk.Combobox(
            fila_opciones,
            values=["Red Vial (Capas)", "Kamada-Kawai", "Circular (Anillo)", "Fuerzas (Spring)"],
            state="readonly", width=15
        )
        self.combo_layout.set("Red Vial (Capas)")
        self.combo_layout.pack(side=tk.LEFT)
        self.combo_layout.bind("<<ComboboxSelected>>", lambda e: self.accion_recalcular_posiciones())

        # 2. Matriz de Adyacencia
        lbl_paso2 = tk.LabelFrame(panel_izq, text=" 2. Matriz de Distancias en Metros (Editable) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso2.pack(fill=tk.BOTH, expand=True, pady=(0, 6))

        tk.Label(
            lbl_paso2,
            text="Límite: Máx. 4 calles por cruce normal | 1 Rotonda (5 a 6 calles):",
            bg="#ffffff", fg="#b45309", font=("sans-serif", 8, "bold")
        ).pack(anchor="w")

        self.frame_tabla = tk.Frame(lbl_paso2, bg="#ffffff")
        self.frame_tabla.pack(pady=4)

        tk.Button(
            lbl_paso2, text="Validar Límites y Actualizar Mapa", bg="#0d9488", fg="white",
            relief=tk.FLAT, pady=4, command=self.accion_leer_matriz_manual
        ).pack(fill=tk.X, pady=(4, 0))

        # 3. Cálculo Dijkstra
        lbl_paso3 = tk.LabelFrame(panel_izq, text=" 3. Cálculo de Ruta Más Corta (Dijkstra) ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
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
            fila_nodos, text="Calcular Ruta Mínima", bg="#16a34a", fg="white",
            font=("sans-serif", 9, "bold"), relief=tk.FLAT, padx=8,
            command=self.accion_calcular_dijkstra
        ).pack(side=tk.RIGHT)

        # 4. Resultado y Conclusión
        lbl_paso4 = tk.LabelFrame(panel_izq, text=" 4. Resultado y Conclusión del Recorrido ", bg="#ffffff", font=("sans-serif", 9, "bold"), padx=8, pady=6)
        lbl_paso4.pack(fill=tk.X)

        self.lbl_resultado = tk.Label(
            lbl_paso4,
            text="Seleccione origen y destino para calcular la distancia mínima.",
            bg="#f8fafc", fg="#0f172a", font=("sans-serif", 9),
            justify=tk.LEFT, anchor="w", wraplength=410,
            padx=8, pady=8, relief=tk.SUNKEN
        )
        self.lbl_resultado.pack(fill=tk.X)

        # Panel Derecho: Mapa Vial
        panel_der = tk.Frame(contenedor, bg="#ffffff", bd=1, relief=tk.SOLID)
        panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        barra_ayuda = tk.Frame(panel_der, bg="#e2e8f0", pady=4, padx=10)
        barra_ayuda.pack(fill=tk.X)
        tk.Label(
            barra_ayuda,
            text="Celeste = Cruce (Máx. 4 calles)  |  Ámbar = Rotonda (5-6 calles)  |  Verde/Rojo = Ruta Más Corta  |  Arrastra nodos con el mouse",
            bg="#e2e8f0", fg="#1e293b", font=("sans-serif", 8, "bold")
        ).pack(side=tk.LEFT)

        tk.Button(
            barra_ayuda, text="Ver Mapa Completo", bg="#64748b", fg="white",
            font=("sans-serif", 8), relief=tk.FLAT, padx=6,
            command=lambda: self._dibujar_grafo_en_ventana(camino=None, titulo="Mapa Vial Ponderado (Distancia en metros)", recalcular_pos=False)
        ).pack(side=tk.RIGHT)

        self.fig = Figure(figsize=(7.5, 6.2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=panel_der)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.canvas.mpl_connect("button_press_event", self._on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self.canvas.mpl_connect("button_release_event", self._on_mouse_release)

    # ================= DISPOSICIÓN ESPACIAL SIN SUPERPOSICIÓN VERTICAL =================

    def _calcular_layout(self, G):
        modo = self.combo_layout.get()
        if modo == "Red Vial (Capas)":
            columnas = 4 if self.n <= 10 else 5
            tam_col = int(np.ceil(self.n / columnas))
            pos = {}
            for i in range(self.n):
                col = i // tam_col
                fila_en_col = i % tam_col
                x = col * 1.3 + (0.22 if fila_en_col % 2 == 1 else -0.15)
                y = -fila_en_col * 1.1 + (col % 2) * 0.25
                pos[i] = np.array([x, y], dtype=float)
            return pos
        elif modo == "Circular (Anillo)":
            return nx.circular_layout(G)
        elif modo == "Kamada-Kawai":
            return nx.kamada_kawai_layout(G)
        else:
            return nx.spring_layout(G, seed=42, k=1.8 / np.sqrt(self.n), iterations=120)

    def _crear_objeto_grafo(self):
        G = nx.DiGraph() if self.var_dirigido.get() else nx.Graph()
        for i in range(self.n):
            G.add_node(i)
        for i in range(self.n):
            for j in range(self.n):
                if i != j and self.matriz[i][j] > 0:
                    G.add_edge(i, j, weight=int(self.matriz[i][j]))
        return G

    # ================= DRAG & DROP DE NODOS =================

    def _on_mouse_press(self, event):
        if event.inaxes != self.ax or not self.pos:
            return
        xs = [c[0] for c in self.pos.values()]
        rango = (max(xs) - min(xs)) if len(xs) > 1 else 1.0
        umbral = max(0.12, rango * 0.06)
        seleccionado = None
        for nodo, (x, y) in self.pos.items():
            dist = np.hypot(event.xdata - x, event.ydata - y)
            if dist < umbral:
                umbral = dist
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

    # ================= CONTROL Y VALIDACIÓN DE LÍMITES =================

    def _validar_n_interfaz(self):
        try:
            n = int(self.var_n.get())
            if 5 <= n <= 15:
                return n
            messagebox.showerror("Error", "El número de intersecciones (n) debe estar entre 5 y 15.")
            return None
        except ValueError:
            messagebox.showerror("Error", "Ingrese un número entero válido.")
            return None

    def _resumen_grados_texto(self):
        es_dir = self.var_dirigido.get()
        grados = [grado_total_nodo(self.matriz, i, es_dir) for i in range(self.n)]
        rotondas = [i for i, g in enumerate(grados) if g >= 5]
        rot_str = ", ".join([f"Nodo {r} ({grados[r]} calles)" for r in rotondas]) if rotondas else "Ninguna (>4)"
        max_normal = max([g for i, g in enumerate(grados) if i not in rotondas], default=0)
        return f"Rotonda: {rot_str}  |  Máx. calles por cruce normal: {max_normal}/4"

    def _reconstruir_tabla_matriz(self):
        for widget in self.frame_tabla.winfo_children():
            widget.destroy()

        self.celdas_matriz = []
        for j in range(self.n):
            color_cab = "#fde68a" if j == self.rotonda else "#e2e8f0"
            tk.Label(self.frame_tabla, text=str(j), bg=color_cab, width=3, font=("sans-serif", 8, "bold")).grid(row=0, column=j + 1, padx=1, pady=1)

        for i in range(self.n):
            color_cab = "#fde68a" if i == self.rotonda else "#e2e8f0"
            tk.Label(self.frame_tabla, text=str(i), bg=color_cab, width=3, font=("sans-serif", 8, "bold")).grid(row=i + 1, column=0, padx=1, pady=1)
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
        self.matriz, self.rotonda = generar_matriz_calles_y_rotonda(self.n, dirigido=self.var_dirigido.get())
        self._reconstruir_tabla_matriz()
        self.lbl_resultado.config(
            text=f"Red vial generada con éxito.\n{self._resumen_grados_texto()}\n"
                 f"Elija el nodo de origen y destino para calcular la ruta más corta en metros."
        )
        self._dibujar_grafo_en_ventana(camino=None, titulo="Mapa Vial Ponderado (Distancia en metros)", recalcular_pos=True)

    def accion_preparar_manual(self):
        n_val = self._validar_n_interfaz()
        if n_val is None:
            return
        self.n = n_val
        self.rotonda = self.n // 2
        self.matriz = np.zeros((self.n, self.n), dtype=int)
        self._reconstruir_tabla_matriz()
        self.lbl_resultado.config(
            text=f"Matriz en 0. Nodo {self.rotonda} sugerido como rotonda (hasta 6 calles).\nDemás intersecciones: máx. 4 calles."
        )
        self._dibujar_grafo_en_ventana(camino=None, titulo="Mapa Vial (Ingreso Manual en metros)", recalcular_pos=True)

    def accion_cambiar_diseno(self):
        self._dibujar_grafo_en_ventana(camino=self.ultimo_camino, titulo=self.ultimo_titulo, recalcular_pos=False)

    def accion_recalcular_posiciones(self):
        self._dibujar_grafo_en_ventana(camino=self.ultimo_camino, titulo=self.ultimo_titulo, recalcular_pos=True)

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
                        messagebox.showerror("Error", f"La distancia entre ({i}, {j}) no puede ser negativa.")
                        return False
                    nueva_matriz[i][j] = peso

            es_dir = self.var_dirigido.get()
            grados = [grado_total_nodo(nueva_matriz, i, es_dir) for i in range(self.n)]
            excedidos_6 = [i for i, g in enumerate(grados) if g > 6]
            nodos_rotonda = [i for i, g in enumerate(grados) if 5 <= g <= 6]

            if excedidos_6:
                messagebox.showerror(
                    "Límite vial excedido",
                    f"El nodo {excedidos_6[0]} tiene {grados[excedidos_6[0]]} caminos.\n"
                    "Ninguna rotonda puede superar los 6 caminos."
                )
                return False

            if len(nodos_rotonda) > 2:
                messagebox.showerror(
                    "Demasiadas rotondas",
                    f"Los nodos {nodos_rotonda} tienen más de 4 caminos.\n"
                    "Solo se permite 1 o 2 rotondas (5-6 caminos); las demás intersecciones deben tener máximo 4."
                )
                return False

            if nodos_rotonda:
                self.rotonda = nodos_rotonda[0]

            self.matriz = nueva_matriz
            self.lbl_resultado.config(text=f"Mapa actualizado.\n{self._resumen_grados_texto()}")
            self._dibujar_grafo_en_ventana(camino=None, titulo="Mapa Vial Actualizado (Distancia en metros)", recalcular_pos=False)
            return True
        except ValueError:
            messagebox.showerror("Error", "Todas las distancias deben ser números enteros (metros).")
            return False

    def accion_calcular_dijkstra(self):
        if not self.accion_leer_matriz_manual():
            return

        origen = int(self.combo_origen.get())
        destino = int(self.combo_destino.get())

        camino, distancia_total = dijkstra(self.matriz, origen, destino, self.n)

        if camino:
            secuencia_str = " -> ".join(map(str, camino))
            paso_rotonda = f" (Pasa por Rotonda {self.rotonda})" if self.rotonda in camino else ""

            # Formatear lista de nodos en texto natural (ej: "0, 3, 5 y 9")
            if len(camino) > 1:
                nodos_prosa = ", ".join(map(str, camino[:-1])) + f" y {camino[-1]}"
                tramos = [f"{camino[i]}→{camino[i+1]} ({self.matriz[camino[i]][camino[i+1]]}m)" for i in range(len(camino) - 1)]
                desglose_tramos = " + ".join(tramos)
            else:
                nodos_prosa = str(camino[0])
                desglose_tramos = "0m (Mismo nodo)"

            mensaje_conclusion = (
                f"Secuencia óptima: {secuencia_str}{paso_rotonda}\n"
                f"Tramos: {desglose_tramos}\n"
                f"Distancia total: {distancia_total} metros\n\n"
                f"Conclusión: Si se toma el recorrido pasando por los nodos {nodos_prosa}, "
                f"se llega a la conclusión de que, al recorrer una distancia total de {distancia_total} metros "
                f"(la menor medida posible), esta es la ruta más corta y la más óptima para ir del nodo {origen} al nodo {destino}."
            )

            self.lbl_resultado.config(text=mensaje_conclusion)
            self._dibujar_grafo_en_ventana(
                camino=camino,
                titulo=f"Ruta más corta y óptima: {origen} --> {destino}  |  Distancia: {distancia_total} metros",
                recalcular_pos=False
            )
        else:
            self.lbl_resultado.config(
                text=f"Conclusión: No existe una ruta vial conectada que permita ir desde el nodo {origen} hasta el nodo {destino}."
            )
            self._dibujar_grafo_en_ventana(
                camino=None, titulo="Mapa Vial (Sin ruta disponible)", recalcular_pos=False
            )

    # ================= DIBUJO DEL GRAFO Y ETIQUETAS SOBRE CURVAS =================

    def _dibujar_etiquetas_curvas(self, G, edges_a_etiquetar, rad, es_camino=False):
        """
        Coloca la distancia en metros exactamente sobre la curva de cada flecha
        para que dos calles nunca superpongan sus números.
        """
        pesos = nx.get_edge_attributes(G, "weight")
        for (u, v) in edges_a_etiquetar:
            if (u, v) not in pesos:
                continue
            p1 = np.array(self.pos[u], dtype=float)
            p2 = np.array(self.pos[v], dtype=float)
            delta = p2 - p1
            dist = np.linalg.norm(delta)
            if dist == 0:
                continue

            t = 0.38
            punto_recto = p1 + t * delta
            normal = np.array([delta[1], -delta[0]]) / dist
            desplazamiento = normal * (rad * dist * 0.48)
            pos_etiqueta = punto_recto + desplazamiento

            texto = f"{pesos[(u, v)]}m"
            if es_camino:
                self.ax.text(
                    pos_etiqueta[0], pos_etiqueta[1], texto,
                    fontsize=8.5, fontweight="bold", color="#b91c1c",
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.2", fc="#fef2f2", ec="#dc2626", lw=1.0, alpha=0.95)
                )
            else:
                self.ax.text(
                    pos_etiqueta[0], pos_etiqueta[1], texto,
                    fontsize=7.8, fontweight="bold", color="#1e293b",
                    ha="center", va="center",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="#cbd5e1", lw=0.6, alpha=0.88)
                )

    def _dibujar_grafo_en_ventana(self, camino=None, titulo="Mapa Vial Ponderado", recalcular_pos=True):
        self.ax.clear()
        self.ultimo_camino = camino
        self.ultimo_titulo = titulo

        G = self._crear_objeto_grafo()
        if recalcular_pos or len(self.pos) != self.n:
            self.pos = self._calcular_layout(G)

        es_dirigido = self.var_dirigido.get()
        rad_curva = 0.16 if es_dirigido else 0.0
        estilo_arco = f"arc3,rad={rad_curva}"

        edges_camino = []
        if camino and len(camino) > 1:
            edges_camino = [(camino[i], camino[i + 1]) for i in range(len(camino) - 1)]

        aristas_secundarias = [
            e for e in G.edges()
            if e not in edges_camino and (es_dirigido or (e[1], e[0]) not in edges_camino)
        ]
        opacidad_base = 0.22 if edges_camino else 0.80

        # 1. Dibujar calles secundarias
        nx.draw_networkx_edges(
            G, self.pos, edgelist=aristas_secundarias, ax=self.ax,
            edge_color="#64748b", width=1.4, alpha=opacidad_base,
            arrows=es_dirigido, arrowstyle="-|>", arrowsize=15,
            connectionstyle=estilo_arco, node_size=650
        )

        # 2. Clasificar nodos: Intersecciones normales vs Rotonda(s) (>=5 caminos) vs Camino mínimo
        grados = {i: grado_total_nodo(self.matriz, i, es_dirigido) for i in range(self.n)}
        nodos_rotonda = [i for i in G.nodes() if (grados[i] >= 5 or i == self.rotonda) and (not camino or i not in camino)]
        nodos_normales = [i for i in G.nodes() if i not in nodos_rotonda and (not camino or i not in camino)]

        nx.draw_networkx_nodes(
            G, self.pos, nodelist=nodos_normales, ax=self.ax,
            node_color="#bae6fd", edgecolors="#0284c7", linewidths=1.5,
            node_size=600, alpha=0.55 if edges_camino else 1.0
        )

        if nodos_rotonda:
            nx.draw_networkx_nodes(
                G, self.pos, nodelist=nodos_rotonda, ax=self.ax,
                node_color="#fde047", edgecolors="#b45309", linewidths=2.2,
                node_size=760, alpha=0.75 if edges_camino else 1.0
            )

        # 3. Dibujar ruta mínima si está activa
        if camino:
            nx.draw_networkx_nodes(
                G, self.pos, nodelist=camino, ax=self.ax,
                node_color="#4ade80", edgecolors="#15803d", linewidths=2.3, node_size=700
            )
            if edges_camino:
                nx.draw_networkx_edges(
                    G, self.pos, edgelist=edges_camino, ax=self.ax,
                    edge_color="#dc2626", width=2.8,
                    arrows=es_dirigido, arrowstyle="-|>", arrowsize=20,
                    connectionstyle=estilo_arco, node_size=700
                )

        nx.draw_networkx_labels(G, self.pos, ax=self.ax, font_weight="bold", font_size=9)

        # 4. Dibujar etiquetas de metros siguiendo la curva real de cada flecha
        if edges_camino:
            self._dibujar_etiquetas_curvas(G, edges_camino, rad_curva, es_camino=True)
        else:
            self._dibujar_etiquetas_curvas(G, list(G.edges()), rad_curva, es_camino=False)

        self.ax.set_title(titulo, fontsize=12, fontweight="bold", pad=10)
        self.ax.axis("off")
        self.fig.tight_layout()
        self.canvas.draw_idle()


if __name__ == "__main__":
    root = tk.Tk()
    app = SistemaCaminoMinimoApp(root)
    root.mainloop()