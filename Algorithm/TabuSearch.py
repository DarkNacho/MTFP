import numpy as np
import time

from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from SolutionResult import SolutionResult

class TabuSearch(MTFP_BaseSolver):
    """
    Implementación de Tabu Search adaptada al framework MTFP.
    
    Características:
    - Movimiento: Reasignación de un grupo de habilidad (N^1).
    - Atributo Tabú: Índice de la habilidad modificada (no se puede volver a tocar por N turnos).
    - Criterio de Aspiración: Permite movimiento tabú si mejora el óptimo global.
    - Reinicio: Estrategia de reinicio cíclico para diversificación.
    """
    
    def solve(self, max_iterations=1000, tabu_size=None, n_candidates=None, verbose=True):
        start_time = time.time()
        
        if tabu_size is None:
            tabu_size = max(1, self.problem.K // 2)
                    
        # Validación de seguridad (por si alguien pasa un número muy grande manual)
        if tabu_size >= self.problem.K:
            tabu_size = max(1, self.problem.K - 1)

            if verbose:
                print(f"[Tabu] Ajustando tabu_size a {tabu_size} (debe ser < n_skills)")


        if n_candidates is None:
            # Queremos explorar el doble de la cantidad de habilidades disponibles
            # Para asegurar buena cobertura del vecindario
            n_candidates = max(20, self.problem.K * 2)

            
        if verbose:
            print(f"\n[Tabu Search] Iniciando búsqueda (Max Iter: {max_iterations})")
            print(f"             Tabu Size: {tabu_size}, Candidates per iter: {n_candidates}")
            print("="*60)

        # 1. Solución Inicial
        current_X = self._construct_feasible_solution()
        current_eff = self._get_efficiency_fast(current_X)
        
        best_X = current_X.copy()
        best_eff = current_eff
        
        # Estructuras de Memoria
        tabu_list = []  # Lista de índices de habilidades prohibidas
        history = [best_eff]
        
        for iteration in range(max_iterations):
            
            # --- Generación de Vecindario (Candidate List) ---
            best_neighbor_X = None
            best_neighbor_eff = -np.inf
            best_move_skill = None
            
            # Generamos 'n_candidates' vecinos posibles
            # Intentamos explorar diferentes habilidades
            candidate_skills = self.rng.choice(self.problem.K, size=n_candidates, replace=True)
            
            for skill_idx in candidate_skills:
                # 2. Generar vecino usando el operador seguro de la clase base
                neighbor_X = self._reassign_skill_group(current_X, skill_idx)
                neighbor_eff = self._get_efficiency_fast(neighbor_X)
                
                # 3. Verificar estatus Tabú y Criterio de Aspiración
                is_tabu = skill_idx in tabu_list
                is_aspiration = neighbor_eff > best_eff
                
                if not is_tabu or is_aspiration:
                    # Si es mejor que el mejor vecino de esta iteración, lo guardamos
                    if neighbor_eff > best_neighbor_eff:
                        best_neighbor_X = neighbor_X
                        best_neighbor_eff = neighbor_eff
                        best_move_skill = skill_idx

            # --- Movimiento ---
            if best_neighbor_X is not None:
                current_X = best_neighbor_X
                current_eff = best_neighbor_eff
                
                # Actualizar Mejor Global
                if current_eff > best_eff:
                    best_X = current_X.copy()
                    best_eff = current_eff
                    if verbose:
                        print(f"[Tabu] Iter {iteration}: Nuevo récord = {best_eff:.4f}")

                # Actualizar Lista Tabú
                tabu_list.append(best_move_skill)
                if len(tabu_list) > tabu_size:
                    tabu_list.pop(0)
            
            # --- Estrategia de Reinicio (Diversificación) ---
            # Similar a tu código original: cada 200 iteraciones, reiniciamos desde otro punto
            if iteration > 0 and iteration % 200 == 0:
                if verbose: print(f"[Tabu] Iter {iteration}: Reinicio estocástico...")
                current_X = self._construct_feasible_solution()
                current_eff = self._get_efficiency_fast(current_X)
                tabu_list = [] # Limpiar memoria

            history.append(best_eff)

        end_time = time.time()
        execution_time = end_time - start_time
        
        # Evaluación final completa
        final_eval = self.problem.evaluate_solution(best_X)

        if verbose:
            print(f"\n[Tabu Search] Búsqueda completada.")
            print(f"   Eficiencia Final: {best_eff:.4f}")
            print(f"   Tiempo: {execution_time:.2f}s")

        return SolutionResult.from_eval(
            X=best_X,
            eval_result=final_eval,
            method="Tabu Search",
            history=history,
            execution_time=execution_time
        )