"""
memory_scaling_test.py

What it does:
- For each memory size in MEMORY_SIZES:
  - updates the Lambda function memory
  - waits until update completes
  - disables EventBridge pre-warm (if you used it) by calling a CLI or by manual step (see instructions)
  - waits an "idle_period" (so you get a cold start)
  - invokes Lambda once and records Init Duration, Duration, Max Memory Used via CloudWatch logs
  - repeats 'SAMPLES_PER_SIZE' times (useful to get variation)
  - writes results to CSV: memory, timestamp, init_ms, duration_ms, max_mem_mb, sample_index

Run: python memory_scaling_test.py
Requirements: boto3 aws credentials (CloudShell or local profile), the lambda function exists.
"""
import boto3, time, csv, re
from datetime import datetime

FUNCTION_NAME = "serverlessrepo-serverless-todo-siteFunction-R4pAlPmZYXuk"
REGION = "us-east-2"
MEMORY_SIZES = [128, 256, 512, 1024]     # change/add if you want
SAMPLES_PER_SIZE = 5                     # invokes per memory size
IDLE_PERIOD_SECONDS = 15 * 60           # 15 minutes idle before test invoke
LOG_POLL_DELAY = 5                       # seconds to wait for logs to appear
OUTPUT_CSV = "memory_scaling_results.csv"

lambda_client = boto3.client("lambda", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)

def wait_for_update(memory_size, timeout=120):
    print(f"Waiting for memory to be updated to {memory_size} MB...")
    deadline = time.time() + timeout
    while time.time() < deadline:
        conf = lambda_client.get_function_configuration(FunctionName=FUNCTION_NAME)
        if conf.get("MemorySize") == memory_size:
            print("Update confirmed.")
            return True
        time.sleep(2)
    raise TimeoutError("Timeout waiting for function config update")

def invoke_and_get_report():
    # synchronous invoke
    lambda_client.invoke(FunctionName=FUNCTION_NAME, InvocationType="RequestResponse", Payload=b"{}")
    # get latest log stream
    log_group = f"/aws/lambda/{FUNCTION_NAME}"
    # wait briefly for logs to flush
    time.sleep(LOG_POLL_DELAY)
    streams = logs_client.describe_log_streams(logGroupName=log_group, orderBy="LastEventTime", descending=True, limit=1)
    if not streams["logStreams"]:
        return None
    stream = streams["logStreams"][0]["logStreamName"]
    events = logs_client.get_log_events(logGroupName=log_group, logStreamName=stream, startFromHead=False, limit=50)
    # parse last REPORT line
    init_ms = None
    duration_ms = None
    max_mem = None
    for ev in reversed(events["events"]):
        m = ev["message"]
        if "REPORT RequestId" in m:
            mm = re.search(r"Duration: ([0-9.]+) ms", m)
            if mm: duration_ms = float(mm.group(1))
            mm2 = re.search(r"Max Memory Used: (\d+) MB", m)
            if mm2: max_mem = int(mm2.group(1))
            mm3 = re.search(r"Init Duration: ([0-9.]+) ms", m)
            if mm3: init_ms = float(mm3.group(1))
            break
    return init_ms, duration_ms, max_mem

def main():
    # CSV header
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["memory_mb","sample_idx","timestamp","init_ms","duration_ms","max_memory_mb"])
    for mem in MEMORY_SIZES:
        print("=======================================")
        print(f"Setting memory to {mem} MB")
        lambda_client.update_function_configuration(FunctionName=FUNCTION_NAME, MemorySize=mem)
        wait_for_update(mem)
        print(f"Now waiting {IDLE_PERIOD_SECONDS/60:.1f} minutes to ensure idle -> cold start")
        time.sleep(IDLE_PERIOD_SECONDS)  # ensures cold start, adjust as needed

        for i in range(1, SAMPLES_PER_SIZE+1):
            print(f"[{datetime.utcnow()}] Sample {i}/{SAMPLES_PER_SIZE} for {mem} MB: invoking...")
            init_ms, duration_ms, max_mem = invoke_and_get_report()
            print("Result:", init_ms, duration_ms, max_mem)
            with open(OUTPUT_CSV, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([mem, i, datetime.utcnow().isoformat(), init_ms if init_ms else 0, duration_ms if duration_ms else 0, max_mem if max_mem else 0])
            # small gap between samples to let logs show
            time.sleep(10)
    print("Done. Results in", OUTPUT_CSV)

if __name__ == "__main__":
    main()
