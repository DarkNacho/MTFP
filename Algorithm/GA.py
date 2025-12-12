from pymoo.core.sampling import Sampling
from pymoo.core.mutation import Mutation
from pymoo.core.crossover import Crossover
import numpy as np
from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize

from SolutionResult import SolutionResult 

def run_mtfp_ga_standardized(problem, pop_size=100, n_gen=500, seed=42, verbose=True):
    """
    Ejecuta el GA con operadores de descomposición y devuelve un SolutionResult.
    """
    
    # 1. Configurar el Algoritmo con tus Clases Custom
    algorithm = GA(
        pop_size=pop_size,
        sampling=MTFPDecompositionSampling(problem),      # Tu sampling
        crossover=MTFPSkillCrossover(problem, prob=0.9),  # Tu crossover
        mutation=MTFPSkillMutation(problem, prob=0.2),    # Tu mutation
        eliminate_duplicates=True
    )
    
    if verbose:
        print(f"\n[GA-Decomposition] Iniciando (Gen: {n_gen}, Pop: {pop_size})...")

    # 2. Ejecutar Pymoo Minimize
    # save_history=True es vital para graficar convergencia después
    res = minimize(
        problem,
        algorithm,
        ('n_gen', n_gen),
        seed=seed,
        verbose=verbose,
        save_history=True 
    )
    
    # 3. Convertir al formato unificado SolutionResult
    # Usamos el método de clase que creamos anteriormente
    result = SolutionResult.from_pymoo_result(
        res, 
        problem, 
        method_name="Genetic Algorithm"
    )
    
    if verbose:
        print(f"[GA] Fin. Eficiencia: {result.F:.4f}")
        
    return result

class MTFPDecompositionSampling(Sampling):
    """
    Sampling (Inicialización) basado en la descomposición por habilidades del Paper.
    Usa MTFP_BaseSolver para generar soluciones iniciales factibles y diversas.
    """
    
    def __init__(self, problem):
        super().__init__()
        self.problem = problem
        # Instanciamos el solver base como "fábrica" de soluciones
        # No pasamos seed fija aquí para asegurar diversidad en cada llamada
        self.solver_factory = MTFP_BaseSolver(problem) 
    
    def _do(self, problem, n_samples, **kwargs):
        # Matriz de población vacía
        X = np.zeros((n_samples, problem.n_var), dtype=int)
        
        # Generar n_samples individuos usando el Algoritmo 1 del paper
        for i in range(n_samples):
            # _construct_feasible_solution usa shuffle interno, 
            # así que cada iteración produce una solución distinta.
            X[i, :] = self.solver_factory._construct_feasible_solution()
            
        return X
    

class MTFPSkillMutation(Mutation):
    """
    Mutación que 'reinicia' una habilidad usando la heurística constructiva.
    Equivale a un movimiento aleatorio en el vecindario N^1.
    """
    def __init__(self, problem, prob=0.2):
        super().__init__()
        self.prob = prob
        self.problem = problem
        # Instanciamos el solver base para usar su lógica de reasignación
        # (Asumiendo que tienes la clase MTFP_BaseSolver definida arriba)
        self.solver_helper = MTFP_BaseSolver(problem) 

    def _do(self, problem, X, **kwargs):
        n_matings, n_var = X.shape
        Y = X.copy()
        
        for k in range(n_matings):
            if np.random.random() < self.prob:
                individual = X[k].copy()
                
                # Elegir UNA habilidad al azar para mutar
                skill_to_mutate = np.random.randint(0, self.problem.K)
                
                # Usar la lógica segura de reasignación
                # Nota: _reassign_skill_group devuelve un nuevo array completo
                # pero queremos modificar solo el individuo actual.
                # Dado que reassign devuelve el individuo completo modificado, sirve directo.
                mutated_ind = self.solver_helper._reassign_skill_group(individual, skill_to_mutate)
                
                Y[k] = mutated_ind
        
        return Y
    

class MTFPSkillCrossover(Crossover):
    """
    Crossover que intercambia BLOQUES de habilidades completos.
    Garantiza que si los padres son factibles, los hijos también lo son (estructuralmente).
    """
    def __init__(self, problem, prob=0.9):
        super().__init__(2, 2)
        self.prob = prob
        self.problem = problem

    def _do(self, problem, X, **kwargs):
        n_parents, n_matings, n_var = X.shape
        Y = np.full((self.n_offsprings, n_matings, n_var), -1, dtype=int)
        
        for k in range(n_matings):
            # Padres
            parent_a, parent_b = X[0, k], X[1, k]
            
            # Hijos (copias iniciales)
            child_1, child_2 = parent_a.copy(), parent_b.copy()
            
            # Si ocurre el cruce
            if np.random.random() < self.prob:
                # Iterar por cada Habilidad (Bloque)
                for skill_idx in range(self.problem.K):
                    # Obtener las variables que pertenecen a esta habilidad
                    # Necesitamos mapear personas -> índices de variables (flat)
                    people_idxs = self.problem.skill_groups[skill_idx]
                    
                    # Calcular los índices planos en el array X
                    # X es (H * P). Las variables de la persona i son [i*P : (i+1)*P]
                    var_indices = []
                    for p_idx in people_idxs:
                        start = p_idx * self.problem.P
                        end = start + self.problem.P
                        var_indices.extend(range(start, end))
                    
                    var_indices = np.array(var_indices)
                    
                    # Crossover Uniforme de BLOQUES
                    # 50% de probabilidad de intercambiar la configuración de ESTA habilidad
                    if np.random.random() < 0.5:
                        # Intercambiar genes solo para esta habilidad
                        child_1[var_indices] = parent_b[var_indices]
                        child_2[var_indices] = parent_a[var_indices]
            
            Y[0, k], Y[1, k] = child_1, child_2
            
        return Y
    

def run_mtfp_ga(problem, pop_size=100, n_gen=500, seed=42, verbose=True):
    """
    Ejecuta el GA con operadores de descomposición y devuelve un SolutionResult.
    """
    
    # 1. Configurar el Algoritmo con tus Clases Custom
    algorithm = GA(
        pop_size=pop_size,
        sampling=MTFPDecompositionSampling(problem),      # Tu sampling
        crossover=MTFPSkillCrossover(problem, prob=0.9),  # Tu crossover
        mutation=MTFPSkillMutation(problem, prob=0.2),    # Tu mutation
        eliminate_duplicates=True
    )
    
    if verbose:
        print(f"\n[GA-Decomposition] Iniciando (Gen: {n_gen}, Pop: {pop_size})...")

    # 2. Ejecutar Pymoo Minimize
    # save_history=True es vital para graficar convergencia después
    res = minimize(
        problem,
        algorithm,
        ('n_gen', n_gen),
        seed=seed,
        verbose=verbose,
        save_history=True,
        return_least_infeasible=True
    )
    
    # 3. Convertir al formato unificado SolutionResult
    # Usamos el método de clase que creamos anteriormente
    result = SolutionResult.from_pymoo_result(
        res, 
        problem, 
        method_name="Genetic Algorithm"
    )
    
    if verbose:
        print(f"[GA] Fin. Eficiencia: {result.F:.4f}")
        
    return result