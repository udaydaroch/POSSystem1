#!/usr/bin/env python3
"""
Mini Prism — Instance Control
==============================
Interactive mode: python3 scripts/instance.py
"""

import subprocess
import sys
import time

INSTANCE_ID = "i-08ef9cc952d14d8ef"
REGION      = None


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        return None
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
    if state is None:
        return
    if state == "running":
        print(f"Already running — http://{get_ip()}")
        return
    if state not in ("stopped", "stopping"):
        print(f"Cannot start — instance is currently: {state}")
        return

    print("Starting instance...")
    run(["aws", "ec2", "start-instances", "--instance-ids", INSTANCE_ID, "--region", REGION])

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
    if state is None:
        return
    if state == "stopped":
        print("Already stopped.")
        return
    if state != "running":
        print(f"Cannot stop — instance is currently: {state}")
        return

    run(["aws", "ec2", "stop-instances", "--instance-ids", INSTANCE_ID, "--region", REGION])
    print("Stopping... (takes ~30s, RDS and ECR images are preserved)")


def status():
    state = get_state()
    if state is None:
        return
    print(f"State: {state}")
    if state == "running":
        ip = get_ip()
        print(f"URL:   http://{ip}")


def show_ip():
    ip = get_ip()
    if ip:
        print(f"IP: {ip}")


MENU = {
    "1": ("Start",  start),
    "2": ("Stop",   stop),
    "3": ("Status", status),
    "4": ("IP",     show_ip),
}


if __name__ == "__main__":
    print("Mini Prism — Instance Control")
    print("=" * 34)

    INSTANCE_ID = input("Instance ID: ").strip()
    REGION      = input("Region [ap-southeast-2]: ").strip() or "ap-southeast-2"

    print()

    while True:
        print("\nOptions:")
        for key, (label, _) in MENU.items():
            print(f"  {key}) {label}")
        print("  q) Quit")

        choice = input("\nChoice: ").strip().lower()

        if choice == "q":
            print("Bye.")
            break
        elif choice in MENU:
            print()
            MENU[choice][1]()
        else:
            print("Invalid choice.")
