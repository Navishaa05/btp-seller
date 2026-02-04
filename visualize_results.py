import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

# 1. Load latest run
list_of_runs = glob.glob('runs/*')
latest_run = max(list_of_runs, key=os.path.getctime)
df = pd.read_csv(os.path.join(latest_run, 'history.csv'))

# 2. SORT BY TIME (CRITICAL FIX)
df = df.sort_values(['seller_id', 'elapsed_frac'])

# 3. Setup Plot
plt.figure(figsize=(12, 6))
sns.lineplot(data=df, x='elapsed_frac', y='shading', hue='policy')

plt.title('Final BTP Result: Seller Strategy Adaptation Over 24h')
plt.xlabel('Time Progress (0.0 = Start, 1.0 = End of Day)')
plt.ylabel('Bid Shading (Internal Valuation Adjustment)')
plt.grid(True, alpha=0.3)

plt.savefig(os.path.join(latest_run, 'final_btp_report_graph.png'))
plt.show()