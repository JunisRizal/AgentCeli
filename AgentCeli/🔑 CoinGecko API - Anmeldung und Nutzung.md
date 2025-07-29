# 🔑 CoinGecko API - Anmeldung und Nutzung

## 📋 Übersicht der API-Optionen

### 1. 🆓 **Kostenlose Nutzung (OHNE Anmeldung)**
- ✅ **Keine Registrierung erforderlich**
- ✅ **Sofort einsatzbereit**
- ⚠️ **Begrenzte Rate Limits** (10-50 Anfragen/Minute)
- ✅ **Alle wichtigen Endpoints verfügbar**
- ✅ **Historische Daten (365 Tage)**

### 2. 🔑 **Demo API (MIT kostenloser Anmeldung)**
- 📝 **Kostenlose Registrierung erforderlich**
- ✅ **Höhere Rate Limits**
- ✅ **API-Key für bessere Performance**
- ✅ **Erweiterte Features**

### 3. 💰 **Pro API (Kostenpflichtig)**
- 💳 **Bezahlte Pläne ab $129/Monat**
- ✅ **Unbegrenzte historische Daten**
- ✅ **Höchste Rate Limits**
- ✅ **Premium Features**

## 🚀 **Empfehlung: Starten Sie kostenlos!**

Der Agent funktioniert **sofort ohne Anmeldung**. Für bessere Performance können Sie später einen kostenlosen Demo-API-Key hinzufügen.

## 📝 Anmeldung für Demo API (Optional)

### Schritt 1: Registrierung
1. Besuchen Sie: https://www.coingecko.com/en/developers/dashboard
2. Klicken Sie auf "Sign Up"
3. Erstellen Sie ein kostenloses Konto

### Schritt 2: API-Key generieren
1. Gehen Sie zum Developer Dashboard
2. Klicken Sie auf "Generate API Key"
3. Kopieren Sie Ihren Demo API Key

### Schritt 3: API-Key verwenden
```python
# Im Live-Agent
agent = LiveCryptoAgent(api_key="IHR_API_KEY_HIER")
```

## 🔧 Rate Limits Vergleich

| Plan | Anfragen/Minute | Anfragen/Monat | Kosten |
|------|----------------|----------------|---------|
| **Kostenlos** | 10-50 | ~50.000 | 🆓 Kostenlos |
| **Demo** | 30 | ~50.000 | 🆓 Kostenlos |
| **Analyst** | 500 | 1.000.000 | $129/Monat |
| **Lite** | 10.000 | 10.000.000 | $499/Monat |

## 🎯 **Für Ihren Use Case (10-15 Coins Live-Daten)**

### ✅ **Kostenlose API ist ausreichend!**

**Warum:**
- 1 Anfrage für alle 15 Coins gleichzeitig
- Bei 60-Sekunden-Updates: nur 1440 Anfragen/Tag
- Weit unter dem kostenlosen Limit

**Berechnung:**
```
15 Coins in 1 Anfrage × 60 Updates/Stunde × 24 Stunden = 1.440 Anfragen/Tag
Monatlich: ~43.200 Anfragen (unter dem 50.000 Limit)
```

## 🔄 **Live-Agent Konfiguration**

### Ohne API-Key (Empfohlen für Start)
```python
agent = LiveCryptoAgent()  # Keine Anmeldung nötig
```

### Mit Demo API-Key (Optional für bessere Performance)
```python
agent = LiveCryptoAgent(api_key="cgk-demo-xxxxxxxx")
```

## 📊 **Verfügbare Endpoints**

### 1. Simple Price API (Für Live-Daten)
```
GET /simple/price?ids=bitcoin,ethereum&vs_currencies=usd,eur
```
- ✅ Bis zu 250 Coins pro Anfrage
- ✅ Preise, Marktkapitalisierung, Volumen
- ✅ 24h Änderungen

### 2. Markets API (Für detaillierte Daten)
```
GET /coins/markets?vs_currency=usd&ids=bitcoin,ethereum
```
- ✅ Ranking, Prozentuale Änderungen
- ✅ 1h, 24h, 7d Änderungen
- ✅ Coin-Bilder und Metadaten

### 3. Historical Data API
```
GET /coins/bitcoin/history?date=17-07-2025
```
- ✅ Historische Preise
- ✅ 365 Tage kostenlos verfügbar

## 🚨 **Wichtige Hinweise**

### Rate Limiting
- **Automatisch im Agent implementiert**
- **1.2 Sekunden Pause zwischen Anfragen**
- **Fehlerbehandlung bei Überschreitung**

### API-Key Sicherheit
```python
# ✅ Sicher: Umgebungsvariable
import os
api_key = os.getenv('COINGECKO_API_KEY')

# ❌ Unsicher: Hardcoded im Code
api_key = "cgk-demo-xxxxxxxx"  # Nicht empfohlen
```

### Headers vs Query Parameter
```python
# ✅ Empfohlen: Header
headers = {'x-cg-demo-api-key': 'IHR_KEY'}

# ❌ Weniger sicher: Query Parameter
url = "https://api.coingecko.com/api/v3/ping?x_cg_demo_api_key=IHR_KEY"
```

## 🎯 **Fazit für Ihr Projekt**

### ✅ **Sofort starten:**
1. Verwenden Sie den Live-Agent **ohne API-Key**
2. Testen Sie mit 10-15 Coins
3. Überwachen Sie die Performance

### 🔄 **Bei Bedarf upgraden:**
1. Registrieren Sie sich für Demo API
2. Fügen Sie API-Key hinzu
3. Profitieren Sie von höheren Limits

### 📈 **Für Production:**
- Kostenlose API reicht für die meisten Use Cases
- Demo API für bessere Zuverlässigkeit
- Pro API nur bei sehr hohem Volumen nötig

## 🛠️ **Nächste Schritte**

1. **Testen Sie den Live-Agent** ohne API-Key
2. **Überwachen Sie die Rate Limits** in der Konsole
3. **Registrieren Sie sich** nur bei Bedarf für Demo API
4. **Skalieren Sie** je nach Anforderungen

**Der Agent ist bereits vollständig funktionsfähig - keine Anmeldung erforderlich!** 🚀

