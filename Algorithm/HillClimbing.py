import time
import numpy as np

from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from SolutionResult import SolutionResult


class HillClimbing(MTFP_BaseSolver):
    """
    Hill Climbing (First-Improvement) adaptado para MTFP.
    
    Diferencia clave con tu código original:
    - En lugar de 'swaps' aleatorios (que suelen ser infactibles),
      usamos reasignación de habilidades completa (siempre factible).
    """
    
    def solve(self, max_iterations=500, sample_size=20, verbose=True):
        start_time = time.time()
        
        if verbose:
            print(f"\n[Hill Climbing] Iniciando búsqueda (Max Iter: {max_iterations})")
            print(f"                Muestras por iteración: {sample_size}")
            print("="*60)

        # 1. Solución Inicial (Usando la base constructiva)
        current_X = self._construct_feasible_solution()
        current_eff = self._get_efficiency_fast(current_X)
        
        history = [current_eff]
        
        for iteration in range(max_iterations):
            improved = False
            
            # Intentamos 'sample_size' vecinos aleatorios
            # Estrategia: First-Improvement (Nos quedamos con el primero que mejore)
            for _ in range(sample_size):
                
                # Generar vecino modificando UNA habilidad al azar
                # (Esto garantiza factibilidad, a diferencia del swap simple)
                skill_idx = self.rng.integers(0, self.problem.K)
                neighbor_X = self._reassign_skill_group(current_X, skill_idx)
                neighbor_eff = self._get_efficiency_fast(neighbor_X)
                
                # Si mejora, lo aceptamos inmediatamente y pasamos a la siguiente iteración
                if neighbor_eff > current_eff:
                    current_X = neighbor_X
                    current_eff = neighbor_eff
                    improved = True
                    
                    if verbose:
                        print(f"[Hill Climbing] Iter {iteration}: Mejora a {current_eff:.4f}")
                    break # Salir del bucle de muestreo (First Improvement)
            
            history.append(current_eff)
            
            # Criterio de Parada: Si tras 'sample_size' intentos no mejoramos, estamos en un Óptimo Local
            if not improved:
                if verbose:
                    print(f"[Hill Climbing] Iter {iteration}: Estancado (Óptimo Local alcanzado).")
                break
                
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Evaluación final completa
        final_eval = self.problem.evaluate_solution(current_X)
        
        if verbose:
            print(f"[Hill Climbing] Fin. Eficiencia Final: {current_eff:.4f}")

        return SolutionResult.from_eval(
            X=current_X,
            eval_result=final_eval,
            method="Hill Climbing",
            history=history,
            execution_time=execution_time
        )