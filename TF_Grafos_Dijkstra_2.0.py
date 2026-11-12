"""
TRABAJO FINAL - MATEMÁTICA COMPUTACIONAL (Sección 3215)

Aplicación con interfaz gráfica (no usa la consola) que permite:
  * Trabajar con grafos DIRIGIDOS (flechas) o BIDIRECCIONALES (no dirigidos).
  * Construir el grafo de dos formas separadas:
        - Modo AUTOMÁTICO: se genera un grafo aleatorio y conexo.
        - Modo MANUAL: se agregan aristas con formularios o haciendo
          clic en dos vértices del dibujo.
  * Ver la matriz de adyacencia ponderada.
  * Calcular los GRADOS de cada vértice:
        - Dirigido: grado de entrada g-(v), grado de salida g+(v) y total.
        - Bidireccional: grado g(v).
  * Calcular el camino mínimo entre dos vértices con Dijkstra.

Requisitos:  pip install numpy networkx matplotlib
Ejecutar:    python TF_Grafos_Dijkstra.py
"""

import heapq
import platform
import random
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import numpy as np
import networkx as nx
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # noqa: E402


# =======================CARÁTULA =======================

TITULO_TRABAJO = "TRABAJO FINAL"
TEMA = ("GRAFOS DIRIGIDOS Y BIDIRECCIONALES:\n"
        "GRADOS DE LOS VÉRTICES Y CAMINO MÍNIMO (DIJKSTRA)")
CURSO = "MATEMÁTICA COMPUTACIONAL"
PROFESOR = "Antonio Marcos Medina Martinez"
SECCION = "3215"
INTEGRANTES = ["Huachaca Quinteros Gianfranco Carlos","Ivette Lucero Villavicencio Davila", "Tarazona Muñoz, Juan Sebastian" ]  

N_MIN, N_MAX = 5, 15
PESO_MIN, PESO_MAX = 1, 999
MAX_GRADO = 5   # máximo de aristas por vértice en el modo automático

FUENTE = {"Windows": "Segoe UI", "Darwin": "Helvetica"}.get(platform.system(), "DejaVu Sans")
C_FONDO = "#f1f5f9"
C_PANEL = "#ffffff"
C_OSCURO = "#1e293b"
C_TEXTO = "#0f172a"
C_TENUE = "#64748b"
C_AZUL = "#2563eb"
C_VERDE = "#16a34a"
C_ROJO = "#dc2626"
C_NARANJA = "#ea580c"


# ======================= LÓGICA MATEMÁTICA =======================

def _construir_matriz_auto(n, dirigido, densidad, peso_min, peso_max, max_grado):
    matriz = np.zeros((n, n), dtype=int)
    grado = [0] * n                      # aristas que tocan a cada vértice (entran + salen)
    span = max(0, peso_max - peso_min)

    def agregar(u, v, w):
        matriz[u][v] = w
        if not dirigido:
            matriz[v][u] = w
        grado[u] += 1
        grado[v] += 1

    # 1. Ruta base 0 -> ... -> n-1 con los vértices intermedios en orden aleatorio.
    #    Sus pesos son bajos; en dirigido se cierra con n-1 -> 0 (alcanzable desde cualquier vértice).
    medios = list(range(1, n - 1))
    random.shuffle(medios)
    orden = [0] + medios + [n - 1]
    posicion = {v: k for k, v in enumerate(orden)}
    tope_bajo = peso_min + int(0.4 * span)
    for k in range(n - 1):
        agregar(orden[k], orden[k + 1], random.randint(peso_min, tope_bajo))
    if dirigido and n > 2:
        agregar(orden[-1], orden[0], random.randint(peso_min, tope_bajo))

    # 2. Aristas extra entre cualquier par de vértices, sin superar max_grado y
    #    sin arcos en ambos sentidos. Cuanto más "salta" una arista respecto a la
    #    ruta base, más cara es: así el camino mínimo no se reduce a 2 aristas.
    pares = [(orden[a], orden[b]) for a in range(n) for b in range(a + 2, n)]
    random.shuffle(pares)
    extra = int(round(densidad * n * (n - 1) / 2))
    for u, v in pares:
        if extra <= 0:
            break
        if matriz[u][v] or matriz[v][u]:
            continue
        if grado[u] >= max_grado or grado[v] >= max_grado:
            continue
        salto = abs(posicion[v] - posicion[u])
        piso = peso_min + int(min(0.9, 0.15 * salto) * span)
        w = random.randint(piso, peso_max)
        if dirigido and random.random() < 0.3:
            agregar(v, u, w)             # arista de retroceso
        else:
            agregar(u, v, w)
        extra -= 1
    return matriz


def generar_matriz_automatica(n, dirigido, densidad=0.25, peso_min=1, peso_max=50,
                              max_grado=MAX_GRADO):
    """Matriz ponderada aleatoria, conexa, con grado total <= max_grado por vértice.

    Se regenera hasta que el camino mínimo 0 -> n-1 tenga varios saltos.
    """
    min_saltos = max(3, n // 3)
    matriz = None
    for _ in range(300):
        matriz = _construir_matriz_auto(n, dirigido, densidad, peso_min, peso_max, max_grado)
        camino, _, _ = dijkstra(matriz, 0, n - 1)
        if len(camino) - 1 >= min_saltos:
            break
    return matriz


def simetrizar(matriz):
    """Convierte una matriz dirigida en bidireccional (toma el menor peso)."""
    n = len(matriz)
    res = np.zeros_like(matriz)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = int(matriz[i][j]), int(matriz[j][i])
            w = min(a, b) if (a and b) else (a or b)
            res[i][j] = res[j][i] = w
    return res


def lista_aristas(matriz, dirigido):
    """Devuelve [(u, v, peso)]. En bidireccional cada arista aparece una vez (u < v)."""
    n = len(matriz)
    aristas = []
    for i in range(n):
        for j in range(n):
            if i == j or matriz[i][j] <= 0:
                continue
            if dirigido or i < j:
                aristas.append((i, j, int(matriz[i][j])))
    return aristas


def calcular_grados(matriz, dirigido):
    """Calcula los grados a partir de la matriz de adyacencia.

    Dirigido:      g+(v) = nº de 1s (pesos > 0) en la fila v    (salida)
                   g-(v) = nº de 1s (pesos > 0) en la columna v (entrada)
    Bidireccional: g(v)  = nº de pesos > 0 en la fila v
    """
    ady = (np.asarray(matriz) > 0).astype(int)
    salida = ady.sum(axis=1)
    entrada = ady.sum(axis=0)
    if dirigido:
        return {"entrada": entrada, "salida": salida, "total": entrada + salida}
    return {"grado": salida}


def dijkstra(matriz, origen, destino):
    """Algoritmo de Dijkstra. Devuelve (camino, costo, distancias)."""
    n = len(matriz)
    dist = [float("inf")] * n
    padre = [None] * n
    dist[origen] = 0
    cola = [(0, origen)]
    visitado = [False] * n

    while cola:
        d, u = heapq.heappop(cola)
        if visitado[u]:
            continue
        visitado[u] = True
        for v in range(n):
            w = int(matriz[u][v])
            if w > 0 and d + w < dist[v]:
                dist[v] = d + w
                padre[v] = u
                heapq.heappush(cola, (dist[v], v))

    camino = []
    if dist[destino] != float("inf"):
        nodo = destino
        while nodo is not None:
            camino.insert(0, nodo)
            nodo = padre[nodo]
    return camino, dist[destino], dist


# ======================= ESTADO DE CADA MODO =======================

class EstadoGrafo:
    """Cada modo (automático / manual) guarda su propio grafo."""

    def __init__(self, n):
        self.n = n
        self.matriz = np.zeros((n, n), dtype=int)
        self.pos = {}
        self.camino = None
        self.titulo = None
        self.resultado = None


# ======================= WIDGET AUXILIAR =======================

class PanelDesplazable(ttk.Frame):
    """Frame con barra de desplazamiento vertical (para pantallas pequeñas)."""

    def __init__(self, padre, ancho=400, **kw):
        super().__init__(padre, **kw)
        self.canvas = tk.Canvas(self, width=ancho, bg=C_PANEL, highlightthickness=0)
        barra = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.interior = ttk.Frame(self.canvas, style="Panel.TFrame", padding=10)
        self._id = self.canvas.create_window((0, 0), window=self.interior, anchor="nw")
        self.canvas.configure(yscrollcommand=barra.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.interior.bind("<Configure>",
                           lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfigure(self._id, width=e.width))
        self.bind_all("<MouseWheel>", self._rueda, add="+")
        self.bind_all("<Button-4>", self._rueda, add="+")
        self.bind_all("<Button-5>", self._rueda, add="+")

    def _rueda(self, event):
        w = event.widget
        while w is not None:
            if w is self:
                break
            w = getattr(w, "master", None)
        if w is None:
            return
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.canvas.yview_scroll(-2, "units")
        else:
            self.canvas.yview_scroll(2, "units")


# ======================= APLICACIÓN PRINCIPAL =======================

class AplicacionGrafos:
    TAM_NODO = 620

    def __init__(self, root):
        self.root = root
        root.title("Grafos Dirigidos y Bidireccionales - Matemática Computacional (Sección 3215)")
        root.geometry("1360x800")
        root.minsize(1100, 640)
        root.configure(bg=C_FONDO)

        self.estados = {"auto": EstadoGrafo(8), "manual": EstadoGrafo(6)}
        self.modo = "auto"
        self.nodo_presionado = None
        self.punto_presion = None
        self.arrastrando = False
        self.nodo_seleccionado = None

        self._estilos()
        self._encabezado()
        self._barra_estado()
        self._cuerpo()

        self.accion_generar_automatico()

    # ---------- utilidades ----------

    @property
    def est(self):
        return self.estados[self.modo]

    def es_dirigido(self):
        return self.var_tipo.get() == "dirigido"

    def estado(self, texto):
        self.lbl_estado.config(text=texto)

    # ---------- estilos ----------

    def _estilos(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure(".", font=(FUENTE, 9), background=C_PANEL, foreground=C_TEXTO)
        s.configure("TFrame", background=C_PANEL)
        s.configure("Panel.TFrame", background=C_PANEL)
        s.configure("Fondo.TFrame", background=C_FONDO)
        s.configure("TLabel", background=C_PANEL)
        s.configure("Tenue.TLabel", foreground=C_TENUE, font=(FUENTE, 8))
        s.configure("TLabelframe", background=C_PANEL, bordercolor="#cbd5e1")
        s.configure("TLabelframe.Label", background=C_PANEL, foreground=C_OSCURO,
                    font=(FUENTE, 10, "bold"))
        s.configure("TRadiobutton", background=C_PANEL)
        s.configure("TCheckbutton", background=C_PANEL)
        s.configure("TNotebook", background=C_PANEL, borderwidth=0)
        s.configure("TNotebook.Tab", padding=(12, 5), font=(FUENTE, 9, "bold"))
        s.map("TNotebook.Tab", background=[("selected", C_PANEL)],
              foreground=[("selected", C_AZUL)])
        s.configure("Treeview", rowheight=22, font=(FUENTE, 9))
        s.configure("Treeview.Heading", font=(FUENTE, 9, "bold"))
        for nombre, color in [("Azul", C_AZUL), ("Verde", C_VERDE),
                              ("Rojo", C_ROJO), ("Gris", "#475569")]:
            s.configure(f"{nombre}.TButton", background=color, foreground="white",
                        font=(FUENTE, 9, "bold"), padding=(10, 5), borderwidth=0)
            s.map(f"{nombre}.TButton", background=[("active", C_OSCURO)])

    # ---------- encabezado ----------

    def _encabezado(self):
        h = tk.Frame(self.root, bg=C_OSCURO, pady=7)
        h.pack(fill="x")
        tk.Label(h, text=f"{TITULO_TRABAJO}: " + TEMA.replace("\n", " "),
                 fg="white", bg=C_OSCURO, font=(FUENTE, 11, "bold")).pack()
        tk.Label(h, text=f"Curso: {CURSO}   |   Profesor: {PROFESOR}   |   Sección: {SECCION}",
                 fg="#cbd5e1", bg=C_OSCURO, font=(FUENTE, 9)).pack()
        tk.Button(h, text="? Ayuda", command=self.ventana_ayuda, bg="#334155", fg="white",
                  relief="flat", activebackground=C_AZUL, font=(FUENTE, 9, "bold"),
                  padx=10).place(relx=1.0, rely=0.5, x=-12, anchor="e")

    def _barra_estado(self):
        self.lbl_estado = tk.Label(self.root, text="Listo.", anchor="w", bg="#e2e8f0",
                                   fg=C_OSCURO, font=(FUENTE, 9), padx=10, pady=3)
        self.lbl_estado.pack(fill="x", side="bottom")

    # ---------- cuerpo ----------

    def _cuerpo(self):
        cuerpo = ttk.Frame(self.root, style="Fondo.TFrame", padding=8)
        cuerpo.pack(fill="both", expand=True)

        izq = PanelDesplazable(cuerpo, ancho=390, style="Panel.TFrame")
        izq.pack(side="left", fill="y", padx=(0, 8))
        self._panel_controles(izq.interior)

        der = ttk.Frame(cuerpo, style="Panel.TFrame")
        der.pack(side="left", fill="both", expand=True)
        self._panel_resultados(der)

    def _panel_controles(self, p):
        # --- 1. Configuración ---
        f1 = ttk.LabelFrame(p, text=" 1. Configuración del grafo ", padding=8)
        f1.pack(fill="x", pady=(0, 8))

        fila = ttk.Frame(f1)
        fila.pack(fill="x", pady=(0, 6))
        ttk.Label(fila, text=f"Número de vértices n ({N_MIN} - {N_MAX}):").pack(side="left")
        self.var_n = tk.StringVar(value=str(self.estados["auto"].n))
        self.spin_n = ttk.Spinbox(fila, from_=N_MIN, to=N_MAX, textvariable=self.var_n,
                                  width=5, state="readonly", command=self.accion_cambiar_n)
        self.spin_n.pack(side="left", padx=8)

        ttk.Label(f1, text="Tipo de grafo:").pack(anchor="w")
        self.var_tipo = tk.StringVar(value="dirigido")
        ttk.Radiobutton(f1, text="Dirigido  (aristas con flecha  u → v)", value="dirigido",
                        variable=self.var_tipo, command=self.accion_cambiar_tipo).pack(anchor="w", padx=10)
        ttk.Radiobutton(f1, text="Bidireccional / no dirigido  (u ↔ v)", value="bidireccional",
                        variable=self.var_tipo, command=self.accion_cambiar_tipo).pack(anchor="w", padx=10)

        # --- 2. Método de construcción ---
        f2 = ttk.LabelFrame(p, text=" 2. Método de ingreso de datos ", padding=6)
        f2.pack(fill="x", pady=(0, 8))
        self.nb_modo = ttk.Notebook(f2)
        self.nb_modo.pack(fill="x")

        # Pestaña automática
        ta = ttk.Frame(self.nb_modo, padding=8)
        self.nb_modo.add(ta, text="  Automático  ")
        ttk.Label(ta, text="El programa genera un grafo aleatorio y conexo.",
                  style="Tenue.TLabel").pack(anchor="w", pady=(0, 6))
        fd = ttk.Frame(ta)
        fd.pack(fill="x")
        ttk.Label(fd, text="Densidad de aristas:").pack(side="left")
        self.var_densidad = tk.IntVar(value=18)
        self.lbl_densidad = ttk.Label(fd, text="18 %", width=5)
        self.lbl_densidad.pack(side="right")
        ttk.Scale(fd, from_=5, to=80, variable=self.var_densidad,
                  command=lambda v: self.lbl_densidad.config(text=f"{int(float(v))} %")
                  ).pack(side="left", fill="x", expand=True, padx=6)

        fp = ttk.Frame(ta)
        fp.pack(fill="x", pady=6)
        ttk.Label(fp, text="Pesos entre").pack(side="left")
        self.var_pmin = tk.StringVar(value="1")
        self.var_pmax = tk.StringVar(value="50")
        ttk.Spinbox(fp, from_=1, to=PESO_MAX, textvariable=self.var_pmin, width=5).pack(side="left", padx=4)
        ttk.Label(fp, text="y").pack(side="left")
        ttk.Spinbox(fp, from_=1, to=PESO_MAX, textvariable=self.var_pmax, width=5).pack(side="left", padx=4)

        ttk.Button(ta, text="⟳  Generar grafo automático", style="Azul.TButton",
                   command=self.accion_generar_automatico).pack(fill="x", pady=(4, 0))

        # Pestaña manual
        tm = ttk.Frame(self.nb_modo, padding=8)
        self.nb_modo.add(tm, text="  Manual  ")
        ttk.Label(tm, text="Elige los vértices y el peso, luego pulsa Agregar.\n"
                           "También puedes hacer clic en un vértice del dibujo\n"
                           "y luego en otro para crear la arista.",
                  style="Tenue.TLabel", justify="left").pack(anchor="w", pady=(0, 6))

        ff = ttk.Frame(tm)
        ff.pack(fill="x")
        self.lbl_desde = ttk.Label(ff, text="Desde:")
        self.lbl_desde.grid(row=0, column=0, sticky="w")
        self.cb_desde = ttk.Combobox(ff, width=4, state="readonly")
        self.cb_desde.grid(row=0, column=1, padx=(2, 8))
        self.lbl_hacia = ttk.Label(ff, text="Hacia:")
        self.lbl_hacia.grid(row=0, column=2, sticky="w")
        self.cb_hacia = ttk.Combobox(ff, width=4, state="readonly")
        self.cb_hacia.grid(row=0, column=3, padx=(2, 8))
        ttk.Label(ff, text="Peso:").grid(row=0, column=4, sticky="w")
        self.var_peso = tk.StringVar(value="10")
        sp = ttk.Spinbox(ff, from_=PESO_MIN, to=PESO_MAX, textvariable=self.var_peso, width=5)
        sp.grid(row=0, column=5, padx=2)
        sp.bind("<Return>", lambda e: self.accion_agregar_arista())

        ttk.Button(tm, text="＋  Agregar / actualizar arista", style="Verde.TButton",
                   command=self.accion_agregar_arista).pack(fill="x", pady=6)

        ft = ttk.Frame(tm)
        ft.pack(fill="x")
        self.tree_aristas = ttk.Treeview(ft, columns=("a", "b", "w"), show="headings",
                                         height=6, selectmode="browse")
        for col, txt in zip(("a", "b", "w"), ("Desde", "Hacia", "Peso")):
            self.tree_aristas.heading(col, text=txt)
            self.tree_aristas.column(col, width=80, anchor="center")
        sb = ttk.Scrollbar(ft, orient="vertical", command=self.tree_aristas.yview)
        self.tree_aristas.configure(yscrollcommand=sb.set)
        self.tree_aristas.pack(side="left", fill="x", expand=True)
        sb.pack(side="right", fill="y")
        self.tree_aristas.bind("<<TreeviewSelect>>", self._al_seleccionar_arista)

        fb = ttk.Frame(tm)
        fb.pack(fill="x", pady=(6, 0))
        ttk.Button(fb, text="Eliminar seleccionada", style="Rojo.TButton",
                   command=self.accion_eliminar_arista).pack(side="left", fill="x", expand=True, padx=(0, 3))
        ttk.Button(fb, text="Borrar todas", style="Gris.TButton",
                   command=self.accion_borrar_todas).pack(side="left", fill="x", expand=True, padx=(3, 0))

        # Carga rápida: una arista por línea con el formato "desde hasta peso"
        fr = ttk.LabelFrame(tm, text=" Carga rápida | Arista por línea ", padding=6)
        fr.pack(fill="x", pady=(8, 0))
        ttk.Label(fr, text="Formato:  desde  hasta  peso     (ej.:  0 3 25)",
                  style="Tenue.TLabel").pack(anchor="w")
        self.txt_rapida = tk.Text(fr, height=5, width=30, font="TkFixedFont")
        self.txt_rapida.pack(fill="x", pady=4)
        ttk.Button(fr, text="Cargar aristas", style="Verde.TButton",command=self.accion_carga_rapida).pack(fill="x")
        
        self.nb_modo.bind("<<NotebookTabChanged>>", self._al_cambiar_modo)

        # --- 3. Dijkstra ---
        f3 = ttk.LabelFrame(p, text=" 3. Camino mínimo (Dijkstra) ", padding=8)
        f3.pack(fill="x", pady=(0, 8))
        fo = ttk.Frame(f3)
        fo.pack(fill="x")
        ttk.Label(fo, text="Origen:").pack(side="left")
        self.cb_origen = ttk.Combobox(fo, width=4, state="readonly")
        self.cb_origen.pack(side="left", padx=(2, 10))
        ttk.Label(fo, text="Destino:").pack(side="left")
        self.cb_destino = ttk.Combobox(fo, width=4, state="readonly")
        self.cb_destino.pack(side="left", padx=2)
        ttk.Button(f3, text="▶  Calcular camino mínimo", style="Verde.TButton",
                   command=self.accion_dijkstra).pack(fill="x", pady=(8, 6))

        self.lbl_resultado = tk.Label(f3, text="Elige origen y destino y pulsa Calcular.",
                                      bg="#f8fafc", fg=C_TEXTO, font=(FUENTE, 9), justify="left",
                                      anchor="nw", wraplength=330, padx=8, pady=8,
                                      relief="groove")
        self.lbl_resultado.pack(fill="x")

    def _panel_resultados(self, p):
        self.nb_vistas = ttk.Notebook(p)
        self.nb_vistas.pack(fill="both", expand=True)

        # Pestaña Grafo
        tg = ttk.Frame(self.nb_vistas)
        self.nb_vistas.add(tg, text="  Grafo  ")
        barra = ttk.Frame(tg, padding=(8, 6))
        barra.pack(fill="x")
        ttk.Label(barra, text="Diseño:").pack(side="left")
        self.cb_layout = ttk.Combobox(barra, values=["Circular", "Fuerzas (spring)", "Capas (shell)"],
                                      state="readonly", width=15)
        self.cb_layout.set("Circular")
        self.cb_layout.pack(side="left", padx=(4, 8))
        self.cb_layout.bind("<<ComboboxSelected>>", lambda e: self.accion_reordenar())
        ttk.Button(barra, text="Reordenar", style="Gris.TButton",
                   command=self.accion_reordenar).pack(side="left")
        self.var_mostrar_grados = tk.BooleanVar(value=True)
        ttk.Checkbutton(barra, text="Mostrar grados en el dibujo", variable=self.var_mostrar_grados,
                        command=self.dibujar_grafo).pack(side="left", padx=12)
        ttk.Button(barra, text="Quitar resaltado", style="Gris.TButton",
                   command=self.accion_quitar_resaltado).pack(side="right")
        ttk.Label(tg, text="Tip: arrastra los vértices con el mouse para acomodar el dibujo.",
                  style="Tenue.TLabel").pack(anchor="w", padx=10)

        self.fig = Figure(figsize=(7.5, 6), dpi=100)
        self.fig.patch.set_facecolor("white")
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=tg)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvas.mpl_connect("button_press_event", self._mouse_presion)
        self.canvas.mpl_connect("motion_notify_event", self._mouse_mover)
        self.canvas.mpl_connect("button_release_event", self._mouse_soltar)

        # Pestaña Matriz
        tmz = ttk.Frame(self.nb_vistas, padding=10)
        self.nb_vistas.add(tmz, text="  Matriz de adyacencia  ")
        self.lbl_info_matriz = ttk.Label(tmz, text="", style="Tenue.TLabel", justify="left")
        self.lbl_info_matriz.pack(anchor="w", pady=(0, 8))
        self.frame_matriz = tk.Frame(tmz, bg=C_PANEL)
        self.frame_matriz.pack(anchor="nw")

        # Pestaña Grados
        tgr = ttk.Frame(self.nb_vistas, padding=10)
        self.nb_vistas.add(tgr, text="  Grados de los vértices  ")
        self.lbl_resumen_grados = tk.Label(tgr, text="", bg="#f8fafc", fg=C_TEXTO, justify="left",
                                           anchor="w", font=(FUENTE, 10), padx=10, pady=8,
                                           relief="groove")
        self.lbl_resumen_grados.pack(side="bottom", fill="x", pady=(10, 0))
        arriba = ttk.Frame(tgr)
        arriba.pack(fill="both", expand=True)
        self.tree_grados = ttk.Treeview(arriba, show="headings", height=15)
        self.tree_grados.pack(side="left", fill="y")
        self.tree_grados.tag_configure("par", background="#f8fafc")
        self.fig_g = Figure(figsize=(5, 3.6), dpi=100)
        self.ax_g = self.fig_g.add_subplot(111)
        self.canvas_g = FigureCanvasTkAgg(self.fig_g, master=arriba)
        self.canvas_g.get_tk_widget().pack(side="left", fill="both", expand=True, padx=(10, 0))

    # ======================= VENTANA DE AYUDA =======================

    def ventana_ayuda(self):
        v = tk.Toplevel(self.root)
        v.title("Ayuda - Cómo usar el programa")
        v.configure(bg=C_PANEL)
        v.geometry("560x520")
        v.transient(self.root)
        texto = (
            "1. CONFIGURACIÓN\n"
            "   • Elige el número de vértices n (entre 5 y 15).\n"
            "   • Elige el tipo: Dirigido (flechas) o Bidireccional (sin dirección).\n\n"
            "2. MÉTODO DE INGRESO (son dos formas separadas)\n"
            "   • Automático: define densidad y rango de pesos, pulsa Generar.\n"
            "   • Manual: elige 'Desde', 'Hacia' y 'Peso' y pulsa Agregar.\n"
            "     O haz clic en un vértice del dibujo y luego en otro: se te\n"
            "     pedirá el peso. Selecciona una arista de la lista para\n"
            "     editarla o eliminarla.\n"
            "   Cada modo guarda su propio grafo.\n\n"
            "3. GRADOS\n"
            "   • Dirigido: g⁻(v) = aristas que ENTRAN a v (columna de la matriz),\n"
            "     g⁺(v) = aristas que SALEN de v (fila de la matriz).\n"
            "     Se cumple Σ g⁻(v) = Σ g⁺(v) = |A|.\n"
            "   • Bidireccional: g(v) = aristas incidentes en v.\n"
            "     Se cumple Σ g(v) = 2·|E| (lema del apretón de manos).\n\n"
            "4. CAMINO MÍNIMO\n"
            "   • Elige origen y destino y pulsa Calcular. El camino se\n"
            "     resalta en rojo en el grafo y en la matriz.\n"
            "   • En grafos dirigidos solo se avanza en el sentido de la flecha."
        )
        tk.Label(v, text=texto, justify="left", anchor="nw", bg=C_PANEL, fg=C_TEXTO,
                 font=(FUENTE, 10), padx=18, pady=16).pack(fill="both", expand=True)
        ttk.Button(v, text="Cerrar", style="Azul.TButton", command=v.destroy).pack(pady=(0, 14))

    # ======================= ACCIONES =======================

    def _leer_int(self, var, nombre, minimo, maximo):
        try:
            val = int(str(var.get()).strip())
        except ValueError:
            messagebox.showerror("Dato inválido", f"{nombre} debe ser un número entero.")
            return None
        if not (minimo <= val <= maximo):
            messagebox.showerror("Dato inválido", f"{nombre} debe estar entre {minimo} y {maximo}.")
            return None
        return val

    def accion_generar_automatico(self):
        n = self._leer_int(self.var_n, "El número de vértices", N_MIN, N_MAX)
        pmin = self._leer_int(self.var_pmin, "El peso mínimo", PESO_MIN, PESO_MAX)
        pmax = self._leer_int(self.var_pmax, "El peso máximo", PESO_MIN, PESO_MAX)
        if None in (n, pmin, pmax):
            return
        if pmin > pmax:
            messagebox.showerror("Dato inválido", "El peso mínimo no puede ser mayor que el máximo.")
            return
        est = self.estados["auto"]
        est.n = n
        est.matriz = generar_matriz_automatica(n, self.es_dirigido(),
                                               self.var_densidad.get() / 100, pmin, pmax)
        est.pos = {}
        est.camino = None
        est.titulo = None
        self.lbl_resultado.config(text="Grafo generado. Elige origen y destino y pulsa Calcular.")
        self.refrescar_todo()
        self.estado(f"Grafo automático generado: n = {n}, "
                    f"{len(lista_aristas(est.matriz, self.es_dirigido()))} aristas.")

    def accion_cambiar_n(self):
        n = int(self.var_n.get())
        if self.modo == "auto":
            self.accion_generar_automatico()
            return
        est = self.est
        if n == est.n:
            return
        if n < est.n:
            perdidas = [(u, v, w) for u, v, w in lista_aristas(est.matriz, self.es_dirigido())
                        if u >= n or v >= n]
            if perdidas and not messagebox.askyesno(
                    "Reducir vértices",
                    f"Se eliminarán {len(perdidas)} arista(s) de los vértices {n} a {est.n - 1}.\n¿Continuar?"):
                self.var_n.set(str(est.n))
                return
        nueva = np.zeros((n, n), dtype=int)
        k = min(n, est.n)
        nueva[:k, :k] = est.matriz[:k, :k]
        est.matriz, est.n = nueva, n
        est.pos, est.camino, est.titulo = {}, None, None
        self.nodo_seleccionado = None
        self.refrescar_todo()
        self.estado(f"Modo manual: ahora el grafo tiene {n} vértices.")

    def accion_cambiar_tipo(self):
        dirigido = self.es_dirigido()
        man = self.estados["manual"]
        if not dirigido and len(lista_aristas(man.matriz, True)) > 0:
            man.matriz = simetrizar(man.matriz)
        for e in self.estados.values():
            e.camino, e.titulo = None, None
        # En modo automático se genera un nuevo grafo del tipo elegido
        aut = self.estados["auto"]
        aut.matriz = generar_matriz_automatica(aut.n, dirigido, self.var_densidad.get() / 100,
                                               *self._pesos_auto())
        aut.pos = {}
        self.lbl_resultado.config(text="Tipo de grafo cambiado. Vuelve a calcular el camino.")
        self.refrescar_todo()
        self.estado("Tipo de grafo: " + ("DIRIGIDO" if dirigido else "BIDIRECCIONAL (no dirigido)") +
                    (". Las aristas manuales se convirtieron en bidireccionales." if not dirigido
                     else ". Cada arista manual ahora equivale a dos arcos (ida y vuelta)."))

    def _pesos_auto(self):
        try:
            a, b = int(self.var_pmin.get()), int(self.var_pmax.get())
            if PESO_MIN <= a <= b <= PESO_MAX:
                return a, b
        except ValueError:
            pass
        return 1, 50

    def _al_cambiar_modo(self, _evento=None):
        idx = self.nb_modo.index(self.nb_modo.select())
        self.modo = "auto" if idx == 0 else "manual"
        self.nodo_seleccionado = None
        self.var_n.set(str(self.est.n))
        if self.est.titulo and self.est.resultado:
            self.lbl_resultado.config(text=self.est.resultado)
        else:
            self.lbl_resultado.config(text="Elige origen y destino y pulsa Calcular.")
        self.refrescar_todo()
        self.estado("Modo AUTOMÁTICO." if self.modo == "auto" else
                    "Modo MANUAL: agrega aristas con el formulario o haciendo clic en dos vértices.")

    def _agregar_arista(self, u, v, w):
        est = self.est
        existia = est.matriz[u][v] > 0
        est.matriz[u][v] = w
        if not self.es_dirigido():
            est.matriz[v][u] = w
        est.camino, est.titulo = None, None
        self.refrescar_todo()
        flecha = "→" if self.es_dirigido() else "↔"
        self.estado(f"Arista {u} {flecha} {v} {'actualizada' if existia else 'agregada'} con peso {w}.")

    def accion_agregar_arista(self):
        if self.modo != "manual":
            return
        if not self.cb_desde.get() or not self.cb_hacia.get():
            messagebox.showwarning("Faltan datos", "Selecciona los vértices 'Desde' y 'Hacia'.")
            return
        u, v = int(self.cb_desde.get()), int(self.cb_hacia.get())
        if u == v:
            messagebox.showerror("Arista inválida", "No se permiten lazos: elige dos vértices distintos.")
            return
        w = self._leer_int(self.var_peso, "El peso", PESO_MIN, PESO_MAX)
        if w is None:
            return
        self._agregar_arista(u, v, w)

    def accion_carga_rapida(self):
        #"""Agrega varias aristas a la vez desde la caja de texto (una por línea)."""
        if self.modo != "manual":
            return
        est = self.est
        nuevas, errores = [], []
        for num, linea in enumerate(self.txt_rapida.get("1.0", "end").splitlines(), start=1):
            linea = linea.split("#")[0]                      # permite comentarios con #
            for sep in (",", ";", "->", "→", "↔", "—", "-"):
                linea = linea.replace(sep, " ")
            partes = linea.split()
            if not partes:
                continue
            try:
                if len(partes) != 3:
                    raise ValueError("se esperaban 3 números: desde hasta peso")
                u, v, w = (int(x) for x in partes)
                if not (0 <= u < est.n and 0 <= v < est.n):
                    raise ValueError(f"los vértices deben estar entre 0 y {est.n - 1}")
                if u == v:
                    raise ValueError("no se permiten lazos (desde = hasta)")
                if not (PESO_MIN <= w <= PESO_MAX):
                    raise ValueError(f"el peso debe estar entre {PESO_MIN} y {PESO_MAX}")
            except ValueError as e:
                msg = str(e)
                if msg.startswith("invalid literal"):
                    msg = "solo se permiten números enteros"
                errores.append(f"Línea {num}: {msg}")
                continue
            nuevas.append((u, v, w))
        if errores:
            extra = f"\n... y {len(errores) - 8} más." if len(errores) > 8 else ""
            messagebox.showerror("Carga rápida",
                                 "No se cargó ninguna arista. Corrige estas líneas:\n\n"
                                 + "\n".join(errores[:8]) + extra)
            return
        if not nuevas:
            messagebox.showinfo("Carga rápida", "Escribe al menos una arista (ej.: 0 3 25).")
            return
        for u, v, w in nuevas:
            est.matriz[u][v] = w
            if not self.es_dirigido():
                est.matriz[v][u] = w
        est.camino, est.titulo = None, None
        self.txt_rapida.delete("1.0", "end")
        self.refrescar_todo()
        self.estado(f"Carga rápida: {len(nuevas)} arista(s) agregada(s) o actualizada(s).")

    def _al_seleccionar_arista(self, _e=None):
        sel = self.tree_aristas.selection()
        if not sel:
            return
        u, v, w = self.tree_aristas.item(sel[0], "values")
        self.cb_desde.set(u)
        self.cb_hacia.set(v)
        self.var_peso.set(w)

    def accion_eliminar_arista(self):
        sel = self.tree_aristas.selection()
        if not sel:
            messagebox.showinfo("Eliminar", "Selecciona una arista de la lista.")
            return
        u, v, _ = (int(x) for x in self.tree_aristas.item(sel[0], "values"))
        est = self.est
        est.matriz[u][v] = 0
        if not self.es_dirigido():
            est.matriz[v][u] = 0
        est.camino, est.titulo = None, None
        self.refrescar_todo()
        self.estado(f"Arista {u} - {v} eliminada.")

    def accion_borrar_todas(self):
        est = self.est
        if not lista_aristas(est.matriz, self.es_dirigido()):
            return
        if messagebox.askyesno("Borrar todas", "¿Eliminar todas las aristas del grafo manual?"):
            est.matriz = np.zeros((est.n, est.n), dtype=int)
            est.camino, est.titulo = None, None
            self.refrescar_todo()
            self.estado("Se eliminaron todas las aristas.")

    def accion_dijkstra(self):
        est = self.est
        if not lista_aristas(est.matriz, self.es_dirigido()):
            messagebox.showwarning("Grafo vacío", "El grafo no tiene aristas todavía.")
            return
        if not self.cb_origen.get() or not self.cb_destino.get():
            messagebox.showwarning("Faltan datos", "Selecciona el vértice de origen y el de destino.")
            return
        o, d = int(self.cb_origen.get()), int(self.cb_destino.get())
        camino, costo, dist = dijkstra(est.matriz, o, d)
        flecha = " → " if self.es_dirigido() else " — "
        dist_txt = ",  ".join(f"{i}: {'∞' if x == float('inf') else int(x)}" for i, x in enumerate(dist))
        if camino:
            est.camino = camino
            est.titulo = f"Camino mínimo {o} → {d}   |   Costo total: S/ {int(costo)}"
            texto = (f"Ruta: {flecha.join(map(str, camino))}\n"
                     f"Secuencia de vértices: {camino}\n"
                     f"Número de aristas recorridas: {len(camino) - 1}\n"
                     f"Costo total del recorrido: S/ {int(costo)}\n\n"
                     f"Distancias mínimas desde {o}:\n{dist_txt}")
            self.estado(f"Camino mínimo encontrado de {o} a {d} con costo S/ {int(costo)}.")
        else:
            est.camino = None
            est.titulo = f"No existe camino de {o} a {d}"
            texto = (f"No existe un camino posible de {o} a {d}"
                     f"{' respetando el sentido de las flechas' if self.es_dirigido() else ''}.\n\n"
                     f"Distancias mínimas desde {o}:\n{dist_txt}")
            self.estado("No existe camino entre los vértices seleccionados.")
        est.resultado = texto
        self.lbl_resultado.config(text=texto)
        self.refrescar_todo(conservar_combos=True)
        self.nb_vistas.select(0)

    def accion_reordenar(self):
        self.est.pos = {}
        self.dibujar_grafo()

    def accion_quitar_resaltado(self):
        self.est.camino, self.est.titulo = None, None
        self.nodo_seleccionado = None
        self.refrescar_todo(conservar_combos=True)

    # ======================= REFRESCO DE VISTAS =======================

    def refrescar_todo(self, conservar_combos=True):
        n = self.est.n
        opciones = [str(i) for i in range(n)]
        for cb, defecto in [(self.cb_origen, "0"), (self.cb_destino, str(n - 1)),
                            (self.cb_desde, "0"), (self.cb_hacia, "1")]:
            actual = cb.get()
            cb["values"] = opciones
            if not (conservar_combos and actual in opciones):
                cb.set(defecto)
        dirigido = self.es_dirigido()
        self.lbl_desde.config(text="Desde:" if dirigido else "Vértice:")
        self.lbl_hacia.config(text="Hacia:" if dirigido else "Vértice:")
        self.tree_aristas.heading("a", text="Desde" if dirigido else "Vértice A")
        self.tree_aristas.heading("b", text="Hacia" if dirigido else "Vértice B")
        self._refrescar_lista_aristas()
        self._refrescar_matriz()
        self._refrescar_grados()
        self.dibujar_grafo()

    def _refrescar_lista_aristas(self):
        self.tree_aristas.delete(*self.tree_aristas.get_children())
        for u, v, w in lista_aristas(self.estados["manual"].matriz, self.es_dirigido()):
            self.tree_aristas.insert("", "end", values=(u, v, w))

    def _refrescar_matriz(self):
        for w in self.frame_matriz.winfo_children():
            w.destroy()
        est = self.est
        n, M = est.n, est.matriz
        dirigido = self.es_dirigido()
        grados = calcular_grados(M, dirigido)
        camino = est.camino or []
        celdas_camino = set(zip(camino, camino[1:]))
        if not dirigido:
            celdas_camino |= {(b, a) for a, b in celdas_camino}

        self.lbl_info_matriz.config(text=(
            "Filas = vértice de ORIGEN, columnas = vértice de DESTINO. Un 0 significa que no hay arista.\n"
            + ("Grafo dirigido: la matriz NO es necesariamente simétrica. "
               "Última columna: g⁺(v) (salida). Última fila: g⁻(v) (entrada)."
               if dirigido else
               "Grafo bidireccional: la matriz es SIMÉTRICA (M[i][j] = M[j][i]). Última columna: g(v).")
            + "\nLas celdas en rojo forman el camino mínimo calculado."))

        fuente = (FUENTE, 9)
        fuente_b = (FUENTE, 9, "bold")
        ancho = 4

        def celda(r, c, txt, bg, fg=C_TEXTO, font=fuente):
            tk.Label(self.frame_matriz, text=txt, bg=bg, fg=fg, font=font, width=ancho,
                     relief="flat", padx=2, pady=3).grid(row=r, column=c, padx=1, pady=1)

        celda(0, 0, "M", C_OSCURO, "white", fuente_b)
        for j in range(n):
            celda(0, j + 1, str(j), "#cbd5e1", font=fuente_b)
        celda(0, n + 1, "g⁺" if dirigido else "g", "#fde68a", font=fuente_b)
        for i in range(n):
            celda(i + 1, 0, str(i), "#cbd5e1", font=fuente_b)
            for j in range(n):
                val = int(M[i][j])
                if i == j:
                    bg, fg = "#e2e8f0", "#94a3b8"
                elif (i, j) in celdas_camino:
                    bg, fg = "#fecaca", "#991b1b"
                elif val > 0:
                    bg, fg = "#dbeafe", "#1e3a8a"
                else:
                    bg, fg = "#f8fafc", "#94a3b8"
                celda(i + 1, j + 1, str(val), bg, fg, fuente_b if val > 0 else fuente)
            g = grados["salida"][i] if dirigido else grados["grado"][i]
            celda(i + 1, n + 1, str(int(g)), "#fef3c7", font=fuente_b)
        if dirigido:
            celda(n + 1, 0, "g⁻", "#fde68a", font=fuente_b)
            for j in range(n):
                celda(n + 1, j + 1, str(int(grados["entrada"][j])), "#fef3c7", font=fuente_b)

    def _refrescar_grados(self):
        est = self.est
        dirigido = self.es_dirigido()
        M = est.matriz
        n = est.n
        g = calcular_grados(M, dirigido)
        m = len(lista_aristas(M, dirigido))
        tv = self.tree_grados
        tv.delete(*tv.get_children())

        if dirigido:
            cols = ("v", "ent", "sal", "tot", "obs")
            heads = ("Vértice", "Grado entrada g⁻(v)", "Grado salida g⁺(v)", "Grado total", "Observación")
            anchos = (60, 130, 125, 85, 150)
        else:
            cols = ("v", "g", "vec", "obs")
            heads = ("Vértice", "Grado g(v)", "Vértices adyacentes", "Observación")
            anchos = (60, 80, 200, 150)
        tv["columns"] = cols
        for c, h, a in zip(cols, heads, anchos):
            tv.heading(c, text=h)
            tv.column(c, width=a, anchor="center")
        tv.configure(height=max(n, 5))

        for v in range(n):
            tag = ("par",) if v % 2 == 0 else ()
            if dirigido:
                e, s = int(g["entrada"][v]), int(g["salida"][v])
                if e == 0 and s == 0:
                    obs = "Aislado"
                elif e == 0:
                    obs = "Fuente (no le llegan)"
                elif s == 0:
                    obs = "Sumidero (no salen)"
                elif e == s:
                    obs = "Balanceado (g⁻ = g⁺)"
                else:
                    obs = "—"
                tv.insert("", "end", values=(v, e, s, e + s, obs), tags=tag)
            else:
                gv = int(g["grado"][v])
                vecinos = [str(j) for j in range(n) if M[v][j] > 0]
                obs = "Aislado" if gv == 0 else ("Pendiente (hoja)" if gv == 1 else
                                                 ("Par" if gv % 2 == 0 else "Impar"))
                tv.insert("", "end", values=(v, gv, ", ".join(vecinos) or "—", obs), tags=tag)

        # Resumen y verificación
        if dirigido:
            se, ss = int(g["entrada"].sum()), int(g["salida"].sum())
            tot = g["total"]
            texto = (f"Grafo DIRIGIDO:  |V| = {n} vértices,  |A| = {m} arcos.\n"
                     f"Σ g⁻(v) = {se}   y   Σ g⁺(v) = {ss}   →   ambos son iguales a |A| = {m}  "
                     f"{'✔ se cumple' if se == ss == m else '✘'}\n"
                     f"Σ grado total = {int(tot.sum())} = 2·|A|.   "
                     f"Grado total máximo: {int(tot.max())} (vértice {int(tot.argmax())}),  "
                     f"mínimo: {int(tot.min())} (vértice {int(tot.argmin())}).")
        else:
            gg = g["grado"]
            s = int(gg.sum())
            regular = len(set(gg.tolist())) == 1
            impares = int((gg % 2 == 1).sum())
            texto = (f"Grafo BIDIRECCIONAL:  |V| = {n} vértices,  |E| = {m} aristas.\n"
                     f"Lema del apretón de manos:  Σ g(v) = {s} = 2·|E| = 2·{m} = {2 * m}  "
                     f"{'✔ se cumple' if s == 2 * m else '✘'}\n"
                     f"Grado máximo Δ(G) = {int(gg.max())},  grado mínimo δ(G) = {int(gg.min())},  "
                     f"vértices de grado impar: {impares} (siempre es un número par)."
                     + (f"\nEl grafo es {int(gg[0])}-regular (todos los vértices tienen el mismo grado)."
                        if regular else ""))
        self.lbl_resumen_grados.config(text=texto)

        # Gráfico de barras
        ax = self.ax_g
        ax.clear()
        x = np.arange(n)
        if dirigido:
            ax.bar(x - 0.2, g["entrada"], width=0.4, label="Entrada g⁻(v)", color="#3b82f6")
            ax.bar(x + 0.2, g["salida"], width=0.4, label="Salida g⁺(v)", color="#f59e0b")
            ax.legend(fontsize=8, frameon=False)
        else:
            ax.bar(x, g["grado"], width=0.6, label="g(v)", color="#3b82f6")
        tope = max(g["entrada"].max(), g["salida"].max()) if dirigido else g["grado"].max()
        ax.set_ylim(0, max(int(tope), 1) + 1.5)
        ax.set_xticks(x)
        ax.set_xlabel("Vértice", fontsize=9)
        ax.set_ylabel("Grado", fontsize=9)
        ax.set_title("Grado de cada vértice", fontsize=10, fontweight="bold")
        ax.yaxis.get_major_locator().set_params(integer=True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(labelsize=8)
        self.fig_g.tight_layout()
        self.canvas_g.draw_idle()

    # ======================= DIBUJO DEL GRAFO =======================

    def _calcular_layout(self, n):
        G = nx.empty_graph(n)
        modo = self.cb_layout.get()
        if modo.startswith("Fuerzas"):
            for u, v, _ in lista_aristas(self.est.matriz, False):
                G.add_edge(u, v)
            pos = nx.spring_layout(G, seed=random.randint(0, 9999), k=2.5 / np.sqrt(n), iterations=200)
            pos= self.expandir_posiciones_Nodos(pos)
            
        elif modo.startswith("Capas"):
            mitad = n // 3
            pos = nx.shell_layout(G, [list(range(mitad)), list(range(mitad, n))])
        else:
            pos = nx.circular_layout(G)
        return {k: np.array(v, dtype=float) for k, v in pos.items()}

    def expandir_posiciones_Nodos(self, pos):
        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        return {
        nodo: np.array([
                2 * (p[0] - x0) / ((x1 - x0) or 1) - 1,
                2 * (p[1] - y0) / ((y1 - y0) or 1) - 1,])
        for nodo, p in pos.items()
        }
    
    
    def dibujar_grafo(self, fijar_limites=False):
        est = self.est
        ax = self.ax
        limites = (ax.get_xlim(), ax.get_ylim()) if fijar_limites else None
        ax.clear()
        n, M = est.n, est.matriz
        dirigido = self.es_dirigido()
        if len(est.pos) != n:
            est.pos = self._calcular_layout(n)
        pos = est.pos

        G = nx.DiGraph() if dirigido else nx.Graph()
        G.add_nodes_from(range(n))
        aristas = lista_aristas(M, dirigido)
        for u, v, w in aristas:
            G.add_edge(u, v, weight=w)

        camino = est.camino or []
        ar_camino = set(zip(camino, camino[1:]))
        if not dirigido:
            ar_camino |= {(b, a) for a, b in ar_camino}
        hay_camino = bool(camino)

        coords = np.array([pos[i] for i in range(n)])
        centro = coords.mean(axis=0)
        span = max(np.ptp(coords[:, 0]), np.ptp(coords[:, 1]), 0.5)
        RAD = 0.18

        # --- aristas ---
        grupos = {}
        for u, v, w in aristas:
            curva = dirigido and M[v][u] > 0
            clave = ((u, v) in ar_camino, curva)
            grupos.setdefault(clave, []).append((u, v))
        for (en_camino, curva), lista in grupos.items():
            kw = dict(edgelist=lista, ax=ax, node_size=self.TAM_NODO,
                      edge_color=C_ROJO if en_camino else "#64748b",
                      width=3.0 if en_camino else 1.4,
                      alpha=1.0 if en_camino else (0.25 if hay_camino else 0.85))
            if dirigido:
                kw.update(arrows=True, arrowstyle="-|>", arrowsize=20 if en_camino else 15,
                          connectionstyle=f"arc3,rad={RAD if curva else 0.0}")
            else:
                kw.update(arrows=False)
            nx.draw_networkx_edges(G, pos, **kw)

        # --- pesos (posición calculada a mano para que coincida con la curva) ---
        for u, v, w in aristas:
            (x1, y1), (x2, y2) = pos[u], pos[v]
            rad = RAD if (dirigido and M[v][u] > 0) else 0.0
            dx, dy = x2 - x1, y2 - y1
            lx = (x1 + x2) / 2 + 0.5 * rad * dy
            ly = (y1 + y2) / 2 - 0.5 * rad * dx
            en_camino = (u, v) in ar_camino
            if en_camino:
                ax.text(lx, ly, str(w), fontsize=9, fontweight="bold", color="#991b1b",
                        ha="center", va="center", zorder=5,
                        bbox=dict(boxstyle="round,pad=0.2", fc="#fef2f2", ec=C_ROJO, lw=1))
            else:
                ax.text(lx, ly, str(w), fontsize=8, color=C_TEXTO, ha="center", va="center",
                        alpha=0.35 if hay_camino else 1.0, zorder=4,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                                  alpha=0.35 if hay_camino else 0.85))

        # --- vértices ---
        normales = [v for v in range(n) if v not in camino and v != self.nodo_seleccionado]
        nx.draw_networkx_nodes(G, pos, nodelist=normales, ax=ax, node_size=self.TAM_NODO,
                               node_color="#bfdbfe", edgecolors="#1e3a8a", linewidths=1.4,
                               alpha=0.5 if hay_camino else 1.0)
        if camino:
            nx.draw_networkx_nodes(G, pos, nodelist=camino, ax=ax, node_size=self.TAM_NODO + 80,
                                   node_color="#86efac", edgecolors="#14532d", linewidths=2.2)
            nx.draw_networkx_nodes(G, pos, nodelist=[camino[0], camino[-1]], ax=ax,
                                   node_size=self.TAM_NODO + 80, node_color="#4ade80",
                                   edgecolors="#14532d", linewidths=3.2)
        if self.nodo_seleccionado is not None and self.nodo_seleccionado < n:
            nx.draw_networkx_nodes(G, pos, nodelist=[self.nodo_seleccionado], ax=ax,
                                   node_size=self.TAM_NODO + 120, node_color="#fdba74",
                                   edgecolors=C_NARANJA, linewidths=3)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight="bold", font_color=C_TEXTO)

        # --- grados al costado de cada vértice ---
        if self.var_mostrar_grados.get():
            g = calcular_grados(M, dirigido)
            for v in range(n):
                d = pos[v] - centro
                norma = np.hypot(*d)
                d = d / norma if norma > 1e-6 else np.array([0.0, -1.0])
                tx, ty = pos[v] + d * 0.11 * span
                txt = (f"g⁻={int(g['entrada'][v])} g⁺={int(g['salida'][v])}" if dirigido
                       else f"g={int(g['grado'][v])}")
                ax.text(tx, ty, txt, fontsize=7.5, color="#7c2d12", ha="center", va="center",
                        zorder=6, bbox=dict(boxstyle="round,pad=0.15", fc="#fff7ed",
                                            ec="#fdba74", lw=0.6))

                # --- etiquetas INICIO / FIN del camino mínimo ---
        if camino:
            marcas = [(camino[0], "INICIO", C_VERDE)]
            if len(camino) > 1:
                marcas.append((camino[-1], "FIN", C_ROJO))
            for v, texto, color in marcas:
                d = pos[v] - centro
                norma = np.hypot(*d)
                d = d / norma if norma > 1e-6 else np.array([0.0, 1.0])
                tx, ty = pos[v] - d * 0.11 * span
                ax.text(tx, ty, texto, fontsize=8, fontweight="bold", color="white",
                        ha="center", va="center", zorder=8,
                        bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="none"))

        # --- título y leyenda ---
        tipo = "dirigido" if dirigido else "bidireccional (no dirigido)"
        modo = "automático" if self.modo == "auto" else "manual"
        titulo = est.titulo or (f"Grafo {tipo} ponderado  —  n = {n},  "
                                f"{'|A|' if dirigido else '|E|'} = {len(aristas)}")
        ax.set_title(titulo, fontsize=12, fontweight="bold", color=C_OSCURO, pad=10)
        ax.text(0.0, 0.0, f"Modo {modo}", transform=ax.transAxes, fontsize=8, color=C_TENUE)
        if not aristas:
            ax.text(0.5, 0.5, "Sin aristas todavía.\nAgrega aristas desde el panel 'Manual'\n"
                    "o haz clic en un vértice y luego en otro.", transform=ax.transAxes,
                    ha="center", va="center", fontsize=10, color=C_TENUE, zorder=7,
                    bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="#cbd5e1"))
        if hay_camino:
            ax.text(1.0, 0.0, "Rojo: camino mínimo", transform=ax.transAxes, ha="right",
                    fontsize=8, color=C_ROJO, fontweight="bold")

        ax.axis("off")
        if limites:
            ax.set_xlim(*limites[0])
            ax.set_ylim(*limites[1])
        else:
            pad = 0.22 * span
            ax.set_xlim(coords[:, 0].min() - pad, coords[:, 0].max() + pad)
            ax.set_ylim(coords[:, 1].min() - pad, coords[:, 1].max() + pad)
        ax.set_aspect("equal", adjustable="box")
        self.fig.tight_layout()
        self.canvas.draw_idle()

    # ======================= INTERACCIÓN CON EL MOUSE =======================

    def _nodo_en(self, event):
        if event.inaxes != self.ax or event.x is None:
            return None
        mejor, dmin = None, 22.0  # píxeles
        for v, p in self.est.pos.items():
            px, py = self.ax.transData.transform(p)
            d = np.hypot(px - event.x, py - event.y)
            if d < dmin:
                mejor, dmin = v, d
        return mejor

    def _mouse_presion(self, event):
        if event.button != 1:
            return
        self.nodo_presionado = self._nodo_en(event)
        self.punto_presion = (event.x, event.y)
        self.arrastrando = False

    def _mouse_mover(self, event):
        if self.nodo_presionado is None or event.xdata is None:
            return
        if not self.arrastrando:
            if np.hypot(event.x - self.punto_presion[0], event.y - self.punto_presion[1]) < 5:
                return
            self.arrastrando = True
        self.est.pos[self.nodo_presionado] = np.array([event.xdata, event.ydata])
        self.dibujar_grafo(fijar_limites=True)

    def _mouse_soltar(self, event):
        nodo, arrastro = self.nodo_presionado, self.arrastrando
        self.nodo_presionado, self.arrastrando = None, False
        if arrastro:
            self.dibujar_grafo()
            return
        if self.modo != "manual":
            if nodo is not None:
                self.estado(f"Vértice {nodo}. En modo Manual puedes crear aristas haciendo clic en dos vértices.")
            return
        if nodo is None:
            if self.nodo_seleccionado is not None:
                self.nodo_seleccionado = None
                self.dibujar_grafo()
            return
        if self.nodo_seleccionado is None:
            self.nodo_seleccionado = nodo
            self.cb_desde.set(str(nodo))
            self.dibujar_grafo()
            self.estado(f"Vértice {nodo} seleccionado. Ahora haz clic en el vértice "
                        f"{'destino' if self.es_dirigido() else 'a conectar'}.")
            return
        if nodo == self.nodo_seleccionado:
            self.nodo_seleccionado = None
            self.dibujar_grafo()
            self.estado("Selección cancelada.")
            return
        u, v = self.nodo_seleccionado, nodo
        self.nodo_seleccionado = None
        self.cb_hacia.set(str(v))
        flecha = "→" if self.es_dirigido() else "↔"
        actual = int(self.est.matriz[u][v])
        w = simpledialog.askinteger(
            "Peso de la arista",
            f"Peso de la arista {u} {flecha} {v}:" + (f"\n(peso actual: {actual})" if actual else ""),
            parent=self.root, minvalue=PESO_MIN, maxvalue=PESO_MAX,
            initialvalue=actual or self._peso_formulario())
        if w is None:
            self.dibujar_grafo()
            self.estado("Arista cancelada.")
            return
        self.var_peso.set(str(w))
        self._agregar_arista(u, v, w)

    def _peso_formulario(self):
        try:
            return max(PESO_MIN, min(PESO_MAX, int(self.var_peso.get())))
        except ValueError:
            return 10


# ======================= VENTANA DE CARÁTULA =======================

def mostrar_caratula(root, al_continuar):
    v = tk.Toplevel(root)
    v.title("Carátula - Matemática Computacional")
    v.configure(bg=C_PANEL)
    v.resizable(False, False)
    ancho, alto = 680, 390 + (40 + 24 * len(INTEGRANTES) if INTEGRANTES else 0)
    v.update_idletasks()
    x = (v.winfo_screenwidth() - ancho) // 2
    y = (v.winfo_screenheight() - alto) // 3
    v.geometry(f"{ancho}x{alto}+{x}+{y}")

    banda = tk.Frame(v, bg=C_OSCURO, pady=18)
    banda.pack(fill="x")
    tk.Label(banda, text=TITULO_TRABAJO, fg="#93c5fd", bg=C_OSCURO,
             font=(FUENTE, 12, "bold")).pack()
    tk.Label(banda, text=TEMA, fg="white", bg=C_OSCURO, font=(FUENTE, 14, "bold"),
             justify="center").pack(pady=(6, 0))

    cuerpo = tk.Frame(v, bg=C_PANEL, pady=18)
    cuerpo.pack(fill="both", expand=True)
    for etiqueta, valor in [("Curso", CURSO), ("Profesor", PROFESOR), ("Sección", SECCION)]:
        f = tk.Frame(cuerpo, bg=C_PANEL)
        f.pack(pady=3)
        tk.Label(f, text=f"{etiqueta}:", bg=C_PANEL, fg=C_TENUE, font=(FUENTE, 11)).pack(side="left")
        tk.Label(f, text=valor, bg=C_PANEL, fg=C_TEXTO, font=(FUENTE, 11, "bold")).pack(side="left", padx=6)
    if INTEGRANTES:
        tk.Label(cuerpo, text="Integrantes:", bg=C_PANEL, fg=C_TENUE,
                 font=(FUENTE, 11)).pack(pady=(10, 2))
        for nombre in INTEGRANTES:
            tk.Label(cuerpo, text=nombre, bg=C_PANEL, fg=C_TEXTO, font=(FUENTE, 10)).pack()

    tk.Label(cuerpo, text="Grafos dirigidos y bidireccionales  •  Grados de los vértices  •  "
                          "Matriz de adyacencia  •  Dijkstra",
             bg=C_PANEL, fg=C_TENUE, font=(FUENTE, 9)).pack(pady=(16, 0))

    botones = tk.Frame(v, bg=C_PANEL, pady=16)
    botones.pack(fill="x")

    def continuar():
        v.destroy()
        al_continuar()

    ttk.Button(botones, text="Ingresar al sistema  ▶", style="Azul.TButton",
               command=continuar).pack(side="right", padx=20)
    ttk.Button(botones, text="Salir", style="Gris.TButton",
               command=root.destroy).pack(side="right")
    v.protocol("WM_DELETE_WINDOW", root.destroy)
    v.bind("<Return>", lambda e: continuar())
    v.focus_force()
    return v


def main():
    root = tk.Tk()
    root.withdraw()
    estilo = ttk.Style(root)
    estilo.theme_use("clam")
    for nombre, color in [("Azul", C_AZUL), ("Gris", "#475569")]:
        estilo.configure(f"{nombre}.TButton", background=color, foreground="white",
                         font=(FUENTE, 10, "bold"), padding=(14, 7), borderwidth=0)
        estilo.map(f"{nombre}.TButton", background=[("active", C_OSCURO)])

    def abrir_principal():
        AplicacionGrafos(root)
        root.deiconify()

    mostrar_caratula(root, abrir_principal)
    root.mainloop()


if __name__ == "__main__":
    main()
