import numpy as np
import time
from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from SolutionResult import SolutionResult

class Greedy(MTFP_BaseSolver):
    """
    Tu heurística Greedy original (Project-Oriented).
    Es determinista: siempre produce la misma solución para el mismo problema.
    """
    
    def solve(self, verbose=False):
        start = time.time()
        
        allocation = np.zeros((self.problem.H, self.problem.P))
        levels = self.problem.levels
        
        # Copia de requerimientos para no modificar el problema original
        R_temp = self.problem.R.copy()
        
        # Iterar Proyecto -> Habilidad (A diferencia del paper que es Skill -> Project)
        for l in range(self.problem.P):
            for k in range(self.problem.K):
                required = R_temp[k, l]
                if required <= 0: continue
                
                people_in_skill = self.problem.skill_groups[k]
                
                # Sin shuffle -> Determinista
                for person in people_in_skill:
                    if required <= 1e-6: break
                    
                    current_total = allocation[person, :].sum()
                    if current_total >= 1.0 - 1e-6: continue
                    
                    available = 1.0 - current_total
                    to_allocate = min(available, required)
                    
                    # Snap al nivel más cercano
                    level_idx = np.argmin(np.abs(levels - to_allocate))
                    actual = levels[level_idx]
                    
                    if actual > 0:
                        allocation[person, l] = actual
                        required -= actual
                        
        # Convertir matriz a vector X (índices)
        X = self._encode(allocation)
        
        # Evaluar
        end = time.time()
        final_eval = self.problem.evaluate_solution(X)
        
        return SolutionResult.from_eval(
            X, final_eval, 
            method="Greedy", 
            execution_time=end - start
        )