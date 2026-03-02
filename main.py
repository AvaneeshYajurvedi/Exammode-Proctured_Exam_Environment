import argparse
import subprocess
import os
import sys
import json
import shutil

POLICY_DIR = "/etc/firefox/policies"
POLICY_FILE = "/etc/firefox/policies/policies.json"

BLOCKED_DOMAINS = [
    "chat.openai.com", "chatgpt.com", "openai.com",
    "gemini.google.com", "bard.google.com",
    "claude.ai", "anthropic.com", "perplexity.ai",
    "poe.com", "you.com",
    "stackoverflow.com", "stackexchange.com",
    "geeksforgeeks.org", "tutorialspoint.com",
    "w3schools.com", "programiz.com",
    "youtube.com", "youtu.be"
]

# ---------- Utilities ----------

def require_root():
    if os.geteuid() != 0:
        print("Exammode must be run with sudo.")
        sys.exit(1)

def run(cmd):
    subprocess.run(cmd, shell=True)

def run_as_user(cmd):
    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        print("Cannot determine real user.")
        sys.exit(1)

    user_id = subprocess.check_output(
        f"id -u {real_user}", shell=True
    ).decode().strip()

    display = os.environ.get("DISPLAY", ":0")
    dbus_address = f"unix:path=/run/user/{user_id}/bus"

    full_cmd = (
        f"sudo -u {real_user} "
        f"DISPLAY={display} "
        f"DBUS_SESSION_BUS_ADDRESS={dbus_address} "
        f"{cmd}"
    )

    subprocess.Popen(full_cmd, shell=True)


# ---------- Firefox Profile Detection ----------

def get_default_firefox_profile():
    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        print("Cannot determine real user.")
        sys.exit(1)

    import pwd
    pw_record = pwd.getpwnam(real_user)
    firefox_base = f"{pw_record.pw_dir}/snap/firefox/common/.mozilla/firefox"
    profiles_ini = os.path.join(firefox_base, "profiles.ini")

    if not os.path.exists(profiles_ini):
        print("Firefox profiles.ini not found.")
        sys.exit(1)

    with open(profiles_ini, "r") as f:
        lines = f.readlines()

    profile_path = None
    for line in lines:
        if line.startswith("Path="):
            profile_path = line.strip().split("=")[1]
            break

    if not profile_path:
        print("No Firefox profile found.")
        sys.exit(1)

    return os.path.join(firefox_base, profile_path)


def apply_firefox_ui_lock():
    print("Applying Firefox UI lockdown...")

    profile_path = get_default_firefox_profile()
    chrome_dir = os.path.join(profile_path, "chrome")
    os.makedirs(chrome_dir, exist_ok=True)

    css_content = """
#TabsToolbar { visibility: collapse !important; }
#tabs-newtab-button { display: none !important; }
.tabbrowser-tab .tab-close-button { display: none !important; }
"""

    with open(os.path.join(chrome_dir, "userChrome.css"), "w") as f:
        f.write(css_content)

    with open(os.path.join(profile_path, "user.js"), "a") as f:
        f.write('user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);\n')

    print("UI lockdown applied.")


# ---------- Domain Blocking ----------

def block_domains():
    print("Blocking AI and help sites...")
    for domain in BLOCKED_DOMAINS:
        run(f'echo "127.0.0.1 {domain}" >> /etc/hosts')
        run(f'echo "127.0.0.1 www.{domain}" >> /etc/hosts')

def unblock_domains():
    print("Restoring blocked domains...")
    for domain in BLOCKED_DOMAINS:
        run(f"sed -i '/{domain}/d' /etc/hosts")


# ---------- GNOME Control ----------

def disable_shortcuts():
    run_as_user("gsettings set org.gnome.desktop.wm.keybindings switch-applications \"[]\"")
    run_as_user("gsettings set org.gnome.desktop.wm.keybindings switch-windows \"[]\"")
    run_as_user("gsettings set org.gnome.desktop.wm.keybindings close \"[]\"")
    run_as_user("gsettings set org.gnome.mutter overlay-key ''")

def hide_dock():
    run_as_user("gnome-extensions disable ubuntu-dock@ubuntu.com")

def show_dock():
    run_as_user("gnome-extensions enable ubuntu-dock@ubuntu.com")

def restore_shortcuts():
    run_as_user("gsettings reset org.gnome.desktop.wm.keybindings switch-applications")
    run_as_user("gsettings reset org.gnome.desktop.wm.keybindings switch-windows")
    run_as_user("gsettings reset org.gnome.desktop.wm.keybindings close")
    run_as_user("gsettings reset org.gnome.mutter overlay-key")


# ---------- Firefox ----------

def kill_firefox():
    run("pkill -9 firefox || true")
    run("pkill -9 snap.firefox || true")
    run("pkill -9 -f snap/firefox || true")
    run("sleep 2")

def launch_firefox():
    print("Launching Firefox...")

    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        print("No SUDO_USER found.")
        return

    # Kill any existing firefox instances
    kill_firefox()

    user_id = subprocess.check_output(
        f"id -u {real_user}", shell=True
    ).decode().strip()

    display = os.environ.get("DISPLAY", ":0")
    dbus_address = f"unix:path=/run/user/{user_id}/bus"

    cmd = (
        f"sudo -u {real_user} "
        f"DISPLAY={display} "
        f"DBUS_SESSION_BUS_ADDRESS={dbus_address} "
        f"nohup snap run firefox https://www.google.com "
        f"> /dev/null 2>&1 &"
    )

    subprocess.Popen(cmd, shell=True)


# ---------- Core Logic ----------

def lockdown():
    print("---- ENABLING LOCKDOWN MODE ----")
    disable_shortcuts()
    block_domains()
    apply_firefox_ui_lock()
    launch_firefox()
    hide_dock()
    print("LOCKDOWN MODE ENABLED.")

def disable():
    print("---- DISABLING LOCKDOWN MODE ----")
    restore_shortcuts()
    unblock_domains()
    show_dock()
    kill_firefox()
    print("LOCKDOWN MODE DISABLED.")


def status():
    real_user = os.environ.get("SUDO_USER")
    if real_user:
        result = subprocess.check_output(
            f"sudo -u {real_user} gsettings get org.gnome.desktop.wm.keybindings switch-applications",
            shell=True
        ).decode().strip()

        if result in ["[]", "@as []"]:
            print("Lockdown mode is ENABLED.")
        else:
            print("Lockdown mode is DISABLED.")
    else:
        print("Unable to determine user session.")


# ---------- Main ----------

def main():
    require_root()

    parser = argparse.ArgumentParser(description="ExamMode Lockdown Utility")
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
