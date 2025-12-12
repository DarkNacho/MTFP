import numpy as np
import time

class MTFP_BaseSolver:
    """
    Implementa la heurística constructiva basada en la descomposición por habilidades
    """
    def __init__(self, problem, seed=None):
        self.problem = problem
        self.rng = np.random.default_rng(seed)

    def _construct_feasible_solution(self) -> np.ndarray:
        """Genera una solución inicial factible desde cero."""
        sol = np.zeros(self.problem.n_var, dtype=int)
        for k in range(self.problem.K):
            sol = self._reassign_skill_group(sol, k)
        return sol


    def _reassign_skill_group(self, solution: np.ndarray, skill_idx: int) -> np.ndarray:
        """
        Versión Ajustada al Paper:
        Permite que una persona divida su tiempo entre proyectos (ej. 0.5 en P1, 0.5 en P2).
        """
        # 1. Decodificar
        alloc_matrix = self.problem.get_allocation_matrix(solution)
        people_idxs = self.problem.skill_groups[skill_idx]
        
        # 2. Resetear asignaciones de este grupo (Borrado lógico)
        # Esto libera la capacidad de todos en este skill
        alloc_matrix[people_idxs, :] = 0.0
        
        # 3. Reconstruir factibilidad
        
        # Array para rastrear cuánto tiempo libre le queda a cada persona (inicialmente 1.0)
        # Usamos un diccionario o mapa para acceso rápido basado en el índice global
        remaining_capacity = {pidx: 1.0 for pidx in people_idxs}
        
        # Lista de candidatos base (se baraja para estocasticidad)
        candidates = list(people_idxs)
        self.rng.shuffle(candidates)
        
        for p_idx in range(self.problem.P):
            req = self.problem.R[skill_idx, p_idx]
            if req <= 0: continue
            
            current_fill = 0.0
            
            # Intentamos llenar el requerimiento con los candidatos disponibles
            # Barajamos de nuevo para cada proyecto para evitar sesgos de orden? 
            # El paper no especifica, pero barajar solo una vez al inicio (como tenías)
            # suele ser más eficiente. Mantengamos tu orden aleatorio original.
            
            for person_idx in candidates:
                if current_fill >= req: break
                
                # Capacidad actual de esta persona
                cap = remaining_capacity[person_idx]
                
                # Si no tiene capacidad útil (menor al nivel mínimo), saltar
                if cap < self.problem.levels[1]: # asumiendo levels[0] es 0.0
                    continue
                
                needed = req - current_fill
                
                # Encontrar niveles válidos que quepan en lo que se necesita 
                # Y que quepan en la capacidad de la persona
                valid_levels = [l for l in self.problem.levels 
                                if l <= needed + 1e-5 and l <= cap + 1e-5]
                
                if not valid_levels: continue
                
                # Greedy: tomar el nivel más alto posible (excluyendo 0 si es posible)
                best_level = valid_levels[-1]
                
                if best_level > 0:
                    alloc_matrix[person_idx, p_idx] = best_level
                    current_fill += best_level
                    
                    # Actualizar capacidad restante
                    remaining_capacity[person_idx] -= best_level

        # 4. Codificar de vuelta
        return self._encode(alloc_matrix)
    


    def _get_efficiency_fast(self, X_indices):
        """Evaluación rápida (solo escalar F)."""
        X_reshaped = X_indices.reshape(1, -1)
        out = {}
        self.problem._evaluate(X_reshaped, out)
        return -out["F"][0, 0] # Convertir minimización a maximización

    def _encode(self, alloc_matrix: np.ndarray) -> np.ndarray:
        """Helper: Matriz -> Índices"""
        X_flat = []
        for h in range(self.problem.H):
            for p in range(self.problem.P):
                val = alloc_matrix[h, p]
                idx = (np.abs(self.problem.levels - val)).argmin()
                X_flat.append(idx)
        return np.array(X_flat, dtype=int)