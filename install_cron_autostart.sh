#!/bin/bash
# Installation Script für AgentCeli Cron Autostart

echo "🚀 AgentCeli Cron Autostart Installation"
echo "======================================="

AGENTCELI_DIR="/Users/julius/Desktop/AgentCeli"
CRON_SCRIPT="$AGENTCELI_DIR/agentceli_cron_starter.sh"

# Prüfen ob Script vorhanden ist
if [ ! -f "$CRON_SCRIPT" ]; then
    echo "❌ Cron-Script nicht gefunden: $CRON_SCRIPT"
    exit 1
fi

# Script ausführbar machen
chmod +x "$CRON_SCRIPT"
echo "✅ Cron-Script ist ausführbar"

# Log-Verzeichnis erstellen
mkdir -p "$AGENTCELI_DIR/logs"
echo "✅ Log-Verzeichnis erstellt"

# Aktuelle Crontab sichern
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null
echo "✅ Aktuelle Crontab gesichert"

# Neue Cron-Regel hinzufügen (alle 60 Minuten)
echo "📝 Cron-Job wird hinzugefügt..."

# Prüfen ob bereits ein AgentCeli Cron-Job existiert
if crontab -l 2>/dev/null | grep -q "agentceli_cron_starter.sh"; then
    echo "⚠️ AgentCeli Cron-Job existiert bereits"
    echo "Aktuelle Cron-Jobs:"
    crontab -l | grep agentceli
else
    # Neuen Cron-Job hinzufügen
    (crontab -l 2>/dev/null; echo "0 * * * * $CRON_SCRIPT # AgentCeli Autostart alle 60min") | crontab -
    echo "✅ Cron-Job hinzugefügt: alle 60 Minuten"
fi

# Aktuelle Crontab anzeigen
echo ""
echo "📋 Aktuelle Cron-Jobs:"
crontab -l | grep -E "(agentceli|#)"

echo ""
echo "🎉 Installation abgeschlossen!"
echo ""
echo "📊 Was passiert jetzt:"
echo "   • Jede Stunde (zur vollen Stunde) prüft das System"
echo "   • Falls AgentCeli nicht läuft, wird es gestartet"
echo "   • Logs werden gespeichert in: $AGENTCELI_DIR/logs/"
echo ""
echo "📁 Log-Dateien:"
echo "   • $AGENTCELI_DIR/logs/cron_starter.log"
echo "   • $AGENTCELI_DIR/logs/agentceli_output.log"
echo ""
echo "🛠️ Manueller Test:"
echo "   $CRON_SCRIPT"
echo ""
echo "🗑️ Cron-Job entfernen:"
echo "   crontab -e  # und die AgentCeli-Zeile löschen"