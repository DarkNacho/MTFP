---
marp: true
theme: default
paginate: true
style: |
  .header {
    position: absolute;
    top: 10px;
    right: 10px;
    height: 60px;
  }
  section {
    /* Mantenemos el fondo de la universidad */
    background-image: url('utalca.png'); 
    background-position: top right;
    background-repeat: no-repeat;
    background-size: 400px;
    padding-top: 30px;
  }
  h2 { color: #4F81BD; } /* Color azul sobrio para títulos */
  table { font-size: 0.7em; }
  td, th { padding: 2px; }
  .key-point { font-size: 1.1em; color: #C0504D; font-weight: bold; } /* Destacar puntos clave */
  .center-content { display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; height: 100%; }
---

# A Fully Heuristic Framework for the Sociometric Multiple Team Formation Problem

**Ignacio Martínez Hernández**  
Doctorado en Sistemas de Ingeniería  
Universidad de Talca

_Metahurísticas_

[https://github.com/DarkNacho/MTFP](https://github.com/DarkNacho/MTFP)


---

## Introducción y Motivación

- **Contexto:** Formación de equipos para múltiples proyectos concurrentes en organizaciones.
- **Objetivo:** Optimizar la asignación de recursos humanos, satisfaciendo:
    1.  Requerimientos de habilidades ($r_{kl}$).
    2.  Capacidad laboral individual ($\le 100\%$).
    3.  Afinidad sociométrica (Maximizar $E$).

<br>

---

### Limitación del Estado del Arte

El enfoque original para el MTFP (Gutiérrez et al., 2016) se basó en una búsqueda híbrida que dependía de **solucionadores exactos de Programación por Restricciones (CP)** para validar la factibilidad.

<br>

### Contribución Principal

Método totalmente heurístico que reemplaza el uso de solver.

---

## Formulación Matemática (MTFP)

El objetivo es maximizar la eficiencia global ($E$), una suma ponderada de las eficiencias de proyecto ($e_l$).

### Función Objetivo: Eficiencia Sociométrica

$$E = \sum_{l \in \mathcal{P}} w_l \cdot e_l$$

<br>

$$e_l = \frac{1}{2} \left(1 + \frac{\sum_{i,j} \mathbf{s_{ij}} \cdot \mathbf{x_{il} x_{jl}}}{\left(\sum_k r_{kl}\right)^2}\right)$$

- $\mathbf{s_{ij}}$: Matriz de afinidad sociométrica (ej. $\in \{-1, 0, 1\}$).
- $\mathbf{x_{il} x_{jl}}$: El impacto sociométrico se escala por la dedicación simultánea.

<br>

---

### Restricciones

1.  **Capacidad**: $\sum_l x_{il} \le 1$
2.  **Habilidades**: $\sum_{i \in Q_k} x_{il} = r_{kl}$
3.  **Dedicación Discreta**: $x_{il} \in \mathcal{D}$ (ej. $\{0.0, 0.25, 0.5, 0.75, 1.0\}$)

---

## Metodología: El Núcleo Heurístico

### Randomized Greedy Constructive Heuristic (RGCH)

**Función:** Generar sub-soluciones factibles, sustituyendo la llamada al solver exacto.

- **Estrategia:** Explotación de la **Descomposición del Problema por Habilidad** ($\mathcal{K}$).
- **Procedimiento:**
    1.  Reiniciar asignaciones para la habilidad $k$.
    2.  Aleatorizar el orden de los candidatos de habilidad $Q_k$ (Estocasticidad).
    3.  Asignar dedicaciones discretas de forma **Greedy** hasta satisfacer el requerimiento $r_{kl}$ sin violar la capacidad individual.

---

### Estructura de Vecindario Fundamental ($N^1$)

- **Generación de Vecino ($X'$):**
    1.  Seleccionar aleatoriamente una habilidad $k$.
    2.  Aplicar el **RGCH** para reconstruir la asignación de esa única habilidad.
- **Propiedad Clave:** Todos los vecinos $X' \in N^1(X)$ son inherentemente **factibles**.

---

## Algoritmos de Búsqueda Comparados

Se evaluaron siete algoritmos bajo un presupuesto de **Evaluaciones de Función (NFE)** escalado para garantizar una comparación justa.

### Componente Unificador: $N^1$ y RGCH

Todos los algoritmos de búsqueda (HC, TS, SLS, VNS, GA) utilizan el **RGCH** como motor para generar:

- Movimientos de exploración (Vecinos en $N^1$).
- Mutaciones (en el GA).

---

### Descripción del Algoritmo Genético (GA)

El GA se diseñó para explotar la descomposición por habilidades:

- **Cruce (Crossover):** Cruce Uniforme que intercambia **bloques completos de asignaciones de habilidad** entre padres. Esto garantiza la **factibilidad** estructural de la descendencia.

- **Mutación:** Se selecciona una habilidad $k$ y su asignación se **reconstruye** completamente usando el **RGCH**, actuando como un movimiento aleatorio dentro del vecindario $N^1$.

---

## Algoritmos de Búsqueda Comparados

Se evaluaron siete algoritmos bajo un presupuesto de **Evaluaciones de Función (NFE)** escalado para garantizar una comparación justa.

| Clase de Algoritmo            | Estrategia                                              | Algoritmos                                                  |
| :---------------------------- | :------------------------------------------------------ | :---------------------------------------------------------- |
| **Líneas Base Determinista**  | Construcción no estocástica                             | Greedy (DG)                                                 |
| **Líneas Base Estocástica**   | Generación de soluciones al azar (Explotación de RGCH)  | **Random Search (RS)**                                      |
| **Búsqueda Focalizada**       | Explotación de $N^1$                                    | Hill Climbing (HC), Tabu Search (TS)                        |
| **Nuestro Enfoque**           | Explotación **Persistente** de $N^1$                    | **Stochastic Local Search (SLS)**                           |
| **Metaheurísticas**           | Diversificación y Población                             | Genetic Algorithm (GA), Variable Neighborhood Search (VNS)  |

---

## Marco de Análisis Estadístico

### Diseño y Metodología

- **Diseño:** 30 ejecuciones independientes por algoritmo (Muestras Pareadas).
- **Métrica:** Eficiencia media ($E_{mean}$).

### Pruebas de Normalidad

- **Razón:** Los resultados acotados ($E \in [0, 1]$) producen **asimetría negativa (efecto de techo)**.
- **Verificación:** Prueba de **Shapiro-Wilk**.

### Prueba de Hipótesis Principal

- **Test:** **Wilcoxon Signed-Rank Test** (no paramétrico).
- **Hipótesis Nula ($H_0$):** No hay diferencia significativa en la calidad de la solución.

---

### Interpretación del $p$-valor ($\alpha = 0.05$)

| Condición         | Veredicto                                 | Implicación Práctica         |
| :---------------- | :---------------------------------------- | :--------------------------- |
| **$p < 0.05$**    | Rechazar $H_0$                            | **Superioridad Estadística** |
| **$p \ge 0.05$**  | **No hay evidencia para rechazar $H_0$**  | Rendimiento Comparable       |

---

## Configuración Experimental

### Escalas de Instancias

<div style="width:100%; display:flex; justify-content:center;">
  <table style="width:80%; font-size:1.05em; border-collapse:collapse; text-align:left;">
    <thead>
      <tr>
        <th style="padding:8px 12px; border-bottom:1px solid #ddd;">Escala</th>
        <th style="padding:8px 12px; border-bottom:1px solid #ddd;">Personas (|𝓗|)</th>
        <th style="padding:8px 12px; border-bottom:1px solid #ddd;">Proyectos (|𝓟|)</th>
        <th style="padding:8px 12px; border-bottom:1px solid #ddd;">Habilidades (|𝓚|)</th>
        <th style="padding:8px 12px; border-bottom:1px solid #ddd;">Presupuesto (NFE)</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">Pequeña</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">20</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">3</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">2</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">20,000</td>
      </tr>
      <tr>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">Mediana</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">100</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">10</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">10</td>
        <td style="padding:8px 12px; border-bottom:1px solid #f0f0f0;">50,000</td>
      </tr>
      <tr>
        <td style="padding:8px 12px;">Grande</td>
        <td style="padding:8px 12px;">200</td>
        <td style="padding:8px 12px;">20</td>
        <td style="padding:8px 12px;">20</td>
        <td style="padding:8px 12px;">100,000</td>
      </tr>
    </tbody>
  </table>
</div>

_Densidad sociométrica: 30% de relaciones positivas_

---

## Resultados: Resumen de Rendimiento

<!-- Tres tablas independientes lado a lado para Marp -->
<div style="display:flex; gap:18px; align-items:flex-start; justify-content:center; width:100%; font-size:0.95em;">

  <!-- Pequeña -->
  <div style="flex:0 0 32%; min-width:260px;">
    <strong>Pequeña (N=20)</strong>
    <table style="width:100%; margin-top:8px; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; padding:6px 8px;">Algorithm</th>
          <th style="text-align:right; padding:6px 8px;">Mean ± Std</th>
          <th style="text-align:right; padding:6px 8px;">Best</th>
          <th style="text-align:right; padding:6px 8px;">Time(s)</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding:6px 8px;">Greedy</td><td style="text-align:right;padding:6px 8px;">0.694 ± 0.000</td><td style="text-align:right;padding:6px 8px;">0.694</td><td style="text-align:right;padding:6px 8px;"><strong>0.01</strong></td></tr>
        <tr><td style="padding:6px 8px;">Hill Climbing</td><td style="text-align:right;padding:6px 8px;">0.801 ± 0.028</td><td style="text-align:right;padding:6px 8px;">0.855</td><td style="text-align:right;padding:6px 8px;">0.01</td></tr>
        <tr><td style="padding:6px 8px;">Random Search</td><td style="text-align:right;padding:6px 8px;">0.878 ± 0.011</td><td style="text-align:right;padding:6px 8px;">0.912</td><td style="text-align:right;padding:6px 8px;">8.50</td></tr>
        <tr><td style="padding:6px 8px;">Tabu Search</td><td style="text-align:right;padding:6px 8px;">0.891 ± 0.009</td><td style="text-align:right;padding:6px 8px;">0.912</td><td style="text-align:right;padding:6px 8px;">4.99</td></tr>
        <tr><td style="padding:6px 8px;">Genetic Alg. (GA)</td><td style="text-align:right;padding:6px 8px;">0.903 ± 0.015</td><td style="text-align:right;padding:6px 8px;">0.932</td><td style="text-align:right;padding:6px 8px;">11.77</td></tr>
        <tr><td style="padding:6px 8px;"><strong>VNS</strong></td><td style="text-align:right;padding:6px 8px;"><strong>0.907 ± 0.017</strong></td><td style="text-align:right;padding:6px 8px;"><strong>0.939</strong></td><td style="text-align:right;padding:6px 8px;">5.23</td></tr>
        <tr><td style="padding:6px 8px;"><strong>Stoch. LS (Ours)</strong></td><td style="text-align:right;padding:6px 8px;">0.896 ± 0.018</td><td style="text-align:right;padding:6px 8px;"><strong>0.939</strong></td><td style="text-align:right;padding:6px 8px;">4.98</td></tr>
      </tbody>
    </table>
  </div>

---

  <!-- Mediana -->
  <div style="flex:0 0 32%; min-width:260px;">
    <strong>Mediana (N=100)</strong>
    <table style="width:100%; margin-top:8px; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; padding:6px 8px;">Algorithm</th>
          <th style="text-align:right; padding:6px 8px;">Mean ± Std</th>
          <th style="text-align:right; padding:6px 8px;">Best</th>
          <th style="text-align:right; padding:6px 8px;">Time(s)</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding:6px 8px;">Greedy</td><td style="text-align:right;padding:6px 8px;">0.646 ± 0.000</td><td style="text-align:right;padding:6px 8px;">0.646</td><td style="text-align:right;padding:6px 8px;"><strong>0.01</strong></td></tr>
        <tr><td style="padding:6px 8px;">Hill Climbing</td><td style="text-align:right;padding:6px 8px;">0.775 ± 0.020</td><td style="text-align:right;padding:6px 8px;">0.812</td><td style="text-align:right;padding:6px 8px;">0.32</td></tr>
        <tr><td style="padding:6px 8px;">Random Search</td><td style="text-align:right;padding:6px 8px;">0.788 ± 0.006</td><td style="text-align:right;padding:6px 8px;">0.800</td><td style="text-align:right;padding:6px 8px;">1129.1</td></tr>
        <tr><td style="padding:6px 8px;">Tabu Search</td><td style="text-align:right;padding:6px 8px;">0.829 ± 0.004</td><td style="text-align:right;padding:6px 8px;">0.841</td><td style="text-align:right;padding:6px 8px;">149.6</td></tr>
        <tr><td style="padding:6px 8px;"><strong>Genetic Alg. (GA)</strong></td><td style="text-align:right;padding:6px 8px;">0.848 ± 0.008</td><td style="text-align:right;padding:6px 8px;"><strong>0.862</strong></td><td style="text-align:right;padding:6px 8px;">250.6</td></tr>
        <tr><td style="padding:6px 8px;">VNS</td><td style="text-align:right;padding:6px 8px;">0.837 ± 0.006</td><td style="text-align:right;padding:6px 8px;">0.849</td><td style="text-align:right;padding:6px 8px;">163.0</td></tr>
        <tr><td style="padding:6px 8px;"><strong>Stoch. LS (Ours)</strong></td><td style="text-align:right;padding:6px 8px;"><strong>0.852 ± 0.004</strong></td><td style="text-align:right;padding:6px 8px;">0.861</td><td style="text-align:right;padding:6px 8px;">148.1</td></tr>
      </tbody>
    </table>
  </div>

---

  <!-- Grande -->
  <div style="flex:0 0 32%; min-width:260px;">
    <strong>Grande (N=200)</strong>
    <table style="width:100%; margin-top:8px; border-collapse:collapse;">
      <thead>
        <tr>
          <th style="text-align:left; padding:6px 8px;">Algorithm</th>
          <th style="text-align:right; padding:6px 8px;">Mean ± Std</th>
          <th style="text-align:right; padding:6px 8px;">Best</th>
          <th style="text-align:right; padding:6px 8px;">Time(s)</th>
        </tr>
      </thead>
      <tbody>
        <tr><td style="padding:6px 8px;">Greedy</td><td style="text-align:right;padding:6px 8px;">0.590 ± 0.000</td><td style="text-align:right;padding:6px 8px;">0.590</td><td style="text-align:right;padding:6px 8px;"><strong>0.01</strong></td></tr>
        <tr><td style="padding:6px 8px;">Hill Climbing</td><td style="text-align:right;padding:6px 8px;">0.658 ± 0.011</td><td style="text-align:right;padding:6px 8px;">0.672</td><td style="text-align:right;padding:6px 8px;">3.68</td></tr>
        <tr><td style="padding:6px 8px;">Random Search</td><td style="text-align:right;padding:6px 8px;">0.659 ± 0.004</td><td style="text-align:right;padding:6px 8px;">0.669</td><td style="text-align:right;padding:6px 8px;">16692.9</td></tr>
        <tr><td style="padding:6px 8px;">Tabu Search</td><td style="text-align:right;padding:6px 8px;">0.692 ± 0.003</td><td style="text-align:right;padding:6px 8px;">0.699</td><td style="text-align:right;padding:6px 8px;">1104.7</td></tr>
        <tr><td style="padding:6px 8px;">Genetic Alg. (GA)</td><td style="text-align:right;padding:6px 8px;">0.694 ± 0.003</td><td style="text-align:right;padding:6px 8px;">0.700</td><td style="text-align:right;padding:6px 8px;">2036.3</td></tr>
        <tr><td style="padding:6px 8px;">VNS</td><td style="text-align:right;padding:6px 8px;">0.689 ± 0.004</td><td style="text-align:right;padding:6px 8px;">0.697</td><td style="text-align:right;padding:6px 8px;">1284.5</td></tr>
        <tr><td style="padding:6px 8px;"><strong>Stoch. LS (Ours)</strong></td><td style="text-align:right;padding:6px 8px;"><strong>0.700 ± 0.004</strong></td><td style="text-align:right;padding:6px 8px;"><strong>0.708</strong></td><td style="text-align:right;padding:6px 8px;">1103.4</td></tr>
      </tbody>
    </table>
  </div>

</div>

---

## Comportamiento de Convergencia

---

&nbsp;

![width:1300px height:600](../results/MTFP_BASE_CASE_P20_Pr3_Sk2_Pos0.3_plot.png)

---

&nbsp;

![width:1300px height:600](../results/MTFP_PAPER_MAX_P100_Pr10_Sk10_Pos0.3_plot.png)

---

&nbsp;

![width:1300px height:600](../results/MTFP_STRESS_TEST_P200_Pr20_Sk20_Pos0.3_plot.png)

---

## Test Estadístico ($N=200$)

###  Prueba de Normalidad (Shapiro-Wilk)

Para la instancia Grande ($N=200$), verificamos la distribución de las 30 ejecuciones:

| Algoritmo | $p$-valor Shapiro-Wilk |           Veredicto           |
| :-------: | :--------------------: | :---------------------------: |
|    SLS    |        $0.098$         | **No Rechaza $H_0$** (Normal) |
|    GA     |        $0.002$         | **Rechaza $H_0$** (No Normal) |
|    VNS    |        $0.011$         | **Rechaza $H_0$** (No Normal) |

> **Implicación:** Dado que el GA y el VNS no cumplen la condición de normalidad, se requiere el uso de pruebas no paramétricas para asegurar la validez de la comparación.

---

### Análisis de Significación (Wilcoxon Signed-Rank Test)

Se compara el **SLS (0.700)** contra sus principales competidores, utilizando un diseño de muestras pareadas.

| Comparación (SLS vs.)                  | Diferencia Media ($d$) | Desv. Estándar ($\sigma$) |       $\mathbf{p}$-valor       |  Veredicto   |
| :------------------------------------- | :--------------------: | :-----------------------: | :----------------------------: | :----------: |
| **Genetic Algorithm (GA)**             |        $0.0063$        |         $0.0019$          | $\mathbf{1.17 \times 10^{-6}}$ | **Superior** |
| **Variable Neighborhood Search (VNS)** |        $0.011$         |         $0.0028$          | $\mathbf{1.86 \times 10^{-9}}$ | **Superior** |
| **Tabu Search (TS)**                   |        $0.008$         |         $0.0019$          | $\mathbf{8.20 \times 10^{-8}}$ | **Superior** |

**El rendimiento superior de SLS en el caso de Gran Escala es estadísticamente significativo.**

El _p_-valor extremadamente bajo (a pesar de la pequeña diferencia absoluta) se debe a la **alta estabilidad** de los resultados (σ ≈ 0.004) y a la potencia del diseño de muestras pareadas.

---

## Análisis de la Dominancia de SLS

### ¿Por qué SLS supera a Metaheurísticas complejas?

El resultado es contraintuitivo: un algoritmo simple supera a VNS y GA en alta dimensión.

| Factor                | GA / VNS                                                                                 | **SLS (Explotación)**                                                                               |
| :-------------------- | :--------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------- |
| **Enfoque**           | Diversificación (Búsqueda global)                                                        | **Explotación Intensiva** (Búsqueda focalizada)                                                     |
| **Search Landscape**  | Altamente restringido y decomponible.                                                    | Favorece movimientos pequeños y precisos.                                                           |
| **Eficiencia**        | La sobrecarga de la gestión de población (GA) o el _shaking_ agresivo (VNS) es costosa.  | La **persistencia** en la explotación del vecindario $N^1$ es clave para una convergencia profunda. |

<br>

---

## Conclusiones y Trabajo Futuro

### Conclusiones

1.  Se validó con éxito un **marco heurístico completo** (RGCH + $N^1$) para el MTFP, eliminando la dependencia de solvers exactos.
2.  **Stochastic Local Search (SLS)** es el algoritmo más **robusto y escalable** para el MTFP de alta dimensión.
3.  Se demostró que la **explotación intensiva** es más efectiva que la diversificación agresiva o poblacional.
