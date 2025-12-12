from Algorithm.MTFP import MTFP, create_mtfp_problem, explain_mtfp_problem
from SolutionResult import SolutionResult, compare_solutions_side_by_side
from Algorithm.LS import LS
from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from Algorithm.TabuSearch import TabuSearch
from Algorithm.VNS import VNS
from Algorithm.HillClimbing import HillClimbing
from Algorithm.GA import run_mtfp_ga
from Algorithm.RandomSearch import RandomSearch
from Algorithm.Greedy import Greedy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm
#from tqdm.contrib.concurrent import process_map
from concurrent.futures import ProcessPoolExecutor, as_completed

#from joblib import Parallel, delayed
import multiprocessing


def generate_reproducible_seeds(master_seed, n_runs):
    """
    Genera una lista de semillas independientes para cada ejecución
    usando una única semilla maestra.
    
    """
    # Creamos un generador de números aleatorios con la semilla maestra
    rng = np.random.default_rng(master_seed)
    
    # Generamos n_runs enteros aleatorios que servirán como seeds hijas
    # Usamos un rango grande para evitar colisiones
    run_seeds = rng.integers(low=0, high=2**31 - 1, size=n_runs)
    
    return run_seeds

def results_to_dataframe(results_list):
    """
    Convierte una lista de objetos SolutionResult en un DataFrame para análisis.
    """
    data = []
    for res in results_list:
        # Asegurar que F sea un escalar para el DataFrame
        f_scalar = res.F.item() if hasattr(res.F, "item") else res.F
        
        data.append({
            "Algorithm": res.method,
            "Run": res.extra.get("Run"),
            "Seed": res.extra.get("Seed"),
            "Efficiency": f_scalar,
            "Time": res.execution_time,
            "Feasible": res.feasible
        })
    return pd.DataFrame(data)


def execute_algorithm_task(task_data):
    """
    Función 'Worker' que se ejecuta en un núcleo separado.
    Recibe todos los datos necesarios, ejecuta UN algoritmo y devuelve el SolutionResult.
    """
    # Desempaquetamos los datos de la tarea
    algo_type, problem, seed, run_id, params = task_data
    
    result = None
    
    try:
        if algo_type == "GA":
            # Ejecutar GA
            result = run_mtfp_ga(
                problem, 
                pop_size=params['pop_size'], 
                n_gen=params['n_gen'], 
                seed=seed, 
                verbose=False
            )
            
        elif algo_type == "Tabu":
            solver = TabuSearch(problem, seed=seed)
            result = solver.solve(
                max_iterations=params['iter'], 
                n_candidates=params['candidates'], 
                verbose=False
            )
            
        elif algo_type == "LS":
            solver = LS(problem, seed=seed)
            result = solver.solve(
                max_iterations=params['iter'], 
                verbose=False
            )
            
        elif algo_type == "VNS":
                    solver = VNS(problem, seed=seed)
                    result = solver.solve(
                        max_iterations=params['iter'],      
                        ls_max_iterations=params['ls_iter'],
                        verbose=False
                    )
            

        elif algo_type == "Random":
            solver = RandomSearch(problem, seed=seed)
            result = solver.solve(
                budget_nfe=params['budget_nfe'], 
                verbose=False
            )

        elif algo_type == "HillClimbing":
            solver = HillClimbing(problem, seed=seed)
            result = solver.solve(
                max_iterations=params['iter'], 
                sample_size=params['sample_size'], 
                verbose=False
            )
            
        # Inyectar metadatos para trazabilidad
        if result:
            result.extra.update({"Run": run_id, "Seed": seed})
            
        return result.to_serializable_dict()

    except Exception as e:
        #print(f"Error en Run {run_id} ({algo_type}): {e}")
        print(f"❌ Error en Run {run_id} ({algo_type}): {e}")
        import traceback
        traceback.print_exc() # Esto te ayudará a ver errores dentro del hilo
        return None
    


def run_parallel_benchmark(problem, n_runs=30, budget_nfe=50000, master_seed=42):
    
    # 1. Preparar Semillas
    run_seeds = generate_reproducible_seeds(master_seed, n_runs)
    
    # 2. Calcular Parámetros (Presupuesto NFE)
    # GA
    ga_pop = 100
    params_ga = {'pop_size': ga_pop, 'n_gen': budget_nfe // ga_pop}
    

    tabu_cand = max(20, problem.K * 2) 
    params_tabu = {
        'candidates': tabu_cand, 
        'iter': budget_nfe // tabu_cand 
    }
    
    # LS
    params_ls = {'iter': budget_nfe}
    
    # VNS
    vns_ls_iter = 50
    params_vns = {'ls_iter': vns_ls_iter, 'iter': budget_nfe // vns_ls_iter}

    
    # Random Search
    params_random = {'budget_nfe': budget_nfe}
    
    # Hill Climbing ---
    hc_sample_size = max(20, problem.K * 2)
    params_hc = {'sample_size': hc_sample_size, 'iter': budget_nfe // hc_sample_size}
    
    
    # 3. Crear la Lista de Tareas (Queue de trabajo)
    tasks = []
    
    print(f"--- PREPARANDO BENCHMARK PARALELO (N={n_runs}, Budget={budget_nfe}) ---")
    
    for run_id in range(n_runs):
        seed = int(run_seeds[run_id])
        
        # Agregamos una tupla con (Tipo, Problema, Semilla, ID, Parámetros)
        tasks.append(("GA", problem, seed, run_id, params_ga))
        tasks.append(("Tabu", problem, seed, run_id, params_tabu))
        tasks.append(("LS", problem, seed, run_id, params_ls))
        tasks.append(("VNS", problem, seed, run_id, params_vns))
        tasks.append(("Random", problem, seed, run_id, params_random))
        tasks.append(("HillClimbing", problem, seed, run_id, params_hc)) 
        
    total_tasks = len(tasks)
    n_cores = multiprocessing.cpu_count()
    print(f"🚀 Lanzando {total_tasks} tareas en {n_cores} núcleos de CPU...")
    
    # Usar ProcessPoolExecutor para progreso uniforme por tarea completada
    raw_dicts = []
    with ProcessPoolExecutor(max_workers=n_cores) as executor:
        futures = {executor.submit(execute_algorithm_task, task): task for task in tasks}
        with tqdm(total=total_tasks, desc="Procesando tareas") as pbar:
            for future in as_completed(futures):
                result = future.result()
                raw_dicts.append(result)
                pbar.update(1)
    
    print("🔄 Reconstruyendo objetos SolutionResult...")
    all_results = []
    
    for d in raw_dicts:
        if d is not None:
            # Reconvertimos el diccionario a tu objeto clase
            obj = SolutionResult.from_serializable_dict(d)
            all_results.append(obj)
            
    print(f"✅ Benchmark finalizado. {len(all_results)} resultados válidos.")
    return all_results


def plot_convergence_curves(results_list, title="Convergencia Promedio", filename=None):
    """
    Grafica la evolución promedio de la eficiencia con intervalo de confianza (std).
    Maneja automáticamente algoritmos deterministas (líneas planas) y estocásticos (curvas).
    """
    # 1. Obtener nombres únicos de algoritmos y ordenarlos
    algos = sorted(list(set(r.method for r in results_list)))
    
    # Configuración de estilo
    plt.figure(figsize=(12, 7))
    colors = plt.cm.tab10(np.linspace(0, 1, len(algos))) # Colores distintos
    
    # Definir un eje X común normalizado (0% a 100% del proceso)
    x_common = np.linspace(0, 100, 100)
    
    for idx, algo_name in enumerate(algos):
        # Filtrar resultados de este algoritmo
        algo_runs = [r for r in results_list if r.method == algo_name]
        
        if not algo_runs:
            continue
            
        interpolated_curves = []
        
        for run in algo_runs:
            hist = run.history
            
            # --- LÓGICA DE ROBUSTEZ (CRÍTICO PARA GREEDY) ---
            # Si no hay historial o tiene solo 1 punto, asumimos eficiencia constante
            if not hist or len(hist) <= 1:
                # Usamos la eficiencia final (run.F) como valor constante
                # Aseguramos que sea escalar usando .item() si es necesario
                val = run.F.item() if hasattr(run.F, "item") else run.F
                curve = np.full(100, val)
            else:
                # Caso Normal (GA, Tabu, VNS): Interpolación Lineal
                # Eje X original: 0, 1, 2 ... N iteraciones
                x_original = np.linspace(0, 100, len(hist))
                # Interpolar los valores de Y (historia) sobre el eje X común
                curve = np.interp(x_common, x_original, hist)
                
            interpolated_curves.append(curve)
        
        # Convertir a matriz numpy para estadística (n_runs x 100)
        arr_curves = np.array(interpolated_curves)
        
        # Calcular Media y Desviación Estándar
        mean_curve = np.mean(arr_curves, axis=0)
        std_curve = np.std(arr_curves, axis=0)
        
        # --- GRAFICAR ---
        color = colors[idx]
        
        # Si la desviación estándar es 0 (Greedy), dibujamos línea punteada
        if np.sum(std_curve) == 0:
            plt.plot(x_common, mean_curve, label=algo_name, color=color, 
                     linewidth=2, linestyle='--')
        else:
            # Algoritmos estocásticos: Línea sólida + Sombra
            plt.plot(x_common, mean_curve, label=algo_name, color=color, linewidth=2)
            plt.fill_between(
                x_common, 
                mean_curve - std_curve, 
                mean_curve + std_curve, 
                color=color, 
                alpha=0.15 # Transparencia de la sombra
            )
    
    # Decoración del Gráfico
    #plt.title(title, fontsize=14, pad=15)
    #plt.xlabel("% del Presupuesto Computacional (NFE)", fontsize=12)
    #plt.ylabel("Eficiencia Global (Media ± Std)", fontsize=12)
    #plt.legend(loc='lower right', frameon=True, fontsize=10, shadow=True)
    #plt.grid(True, linestyle=':', alpha=0.6)
    
    plt.legend(loc='best', frameon=False, fontsize=12)
    plt.grid(False)

    plt.xlim(0, 100)

    # Eliminar los spines (bordes) del gráfico
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # Ajuste final
    plt.tight_layout()
    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    #plt.show()

if __name__ == "__main__":
    
    # --- 1. DEFINICIÓN DE EXPERIMENTOS ---
    experiments = [
        {
            "name": "BASE_CASE",
            "desc": "Instancia pequeña para validación preliminar",
            "params": {
                "n_people": 20,
                "n_projects": 3,
                "n_skills": 2,
                "positive_ratio": 0.3
            },
            "budget_nfe": 20000,      # Presupuesto menor para el caso fácil
            "n_runs": 30
        },
        {
            "name": "PAPER_MAX",
            "desc": "Replicación del caso más grande de Gutiérrez et al. (2016)",
            "params": {
                "n_people": 100,
                "n_projects": 10,
                "n_skills": 10,
                "positive_ratio": 0.3
            },
            "budget_nfe": 50000,
            "n_runs": 30
        },
        {
            "name": "STRESS_TEST",
            "desc": "Prueba de escalabilidad (Doble tamaño)",
            "params": {
                "n_people": 200,
                "n_projects": 20,
                "n_skills": 20,
                "positive_ratio": 0.3
            },
            "budget_nfe": 100000,     # Presupuesto alto
            "n_runs": 30              # Menos runs si tarda mucho
        }
    ]

    #experiments1 = experiments[0:1]
    #experiments2 = experiments[1:2]
    #experiments3 = experiments[2:3]

    for exp in experiments:
        print("\n" + "="*80)
        print(f"🧪 EJECUTANDO: {exp['name']}")
        print(f"📝 {exp['desc']}")
        print("="*80)
        
        # 1. Crear Problema
        problem, _, _, _, _, _ = create_mtfp_problem(
            **exp['params'],
            seed=12345 
        )
        
        # 2. Benchmark Paralelo
        results = run_parallel_benchmark(
            problem, 
            n_runs=exp['n_runs'], 
            budget_nfe=exp['budget_nfe'], 
            master_seed=42
        )
        
        # 3. Greedy Baseline
        print("Ejecutando Greedy Baseline...")
        greedy_solver = Greedy(problem)
        greedy_result = greedy_solver.solve()
        greedy_result.extra.update({"Run": 0, "Seed": 0})
        results.append(greedy_result)
        
        # 4. Guardar Datos (Tablas)
        df = results_to_dataframe(results)
        summary = df.groupby("Algorithm").agg(
            Mean_Eff=('Efficiency', 'mean'),
            Std_Eff=('Efficiency', 'std'),
            Best_Eff=('Efficiency', 'max'),
            Avg_Time=('Time', 'mean'),
            Feasible_Rate=('Feasible', 'mean')
        ).sort_values(by="Mean_Eff", ascending=False)
        
        base_name = f"results/MTFP_{exp['name']}_P{exp['params']['n_people']}_Pr{exp['params']['n_projects']}_Sk{exp['params']['n_skills']}_Pos{exp['params']['positive_ratio']}"
        df.to_csv(f"{base_name}_raw.csv", index=False)
        summary.to_csv(f"{base_name}_summary.csv")
        
        print(f"\n📊 Resultados {exp['name']}:")
        print(summary)
        
        # 5. Generar y Guardar Gráfico
        plot_convergence_curves(
            results, 
            title=f"Convergencia: {exp['name']} (N={exp['params']['n_people']})", filename=f"{base_name}_plot.png"
        )

    print("\n✅ TODO FINALIZADO EXITOSAMENTE.")