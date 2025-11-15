# Paper Trading Bot - Käyttöohje

## Yleiskatsaus

Automaattinen paper trading -botti, joka:
- ✅ Skannaa Bitcoin, S&P 500 ja Kulta -markkinat tunneittain
- ✅ Tunnistaa ICI, Momentum, Force ja Revival -patternit
- ✅ Avaa automaattisesti paper trade -positiot
- ✅ Hallitsee stop loss ja take profit -exitit
- ✅ Trackaa suorituskykyä reaaliajassa
- ✅ Tallentaa kaikki tradet CSV-tiedostoon

---

## Pika-aloitus

### 1. Käynnistä Paper Trading Bot

```bash
python3 paper_trading_bot.py
```

Botti käynnistyy $10,000 papertilin kanssa ja:
- Skannaa markkinat joka tunti
- Avaa max 10 positiota kerrallaan (max 3 per markkina)
- Riskeeraa 1% per trade
- Ajaa 24 tuntia (tai kunnes pysäytetään Ctrl+C:llä)

### 2. Monitoroi Suorituskykyä

**Toisessa terminaalissa**, aja dashboard:

```bash
python3 paper_trading_dashboard.py
```

Tämä näyttää:
- Nykyisen tilin saldon
- Avoinna olevat positiot
- Win rate, Profit Factor, R-metriikat
- Pattern ja markkina -jakauman
- Viimeisimmät tradet

### 3. Pysäytä Botti

Paina **Ctrl+C** terminaalissa missä botti ajaa.

Botti:
- Sulkee kaikki avoimet positiot markkinahinnalla
- Tallentaa tilan `paper_account_history.json`
- Exporttaa kaikki tradet `paper_trades_log.csv`

---

## Konfigurointi

### Muuta Botin Asetuksia

Muokkaa `paper_trading_bot.py` tiedoston alareunaa:

```python
# Luo botti custom-asetuksilla
bot = PaperTradingBot(
    starting_balance=50000,    # Aloitussaldo ($50k)
    risk_per_trade=0.005       # Riski per trade (0.5%)
)

# Aja jatkuvasti (ei aikarajaa)
bot.run(duration_hours=None)
```

### Muuta Skannausväliä

Muokkaa luokkaa `PaperTradingBot`:

```python
self.scan_interval_minutes = 15  # Skannaa 15min välein (15M patterneille)
```

### Muuta Markkinoita

Muokkaa `markets`-dictionaryä:

```python
self.markets = {
    'BTC-USD': {'name': 'Bitcoin', 'timeframes': ['1h'], 'interval': '1h'},
    'ETH-USD': {'name': 'Ethereum', 'timeframes': ['1h'], 'interval': '1h'},
    'GLD': {'name': 'Gold', 'timeframes': ['1h'], 'interval': '1h'}
}
```

### Muuta Maksimi Positioita

```python
self.max_positions = 20              # Max kokonaispositiot
self.max_positions_per_market = 5    # Max per markkina
```

---

## Tiedostot

### `paper_account_history.json`
Tallentaa botin tilan:
- Tilin saldo ja equity
- Kaikki avoimet positiot
- Kokonaistilastot

**Esimerkki**:
```json
{
  "account": {
    "starting_balance": 10000,
    "current_balance": 10250,
    "equity": 10250,
    "total_trades": 15,
    "wins": 6,
    "losses": 9,
    "total_pnl_r": 2.5
  },
  "positions": [...]
}
```

### `paper_trades_log.csv`
CSV-loki kaikista suljetuista tradeista:

| ID | Entry_Date | Exit_Date | Market | Pattern | Direction | Entry_Price | Exit_Price | PnL_R | Exit_Reason |
|----|------------|-----------|--------|---------|-----------|-------------|------------|-------|-------------|
| 1 | 2025-11-15 | 2025-11-15 | BTC-USD | ICI | LONG | 93500 | 94200 | +1.5 | target |
| 2 | 2025-11-15 | 2025-11-15 | GLD | Revival | LONG | 252 | 251.5 | -0.84 | stop |

### `equity_curve.csv`
Exportoitu equity curve (dashboard luo):
- Kumulatiivinen P&L
- Equity jokaisessa tradessa
- Prosentuaalinen tuotto

---

## Käyttöesimerkkejä

### Esimerkki 1: Ajaa 7 päivää

```python
bot = PaperTradingBot(starting_balance=10000, risk_per_trade=0.01)
bot.run(duration_hours=24*7)  # 7 päivää
```

### Esimerkki 2: Konservatiivinen (0.5% riski)

```python
bot = PaperTradingBot(starting_balance=10000, risk_per_trade=0.005)
bot.run()
```

### Esimerkki 3: Aggressiivinen (2% riski, vain Bitcoin)

Muokkaa markets-dictionaryä:
```python
self.markets = {
    'BTC-USD': {'name': 'Bitcoin', 'timeframes': ['1h'], 'interval': '1h'}
}
```

Luo botti:
```python
bot = PaperTradingBot(starting_balance=10000, risk_per_trade=0.02)
bot.run()
```

### Esimerkki 4: Jatkuva Ajo (24/7)

```python
bot = PaperTradingBot(starting_balance=10000, risk_per_trade=0.01)
bot.run(duration_hours=None)  # Ajaa kunnes Ctrl+C
```

---

## Dashboard Komentoriviltä

### Näytä Nykyinen Tilanne

```bash
python3 paper_trading_dashboard.py
```

Output:
```
================================================================================
PAPER TRADING DASHBOARD
================================================================================
Generated: 2025-11-15 23:30:15
================================================================================

--- ACCOUNT OVERVIEW ---
Starting Balance: $10,000.00
Current Balance: $10,250.00
Total P&L: +$250.00 (+2.50%)
Risk per Trade: 1.0%

--- POSITIONS ---
Total Trades: 15
Open: 3
Closed: 12

Open Positions:
  #13 BTC-USD ICI LONG Entry: $93,500.00 | Target: $96,000.00 | Stop: $92,800.00
  #14 GLD Revival LONG Entry: $252.00 | Target: $254.50 | Stop: $251.00
  #15 SPY ICI SHORT Entry: $645.00 | Target: $642.00 | Stop: $646.00

--- PERFORMANCE METRICS ---
Win Rate: 41.67% (5W / 7L)
Total R: +2.50R
Average R: +0.21R per trade
Average Win: +1.80R
Average Loss: -0.85R
Profit Factor: 1.45

--- BY PATTERN ---
Pattern      count    sum   mean
ICI              6   1.2   0.20
Revival          6   1.3   0.22

--- BY MARKET ---
Market       count    sum   mean
BTC-USD          8   1.8   0.23
GLD              2   0.5   0.25
SPY              2   0.2   0.10

--- RECENT TRADES (Last 10) ---
 ID    Market Pattern Direction Exit_Reason  PnL_R  PnL_Pct  Bars_Held
  3   BTC-USD     ICI      LONG      target   2.10     2.15         12
  4   BTC-USD Revival      LONG        stop  -0.84    -0.80          8
  5       GLD     ICI      LONG     timeout   0.50     0.45         30
...
```

---

## Toiminnot

### Automaattinen Scanning

Botti skannaa markkinat säännöllisin välein (default: joka tunti):

1. **Lataa viimeisin data** jokaisesta markkinasta
2. **Ajaa skannerit**: ICI, Momentum, Force, Revival
3. **Filttaa validit setupit**: EMA, MACD, Fib, Volume alignment
4. **Avaa positiot** jos:
   - Max-positiot ei täynnä (< 10)
   - Markkina-kohtainen max ei täynnä (< 3)
   - Setup löytyy ja validoitu

### Automaattinen Exit Management

Jokaiselle avoimelle positiolle botti:

1. **Tarkistaa minutti-dataa** stop/target hitille
2. **Päivittää max favorable/adverse** hintoja
3. **Sulkee position** jos:
   - **Target hit**: Hinta saavuttaa täyden -0.272 extension targetin
   - **Stop hit**: Hinta osuu stop loss -tasolle
   - **Timeout**: (Ei toteutettu vielä - voidaan lisätä myöhemmin)

4. **Laskee P&L**:
   - R-multiples (kuinka monta riskiä voitettu/hävitty)
   - Prosentuaaliset voitot/tappiot
   - Dollar-arvot

5. **Päivittää tilin**:
   - Balance += P&L
   - Win/loss counter
   - Total R accumulated

### State Management

Botti tallentaa tilan automaattisesti:
- Jokaisen position avaamisella
- Jokaisen position sulkemisella
- Jokaisen skanin jälkeen

**Hyödyt**:
- Voit pysäyttää botin ja jatkaa myöhemmin
- Kaikki positiot säilyvät
- Equity curve jatkuu keskeytymättä

---

## Turvallisuus & Rajoitukset

### Paper Trading = Ei Oikeaa Rahaa

⚠️ **TÄRKEÄÄ**: Tämä on PAPER TRADING botti
- Ei yhdisty oikeisiin brokereihin
- Ei tee oikeita kauppoja
- Simuloi vain tradien suorituskykyä

### Datan Rajoitukset

- **yfinance**: Ilmainen data, voi olla viiveitä
- **Minutti-data**: Rajoitettu historiaan (~7 päivää)
- **Market hours**: SPY ja GLD tradaavat vain 9:30-16:00 ET
- **Bitcoin**: 24/7 data saatavilla

### Slippage & Fees

Botti **EI** simuloi:
- Slippagea (entry/exit aina täsmällinen hinta)
- Trading feeitä
- Spread-kustannuksia

**Realistinen arvio**:
- Todellinen suorituskyky ~90-95% paper-tuloksesta
- Lisää 0.1% fee per trade (entry + exit = 0.2% total)

---

## Kehittyneet Ominaisuudet

### Lisää Trailing Stop

Muokkaa `check_exits()` metodia:

```python
# Jos voitolla yli +1R, siirrä stop breakeven
if unrealized_pnl_r > 1.0:
    position.stop_price = position.entry_price
```

### Lisää Timeout Exit (30 bars)

```python
# Timeout after 30 bars
if position.bars_held >= 30:
    exit_triggered = True
    exit_price = current_price
    exit_reason = 'timeout'
```

### Lisää Partial Profit Taking

```python
# Take 50% profit at +1.5R
if unrealized_pnl_r >= 1.5 and not position.partial_taken:
    position.size *= 0.5  # Reduce size by 50%
    position.partial_taken = True
    print(f"Took 50% profit at +1.5R on position #{position.id}")
```

### Multi-Timeframe Scanning

Muokkaa `markets` dictionary:

```python
self.markets = {
    'BTC-USD': {
        'name': 'Bitcoin',
        'timeframes': ['1h', '15m'],  # Skannaa molemmat
        'interval': '1h'
    }
}
```

---

## Suorituskyvyn Optimointi

### Vähennä API-kutsuja

```python
# Cache data 5 minuutiksi
self.data_cache_ttl = 300  # seconds

def get_latest_data(self, symbol, interval='1h', bars=100):
    cache_key = f"{symbol}_{interval}_{datetime.now().minute // 5}"
    if cache_key in self.data_cache:
        return self.data_cache[cache_key]
    ...
```

### Lisää Rate Limiting

```python
import time

# Sleep between API calls
time.sleep(1)  # 1 second between calls
```

### Async Scanning (Edistynyt)

Skannaa kaikki markkinat rinnakkain:

```python
import asyncio

async def scan_market_async(self, symbol, config):
    df = await self.get_latest_data_async(symbol, config['interval'])
    ...

async def scan_all_markets(self):
    tasks = [self.scan_market_async(s, c) for s, c in self.markets.items()]
    results = await asyncio.gather(*tasks)
    ...
```

---

## Troubleshooting

### Ongelma: "No data available"

**Syy**: yfinance ei palauta dataa symbolille
**Ratkaisu**:
1. Tarkista symbol on oikein (BTC-USD, SPY, GLD)
2. Tarkista internet-yhteys
3. Kokeile eri interval ('1d' toimii yleensä)

### Ongelma: Bot ei löydä setupeja

**Syy**: Markkinat eivät muodosta patterneita juuri nyt
**Ratkaisu**:
1. Odota - patternit harvemmat kuin teoriassa
2. Laajenna timeframeja (lisää 15m, 5m)
3. Laajenna markkinoita (lisää ETH, QQQ, SLV)

### Ongelma: Kaikki positiot menevät stoppiin

**Syy**: Normaalia - win rate ~38%
**Ratkaisu**:
1. Seuraa R-multiple metriikkaa (ei win ratea)
2. Expectancy pitää olla positiivinen (+0.25R)
3. Jos Profit Factor < 1.0, jotain vialla

### Ongelma: State file korruptoitunut

**Ratkaisu**:
```bash
# Poista state ja aloita alusta
rm paper_account_history.json
python3 paper_trading_bot.py
```

---

## Suositellut Strategiat

### Strategi 1: Konservatiivinen (Aloittelijoille)

```python
bot = PaperTradingBot(
    starting_balance=10000,
    risk_per_trade=0.005  # 0.5% riski
)
bot.max_positions = 5
bot.markets = {'GLD': {'name': 'Gold', 'timeframes': ['1h'], 'interval': '1h'}}
bot.run(duration_hours=24*7)  # 1 viikko
```

**Odotettu**:
- ~2-3 tradea/viikko
- Win rate ~52% (Kulta paras)
- +0.25R expectancy

### Strategi 2: Balanced (Suositeltu)

```python
bot = PaperTradingBot(
    starting_balance=10000,
    risk_per_trade=0.01  # 1% riski
)
# Käytä default markkinat (BTC, SPY, GLD)
bot.run(duration_hours=24*30)  # 1 kuukausi
```

**Odotettu**:
- ~15-20 tradea/viikko
- Win rate ~38%
- +0.25R expectancy
- ~+6%/kuukausi

### Strategi 3: Aggressiivinen

```python
bot = PaperTradingBot(
    starting_balance=10000,
    risk_per_trade=0.02  # 2% riski
)
bot.max_positions = 15
bot.markets = {
    'BTC-USD': {'name': 'Bitcoin', 'timeframes': ['1h'], 'interval': '1h'}
}
bot.run()
```

**Odotettu**:
- ~30 tradea/viikko (Bitcoin aktiivinen)
- Win rate ~35%
- +0.26R expectancy
- ~+12%/kuukausi (2x riski)

---

## Seuraavat Askeleet

### Viikko 1: Paper Trade
- Aja bot 1 viikko
- Tarkista dashboard päivittäin
- Varmista expectancy > 0

### Viikko 2-4: Validoi
- Aja bot 1 kuukausi
- Vertaa tuloksia backtestiin
- Win rate ~38%, Profit Factor ~1.49

### Kuukausi 2: Optimoi
- Testaa eri risk%:ja (0.5%, 1%, 1.5%)
- Testaa eri markkinoita
- Testaa partial profit taking

### Kuukausi 3: Valmistaudu Live-kauppaan
- Jos expectancy pysyy positiivisena (+0.20R+)
- Jos Profit Factor > 1.3
- Jos emotionaalisesti valmis

---

## Live Tradingiin Siirtyminen

⚠️ **ÄLÄ SIIRRY LIVE-KAUPPAAN** ennen kuin:

1. ✅ Paper trade vähintään 3 kuukautta
2. ✅ Expectancy pysyy positiivisena (+0.20R+)
3. ✅ Profit Factor > 1.3
4. ✅ Emotionaalisesti valmis häviämään rahaa
5. ✅ Ymmärrät kaikki riskit

**Kun valmis**:
1. Aloita PIENELLÄ ($500-$1,000 max)
2. Käytä 0.5% riskiä (ei 1%!)
3. Seuraa samoja metriikoita
4. Skaalaa hitaasti (kaksinkertaista 3kk välein jos toimii)

---

## Yhteenveto

**Paper Trading Bot** on täysin automaattinen työkalu pattern trading -järjestelmän validointiin reaaliajassa.

**Hyödyt**:
- ✅ Automaattinen 24/7 skannaus
- ✅ Automaattinen position hallinta
- ✅ Täydellinen trade-loki
- ✅ Ei vaadi manuaalista monitorointia
- ✅ Täysin ilmainen (ei broker-yhteyttä)

**Tavoite**:
- Validoi backtest-tulokset reaaliajassa
- Vahvista +0.25R expectancy live-datalla
- Rakenna luottamus ennen live-kauppaa

**Käytä 3 kuukautta** → Jos tulokset matchaavat backtestin → **Valmis live-kauppaan**!

---

*Huom: Tämä on PAPER TRADING botti. Ei tee oikeita kauppoja. Ei vaadi broker-yhteyttä. Täysin turvallinen testata.*
