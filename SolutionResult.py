import numpy as np
import time

class SolutionResult:
    def __init__(self, X, F, feasible, max_violation, constraints, project_efficiencies,
                 method, history=None, execution_time=None, extra=None):
        self.X = X
        self.F = np.array(F)
        self.feasible = feasible
        self.max_violation = max_violation
        self.constraints = constraints
        self.project_efficiencies = project_efficiencies
        self.method = method
        self.history = history if history is not None else []
        self.execution_time = execution_time
        self.extra = extra if extra is not None else {}

    @classmethod
    def from_eval(cls, X, eval_result, method, history=None, execution_time=None, extra=None):
        return cls(
            X=X,
            F=eval_result['efficiency'],
            feasible=eval_result['feasible'],
            max_violation=eval_result['max_violation'],
            constraints=eval_result['constraints'],
            project_efficiencies=eval_result['project_efficiencies'],
            method=method,
            history=history,
            execution_time=execution_time,
            extra=extra
        )
    @classmethod
    def from_pymoo_result(cls, res, problem, method_name="GA (Pymoo)"):
        """Crea resultado desde un objeto Result de Pymoo."""
        
        # 1. Obtener la mejor eficiencia final (Manejo robusto de tipos)
        # res.F puede ser un float o un array numpy dependiendo de la versión/config
        if res.F is not None:
            if isinstance(res.F, np.ndarray):
                # Si es array (n_obj,), tomamos el escalar. .item() es seguro.
                best_val = res.F.item() if res.F.size == 1 else res.F[0]
            else:
                best_val = res.F
        else:
            # Fallback seguro: extraer de la población óptima
            best_val = res.opt.get("F")[0][0]

        efficiency = -best_val # Convertir minimización a maximización (Eficiencia)
        
        # 2. Historial de Convergencia
        history = []
        if res.history:
            # CORRECCIÓN AQUÍ:
            # algo.opt es una Population. No tiene .F directo.
            # Usamos .get("F") para sacar los valores de toda la población óptima 
            # y tomamos el mejor (mínimo).
            history = [-np.min(algo.opt.get("F")) for algo in res.history]
            
        # 3. Evaluación detallada final para obtener restricciones y breakdown
        # res.X suele ser (n_var,) para single-solution, pero aseguramos
        X_final = res.X[0] if (isinstance(res.X, np.ndarray) and res.X.ndim > 1) else res.X
        final_eval = problem.evaluate_solution(X_final)
        
        return cls(
            X=X_final,
            F=efficiency,
            feasible=final_eval['feasible'],
            max_violation=final_eval['max_violation'],
            constraints=final_eval['constraints'],
            project_efficiencies=final_eval['project_efficiencies'],
            method=method_name,
            history=history,
            execution_time=res.exec_time
        )
    

    def to_serializable_dict(self):
            """
            Convierte el objeto en un diccionario de tipos nativos (listas, floats, ints).
            Seguro para enviar entre procesos o guardar en disco.
            """
            return {
                "X": self.X,  # Numpy arrays son seguros con Joblib
                "F": self.F,
                "feasible": self.feasible,
                "max_violation": self.max_violation,
                "constraints": self.constraints, # Asumimos numpy array o lista
                "project_efficiencies": self.project_efficiencies,
                "method": self.method,
                "history": self.history,
                "execution_time": self.execution_time,
                "extra": self.extra
            }

    @classmethod
    def from_serializable_dict(cls, data):
        """
        Reconstruye el objeto SolutionResult a partir del diccionario.
        """
        return cls(
            X=data["X"],
            F=data["F"],
            feasible=data["feasible"],
            max_violation=data["max_violation"],
            constraints=data["constraints"],
            project_efficiencies=data["project_efficiencies"],
            method=data["method"],
            history=data["history"],
            execution_time=data["execution_time"],
            extra=data["extra"]
        )


def compare_solutions_side_by_side(solutions_dict):
    """
    Compare multiple SolutionResult objects in a clear table format.

    Parameters:
    -----------
    solutions_dict : dict
        Dictionary with {solution_name: SolutionResult}
    """

    print("┌" + "─" * 88 + "┐")
    print("│" + "SOLUTIONS COMPARISON".center(88) + "│")
    print("└" + "─" * 88 + "┘")

    results = {}

    # Collect results for each solution
    for name, sol in solutions_dict.items():
        results[name] = {
            'efficiency': float(sol.F),
            'feasible': sol.feasible,
            'max_violation': sol.max_violation,
            'project_efficiencies': sol.project_efficiencies
        }

    # Print comparison table
    print("\n" + "="*88)
    print(f"{'SOLUTION':<20} {'EFFICIENCY':<12} {'FEASIBLE':<10} {'MAX VIOLATION':<15} {'PROJECT EFFICIENCIES'}")
    print("="*88)

    for name, result in results.items():
        feasible_str = "✅" if result['feasible'] else "❌"
        proj_eff_str = " ".join([f"{e:.2f}" for e in result['project_efficiencies']])
        print(f"{name:<20} {result['efficiency']:<12.4f} {feasible_str:<10} {result['max_violation']:<15.6f} [{proj_eff_str}]")

    # Determine winner
    feasible_solutions = {k: v for k, v in results.items() if v['feasible']}

    if feasible_solutions:
        winner = max(feasible_solutions.keys(),
                     key=lambda x: feasible_solutions[x]['efficiency'])

        print("\n" + "="*88)
        print("🏆 WINNER ANALYSIS")
        print("="*88)
        print(f"\nBest solution: {winner}")
        print(f"Efficiency: {feasible_solutions[winner]['efficiency']:.4f}")

        # Calculate improvements over others
        print("\nImprovement over other solutions:")
        for name, result in results.items():
            if name != winner and result['feasible']:
                improvement = (feasible_solutions[winner]['efficiency'] - result['efficiency']) / result['efficiency'] * 100
                print(f"  • {name}: {improvement:+.2f}% better")
    else:
        print("\n⚠️ No feasible solutions found!")

    return results   