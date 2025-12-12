import time
import numpy as np
from Algorithm.LS import LS
from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from SolutionResult import SolutionResult


class VNS(MTFP_BaseSolver):
    """
    Implementación de VNS.
    Usa 'Shaking' para diversificar y 'MTFP_LS' para intensificar.
    """
    def __init__(self, problem, seed=None):
        super().__init__(problem, seed)
        # Composición: VNS tiene un LS para la fase de mejora
        self.ls_engine = LS(problem, seed)

    def solve(self, max_iterations=1000, ls_max_iterations=50,  max_time_seconds=None, verbose=True):
        start_time = time.time()
        if verbose: print(f"\n[VNS] Iniciando VNS (usa LS interna)...")

        # 1. Inicialización
        current_X = self._construct_feasible_solution()
        current_eff = self._get_efficiency_fast(current_X)
        
        best_X = current_X.copy()
        best_eff = current_eff
        history = [best_eff]
        
        k = 1 # Tamaño del vecindario inicial
        iteration = 0
        
        while iteration < max_iterations:
            if max_time_seconds and (time.time() - start_time) > max_time_seconds:
                break
                
            # --- FASE 1: Shaking (Perturbación) ---
            # Generar vecino en N^k (cambiar k habilidades)
            shaken_X = self._shake(current_X, k)
            
            # --- FASE 2: Local Search (Mejora) ---
            # Delegamos la mejora a la clase LS (usando N^1 internamente)
            # El paper define esto en Algoritmo 4, línea 9 
            # Usamos pocas iteraciones internas para no hacerlo muy lento
            improved_X, improved_eff = self.ls_engine.improve_solution(
                shaken_X, max_iterations=ls_max_iterations # LS corta y rápida
            )
            
            # --- FASE 3: Move (Criterio de Aceptación) ---
            if improved_eff > current_eff:
                # Mejora encontrada: Aceptamos y reiniciamos k
                current_X = improved_X
                current_eff = improved_eff
                k = 1
                
                if current_eff > best_eff:
                    best_X = current_X.copy()
                    best_eff = current_eff
                    if verbose:
                        print(f"[VNS] Iter {iteration} (k={k}): Nuevo récord = {best_eff:.4f}")
            else:
                # No mejora: Expandimos el vecindario
                k += 1
                # Si nos pasamos del número de habilidades, volvemos a 1
                if k > self.problem.K:
                    k = 1
            
            history.append(best_eff)
            iteration += 1

        execution_time = time.time() - start_time
        final_eval = self.problem.evaluate_solution(best_X)
        
        return SolutionResult.from_eval(
            X=best_X, eval_result=final_eval, method="Variable Neighborhood Search",
            history=history, execution_time=execution_time,
            extra={"final_k": k}
        )

    def _shake(self, solution: np.ndarray, k: int) -> np.ndarray:
        """
        Operador de Shaking: Cambia k habilidades aleatorias simultáneamente.
        """
        new_sol = solution.copy()
        # Elegir k habilidades únicas
        skills_to_change = self.rng.choice(self.problem.K, size=min(k, self.problem.K), replace=False)
        
        for skill_idx in skills_to_change:
            # Reusamos la lógica de la clase base
            new_sol = self._reassign_skill_group(new_sol, skill_idx)
            
        return new_sol