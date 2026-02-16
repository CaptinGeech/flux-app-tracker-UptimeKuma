import requests
import json
import os
import time
import sys
from pathlib import Path

KUMA_DOMAIN = "http://localhost:3001"

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 monitor.py <IP_ADDRESS> <PORT> <KUMA_PUSH_TOKEN>")
        sys.exit(1)

    target_ip = sys.argv[1]
    target_port = sys.argv[2]
    kuma_push_url = f"{KUMA_DOMAIN}/api/push/{sys.argv[3]}"
    api_url = f"http://{target_ip}:{target_port}/apps/listrunningapps"
    state_file = f"state_{target_ip.replace('.', '_')}_{target_port}.json"

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data_list = response.json().get("data", [])

        # We convert the list of names into a SET to allow subtraction
        current_apps = set([
            item["Names"][0].lstrip('/') 
            for item in data_list 
            if item.get("Names") and len(item["Names"]) > 0
        ])
    except Exception as e:
        print(f"Failed to reach {target_ip}: {e}")
        return

    # Load previous state and convert to SET
    script_path = f"{Path(__file__).resolve().parent}/data"
    os.makedirs(script_path, exist_ok=True)
    if os.path.exists(f"{script_path}/{state_file}"):
        with open(f"{script_path}/{state_file}", "r") as f:
            last_apps = set(json.load(f))
    else:
        # First run: Save and exit
        with open(f"{script_path}/{state_file}", "w") as f:
            json.dump(list(current_apps), f)
        requests.get(f"{kuma_push_url}?msg=Initial+setup+for+{target_ip}&status=up")
        return

    # Set Math
    added = current_apps - last_apps
    removed = last_apps - current_apps

    if not added and not removed:
        # No changes
        requests.get(f"{kuma_push_url}?msg={len(current_apps)}+apps+running&status=up")
    else:
        # Build message
        change_parts = []
        if added: change_parts.append(f"Added {len(added)} apps: {', '.join(added)}")
        if removed: change_parts.append(f"Removed {len(removed)} apps: {', '.join(removed)}")
        msg = f"Change on {target_ip}:{target_port}: " + " | ".join(change_parts)

        print(msg)

        # Alert flip: Down then Up
        requests.get(f"{kuma_push_url}?msg=processing&status=down")
        time.sleep(2)
        requests.get(f"{kuma_push_url}?msg={msg.replace(' ', '+')}&status=up")

        # Update state file for next comparison
        with open(f"{script_path}/{state_file}", "w") as f:
            json.dump(list(current_apps), f)

if __name__ == "__main__":
    main()