import numpy as np
from pymoo.core.problem import Problem
from typing import Optional

class MTFP(Problem):
    """
    Multiple Team Formation Problem (MTFP) - Exact implementation from the paper.
    
    This is the formulation from:
    "The multiple team formation problem using sociometry"
    Computers & Operations Research 75 (2016) 150–162
    
    Features:
    - Exact quadratic objective function from paper
    - Constraints as in Section 3.3
    - Discrete dedication levels (e.g., 0, 0.25, 0.5, 0.75, 1.0)
    - Each person has exactly one skill
    """
    
    def __init__(self,
                 n_people: int,
                 n_projects: int,
                 n_skills: int,
                 affinity_matrix: np.ndarray,
                 requirements: np.ndarray,
                 skill_of_person: np.ndarray,
                 project_weights: Optional[np.ndarray] = None,
                 dedication_levels: Optional[np.ndarray] = None):
        """
        Initialize the MTFP problem.
        
        Parameters:
        -----------
        n_people : int
            Number of people (H)
        n_projects : int
            Number of projects (m)
        n_skills : int
            Number of skills (f)
        affinity_matrix : np.ndarray (H x H)
            Sociometric matrix S with values in {-1, 0, +1}
        requirements : np.ndarray (K x P)
            Requirements matrix R, r_kl = required person-time of skill k for project l
        skill_of_person : np.ndarray (H,)
            Skill index (0 to K-1) for each person
        project_weights : Optional[np.ndarray] (P,)
            Weights w_l for each project (default: equal weights)
        dedication_levels : Optional[np.ndarray]
            Allowed dedication levels (default: [0, 0.25, 0.5, 0.75, 1.0])
        """
        # Store dimensions
        self.H = int(n_people)
        self.P = int(n_projects)
        self.K = int(n_skills)
        
        # Store problem data
        self.S = np.asarray(affinity_matrix, dtype=float)  # Sociometric matrix
        self.R = np.asarray(requirements, dtype=float)     # Requirements matrix
        self.skill_of_person = np.asarray(skill_of_person, dtype=int)  # Skill of each person
        
        # Set dedication levels (default from paper)
        if dedication_levels is None:
            self.levels = np.array([0.0, 0.25, 0.5, 0.75, 1.0], dtype=float)
        else:
            self.levels = np.asarray(dedication_levels, dtype=float)
        
        # Set project weights (default: equal)
        if project_weights is None:
            self.w = np.ones(self.P, dtype=float) / self.P
        else:
            self.w = np.asarray(project_weights, dtype=float)
            self.w = self.w / self.w.sum()  # Normalize to sum to 1 as in paper
        
        # Create skill groups for efficient constraint calculation
        self.skill_groups = [np.where(self.skill_of_person == k)[0] for k in range(self.K)]
        
        # Calculate total requirement per project (for efficiency denominator)
        self.total_req_per_project = np.sum(self.R, axis=0)
        
        # Number of variables: H * P (allocation of each person to each project)
        n_var = self.H * self.P
        
        # Number of objectives: 1 (maximize global efficiency)
        n_obj = 1
        
        # Number of constraints:
        # H: Person capacity constraints (Σ_l x_il ≤ 1)
        # K*P: Skill requirement constraints (|Σ_{i in skill k} x_il - r_kl| ≤ ε)
        n_constr = self.H + self.K * self.P
        
        # Variable bounds: indices into dedication levels
        L = len(self.levels)
        xl = np.zeros(n_var, dtype=int)
        xu = np.full(n_var, L - 1, dtype=int)
        
        # Initialize problem for pymoo
        super().__init__(n_var=n_var, n_obj=n_obj, n_constr=n_constr,
                         xl=xl, xu=xu, type_var=np.int64)
    
    def _decode(self, X: np.ndarray) -> np.ndarray:
        """
        Convert decision variables (indices) to allocation matrix.
        
        Parameters:
        -----------
        X : np.ndarray (n_pop, n_var) or (n_var,)
            Decision variables as indices into self.levels
            
        Returns:
        --------
        allocation : np.ndarray (n_pop, H, P) or (H, P)
            Allocation matrix with actual dedication values
        """
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        n_pop = X.shape[0]
        X_reshaped = X.reshape((n_pop, self.H, self.P))
        
        # Ensure indices are integers (round to nearest integer)
        X_int = np.round(X_reshaped).astype(int)
        
        # Clip to valid range
        X_int = np.clip(X_int, 0, len(self.levels) - 1)
        
        return self.levels[X_int]
    
    def _evaluate(self, X: np.ndarray, out: dict, *args, **kwargs):
        """
        Evaluate objective and constraints for pymoo.
        
        Note: pymoo minimizes, so we return -efficiency for maximization.
        """
        n_pop = X.shape[0]
        allocation = self._decode(X)  # Shape: (n_pop, H, P)
        
        F = np.zeros((n_pop, 1))      # Objectives
        G = np.zeros((n_pop, self.n_constr))  # Constraints
        
        for p in range(n_pop):
            alloc_p = allocation[p]
            
            # Calculate global efficiency (to maximize)
            efficiency = self._calculate_global_efficiency(alloc_p)
            F[p, 0] = -efficiency  # Negative for maximization
            
            # Calculate constraint violations
            G[p, :] = self._calculate_constraints(alloc_p)
        
        out["F"] = F
        out["G"] = G
    
    def _calculate_global_efficiency(self, allocation: np.ndarray) -> float:
        """
        Calculate global efficiency E = Σ_l w_l * e_l.
        
        Uses exact formula from paper (Section 3.1).
        Note: This formula assumes constraints are satisfied.
        For infeasible solutions, efficiency may be outside [0, 1].
        """
        total_efficiency = 0.0
        
        for l in range(self.P):
            x_l = allocation[:, l]
            
            # Calculate project efficiency e_l
            e_l = self._calculate_project_efficiency(x_l, l)
            
            # Weighted contribution
            total_efficiency += self.w[l] * e_l
        
        return total_efficiency
    
    def _calculate_project_efficiency(self, x_l: np.ndarray, project_idx: int) -> float:
        """
        Calculate efficiency for a single project.
        
        e_l = 0.5 * (1 + Σ_{i,j} S_ij * x_il * x_jl / (Σ_a r_al)^2)
        """
        # Numerator: quadratic form
        numerator = x_l.T @ self.S @ x_l
        
        # Denominator: (total requirement for project)^2
        denominator = self.total_req_per_project[project_idx] ** 2
        
        if abs(denominator) < 1e-12:
            return 0.5  # Default when no requirements
        
        return 0.5 * (1.0 + numerator / denominator)
    
    def _calculate_constraints(self, allocation: np.ndarray, epsilon: float = 1e-4) -> np.ndarray:
        """
        Calculate constraint violations.
        
        Constraints should be ≤ 0 for feasibility.
        Returns vector g where g ≤ 0 means feasible.
        """
        g = np.zeros(self.n_constr)
        idx = 0
        
        # 1. Person capacity constraints: Σ_l x_il ≤ 1
        person_totals = allocation.sum(axis=1)
        g[idx:idx+self.H] = person_totals - 1.0
        idx += self.H
        
        # 2. Skill requirement constraints: |Σ_{i in skill k} x_il - r_kl| ≤ ε
        # Convert to g ≤ 0 by subtracting epsilon
        for k in range(self.K):
            people_in_skill = self.skill_groups[k]
            for l in range(self.P):
                delivered = np.sum(allocation[people_in_skill, l])
                required = self.R[k, l]
                g[idx] = abs(delivered - required) - epsilon
                idx += 1
        
        return g
    
    # Helper methods for analysis
    def get_allocation_matrix(self, X: np.ndarray) -> np.ndarray:
        """Convert decision variables to allocation matrix."""
        return self._decode(X.reshape(1, -1))[0] if X.ndim == 1 else self._decode(X)
    
    def is_feasible(self, X: np.ndarray, tol: float = 1e-4) -> bool:
        """Check if solution is feasible."""
        allocation = self.get_allocation_matrix(X)
        constraints = self._calculate_constraints(allocation, epsilon=tol)
        return np.all(constraints <= 0)
    
    def evaluate_solution(self, X: np.ndarray) -> dict:
        """
        Comprehensive evaluation of a solution.
        
        Returns dictionary with:
        - efficiency: Global efficiency
        - feasible: Boolean
        - allocation: Allocation matrix
        - constraints: Constraint violations
        - person_totals: Total dedication per person
        - project_totals: Total allocation per project
        """
        allocation = self.get_allocation_matrix(X)
        
        # Calculate metrics
        efficiency = self._calculate_global_efficiency(allocation)
        constraints = self._calculate_constraints(allocation)
        feasible = np.all(constraints <= 0)
        
        # Per-project efficiencies
        project_efficiencies = np.zeros(self.P)
        for l in range(self.P):
            x_l = allocation[:, l]
            project_efficiencies[l] = self._calculate_project_efficiency(x_l, l)
        
        return {
            'efficiency': efficiency,
            'feasible': feasible,
            'allocation': allocation,
            'constraints': constraints,
            'max_violation': np.max(constraints) if not feasible else 0.0,
            'project_efficiencies': project_efficiencies,
            'person_totals': allocation.sum(axis=1),
            'project_totals': allocation.sum(axis=0),
            'requirements_per_project': self.total_req_per_project
        }


def create_mtfp_problem(n_people: int = 20, 
                               n_projects: int = 3, 
                               n_skills: int = 2,
                               positive_ratio: float = 0.3,
                               seed: Optional[int] = None):
    """
    Generate an MTFP problem instance.
    Returns: problem, skill_names, project_names
    """
    if seed is not None:
        np.random.seed(seed)
    
    skill_of_person = np.random.randint(0, n_skills, size=n_people)
    skill_counts = np.bincount(skill_of_person, minlength=n_skills)
    
    S = np.zeros((n_people, n_people))
    for i in range(n_people):
        S[i, i] = 1
        for j in range(i+1, n_people):
            rand_val = np.random.rand()
            if rand_val < positive_ratio:
                S[i, j] = 1
                S[j, i] = 1
            elif rand_val < 0.5:
                S[i, j] = -1
                S[j, i] = -1
    
    R = np.zeros((n_skills, n_projects))
    skill_names = [f"Skill-{i}" for i in range(n_skills)]
    project_names = [f"Project-{i}" for i in range(n_projects)]
    
    for k in range(n_skills):
        available = skill_counts[k]
        total_needed = max(1, int(available * np.random.uniform(0.5, 0.7)))
        for l in range(n_projects):
            if l < n_projects - 1:
                max_possible = min(3, total_needed)
                req = np.random.randint(0, max_possible + 1)
                R[k, l] = req
                total_needed -= req
            else:
                R[k, l] = max(0, total_needed)
    
    max_total_per_skill = skill_counts * 0.8
    for k in range(n_skills):
        current_total = R[k, :].sum()
        if current_total > max_total_per_skill[k]:
            scale = max_total_per_skill[k] / current_total
            R[k, :] = np.round(R[k, :] * scale)
    
    problem = MTFP(
        n_people=n_people,
        n_projects=n_projects,
        n_skills=n_skills,
        affinity_matrix=S,
        requirements=R,
        skill_of_person=skill_of_person,
        project_weights=None,
        dedication_levels=np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    )
    return problem, skill_names, project_names, skill_counts, S, R

def explain_mtfp_problem(problem, skill_names, project_names, skill_counts, S, R):
    """
    Print a visual explanation for an existing MTFP problem instance.
    """
    n_people = problem.H
    n_projects = problem.P
    n_skills = problem.K
    positive_ratio = (np.sum(S == 1) - n_people) / (n_people * (n_people - 1)) if n_people > 1 else 0

    print("┌" + "─" * 78 + "┐")
    print("│" + "MULTIPLE TEAM FORMATION PROBLEM (MTFP)".center(78) + "│")
    print("└" + "─" * 78 + "┘")
    
    print("\n📊 PROBLEM OVERVIEW:")
    print(f"   • People available: {n_people}")
    print(f"   • Projects to staff: {n_projects}")
    print(f"   • Different skills needed: {n_skills}")
    print(f"   • Positive work relationships: {positive_ratio*100:.0f}% of pairs")
    
    print("\n👥 SKILL DISTRIBUTION (what people can do):")
    for k in range(n_skills):
        print(f"   • {skill_names[k]}: {skill_counts[k]} people available")
    
    print("\n🏗️ PROJECT REQUIREMENTS (what we need to accomplish):")
    print("   " + " " * 15 + " ".join([f"{name:>10}" for name in project_names]))
    for k in range(n_skills):
        requirements_str = " ".join([f"{R[k,l]:>10.1f}" for l in range(n_projects)])
        print(f"   {skill_names[k]:<15}{requirements_str}")
    
    print("\n📈 TOTAL CAPACITY ANALYSIS:")
    for k in range(n_skills):
        required_total = R[k, :].sum()
        available_total = skill_counts[k]
        utilization = (required_total / available_total) * 100 if available_total > 0 else 0
        print(f"   • {skill_names[k]}: {required_total:.1f} person-time needed / " +
              f"{available_total} people available ({utilization:.1f}% utilization)")
    
    print("\n⏱️ ALLOWED WORK SCHEDULES:")
    print("   People can work: 0%, 25%, 50%, 75%, or 100% on each project")
    print("   (No one can work more than 100% total across all projects)")
    
    print("\n🎯 OUR GOAL:")
    print("   1. Assign people to projects to meet all requirements")
    print("   2. Maximize positive work relationships within each project")
    print("   3. Keep everyone's total workload ≤ 100%")
    
    print("\n🔢 PROBLEM SIZE:")
    print(f"   • Decision variables: {problem.n_var} (who works where, how much)")
    print(f"   • Person capacity constraints: {n_people}")
    print(f"   • Skill requirement constraints: {n_skills * n_projects}")
    
    if n_people <= 20:
        print("\n🤝 RELATIONSHIP MATRIX (first 10 people):")
        print("   + = like, - = dislike, 0 = neutral/unknown")
        print("   " + " ".join([f"{i:>2}" for i in range(min(10, n_people))]))
        for i in range(min(10, n_people)):
            row_symbols = []
            for j in range(min(10, n_people)):
                if i == j:
                    row_symbols.append(" •")
                elif S[i, j] == 1:
                    row_symbols.append(" +")
                elif S[i, j] == -1:
                    row_symbols.append(" -")
                else:
                    row_symbols.append(" 0")
            print(f"{i:2}" + "".join(row_symbols))