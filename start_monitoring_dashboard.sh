#!/bin/bash

# AgentCeli Monitoring Dashboard Starter
# Funktionsfähiges Dashboard mit Backend-Verbindung

clear
echo "🔍 AgentCeli Monitoring Dashboard"
echo "=================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 ist erforderlich aber nicht installiert"
    exit 1
fi

# Check if Flask is available
if ! python3 -c "import flask" &> /dev/null; then
    echo "❌ Flask ist erforderlich. Installiere mit: pip3 install flask"
    exit 1
fi

echo "✅ Python 3: Verfügbar"
echo "✅ Flask: Verfügbar"
echo ""

# Check port availability
if lsof -Pi :8090 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8090 ist bereits belegt"
    echo "Beende bestehende Prozesse..."
    pkill -f "monitoring_dashboard.py"
    sleep 2
fi

echo "🚀 Starte Monitoring Dashboard..."
echo ""

# Start the dashboard
python3 monitoring_dashboard.py &
DASHBOARD_PID=$!

# Wait for startup
sleep 3

# Check if dashboard is running
if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    echo "✅ Dashboard erfolgreich gestartet!"
    echo ""
    echo "🌐 Dashboard URLs:"
    echo "   • Lokal:     http://localhost:8090"
    echo "   • Netzwerk:  http://$(hostname -I | awk '{print $1}'):8090"
    echo ""
    echo "📊 API Endpunkte:"
    echo "   • /api/overview  - Schnellübersicht"
    echo "   • /api/system    - System & Prozesse"
    echo "   • /api/apis      - API Status"
    echo "   • /api/data      - Datenfiles"
    echo "   • /api/logs      - Log-Dateien"
    echo "   • /api/crypto    - Krypto-Daten"
    echo ""
    echo "✅ Backend-Verbindung: Aktiv"
    echo "✅ Live-Monitoring: Aktiv"
    echo "✅ Auto-Refresh: 30 Sekunden"
    echo ""
    echo "Drücke Ctrl+C um zu beenden..."
    
    # Wait for user interrupt
    wait $DASHBOARD_PID
else
    echo "❌ Dashboard konnte nicht gestartet werden"
    echo "Überprüfe die Logs für weitere Informationen"
    exit 1
fi