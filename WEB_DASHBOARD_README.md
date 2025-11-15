# Web Dashboard - Käyttöohje

## 🌐 Selainpohjainen Real-Time Dashboard

Seuraa paper trading -bottia kauniissa web-dashboardissa osoitteessa **http://localhost:5000**

---

## 🚀 Pika-aloitus (2 vaihetta)

### Vaihe 1: Asenna Flask

```bash
pip3 install flask
```

### Vaihe 2: Käynnistä Web Dashboard

```bash
cd "/Users/smac/Vault/AI projektit/S&P 500"
python3 web_dashboard.py
```

**Output**:
```
================================================================================
PAPER TRADING WEB DASHBOARD
================================================================================

Starting web server...

🌐 Open your browser and go to:

    http://localhost:5000

📊 Dashboard will show:
  - Real-time account balance
  - Open positions
  - Performance metrics
  - Equity curve chart
  - Recent trades

⚠️  Make sure paper_trading_bot.py is running in another terminal!

🛑 Press Ctrl+C to stop the server
================================================================================

 * Running on http://0.0.0.0:5000
```

### Vaihe 3: Avaa selain

Mene osoitteeseen: **http://localhost:5000**

---

## 📸 Mitä näet dashboardissa?

### 1. Ylhäällä: Key Metrics (6 korttia)

```
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│   Balance   │  Total P&L  │  Win Rate   │ Expectancy  │Profit Factor│Total Trades │
│  $10,250    │  +$250      │   38.31%    │   +0.25R    │    1.49     │     15      │
│             │  (+2.50%)   │  5W / 10L   │             │             │ Open: 3     │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

### 2. Keskellä: Equity Curve Chart

Interaktiivinen käyrä joka näyttää:
- Tilin arvon kehityksen ajan myötä
- Aloitussaldon vertailulinjan
- Jokaisen traden vaikutuksen

**Zoomaa**, **hover** pisteiden päällä = näe tarkka arvo!

### 3. Avoinna olevat positiot

Taulukko jossa:
- Position ID, Markkina, Pattern
- Direction (LONG/SHORT)
- Entry, Stop, Target hinnat
- Kuinka kauan avoinna (bars)

### 4. Viimeisimmät tradet

Taulukko jossa:
- ID, Markkina, Pattern, Direction
- Exit reason (TARGET/STOP/TIMEOUT)
- P&L R-multipleina ja prosentteina
- Kuinka kauan kesti (bars)

---

## 🔄 Auto-Refresh

Dashboard päivittyy automaattisesti **joka 10. sekunti**!

Voit myös päivittää manuaalisesti: **🔄 Refresh Now** -nappi

---

## 💡 Käyttötapaukset

### Tapaus 1: Monitoroi paper tradingbottia

**Terminaali 1**:
```bash
python3 paper_trading_bot.py
```

**Terminaali 2**:
```bash
python3 web_dashboard.py
```

**Selain**:
- Avaa http://localhost:5000
- Jätä välilehti auki
- Seuraa reaaliajassa kun botti tradaa!

### Tapaus 2: Katso historiaa (botti ei käynnissä)

```bash
python3 web_dashboard.py
```

Dashboard näyttää:
- Viimeisen tunnetun tilanteen
- Kaikki suljetut tradet
- Equity curve-historian
- **MUTTA**: Ei päivity (botti ei aja)

### Tapaus 3: Mobile monitoring

Web dashboard toimii myös puhelimella!

1. Tarkista koneesi IP-osoite:
   ```bash
   ifconfig | grep "inet "
   ```

2. Käynnistä dashboard:
   ```bash
   python3 web_dashboard.py
   ```

3. Puhelimessa avaa:
   ```
   http://[KONEESI-IP]:5000
   ```
   Esim: `http://192.168.1.100:5000`

---

## 🎨 Dashboard Features

### Visuaaliset elementit

1. **Värikoodit**:
   - 🟢 Vihreä = Positiivinen (voitot, positiivinen P&L)
   - 🔴 Punainen = Negatiivinen (tappiot, negatiivinen P&L)
   - 🔵 Sininen = Neutraali (otsikot, borders)

2. **Badget**:
   - `LONG` = Vihreä badge
   - `SHORT` = Punainen badge
   - `TARGET` = Tummanvihreä
   - `STOP` = Tummanpunainen
   - `TIMEOUT` = Keltainen

3. **Hover Effects**:
   - Kortit nousevat kun hiiri päällä
   - Taulukkorivit highlightautuvat
   - Chartin tooltips näyttävät tarkat arvot

4. **Responsive Design**:
   - Toimii kaikilla ruudun koilla
   - Mobile-optimized
   - Grid layout sopeutuu

---

## 🔧 Kustomointi

### Muuta Auto-Refresh Interval

Muokkaa `dashboard.html` tiedoston loppua:

```javascript
// Auto-refresh every 10 seconds
setInterval(loadData, 10000);  // Muuta millisekunteja
```

Esimerkkejä:
- `5000` = 5 sekuntia
- `30000` = 30 sekuntia
- `60000` = 1 minuutti

### Muuta Värejä

Muokkaa `<style>` osiota `dashboard.html`:ssä:

```css
/* Muuta pääväri */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Muuta positive-väri */
.positive {
    color: #10b981;  /* Muuta tähän haluamasi väri */
}
```

### Lisää Uusia Metriikoita

1. Muokkaa `web_dashboard.py`:n `get_dashboard_data()` funktiota
2. Lisää uusi metriikka `metrics` dictionaryyn
3. Muokkaa `dashboard.html`:n `renderDashboard()` funktiota
4. Lisää uusi stat-card

---

## 🐛 Troubleshooting

### Ongelma: "Address already in use"

**Syy**: Portti 5000 jo käytössä

**Ratkaisu 1**: Vaihda porttia
```python
# web_dashboard.py, viimeinen rivi:
app.run(debug=True, host='0.0.0.0', port=5001)  # Käytä 5001
```

**Ratkaisu 2**: Tapa vanha prosessi
```bash
lsof -ti:5000 | xargs kill -9
```

### Ongelma: "No data available"

**Syy**: Paper trading bot ei ole ajanut vielä

**Ratkaisu**:
1. Käynnistä `paper_trading_bot.py` toisessa terminaalissa
2. Odota kunnes botti luo tiedostot
3. Refresh dashboard

### Ongelma: Dashboard ei päivity

**Syy**: Auto-refresh ei toimi tai botti ei aja

**Ratkaisu**:
1. Tarkista JavaScript console (F12 selaimessa)
2. Varmista `paper_trading_bot.py` ajaa
3. Klikkaa "🔄 Refresh Now"

### Ongelma: Equity chart ei näy

**Syy**: Ei vielä suljettuja tradeja

**Ratkaisu**:
- Odota että botti sulkee ensimmäisen traden
- Chart ilmestyy automaattisesti

---

## 📊 API Endpoints

Dashboard tarjoaa JSON API:n:

### GET /api/data

Palauttaa kaiken dashboardin datan JSON:na:

```bash
curl http://localhost:5000/api/data
```

**Response**:
```json
{
  "status": "ok",
  "account": {
    "starting_balance": 10000,
    "current_balance": 10250,
    "total_pnl": 250,
    "total_pnl_pct": 2.5,
    "risk_per_trade": 1.0,
    "total_trades": 15,
    "open_positions": 3,
    "closed_positions": 12
  },
  "metrics": {
    "win_rate": 38.31,
    "total_r": 2.5,
    "avg_r": 0.25,
    "profit_factor": 1.49
  },
  "open_positions": [...],
  "recent_trades": [...],
  "equity_curve": [...]
}
```

### GET /api/refresh

Pakottaa datan päivityksen:

```bash
curl http://localhost:5000/api/refresh
```

---

## 🚀 Edistyneet käyttötavat

### 1. Useampi Dashboard

Monitoroi useita botteja samanaikaisesti:

**Botti 1** (portti 5000):
```bash
python3 web_dashboard.py
```

**Botti 2** (portti 5001):
Muokkaa `web_dashboard.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

Avaa selaimessa:
- http://localhost:5000 (Botti 1)
- http://localhost:5001 (Botti 2)

### 2. Julkaise Internetiin (VAROITUS!)

⚠️ **VAIN DEMOKÄYTTÖÖN!** Älä laita oikeita trade-datoja julkiseen nettiin!

1. Käytä ngrok:ia:
```bash
brew install ngrok  # macOS
ngrok http 5000
```

2. Ngrok antaa public URL:n:
```
https://abc123.ngrok.io
```

3. Jaa URL ystäville (demo-tarkoituksiin)

### 3. Custom Alertit

Lisää äänihälytykset dashboardiin:

```javascript
// dashboard.html <script> osioon:
function checkAlerts(data) {
    // Hälytä jos saldo putoaa alle aloitussaldon
    if (data.account.current_balance < data.account.starting_balance) {
        playAlertSound();
    }

    // Hälytä jos uusi trade suljettu
    if (lastTradeCount !== data.metrics.total_trades) {
        playAlertSound();
        lastTradeCount = data.metrics.total_trades;
    }
}

function playAlertSound() {
    const audio = new Audio('https://freesound.org/data/previews/341/341695_5121236-lq.mp3');
    audio.play();
}
```

---

## 📱 Screenshots (Conceptual)

```
┌─────────────────────────────────────────────────────────────────┐
│                  📊 Paper Trading Dashboard                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Balance  │  │Total P&L │  │Win Rate  │  │Expectancy│       │
│  │ $10,250  │  │  +$250   │  │  38.31%  │  │  +0.25R  │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
├─────────────────────────────────────────────────────────────────┤
│                      📈 Equity Curve                            │
│  12000 ┤                                              ╭─╮       │
│  11500 ┤                                    ╭────────╯ │       │
│  11000 ┤                        ╭──────────╯          │       │
│  10500 ┤              ╭────────╯                      │       │
│  10000 ┼─────────────╯────────────────────────────────╯       │
│   9500 ┤                                                       │
├─────────────────────────────────────────────────────────────────┤
│  🔓 Open Positions (3)                                         │
│  #13 BTC-USD ICI LONG   Entry: $93,500  Target: $96,000       │
│  #14 GLD Revival LONG   Entry: $252     Target: $254.50       │
│  #15 SPY ICI SHORT      Entry: $645     Target: $642          │
├─────────────────────────────────────────────────────────────────┤
│  📋 Recent Trades                                              │
│  #12 BTC-USD ICI LONG   TARGET   +2.10R  +2.15%   12 bars    │
│  #11 GLD Revival LONG   STOP     -0.84R  -0.80%    8 bars    │
│  #10 SPY ICI SHORT      TIMEOUT  +0.50R  +0.45%   30 bars    │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✅ Yhteenveto

**Web Dashboard** tarjoaa:
- ✅ Kauniin selainpohjaisen käyttöliittymän
- ✅ Real-time päivitykset (10s autorefresh)
- ✅ Interaktiivisen equity curve -chartin
- ✅ Taulukot positioista ja tradeista
- ✅ Responsive design (toimii mobiilissa)
- ✅ JSON API rajapinnan

**Käyttö**:
1. `pip3 install flask`
2. `python3 web_dashboard.py`
3. Avaa http://localhost:5000
4. Nauti! 🎉

**Perfect for**:
- Paper trading monitorointiin
- Demo-esittelyihin
- Backtest-tulosten visualisointiin
- Multi-screen setupiin (botti yhdellä näytöllä, dashboard toisella)

---

*Huom: Dashboard lukee vain tiedostoja. Se ei kontrolloi bottia. Botti pyörii itsenäisesti.*
