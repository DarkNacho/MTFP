import time
from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from SolutionResult import SolutionResult

class LS(MTFP_BaseSolver):
    """
    Implementación de Local Search (LS).
    Explora el vecindario N^1 hasta alcanzar un óptimo local.
    """
    def solve(self, max_iterations=5000, verbose=True):
        start_time = time.time()
        if verbose: print(f"\n[LS] Iniciando Búsqueda Local...")

        # Solución inicial
        current_X = self._construct_feasible_solution()
        
        # Ejecutar mejora
        best_X, best_eff, history = self.improve_solution(
            current_X, max_iterations=max_iterations, return_history=True
        )

        execution_time = time.time() - start_time
        final_eval = self.problem.evaluate_solution(best_X)
        
        return SolutionResult.from_eval(
            X=best_X, eval_result=final_eval, method="Local Search",
            history=history, execution_time=execution_time
        )

    def improve_solution(self, solution, max_iterations=1000, return_history=False):
        """
        Subrutina pública: Toma una solución y la mejora usando Hill Climbing en N^1.
        Esta es la función que VNS llamará.
        """
        current_X = solution.copy()
        current_eff = self._get_efficiency_fast(current_X)
        
        best_X = current_X.copy()
        best_eff = current_eff
        history = [best_eff]
        
        for _ in range(max_iterations):
            improved_step = False
            
            # Generar vecino N^1 (cambiar 1 habilidad al azar)
            skill_idx = self.rng.integers(0, self.problem.K)
            neighbor_X = self._reassign_skill_group(current_X, skill_idx)
            neighbor_eff = self._get_efficiency_fast(neighbor_X)
            
            # Criterio Greedy (Hill Climbing)
            if neighbor_eff > current_eff:
                current_X = neighbor_X
                current_eff = neighbor_eff
                improved_step = True
                
                if current_eff > best_eff:
                    best_X = current_X.copy()
                    best_eff = current_eff
            
            if return_history:
                history.append(best_eff)
            
            # Opcional: Si exploramos mucho sin mejorar, podríamos salir antes
            # pero el paper sugiere iteraciones fijas o hasta convergencia.
        
        if return_history:
            return best_X, best_eff, history
        return best_X, best_eff