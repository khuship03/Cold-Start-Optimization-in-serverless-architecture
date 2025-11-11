import time
import random
import datetime

# -------------------------
# CONFIG
LAMBDA_NAME = "serverlessrepo-serverless-todo-siteFunction-R4pAlPmZYXuk"
MIN_INTERVAL = 5 * 60     # 5 minutes
MAX_INTERVAL = 15 * 60    # 15 minutes
LOAD_THRESHOLD_HIGH = 80  # simulated high load %
LOAD_THRESHOLD_LOW = 20   # simulated low load %
# -------------------------

def simulate_load():
    """Simulate current load on the Lambda (0–100%)."""
    return random.randint(0, 100)

def invoke_lambda():
    """Simulated Lambda invocation."""
    cold_start = random.choice([True, False])
    init_duration = round(random.uniform(300, 400), 2) if cold_start else 0
    duration = round(random.uniform(5, 50), 2)
    mem_used = random.randint(90, 120)
    timestamp = datetime.datetime.now()
    
    if cold_start:
        print(f"[{timestamp}] Cold start detected! Init = {init_duration} ms | Duration = {duration} ms | MemUsed = {mem_used} MB")
    else:
        print(f"[{timestamp}] Warm start. Duration = {duration} ms | MemUsed = {mem_used} MB")

def adjust_interval(load, current_interval):
    """Adjust invocation interval based on load."""
    if load > LOAD_THRESHOLD_HIGH:
        return max(MIN_INTERVAL, current_interval - 60)  # decrease interval (more frequent)
    elif load < LOAD_THRESHOLD_LOW:
        return min(MAX_INTERVAL, current_interval + 60)  # increase interval (less frequent)
    return current_interval  # keep same

def main():
    interval = MAX_INTERVAL
    print(f"Monitoring Lambda '{LAMBDA_NAME}' adaptively...")

    while True:
        load = simulate_load()
        print(f"\nSimulated load: {load}% | Current interval: {interval/60:.1f} minutes")
        
        invoke_lambda()
        
        interval = adjust_interval(load, interval)
        print(f"Next invocation in {interval/60:.1f} minutes...\n")
        time.sleep(interval)

if __name__ == "__main__":
    main()
