import boto3
import time
import re
from datetime import datetime

# ---------- Configuration ----------
FUNCTION_NAME = "serverlessrepo-serverless-todo-siteFunction-R4pAlPmZYXuk"
REGION_NAME = "us-east-2"
OUTPUT_CSV = "lambda_coldstart_log.csv"
INTERVAL_SECONDS = 900   # 15 minutes

# ---------- AWS Clients ----------
lambda_client = boto3.client("lambda", region_name=REGION_NAME)
logs_client = boto3.client("logs", region_name=REGION_NAME)

def invoke_lambda():
    """Invoke Lambda function once"""
    response = lambda_client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse"
    )
    return response

def fetch_latest_log():
    """Fetch the latest log event from CloudWatch"""
    log_group = f"/aws/lambda/{FUNCTION_NAME}"
    streams = logs_client.describe_log_streams(
        logGroupName=log_group,
        orderBy="LastEventTime",
        descending=True,
        limit=1
    )
    if not streams["logStreams"]:
        return None

    stream_name = streams["logStreams"][0]["logStreamName"]
    events = logs_client.get_log_events(
        logGroupName=log_group,
        logStreamName=stream_name,
        limit=20,
        startFromHead=False
    )
    return events["events"]

def parse_logs(events):
    """Parse Init Duration, Duration, and Memory from logs"""
    init_duration = None
    duration = None
    memory_used = None

    for event in events:
        msg = event["message"]

        # Example log lines:
        # REPORT RequestId: ...  Duration: 4.07 ms  Billed Duration: 5 ms  Memory Size: 128 MB  Max Memory Used: 58 MB  Init Duration: 356.14 ms
        if "REPORT RequestId" in msg:
            m1 = re.search(r"Duration: ([0-9.]+) ms", msg)
            m2 = re.search(r"Max Memory Used: (\d+) MB", msg)
            m3 = re.search(r"Init Duration: ([0-9.]+) ms", msg)

            if m1: duration = float(m1.group(1))
            if m2: memory_used = int(m2.group(1))
            if m3: init_duration = float(m3.group(1))

    return init_duration, duration, memory_used

def log_result(init_duration, duration, memory_used):
    """Append result to CSV"""
    with open(OUTPUT_CSV, "a") as f:
        f.write(f"{datetime.now()},{init_duration},{duration},{memory_used}\n")

def monitor_loop():
    print(f"Monitoring Lambda cold starts every {INTERVAL_SECONDS/60:.1f} minutes...")
    while True:
        print(f"[{datetime.now()}] Invoking Lambda...")
        invoke_lambda()
        time.sleep(5)  # small delay for logs to flush

        events = fetch_latest_log()
        if events:
            init_duration, duration, memory_used = parse_logs(events)

            if init_duration:
                print(f"Cold start detected! Init = {init_duration} ms | Duration = {duration} ms | MemUsed = {memory_used} MB")
            else:
                print(f"Warm start. Duration = {duration} ms | MemUsed = {memory_used} MB")

            log_result(init_duration, duration, memory_used)

        print(f"Waiting {INTERVAL_SECONDS/60:.1f} minutes...\n")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    monitor_loop()
