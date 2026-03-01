import argparse
import subprocess
import os

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

def run(cmd):
    subprocess.run(cmd, shell=True)

# ---------- Domain Blocking ----------

def block_domains():
    print("Blocking AI and help sites...")
    for domain in BLOCKED_DOMAINS:
        run(f'echo "127.0.0.1 {domain}" | sudo tee -a /etc/hosts > /dev/null')
        run(f'echo "127.0.0.1 www.{domain}" | sudo tee -a /etc/hosts > /dev/null')

def unblock_domains():
    print("Restoring blocked domains...")
    for domain in BLOCKED_DOMAINS:
        run(f"sudo sed -i '/{domain}/d' /etc/hosts")

# ---------- GNOME Control ----------

def disable_shortcuts():
    run("gsettings set org.gnome.desktop.wm.keybindings switch-applications \"[]\"")
    run("gsettings set org.gnome.desktop.wm.keybindings switch-windows \"[]\"")
    run("gsettings set org.gnome.desktop.wm.keybindings close \"[]\"")
    run("gsettings set org.gnome.mutter overlay-key ''")

def restore_shortcuts():
    run("gsettings reset org.gnome.desktop.wm.keybindings switch-applications")
    run("gsettings reset org.gnome.desktop.wm.keybindings switch-windows")
    run("gsettings reset org.gnome.desktop.wm.keybindings close")
    run("gsettings reset org.gnome.mutter overlay-key")

# ---------- Firefox ----------

def launch_firefox():
    run("pkill -9 -f firefox || true")
    run("sleep 1")
    run("firefox --kiosk https://www.google.com &")

# ---------- Core Logic ----------

def lockdown():
    print("---- ENABLING LOCKDOWN MODE ----")

    disable_shortcuts()
    block_domains()
    launch_firefox()

    print("LOCKDOWN MODE ENABLED.")

def disable():
    print("---- DISABLING LOCKDOWN MODE ----")

    restore_shortcuts()
    unblock_domains()
    run("pkill -9 -f firefox || true")

    print("LOCKDOWN MODE DISABLED.")

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
