
import argparse
import subprocess
import os
import hashlib
import getpass
import sys

# Store password securely in system location
PASSWORD_DIR = "/etc/exammode"
PASSWORD_FILE = "/etc/exammode/pass.hash"

BLOCKED_DOMAINS = [
    # AI
    "chat.openai.com",
    "chatgpt.com",
    "openai.com",
    "gemini.google.com",
    "bard.google.com",
    "claude.ai",
    "anthropic.com",
    "perplexity.ai",
    "poe.com",
    "you.com",

    # Coding help
    "stackoverflow.com",
    "stackexchange.com",
    "geeksforgeeks.org",
    "tutorialspoint.com",
    "w3schools.com",
    "programiz.com",

    # Video
    "youtube.com",
    "youtu.be"
]

# ---------- Utility ----------

def require_root():
    if os.geteuid() != 0:
        print("Exammode must be run with sudo.")
        sys.exit(1)

def run(cmd):
    subprocess.run(cmd, shell=True)

# ---------- Password System ----------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def set_password():
    print("Set a password for lockdown mode.")
    while True:
        p1 = getpass.getpass("Enter password: ")
        p2 = getpass.getpass("Confirm password: ")

        if p1 != p2:
            print("Passwords do not match.\n")
        elif len(p1) < 4:
            print("Password too short.\n")
        else:
            os.makedirs(PASSWORD_DIR, exist_ok=True)
            with open(PASSWORD_FILE, "w") as f:
                f.write(hash_password(p1))
            os.chmod(PASSWORD_FILE, 0o600)
            print("Password set successfully.\n")
            break

def verify_password():
    if not os.path.exists(PASSWORD_FILE):
        print("No password set. Cannot disable lockdown.")
        return False

    stored_hash = open(PASSWORD_FILE).read().strip()
    entered = getpass.getpass("Enter lockdown password: ")

    if hash_password(entered) == stored_hash:
        return True
    else:
        print("Wrong password. Lockdown remains active.")
        return False

# ---------- AI Blocking ----------

def block_domains():
    print("Blocking AI and help sites...")
    for domain in BLOCKED_DOMAINS:
        run(f'echo "127.0.0.1 {domain}" >> /etc/hosts')
        run(f'echo "127.0.0.1 www.{domain}" >> /etc/hosts')

def unblock_domains():
    print("Restoring blocked domains...")
    for domain in BLOCKED_DOMAINS:
        run(f"sed -i '/{domain}/d' /etc/hosts")

# ---------- Lockdown ----------

def lockdown():
    print("---- ENABLING LOCKDOWN MODE ----")

    if not os.path.exists(PASSWORD_FILE):
        set_password()

    # Disable GNOME shortcuts (must run as user session)
    run("sudo -u $SUDO_USER gsettings set org.gnome.desktop.wm.keybindings switch-applications \"[]\"")
    run("sudo -u $SUDO_USER gsettings set org.gnome.desktop.wm.keybindings switch-windows \"[]\"")
    run("sudo -u $SUDO_USER gsettings set org.gnome.desktop.wm.keybindings close \"[]\"")
    run("sudo -u $SUDO_USER gsettings set org.gnome.mutter overlay-key ''")

    block_domains()

    run("pkill -9 -f firefox || true")
    run("sleep 1")

    subprocess.Popen([
        "sudo", "-u", os.environ.get("SUDO_USER", "root"),
        "firefox",
        "--kiosk",
        "--no-remote",
        "--private-window",
        "https://www.hackerrank.com"
    ])

    print("LOCKDOWN MODE ENABLED.")

# ---------- Disable ----------

def disable():
    print("---- DISABLING LOCKDOWN MODE ----")

    if not verify_password():
        return

    run("sudo -u $SUDO_USER gsettings reset org.gnome.desktop.wm.keybindings switch-applications")
    run("sudo -u $SUDO_USER gsettings reset org.gnome.desktop.wm.keybindings switch-windows")
    run("sudo -u $SUDO_USER gsettings reset org.gnome.desktop.wm.keybindings close")
    run("sudo -u $SUDO_USER gsettings reset org.gnome.mutter overlay-key")

    unblock_domains()

    run("pkill -9 -f firefox || true")

    print("LOCKDOWN MODE DISABLED.")

# ---------- Status ----------

def status():
    result = subprocess.check_output(
        "gsettings get org.gnome.desktop.wm.keybindings switch-applications",
        shell=True
    ).decode().strip()

    if result in ["[]", "@as []"]:
        print("Lockdown mode is ENABLED.")
    else:
        print("Lockdown mode is DISABLED.")

# ---------- Main ----------

def main():
    require_root()

    parser = argparse.ArgumentParser(description="Exam Lockdown Utility (Password + AI Blocking)")
    parser.add_argument("--lockdown", action="store_true")
    parser.add_argument("--disable", action="store_true")
    parser.add_argument("--status", action="store_true")

    args = parser.parse_args()

    if args.lockdown:
        lockdown()
    elif args.disable:
        disable()
    elif args.status:
        status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
