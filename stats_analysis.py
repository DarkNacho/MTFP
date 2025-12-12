import pandas as pd
import numpy as np
from scipy.stats import shapiro, wilcoxon
import glob
import os

NAME_MAPPING = {
    "Variable Neighborhood Search": "VNS",
    "Genetic Algorithm": "GA",
    "Tabu Search": "Tabu",
    "Local Search": "Stoch. LS",
    "Hill Climbing": "Std. HC",
    "Random Search": "Random",
    "Greedy": "Greedy"
}

def normalize_deterministic_algorithms(df):
    """
    Normaliza algoritmos deterministas (como Greedy) que solo tienen 1 ejecución.
    Replica su resultado para todas las semillas presentes en el experimento.
    """
    # 1. Identificar todas las semillas únicas del experimento (usando un algo estocástico como referencia)
    # Buscamos el algoritmo que tenga más filas (runs)
    algo_counts = df['Algorithm'].value_counts()
    robust_algo = algo_counts.idxmax()
    all_seeds = df[df['Algorithm'] == robust_algo]['Seed'].unique()
    
    # 2. Buscar algoritmos con 1 sola ejecución (o muy pocas)
    algos = df['Algorithm'].unique()
    new_rows = []
    
    for algo in algos:
        algo_data = df[df['Algorithm'] == algo]
        
        # Si es Greedy o determinista (ej. 1 sola fila, o todas iguales)
        # Asumimos que si tiene menos del 50% de las semillas, es un baseline determinista
        if len(algo_data) < len(all_seeds) * 0.5:
            print(f"   ℹ️  Normalizando '{algo}': Replicando valor único para {len(all_seeds)} semillas.")
            
            # Tomamos el valor de eficiencia (asumimos que es el primero)
            base_eff = algo_data.iloc[0]['Efficiency']
            
            # Creamos filas artificiales para cada semilla
            for seed in all_seeds:
                # Solo agregamos si no existe ya para esa semilla (para no duplicar)
                if seed not in algo_data['Seed'].values:
                    new_rows.append({
                        'Algorithm': algo,
                        'Run': 0, # Dummy
                        'Seed': seed,
                        'Efficiency': base_eff,
                        'Time': algo_data.iloc[0]['Time'],
                        'Feasible': True
                    })
    
    # 3. Agregar las filas normalizadas al DataFrame original
    if new_rows:
        df_normalized = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
        return df_normalized
    
    return df

def analyze_statistical_significance(file_path):
    print(f"\n{'='*80}")
    print(f"📊 ANALIZANDO ARCHIVO: {os.path.basename(file_path)}")
    print(f"{'='*80}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"Error cargando archivo: {e}")
        return

    if df.empty:
        print("❌ El archivo CSV está vacío.")
        return

    # --- PASO EXTRA: NORMALIZACIÓN DE GREEDY ---
    df = normalize_deterministic_algorithms(df)
    # -------------------------------------------

    # 2. Pivotear tabla (Ahora sí funcionará porque Greedy tendrá todas las semillas)
    pivot_df = df.pivot(index='Seed', columns='Algorithm', values='Efficiency')
    
    if pivot_df.isnull().values.any():
        print("⚠️  ADVERTENCIA: Datos incompletos detectados (Seeds no coincidentes).")
        print(f"   Filas antes de limpiar: {len(pivot_df)}")
        pivot_df = pivot_df.dropna()
        print(f"   Filas después de limpiar: {len(pivot_df)}")
        
        if pivot_df.empty:
            print("❌ ERROR: No hay intersección de semillas. Verifica tus datos.")
            return

    algorithms = pivot_df.columns.tolist()
    
    # PASO A: Normalidad
    print("\n1️⃣  TEST DE NORMALIDAD (Shapiro-Wilk)")
    print(f"{'Algoritmo':<30} | {'p-value':<12} | {'Normal?'}")
    print("-" * 60)

    for algo in algorithms:
        data = pivot_df[algo].values
        if len(data) < 3: continue 

        if np.all(data == data[0]):
            p_str = "N/A"
            is_normal = "⚠️ Constante" # Greedy caerá aquí
        else:
            try:
                stat, p = shapiro(data)
                p_str = f"{p:.2e}"
                is_normal = "✅ SÍ" if p > 0.05 else "❌ NO"
            except:
                p_str = "Error"
                is_normal = "?"
        
        print(f"{algo:<30} | {p_str:<12} | {is_normal}")

    # PASO B: Wilcoxon
    print("\n2️⃣  TEST DE WILCOXON (vs. Ganador)")
    means = pivot_df.mean()
    winner_name = means.idxmax()
    winner_data = pivot_df[winner_name].values
    
    print(f"🏆 GANADOR: {winner_name} (Media: {means[winner_name]:.4f})")
    print(f"{'Comparación':<40} | {'p-value':<12} | {'Significativo?'}")
    print("-" * 70)
    
    latex_rows = []

    for algo in algorithms:
        if algo == winner_name:
            continue
            
        challenger_data = pivot_df[algo].values
        
        try:
            stat, p_val = wilcoxon(winner_data, challenger_data, alternative='greater')
            
            paper_w = NAME_MAPPING.get(winner_name, winner_name)
            paper_l = NAME_MAPPING.get(algo, algo)
            p_tex = "< 0.001" if p_val < 0.001 else f"{p_val:.3f}"
            bold = p_val < 0.05
            latex_rows.append((paper_w, paper_l, p_tex, bold))
            
            sig_str = "✅ SÍ" if p_val < 0.05 else "❌ NO"
        except ValueError:
            # Pasa si son idénticos o uno es constante igual al otro
            p_val = 1.0
            sig_str = "❌ Idénticos"
            latex_rows.append((NAME_MAPPING.get(winner_name), NAME_MAPPING.get(algo), "1.000", False))

        print(f"{winner_name} vs {algo:<20} | {p_val:.2e}   | {sig_str}")

    # PASO C: LaTeX
    if latex_rows:
        print("\n📄 CÓDIGO LATEX SUGERIDO:")
        print("-" * 60)
        print(r"\begin{table}[htbp]")
        print(r"    \caption{Statistical Significance (Wilcoxon Signed-Rank Test).}")
        print(r"    \label{tab:stats_results}")
        print(r"    \centering")
        print(r"    \begin{tabular}{lc}")
        print(r"        \toprule")
        print(r"        \textbf{Comparison} & \textbf{$p$-value} \\")
        print(r"        \midrule")
        for w, l, p, bold in latex_rows:
            p_str = f"\\textbf{{{p}}}" if bold else p
            print(f"        {w} vs. {l} & {p_str} \\\\")
        print(r"        \bottomrule")
        print(r"    \end{tabular}")
        print(r"\end{table}")

if __name__ == "__main__":
    raw_files = glob.glob("results/*_raw.csv")
    if not raw_files:
        print("❌ No se encontraron archivos.")
    else:
        for f in raw_files:
            analyze_statistical_significance(f)