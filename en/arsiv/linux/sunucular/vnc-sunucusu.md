---
title: A VNC server
permalink: /en/arsiv/linux/sunucular/vnc-sunucusu/
status: arsiv
reviewed: 2026-11-02
scope: TightVNC and Xfce; no distribution version specified.
archive_reason: Correct the explanation of VNC security and the SSH tunnel. Verify
  the server’s listening address and authentication settings.
lang: en
translation_key: guide-arsiv-linux-sunucular-vnc-sunucusu
translation_of: /arsiv/linux/sunucular/vnc-sunucusu/
translated: '2026-11-03'
---

# A VNC server

## What is VNC?

VNC (virtual network computing) provides remote access to a computer’s graphical desktop, including servers hosted by providers such as DigitalOcean or Azure. It has its own protocol and port conventions. The original note’s claim that this alone makes VNC completely secure is incorrect; see the archive warning.

## Install VNC

For a Debian-based system, first update package metadata:

```bash
sudo apt update
```

Install TightVNC Server:

```bash
sudo apt install tightvncserver
```

If no desktop environment is installed, the original example uses Xfce:

```bash
sudo apt install xfce4 xfce4-goodies
```

## Configure the VNC server

Run the server for its first-time setup:

```bash
vncserver
```

Enter a password for remote connections. Typed characters are not echoed, so the prompt does not visibly change as you type.

```
You will require a password to access your desktops.

Password:
Verify:
```

The next prompt asks whether to create an additional view-only password. The original procedure skips it:

```
auth:  file /home/zaryob/.Xauthority does not exist

New 'X' desktop is your_hostname:1

Creating default startup script /home/zaryob/.vnc/xstartup
Starting applications specified in /home/zaryob/.vnc/xstartup
Log file is /home/zaryob/.vnc/your_hostname:1.log
```

Initial setup is complete, but the output reports that .Xauthority is missing. Stop the VNC server and configure its desktop startup.

## Configure the desktop environment

Stop the server:

```bash
vncserver -kill :1
```

```
Killing Xtightvnc process ID 17731
```

Back up the existing startup file before editing:

```bash
mv ~/.vnc/xstartup ~/.vnc/xstartup.bak
```

Configure the X session:

```bash
cat > ~/.vnc/xstartup <<EOF
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF
```

`startxfce4` launches the desktop installed above. Other desktop environments require their own startup command.

Make the script executable:

```bash
sudo chmod +x ~/.vnc/xstartup
```

Start the server again:

```bash
vncserver
```

Example output:

```
New 'X' desktop is your_hostname:1

Starting applications specified in /home/zaryob/.vnc/xstartup
Log file is /home/zaryob/.vnc/your_hostname:1.log
```

## Connect to the VNC server

The original notes discuss an SSH tunnel and a graphical client such as TightVNC Viewer or RealVNC Viewer. These have different roles: the tunnel transports traffic, while the viewer displays the desktop.

### SSH tunnel

On GNU/Linux, the example SSH command establishes forwarding for the VNC connection:

```bash
ssh -L 5901:127.0.0.1:5901 -C -N -l zaryob sunucu_ip_adresi
```

Replace `zaryob` with your own server username. An SSH tunnel does not itself open a graphical VNC viewer; that inaccurate description in the original is one of the archive issues.

### VNC Viewer

Connect with RealVNC Viewer or TightVNC Viewer, specifying the server address and port `:5901` if the configuration has not changed the default display/port mapping.
