#!/usr/bin/env python3
"""
Start TWS via IBC and auto-fill TOTP 2FA code.

Usage:
    python start_tws.py          # Start TWS and wait for login
    python start_tws.py --wait   # Start and block until API port is ready
"""

import os
import subprocess
import sys
import time
import argparse

import pyotp

IBC_START_SCRIPT = os.path.expanduser("~/ibc/twsstartmacos.sh")
TOTP_SECRET_FILE = os.path.expanduser("~/.ibkr-totp-secret")
API_PORT = 7496

FIND_2FA_WINDOW = '''
tell application "System Events"
    try
        set proc to first process whose name is "java"
        set wins to every window of proc
        repeat with w in wins
            if name of w contains "Second Factor" then
                return "FOUND"
            end if
        end repeat
    end try
    return ""
end tell
'''

CHECK_LOGIN = '''
tell application "System Events"
    try
        set proc to first process whose name is "java"
        set wins to every window of proc
        repeat with w in wins
            if name of w contains "Interactive Brokers" then
                return name of w
            end if
        end repeat
    end try
    return ""
end tell
'''


def get_totp_secret():
    secret = os.environ.get("TOTP_SECRET")
    if secret:
        return secret.strip()
    if os.path.exists(TOTP_SECRET_FILE):
        with open(TOTP_SECRET_FILE) as f:
            return f.read().strip()
    print("Error: TOTP_SECRET not found in env or ~/.ibkr-totp-secret", file=sys.stderr)
    sys.exit(1)


def run_applescript(script, timeout=10):
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return ""


def make_input_and_submit_script(code):
    return f'''
tell application "System Events"
    set proc to first process whose name is "java"
    set frontmost of proc to true
    delay 0.3
    set w to first window of proc whose name contains "Second Factor"
    perform action "AXRaise" of w
    delay 0.2

    set allFields to every text field of w
    repeat with f in allFields
        if description of f is "text field" then
            click f
            delay 0.2
        end if
    end repeat

    keystroke "{code}"
    delay 0.3

    set btns to every button of w
    repeat with b in btns
        if description of b is "OK" then
            click b
            return "SUBMITTED"
        end if
    end repeat
    return "NO_OK"
end tell
'''


def is_port_listening(port):
    r = subprocess.run(["lsof", "-i", f":{port}", "-sTCP:LISTEN"], capture_output=True, text=True)
    return r.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Start TWS with auto TOTP")
    parser.add_argument("--wait", action="store_true", help="Block until API port is ready")
    args = parser.parse_args()

    secret = get_totp_secret()
    totp = pyotp.TOTP(secret)

    # Check if already running
    if is_port_listening(API_PORT):
        print(f"TWS already running, API on port {API_PORT}")
        return

    # Start IBC
    print("Starting IBC + TWS...")
    subprocess.Popen(
        [IBC_START_SCRIPT, "-inline"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # Wait for 2FA window
    print("Waiting for 2FA window...")
    for i in range(90):
        if run_applescript(FIND_2FA_WINDOW) == "FOUND":
            print(f"2FA window detected ({i * 2}s)")
            break
        time.sleep(2)
    else:
        print("Timeout waiting for 2FA window")
        sys.exit(1)

    # Generate fresh TOTP and submit
    remaining = 30 - (int(time.time()) % 30)
    if remaining < 10:
        print(f"Waiting {remaining}s for fresh TOTP...")
        time.sleep(remaining + 1)

    code = totp.now()
    remaining = 30 - (int(time.time()) % 30)
    print(f"TOTP: {code} (valid {remaining}s)")

    result = run_applescript(make_input_and_submit_script(code))
    print(f"Submit result: {result}")

    if result != "SUBMITTED":
        print("Failed to submit TOTP")
        sys.exit(1)

    # Wait for login
    print("Waiting for login...")
    for i in range(30):
        time.sleep(2)
        win = run_applescript(CHECK_LOGIN)
        if win and "Interactive Brokers" in win:
            print(f"LOGIN SUCCESS: {win}")
            break
    else:
        print("Login did not complete in time")
        sys.exit(1)

    if args.wait:
        print(f"Waiting for API port {API_PORT}...")
        for i in range(30):
            time.sleep(2)
            if is_port_listening(API_PORT):
                print(f"API ready on port {API_PORT}")
                return
        print("API port did not open in time")
        sys.exit(1)


if __name__ == "__main__":
    main()
