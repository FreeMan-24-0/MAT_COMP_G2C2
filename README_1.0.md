# README

# MAT_COMP_G2C2

Código para el proyecto/trabajo grupal de Matemática Computacional 2026-2 (Sección 3215).

## Trabajo final: `TF_Grafos_Dijkstra.py`

### Integrantes:

- Huachaca Quinteros Gianfranco Carlos
- Ivette Lucero Villavicencio Davila
- Tarazona Muñoz, Juan Sebastian

### Profesor: Antonio Marcos Medina Martinez

### Requisitos

- Python 3.10 o superior
- Modo de ejecución

```bash
pip install -r requirements.txt
python TF_Grafos_Dijkstra.py
```

Aplicación con **ventana gráfica** (no usa la consola):

- **Carátula** en una ventana aparte y luego la ventana principal.
- **Tipo de grafo:** dirigido (flechas) o bidireccional / no dirigido.
- **Dos métodos de ingreso separados** (cada uno guarda su propio grafo):
    - *Automático:* elige n, densidad y rango de pesos → genera un grafo aleatorio conexo.
    - *Manual:* elige “Desde”, “Hacia” y “Peso” y pulsa Agregar, o haz clic en un vértice del dibujo y luego en otro. Las aristas se pueden editar o eliminar desde la lista.
        
        Opción adicional de carga rápida mediante el Formato
        
        <aside>
        
        desde hasta peso 
        
        Ejemplo: 0 3 20
        
        </aside>
        
        escrito en una sola línea con espacio.
        
- **Grados de cada vértice:**
    - Dirigido: grado de entrada g⁻(v), grado de salida g⁺(v), total, fuentes y sumideros,
    verificación Σg⁻ = Σg⁺ = |A|.
    - Bidireccional: grado g(v), vecinos, Δ(G), δ(G), verificación Σg(v) = 2|E|.
    - Tabla, gráfico de barras y grados mostrados en el dibujo.
- **Matriz de adyacencia** con los grados en la última fila/columna.
- **Camino mínimo (Algoritmo Dijkstra)** resaltado en el grafo desde  y en la matriz.

### Notas del modo automático

- Cada vértice tiene como máximo 5 aristas (entrantes + salientes)
- El grafo dirigido es conexo: desde cualquier vértice se llega a cualquier otro.
- Con ese límite, la densidad real no supera aproximadamente el 18 % con n = 15.

Versiones anteriores: `proyecto MC01.py` (consola), `Test_01.py`, `Test_02.py`.