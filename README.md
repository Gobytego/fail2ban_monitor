Gobytego Fail2Ban Monitor
============================================

A modern, Python-based graphical dashboard designed to monitor Fail2Ban activity across multiple Linux servers in real-time. This tool allows system administrators to centralize security event monitoring via secure SSH streaming.

Features
--------

* **Live Streaming:** Uses SSH-based tail commands to stream logs instantly.
* **Multi-Server Tabs:** Independent, non-blocking tabs for each configured server.
* **Visual Alerts:** High-visibility red highlighting for IP ban events.
* **Persistent Configuration:** Integrated Settings tab to Manage (Add/Edit/Delete) servers via `servers.json`.
* **Session History:** Retrieves the last 500 lines upon connection to capture offline activity.
* **Log Export:** Export current session data to local text files.

Installation
------------

### 1\. Local Machine Setup 

On Fedora Install the Python environment, Pip package manager, and the Tkinter GUI engine:

    sudo dnf install python3 python3-pip python3-tkinter
    pip install customtkinter paramiko

On Debian/Ubuntu Install the Python environment, Pip package manager, and the Tkinter GUI engine:

    sudo apt install python3 python3-pip python3-tkinter
    pip install customtkinter paramiko

On Solus Install the Python environment, Pip package manager, and the Tkinter GUI engine:

    sudo eopkg it python3 python3-pip python3-tkinter
    pip install customtkinter paramiko


### 2\. Remote Server Setup (Security and Permissions)

Fail2ban logs are typically restricted to the root user. Follow these steps to allow a standard user (e.g., adam) to monitor logs securely.

#### A. Grant Permissions via Groups

Run these commands on every remote server being monitored:

    # Change the file group to 'adm' (standard log-reader group)
    sudo chgrp adm /var/log/fail2ban.log
    
    # Grant the group read access
    sudo chmod 640 /var/log/fail2ban.log
    
    # Add your SSH user (example user is "adam") to the 'adm' group
    sudo usermod -aG adm adam

#### B. Configure Logrotate Persistence

To ensure permissions persist after log rotation, update the logrotate configuration:

1.  Edit the configuration: `sudo nano /etc/logrotate.d/fail2ban`
2.  Update the `create` line:
    
        /var/log/fail2ban.log {
            ...
            create 640 root adm
            ...
        }
    

Usage
-----

* **Launch:** Run `python fail2ban_monitor.py` from your terminal.
* **Configure:** Navigate to the Settings tab to input server Hostnames, Users, and Key Paths.
* **SSH Keys:** Ensure your private key path is absolute (e.g., for user "adam" `/home/adam/.ssh/id_rsa`).
* **Default Log Path:** Use `/var/log/fail2ban.log` unless your system uses a custom path.

**Technical Note:** It might take a few moments to connect and grab the log but... If the application fails to connect, verify that the remote user has read permissions by running `groups` on the remote server to confirm membership in the `adm` group.
