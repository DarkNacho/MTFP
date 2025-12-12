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
    background-image: url('utalca.png');
    background-position: top right;
    background-repeat: no-repeat;
    background-size: 400px;
    padding-top: 30px;
  }
---

# Un Marco Heurístico Completo para el Problema de Formación de Múltiples Equipos Sociométricos

**Ignacio Martínez Hernández**  
Doctorado en Sistemas de Ingeniería  
Universidad de Talca

_Presentación Conferencia IEEE_

---

## Agenda

1. **Introducción y Motivación**
2. **Formulación del Problema** (MTFP)
3. **Metodología**: Marco Heurístico Completo
4. **Configuración Experimental**
5. **Resultados y Análisis Estadístico**
6. **Conclusiones y Trabajo Futuro**

---

## 1. Introducción y Motivación

- Las organizaciones ejecutan múltiples proyectos simultáneamente
- El rendimiento del equipo depende de **habilidades técnicas** + **afinidad social**
- **Problema de Formación de Múltiples Equipos (MTFP)**: Asignar recursos humanos a múltiples proyectos considerando:
  - Requerimientos de habilidades
  - Matrices sociométricas (afinidad interpersonal)
  - Niveles de dedicación fraccional

**Limitación del trabajo previo**: Dependencia de solucionadores exactos de Programación por Restricciones (CP) → sobrecarga computacional

---

## Brecha de Investigación y Contribución

**Enfoque original MTFP** (Gutiérrez et al., 2016):

- VNS híbrido + Solver CP para factibilidad

**Nuestra contribución**: **Marco heurístico completo**

- Reemplazar el solver CP con **Randomized Greedy Constructive Heuristic (RGCH)**
- Evaluación comparativa integral: 7 algoritmos
- **Búsqueda Local Estocástica (SLS)** surge como la más escalable

---

## 2. Formulación Matemática

**Objetivo**: Maximizar la eficiencia sociométrica global

$$
E = \sum_{l \in \mathcal{P}} w_l \cdot \frac{1}{2} \left(1 + \frac{\sum_{i,j} s_{ij} x_{il} x_{jl}}{\left(\sum_k r_{kl}\right)^2}\right)
$$

**Restricciones**:

1. Capacidad: $\sum_l x_{il} \le 1$
2. Requerimientos de habilidades: $\sum_{i \in Q_k} x_{il} = r_{kl}$
3. Dedicación discreta: $x_{il} \in \mathcal{D}$

---

## 3. Metodología: Heurística Central

### Randomized Greedy Constructive Heuristic (RGCH)

- Reemplaza el solver CP exacto
- Explota la **descomposición del problema por habilidad**
- Pasos:
  1. Reiniciar asignaciones para habilidad $k$
  2. Aleatorizar candidatos
  3. Asignación gready para cumplir requerimientos

**Garantiza factibilidad** sin solucionadores externos

---

## 3.1 Estructura de Vecindario

**1-Skill Neighborhood ($N^1$)**:

- Seleccionar una categoría de habilidad $k$
- Eliminar todas las asignaciones para $k$
- Reconstruir usando RGCH

**Propiedad clave**: Cada vecino es factible → No se necesitan mecanismos de reparación

---

## 3.2 Diseño del Algoritmo Genético

**Representación**: Cada solución es un conjunto de sub-soluciones por habilidad

- Preserva la factibilidad estructural

**Operadores especializados**:

1. **Cruce Basado en Habilidades**:
   - Intercambia bloques completos de asignaciones de habilidades entre padres
   - **Garantiza factibilidad**: si padres son factibles, hijos también

---

2. **Mutación**:

   - Selecciona una habilidad $k$ con probabilidad $p_m$
   - Reconstruye asignaciones usando **RGCH** (equivalente a mover en $N^1$

3. **Inicialización**:
   - Población inicial generada con RGCH
   - Todas las soluciones son factibles desde el inicio

---

## 3.3 Evaluación Comparativa de Algoritmos

**Siete algoritmos comparados**:

1. **Líneas base**: Greedy Determinista (DG), Random Search (RS)
2. **Basados en trayectoria**: Hill Climbing (HC), Stochastic Local Search (SLS), Tabu Search (TS)
3. **Basados en población**: **Genetic Algorithm (GA)** con operadores especializados
4. **Metaheurística**: Variable Neighbourhood Search (VNS)

**Presupuesto computacional**: Estandarizado por evaluaciones de función (NFE)

- **Pequeño**: 20,000 NFE
- **Mediano**: 50,000 NFE
- **Grande**: 100,000 NFE

---

## 4. Configuración Experimental

### Escalas de Instancias

| Escala  | Personas | Proyectos | Habilidades |
| ------- | -------- | --------- | ----------- |
| Pequeña | 20       | 3         | 2           |
| Mediana | 100      | 10        | 10          |
| Grande  | 200      | 20        | 20          |

**Densidad sociométrica**: 30% relaciones positivas

#### Rigor Estadístico

- 30 ejecuciones independientes por algoritmo
- Diseño de muestras pareadas (mismas semillas aleatorias)
- **Prueba de Rangos con Signo de Wilcoxon**

---

## 5. Resultados: Resumen de Rendimiento (Instancia Pequeña, N=20)

| Algorithm             | Mean ± Std        | Best      | Time(s)  |
| --------------------- | ----------------- | --------- | -------- |
| Greedy                | 0.694 ± 0.000     | 0.694     | **0.01** |
| Hill Climbing         | 0.801 ± 0.028     | 0.855     | 0.01     |
| Random Search         | 0.878 ± 0.011     | 0.912     | 8.50     |
| Tabu Search           | 0.891 ± 0.009     | 0.912     | 4.99     |
| **Genetic Alg. (GA)** | 0.903 ± 0.015     | 0.932     | 11.77    |
| **VNS**               | **0.907 ± 0.017** | **0.939** | 5.23     |
| **Stoch. LS**         | 0.896 ± 0.018     | **0.939** | 4.98     |

---

## 5. Resultados: Resumen de Rendimiento (Instancia Mediana, N=100)

| Algorithm             | Mean ± Std        | Best      | Time(s)  |
| --------------------- | ----------------- | --------- | -------- |
| Greedy                | 0.646 ± 0.000     | 0.646     | **0.01** |
| Hill Climbing         | 0.775 ± 0.020     | 0.812     | 0.32     |
| Random Search         | 0.788 ± 0.006     | 0.800     | 1129.1   |
| Tabu Search           | 0.829 ± 0.004     | 0.841     | 149.6    |
| **Genetic Alg. (GA)** | 0.848 ± 0.008     | **0.862** | 250.6    |
| **VNS**               | 0.837 ± 0.006     | 0.849     | 163.0    |
| **Stoch. LS**         | **0.852 ± 0.004** | 0.861     | 148.1    |

---

## 5. Resultados: Resumen de Rendimiento (Instancia Grande, N=200)

| Algorithm             | Mean ± Std        | Best      | Time(s)  |
| --------------------- | ----------------- | --------- | -------- |
| Greedy                | 0.590 ± 0.000     | 0.590     | **0.01** |
| Hill Climbing         | 0.658 ± 0.011     | 0.672     | 3.68     |
| Random Search         | 0.659 ± 0.004     | 0.669     | 16692.9  |
| Tabu Search           | 0.692 ± 0.003     | 0.699     | 1104.7   |
| **Genetic Alg. (GA)** | 0.694 ± 0.003     | 0.700     | 2036.3   |
| **VNS**               | 0.689 ± 0.004     | 0.697     | 1284.5   |
| **Stoch. LS**         | **0.700 ± 0.004** | **0.708** | 1103.4   |

---

## 5.1 Análisis de Escalabilidad

**Instancia pequeña**:

- VNS y GA estadísticamente equivalentes (\(p = 0.187\))
- VNS 2.2× más rápido que GA → **VNS recomendado**

**Instancia mediana**:

- **Búsqueda Local Estocástica (SLS)** supera a GA (\(p = 0.0035\)) y VNS (\(p < 0.001\))
- SLS más rápido que GA (148s vs 250s)

**Instancia grande**:

- **SLS domina** (\(p < 10^{-6}\) vs GA)
- La persistencia simple supera mecanismos complejos

---

## 5.2 Comportamiento de Convergencia

- **Grande**: GA se estanca temprano, SLS continúa mejorando

---

&nbsp;

![width:950px height:530](../results/MTFP_BASE_CASE_P20_Pr3_Sk2_Pos0.3_plot.png)

---

&nbsp;

![width:950px height:530](../results/MTFP_PAPER_MAX_P100_Pr10_Sk10_Pos0.3_plot.png)

---

&nbsp;

![width:950px height:530](../results/MTFP_STRESS_TEST_P200_Pr20_Sk20_Pos0.3_plot.png)

---

## 5.3 ¿Por qué SLS Sobresale?

**Paradoja**: Algoritmo simple supera metaheurísticas sofisticadas

**Razones**:

1. **Explotación persistente**: SLS explora exhaustivamente $N^1$
2. **Paisaje MTFP**: Altamente restringido, descomponible → favorece búsqueda focalizada
3. **Limitación VNS**: Búsqueda local superficial (50 evaluaciones) limita convergencia

**Significancia estadística**: Diferencias medias pequeñas (0.700 vs 0.694) pero altamente significativas por baja varianza

---

## 6. Conclusiones

1. **Marco heurístico completo** elimina exitosamente la dependencia de solucionadores CP
2. **Heurística Constructiva Golosa Aleatorizada (RGCH)** garantiza factibilidad eficientemente
3. **Búsqueda Local Estocástica (SLS)** surge como el algoritmo más **escalable**
4. **Hallazgo contraintuitivo**: Búsqueda simple y persistente supera metaheurísticas complejas en instancias grandes

**Implicación práctica**: Para MTFP de alta dimensión, la explotación intensiva supera la diversificación agresiva

---

## 7. Trabajo Futuro

1. **Extensiones del problema**:

   - Múltiples habilidades por persona
   - Requerimientos de proyectos dinámicos
   - Competencias superpuestas

2. **Mejoras algorítmicas**:

   - VNS adaptativo con intensidad de perturbación auto-ajustable
   - Enfoques híbridos combinando persistencia SLS con diversidad GA

3. **Validación en mundo real**: Aplicar a casos de estudio industriales

---
