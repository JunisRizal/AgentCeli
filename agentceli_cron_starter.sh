#!/bin/bash
# AgentCeli Cron Starter Script
# Überprüft ob AgentCeli läuft, startet es wenn nötig

AGENTCELI_DIR="/Users/julius/Desktop/AgentCeli"
PIDFILE="$AGENTCELI_DIR/agentceli.pid"
LOGFILE="$AGENTCELI_DIR/logs/cron_starter.log"

# Log-Verzeichnis erstellen falls nicht vorhanden
mkdir -p "$AGENTCELI_DIR/logs"

# Funktion zum Loggen
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOGFILE"
}

cd "$AGENTCELI_DIR" || {
    log_message "ERROR: Kann nicht zu $AGENTCELI_DIR wechseln"
    exit 1
}

# Prüfen ob AgentCeli bereits läuft
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
        log_message "AgentCeli läuft bereits (PID: $PID)"
        exit 0
    else
        log_message "Stale PID-Datei gefunden, wird entfernt"
        rm -f "$PIDFILE"
    fi
fi

# Prüfen ob Python-Prozess bereits läuft
if pgrep -f "agentceli_hybrid.py" > /dev/null; then
    log_message "AgentCeli-Prozess läuft bereits (ohne PID-Datei)"
    # PID-Datei neu erstellen
    pgrep -f "agentceli_hybrid.py" > "$PIDFILE"
    exit 0
fi

# AgentCeli starten
log_message "Starte AgentCeli..."
nohup python3 agentceli_hybrid.py > logs/agentceli_output.log 2>&1 &
NEW_PID=$!

# PID speichern
echo "$NEW_PID" > "$PIDFILE"
log_message "AgentCeli gestartet (PID: $NEW_PID)"

# Kurz warten und prüfen ob Prozess noch läuft
sleep 5
if kill -0 "$NEW_PID" 2>/dev/null; then
    log_message "AgentCeli erfolgreich gestartet und läuft"
else
    log_message "ERROR: AgentCeli konnte nicht gestartet werden"
    rm -f "$PIDFILE"
    exit 1
fi