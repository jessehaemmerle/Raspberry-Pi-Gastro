# Was ist zu tun? 
Um den Raspberry PI zu verwenden, ist folgendes zu tun: 
- Stromversorgung sicherstellen
- Verbindung mit dem Bildschirm herstellen
- WLAN-Verbindung herstellen
  - Verbindungseinstellungen über das WLAN-Menü in der Titelleiste oben rechts aufrufen
- IP-Adresse notieren
  - Prüfung der IP-Adresse mittels Befehl "ifconfig" in der Kommandozeile
    - Ist in der Titelleiste als schwarzes Rechteck angehängt
    - IP-Adresse ist im Format XXX.XXX.XXX.XXX

Wenn dies gemacht ist, öffnen sich die Dateien auf in dem Ordner von selbst.

# Einstieg auf den Rechner
Der Rechner ist mit einem von selbst startenden VNC-Server ausgestattet. Sobald der PI im Netz hängt, kann mittels VNC-Client und der IP-Adresse mit Zugangsdaten auf den Rechner zugegriffen werden. 

## Zugangsdaten für den PI
Benutzer: annapi
Passwort: annapi
Zur Authentifizierung der Verbindung mittels VNC. 

## Einstieg mittels VNC
Wichtig zu beachten ist, dass der Rechner mit VNC-Client im selben Netzwerk ist wie der PI und dass VNC-Verbindungen nicht gesperrt sind. 
Wenn das der Fall ist, dann kann der VNC-Viewer geöffnet werden und mittels der Suchleiste nach dem korrekten Rechner gesucht werden.
![RVNC-Suchleiste](/img/RVNC-Suchleiste.png)

# Austauschen der Daten
Wenn die Dateien auf dem Screen aktualisiert werden sollen, dann wieder mit VNC auf den Rechner einsteigen und mit der Tastenkombination "Alt+Leertaste" das Kontextmenü öffnen. Das Programm mittels "Schließen"-Schaltfläche schließen. 
Nun befindet sich am Desktop der Ordner "PDF".

## Der Ordner "PDF"
Im PDF-Ordner befinden sich alle Dateien, die zur Ausführung des Programms nötig sind, *diese bitte unter keinen Umständen löschen*. 
Die Datei "Platzhalter" bitte löschen bevor die PDF hinzugefügt werden. 

Im Unterordner "kiosk" sind die PDF, etc. auszutauschen. 

## Dateien sind getauscht
Wenn die Dateien ausgetauscht sind, dann den PI einfach neu starten. Der Inhalt des Ordners "kiosk" wird ausgelesen und die neuen Dateien werden angezeigt. 

# Wichtige Informationen
Im folgenden Abschnitt finden wir noch weitere Informationen zum Betrieb des PI

## Automatische Updates
Der PI ist so konfiguriert, dass er jeden Tag um 2 in der früh selbst Updates installiert und sich um 3 Uhr morgens von selbst neu startet, um Updates sauber zu installieren.

## Unterstützte Dateitypen
Folgende Dateien werden unterstützt vom Programm: 
```
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
PDF_EXTS   = {".pdf"}
```
## Programm-Flags
Diese Angaben sind für die Anpassung des Programms, wenn Intervalle angepasst werden sollen, etc. 
- --dir = Ordner, in dem die PDF sind (Technisch)
- --delay = Wie lange zwischen den Wechseln gewartet werden soll
- --recursive = Sollten irgendwann Unterordner erstellt werden im "kiosk"-Ordner, dann kann damit angegeben werden, dass diese mit einbezogen werden sollen.
- --shuffle = Zufällige Wiedergabe einstellen


