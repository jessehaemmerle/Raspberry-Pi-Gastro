# Informationen
Das Programm startet über das Start.sh-Skript. Dieses muss eingerichtet werden, dass es mit dem Systemstart ausgeführt wird. 
Dann kommt direkt der Wechsler. 

# Neue Dateien hinzufügen
Die PDF-Dateien, die angezeigt werden sollen, müssen im Unterordner "kiosk" abgelegt sein. Nur dann liest das Programm die Dateien aus.
Wenn die Dateien im Ordner geändert werden muss auch immer das Skript gestoppt und dann neu gestartet werden. 
Nur dann werden die neuen Daten ausgelesen.

## Wichtig!
Es werden nur JPEG und PDF-Dateien erkannt, sonst keine weiteren Dateiformate.

# Autostart mittels systemd (Sofern gewollt)
Erst muss die folgende Datei erstellt werden: 
kiosk-viewer.service

Am einfachsten mit dem Befehl: 
`` sudo nano /etc/systemd/system/kiosk-viewer.service ``

Folgender Inhalt der Datei: 
```python
[Unit]
Description=Raspberry Pi Folder Kiosk
After=network-online.target

[Service]
User=pi
Environment=DISPLAY=:0
WorkingDirectory=/home/pi
ExecStart=/usr/bin/python3 /home/pi/Desktop/Bilder/Bilderwechsel.py --dir /home/pi/Desktop/Bilder/kiosk --delay 8 --shuffle --recursive
Restart=always

[Install]
WantedBy=graphical.target
```

## Aktivieren und starten
Mit den folgenden Befehlen wird der Service dann aktiviert und gestartet: 
```bash
sudo systemctl daemon-reload
sudo systemctl enable kiosk-viewer
sudo systemctl start kiosk-viewer
```

So ist sichergestellt, dass der Code auf jeden Fall beim Systemstart ausgeführt wird. 
Dann ist es einfacher, einfach den gesamten Rechhner neu zu starten als nur das Programm. Ist vom Handling her einfacher.

### Erklärung Autostart-Funktion
Die Autostartfunktion wird mittels einem Service realisiert, der auch ohne Nutzeranmeldung funktioniert. 
Bei der Einrichtung des Services kann mittels Flags mitgegeben werden, wie die Bilder wechseln sollen
Es gibt folgende Flags: 
- `--delay X` 
  - Hiermit wird festgelegt, wie viel Zeit zwischen den Bilderwechseln verstreichen soll
- `--shuffle` 
  - Gibt an, dass die Bilder in zufälliger Reihenfolge dargestellt werden sollen
- `--recursive`
  - Das gibt an, in welche Richtung die Bilder laufen sollen bzw. wie diese wiederholt werden sollen
