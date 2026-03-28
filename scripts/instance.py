#!/usr/bin/env python3
"""
Mini Prism — Instance Control
==============================
Usage:
  python3 scripts/instance.py start
  python3 scripts/instance.py stop
  python3 scripts/instance.py ip
  python3 scripts/instance.py status
"""

import json
import subprocess
import sys

INSTANCE_ID = "i-07f691e3fa16938a7"
REGION      = "ap-southeast-2"


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def get_state():
    out = run([
        "aws", "ec2", "describe-instances",
        "--instance-ids", INSTANCE_ID,
        "--region", REGION,
        "--query", "Reservations[0].Instances[0].State.Name",
        "--output", "text",
    ])
    return out


def get_ip():
    return run([
        "aws", "ec2", "describe-instances",
        "--instance-ids", INSTANCE_ID,
        "--region", REGION,
        "--query", "Reservations[0].Instances[0].PublicIpAddress",
        "--output", "text",
    ])


def start():
    state = get_state()
    if state == "running":
        print(f"Already running — http://{get_ip()}")
        return
    if state not in ("stopped", "stopping"):
        print(f"Cannot start — instance is currently: {state}")
        sys.exit(1)

    print("Starting instance...")
    run(["aws", "ec2", "start-instances", "--instance-ids", INSTANCE_ID, "--region", REGION])

    import time
    for _ in range(24):
        time.sleep(5)
        state = get_state()
        ip    = get_ip()
        print(f"  state: {state}")
        if state == "running" and ip and ip != "None":
            print(f"\nUp! App URL: http://{ip}")
            print("(Allow ~60s for containers to start)")
            return

    print("Instance started but couldn't get IP — check AWS console")


def stop():
    state = get_state()
    if state == "stopped":
        print("Already stopped.")
        return
    if state != "running":
        print(f"Cannot stop — instance is currently: {state}")
        sys.exit(1)

    run(["aws", "ec2", "stop-instances", "--instance-ids", INSTANCE_ID, "--region", REGION])
    print("Stopping... (takes ~30s, RDS and ECR images are preserved)")


def status():
    state = get_state()
    print(f"State: {state}")
    if state == "running":
        ip = get_ip()
        print(f"URL:   http://{ip}")


COMMANDS = {"start": start, "stop": stop, "ip": lambda: print(get_ip()), "status": status}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
