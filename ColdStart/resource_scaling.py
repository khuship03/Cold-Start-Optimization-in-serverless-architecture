import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv("memory_scaling_results.csv")

# Clean up / rename columns (assuming your script writes them in order)
df.columns = ["Memory_MB", "Sample", "Timestamp", "Init_ms", "Duration_ms", "MaxMemory_MB"]

# Compute averages per memory size
summary = df.groupby("Memory_MB").agg({
    "Init_ms": "mean",
    "Duration_ms": "mean",
    "MaxMemory_MB": "max"
}).reset_index()

print("=== Summary Table ===")
print(summary)

# ---- Plot Cold Start Init Time ----
plt.figure(figsize=(7,5))
plt.plot(summary["Memory_MB"], summary["Init_ms"], marker="o")
plt.title("Cold Start Init Time vs Memory")
plt.xlabel("Memory (MB)")
plt.ylabel("Init Time (ms)")
plt.grid(True)
plt.show()

# ---- Plot Execution Duration ----
plt.figure(figsize=(7,5))
plt.plot(summary["Memory_MB"], summary["Duration_ms"], marker="o", color="orange")
plt.title("Execution Duration vs Memory")
plt.xlabel("Memory (MB)")
plt.ylabel("Duration (ms)")
plt.grid(True)
plt.show()

# ---- Plot Max Memory Used ----
plt.figure(figsize=(7,5))
plt.bar(summary["Memory_MB"], summary["MaxMemory_MB"], color="green")
plt.title("Max Memory Usage vs Memory Allocated")
plt.xlabel("Memory (MB)")
plt.ylabel("Max Memory Used (MB)")
plt.show()
