
import os
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import random
import sys


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")

def validar_n():
    """Solicita y valida el número de vértices entre 5 y 15"""
    while True:
        try:
            n = int(input("Ingrese el número de vértices n (5 - 15): "))
            if 5 <= n <= 15:
                return n
            else:
                print(f"Error: El valor de n debe ser estrictamente entre 5 y 15 ")
        except ValueError:
            print(f"Error: Por favor, ingrese un número entero válido")

def generar_matriz_automatica(n):
    """Genera aleatoriamente una matriz de adyacencia ponderada"""
    matriz = np.zeros((n, n), dtype=int)
    for i in range(n):
        for j in range(i + 1, n):
            # 30% de probabilidad de no haber conexión 
            if random.random() > 0.3:
                peso = random.randint(1, 50)
                matriz[i][j] = peso
                matriz[j][i] = peso # Grafo no dirigido
    return matriz

def ingresar_matriz_manual(n):
    """Permite al usuario ingresar los pesos de la matriz manualmente"""
    matriz = np.zeros((n, n), dtype=int)
    print("\nIngrese los pesos de las aristas (ingrese 0 si no hay conexión directa)")
    for i in range(n):
        for j in range(i + 1, n):
            while True:
                try:
                    peso = int(input(f"Peso de la arista entre el vértice {i} y {j}: "))
                    if peso >= 0:
                        matriz[i][j] = peso
                        matriz[j][i] = peso
                        break
                    else:
                        print("Error: Los pesos no pueden ser negativos")
                except ValueError:
                    print("Error: Ingrese un número entero")
    return matriz

def mostrar_grafo(matriz, n, camino=None, titulo="Grafo Ponderado"):
    """Genera y muestra el grafo ponderado correspondiente"""
    G = nx.Graph()
    for i in range(n):
        G.add_node(i)
        for j in range(i + 1, n):
            if matriz[i][j] > 0:
                G.add_edge(i, j, weight=matriz[i][j])

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 6))
    plt.suptitle(titulo, fontsize=14, fontweight= 'bold')
    
    # Dibujar nodos y aristas base
    nx.draw(G, pos, with_labels=True, node_color='lightblue', node_size=700, font_weight='bold')
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

    # Resaltar el camino mínimo si existe
    if camino:
        edges_camino = [(camino[i], camino[i+1]) for i in range(len(camino)-1)]
        nx.draw_networkx_edges(G, pos, edgelist=edges_camino, edge_color='red', width=2.5)
        nx.draw_networkx_nodes(G, pos, nodelist=camino, node_color='lightgreen', node_size=700)

    plt.title("Grafo Ponderado")
    plt.axis('off')
    plt.show()

def dijkstra(matriz, origen, destino, n):
    """Encuentra el camino mínimo y su costo. """
    import heapq
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
            peso = matriz[nodo_actual][vecino]
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

def caratula():
    limpiar()
    print("="*50)
    print("PRIMER ENTREGABLE".center(50))
    print("APLICACIÓN DEL ALGORITMO DE DIJKSTRA EN".center(50))
    print("LA SOLUCION DEL PROBLEMA DE CAMINO MINIMO".center(50))
    print("="*50)
    print("Curso: MATEMATICA COMPUTACIONAL".center(50))
    print("Profesor: Antonio Marcos Medina Martinez".center(50))
    print("Seccion: 3215".center(50))
    print("-"*50)

def main():
    caratula()
    input("Presione para continuar... ")
    while True:
        limpiar()
        print("="*50)
        print("SISTEMA DE CAMINO MÍNIMO".center(50))
        print("="*50)
        n = validar_n()
        limpiar()
        print("-"*50)
        print("CREACION DE LA MATRIZ:".center(50))
        print("-"*50)
        print("\nIngresar el metodo de construccion de la matriz: ")
        print("1. Generación automática")
        print("2. Ingreso manual")
        
        while True:
            opcion = input("Seleccione una opción (1 o 2): ")
            if opcion == '1':
                matriz = generar_matriz_automatica(n)
                break
            elif opcion == '2':
                matriz = ingresar_matriz_manual(n)
                break
            else:
                print("Opción inválida.")

        print("\nMatriz generada:")
        print(matriz)
        
        # Muestra el grafo generado
        mostrar_grafo(matriz, n)

        while True:
            try:
                origen = int(input(f"\nIngrese el vértice de origen (0 a {n-1}): "))
                destino = int(input(f"Ingrese el vértice de destino (0 a {n-1}): "))
                if 0 <= origen < n and 0 <= destino < n:
                    break
                else:
                    print(f"Error: Los vértices deben estar entre 0 y {n-1}")
            except ValueError:
                print("Error: Ingrese valores enteros")

        camino, costo = dijkstra(matriz, origen, destino, n)

        if camino:
            print(f"\nResultado:")
            print(f"Secuencia de vértices del camino mínimo: \n{camino}")
            print(f"Costo total del recorrido: S/{costo}")
            # Muestra el grafo con el camino resaltado
            mostrar_grafo(matriz, n, camino, titulo=f"Camino minimo {origen} --> {destino} - S/{costo} ")
        else:
            print("\nNo existe un camino posible entre los vértices seleccionados")

if __name__ == "__main__":
    main()