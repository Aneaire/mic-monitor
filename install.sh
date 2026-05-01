#!/bin/bash
# Mic Monitor installer

cp mic-monitor.py ~/.local/bin/mic-monitor
chmod +x ~/.local/bin/mic-monitor
cp mic-monitor.desktop ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/
echo "Mic Monitor installed! Launch it from your app menu."
