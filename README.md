# Exammode – Proctored Exam Environment

Exammode is a GNOME-based Ubuntu endpoint lockdown utility designed to enforce secure, controlled exam sessions.

It restricts desktop shortcuts, blocks high-risk domains (AI tools, coding help platforms, etc.), launches a kiosk-mode browser session, and protects unlock functionality with password-based authentication.

## Features

- Disables GNOME window switching (Alt+Tab, Super key, etc.)
- Blocks AI and coding help websites via system-level domain control
- Launches Firefox in kiosk mode for controlled assessment access
- Password-protected unlock mechanism
- Root-level enforcement
- Packaged as an installable `.deb` system utility

##  Installation (Recommended)

Download the latest `.deb` file from the **Releases** section.

Install using:

```
sudo dpkg -i exammode_1.0.0_all.deb
```

## Build From Source (Developers)

Clone the repository:

git clone https://github.com/AvaneeshYajurvedi/Exammode-Proctured_Exam_Environment.git

cd LOCKDOWN

Build the Debian package:
```
dpkg-deb --build exammode_package
```
Install:
```
sudo dpkg -i exammode_package.deb
```
## Usage

Enable lockdown:
```
sudo exammode --lockdown
```
Disable lockdown:
```
sudo exammode --disable
```
Check current status:
```
sudo exammode --status
```

## How It Works
- Exammode enforces a hardened exam environment by:
- Modifying GNOME keybindings to restrict session control
- Updating /etc/hosts to block selected domains
- Launching Firefox in kiosk mode
- Storing a hashed unlock password
- Requiring root privileges for activation and deactivation

## Requirements

- Ubuntu (GNOME desktop environment)
- Firefox installed
- sudo/root privileges

## Security Notice

Exammode is intended for controlled lab or academic environments. It is not a replacement for enterprise-grade endpoint management systems.

## Version

- v1.0.0 – Initial public release
- GNOME shortcut restriction
- AI domain blocking
- Password-protected unlock
- Debian package distribution

## Author

Avaneesh Yajurvedi
