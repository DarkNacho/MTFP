import time
from Algorithm.MTFP_BaseSolver import MTFP_BaseSolver
from SolutionResult import SolutionResult

class RandomSearch(MTFP_BaseSolver):
    def solve(self, budget_nfe=50000, verbose=False):
        start = time.time()
        
        best_X = None
        best_eff = -1.0
        history = []
        
        for _ in range(budget_nfe):
            # Generar solución aleatoria válida
            curr_X = self._construct_feasible_solution()
            curr_eff = self._get_efficiency_fast(curr_X)
            
            if curr_eff > best_eff:
                best_eff = curr_eff
                best_X = curr_X.copy()
            
            # En Random Search, el historial suele ser "el mejor hasta ahora"
            history.append(best_eff)
            
        return SolutionResult.from_eval(
            best_X, self.problem.evaluate_solution(best_X), 
            "Random Search", history, time.time() - start
        )