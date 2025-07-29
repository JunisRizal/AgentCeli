# Kryptowährungs-Daten-Agent

Ein Python-Agent zum Abrufen und Verarbeiten historischer Kryptowährungsdaten von der CoinGecko API mit Fokus auf JSON-Datenverarbeitung.

## 🚀 Features

- **JSON-Datenverarbeitung**: Automatisches Abrufen, Parsen und Strukturieren von JSON-Daten
- **Historische Daten**: Zugriff auf historische Preise, Marktkapitalisierung und Handelsvolumen
- **Batch-Verarbeitung**: Verarbeitung mehrerer Kryptowährungen in einem Durchgang
- **Flexible Ausgabe**: JSON, CSV und strukturierte Datenformate
- **Rate Limiting**: Automatische Einhaltung der API-Limits
- **Fehlerbehandlung**: Robuste Behandlung von API-Fehlern und JSON-Parsing-Problemen

## 📁 Dateien

### Basis-Agent

- `crypto_agent.py` - Einfacher Agent für grundlegende JSON-Datenverarbeitung
- `config.json` - Konfigurationsdatei für Coins und Einstellungen

### Erweiterter Agent

- `advanced_crypto_agent.py` - Vollständiger Agent mit erweiterten JSON-Features
- `crypto_data/` - Ausgabeordner für alle generierten Dateien

## 🔧 Installation

```bash
# Abhängigkeiten installieren
pip3 install requests pandas

# Agent ausführen
python3 crypto_agent.py
# oder
python3 advanced_crypto_agent.py
```

## 📊 JSON-Datenstrukturen

### Rohe API-Daten (raw_*.json)

```json
{
  "id": "bitcoin",
  "symbol": "btc", 
  "name": "Bitcoin",
  "market_data": {
    "current_price": {
      "usd": 117678.19,
      "eur": 101378.82,
      "btc": 1.0
    },
    "market_cap": {
      "usd": 2341223394839.92
    },
    "total_volume": {
      "usd": 80299520980.23
    }
  },
  "community_data": {...},
  "developer_data": {...}
}
```

### Verarbeitete Daten (processed_*.json)

```json
{
  "metadata": {
    "coin_id": "bitcoin",
    "symbol": "BTC",
    "name": "Bitcoin",
    "date": "16-07-2025",
    "processed_at": "2025-07-17T22:32:00.783795",
    "data_source": "coingecko_api"
  },
  "market_data": {
    "current_price": {
      "usd": 117678.19,
      "eur": 101378.82,
      "btc": 1.0
    },
    "market_cap": {
      "usd": 2341223394839.92,
      "eur": 2016992049335.33
    },
    "total_volume": {
      "usd": 80299520980.23,
      "eur": 69177394928.30
    }
  },
  "community_data": {...},
  "developer_data": {...},
  "raw_json_size": 5813
}
```

### Zusammenfassung (summary_*.json)

```json
{
  "summary_metadata": {
    "total_coins": 5,
    "generated_at": "2025-07-17T22:32:05.811122",
    "agent_version": "2.0"
  },
  "coins_overview": [
    {
      "coin_id": "bitcoin",
      "symbol": "BTC",
      "name": "Bitcoin",
      "price_usd": 117678.19,
      "market_cap_usd": 2341223394839.92,
      "volume_usd": 80299520980.23
    }
  ],
  "market_summary": {
    "total_market_cap_usd": 2763612910865.14,
    "total_volume_usd": 126189069765.26,
    "average_price_usd": 24166.43
  }
}
```

## ⚙️ Konfiguration

Die `config.json` Datei ermöglicht die Anpassung von:

- **API-Einstellungen**: Rate Limits, Basis-URL
- **Ziel-Coins**: Liste der zu verarbeitenden Kryptowährungen
- **Ausgabe-Optionen**: JSON, CSV, DataFrame-Export
- **Datenfelder**: Auswahl der zu extrahierenden Felder

## 🎯 Verwendungsbeispiele

### Einfache Verwendung

```python
from crypto_agent import CryptoDataAgent

agent = CryptoDataAgent()

# Historische Daten für Bitcoin
btc_data = agent.get_historical_data('bitcoin', '16-07-2025')
extracted = agent.extract_price_data(btc_data)
agent.save_to_json(extracted, 'bitcoin_data.json')
```

### Erweiterte Batch-Verarbeitung

```python
from advanced_crypto_agent import AdvancedCryptoAgent

agent = AdvancedCryptoAgent()

# Batch-Analyse für alle konfigurierten Coins
summary = agent.run_batch_analysis('16-07-2025')
print(f"Verarbeitet: {summary['summary_metadata']['total_coins']} Coins")
```

## 📈 Ausgabedateien

Der Agent generiert folgende Dateien:

1. **Rohe JSON-Daten** (`raw_*.json`) - Originale API-Antworten
2. **Verarbeitete JSON-Daten** (`processed_*.json`) - Strukturierte und bereinigte Daten
3. **Zusammenfassung** (`summary_*.json`) - Aggregierte Marktdaten
4. **CSV-Export** (`crypto_data_*.csv`) - Tabellarische Daten für Excel/Analyse

## 🔍 JSON-Verarbeitungsfeatures

- **Automatisches Parsing**: Robuste JSON-Dekodierung mit Fehlerbehandlung
- **Datenextraktion**: Intelligente Extraktion relevanter Felder aus komplexen JSON-Strukturen
- **Datenvalidierung**: Überprüfung und Bereinigung von JSON-Daten
- **Strukturierung**: Umwandlung flacher API-Daten in hierarchische Strukturen
- **Aggregation**: Zusammenfassung von Daten aus mehreren JSON-Quellen
- **Metadaten**: Anreicherung mit Zeitstempeln und Datenquellen-Informationen

## 🚨 Wichtige Hinweise

- **Rate Limiting**: Die kostenlose CoinGecko API hat Limits (10-50 Anfragen/Minute)
- **Historische Daten**: Kostenlose API beschränkt auf 365 Tage
- **Datenformat**: Datum muss im Format 'dd-mm-yyyy' angegeben werden
- **Zeitzone**: Alle Daten beziehen sich auf 00:00:00 UTC

## 🛠️ Erweiterungsmöglichkeiten

- Integration weiterer APIs (CoinMarketCap, Binance)
- Echtzeit-Datenstreaming
- Erweiterte Datenanalyse und Visualisierung
- Automatische Benachrichtigungen bei Preisänderungen
- Machine Learning für Preisprognosen
- Web-Dashboard für Datenvisualisierung

## 📞 Support

Bei Fragen oder Problemen:

1. Überprüfen Sie die API-Limits von CoinGecko
2. Stellen Sie sicher, dass alle Abhängigkeiten installiert sind
3. Prüfen Sie die Internetverbindung
4. Validieren Sie das Datumsformat (dd-mm-yyyy)
