# Quick Start Guide

## 1. Asennus (30 sekuntia)

```bash
# Asenna riippuvuudet
pip install -r requirements.txt
```

## 2. Perusajo (1 minuutti)

```bash
# Aja kaikki scannerit SPY datalla
python3 main.py
```

**Mitä tapahtuu:**
- Lataa SPY datan viimeiseltä 2 vuodelta
- Skannaa ICI, W/M ja Harmonic patternit
- Tulostaa statistiikat konsoliin
- Luo CSV-tiedoston tuloksista

## 3. Tulokset

### Konsoli output
```
Total setups found: 8
Valid setups: 4 (50.0%)

BY PATTERN TYPE:
ICI:
  Total: 8
  Valid: 4 (50.0%)
  Bullish: 6
  Bearish: 2

MOST RECENT VALID SETUPS:
1. 2025-10-30 - ICI (daily) - LONG
   Entry: $679.83 | Stop: $678.77 | Target: $694.65
   R:R: 14.04 | Fib: 0.430
   EMA: ✓ | MACD: ✓
```

### CSV tiedosto
```
Date,Pattern,Timeframe,Direction,Entry,Stop,Target,Risk_Reward,Valid
2025-10-30,ICI,daily,LONG,679.83,678.77,694.65,14.04,True
...
```

## 4. Esimerkkiskriptit

```bash
# Katso eri käyttötapauksia
python3 example_usage.py
```

Näyttää:
- Perus ICI skannaus
- Fibonacci laskelmat
- Multi-timeframe analyysi
- W/M patternit
- Mukautetut parametrit

## 5. Yksittäisen scannerin käyttö

```python
from data_loader import load_spy_data
from ici_scanner import ICIScanner

# Lataa data
df = load_spy_data(source='yfinance', period='1y')

# Luo scanner
scanner = ICIScanner()

# Skannaa
setups = scanner.scan(df, timeframe='daily')
valid = [s for s in setups if s.valid]

print(f"Löytyi {len(valid)} validia setuppia")
```

## 6. Mukautetut parametrit

```python
# Konservatiivinen skanneri
scanner = ICIScanner(
    min_impulse_candles=4,      # Pidempi impulse
    min_fib_level=0.500,         # Tiukempi Fib range
    max_fib_level=0.618,
    min_risk_reward=2.0          # Korkeampi R:R vaatimus
)

# Aggressiivinen skanneri
scanner = ICIScanner(
    min_impulse_candles=2,       # Lyhyempi impulse
    min_fib_level=0.382,         # Laajempi Fib range
    max_fib_level=0.786,
    min_risk_reward=1.0          # Matalampi R:R vaatimus
)
```

## 7. CSV datan käyttö

```python
from main import run_all_scanners

run_all_scanners(
    data_source='csv',
    csv_path='path/to/spy_data.csv'
)
```

CSV:n tulee sisältää sarakkeet:
- Date
- Open
- High
- Low
- Close
- Volume (valinnainen)

## 8. Eri aikavälien käyttö

```python
from data_loader import load_spy_data, DataLoader

# Lataa 1h data (max 60 päivää)
df_1h = load_spy_data(
    source='yfinance',
    period='60d',
    interval='1h'
)

# Skannaa momentum patternit
from pattern_scanners import MomentumScanner
momentum = MomentumScanner()
setups = momentum.scan(df_1h, '1h')
```

## Tiedostorakenne

```
fibonacci.py         - Fibonacci laskelmat
validators.py        - EMA/MACD/R:R validointi
ici_scanner.py       - ICI pattern skanneri
pattern_scanners.py  - Momentum, W/M, Harmonic scannerit
data_loader.py       - Data lataus (yfinance/CSV)
main.py             - Pääohjelma
example_usage.py    - Esimerkkejä
```

## Validointikriteerit

Setup on validi jos:
- Fibonacci retracement 0.382-0.786
- Risk/Reward ≥ 1.3
- EMA alignment (10 > 20 bullish)
- MACD alignment (> 0 bullish)

## Seuraavat askeleet

1. Aja `python3 main.py` nähdäksesi tulokset
2. Tutki `example_usage.py` eri käyttötapauksia varten
3. Muokkaa parametreja tarpeisiisi sopiviksi
4. Exporttaa CSV ja analysoi tuloksia

**Valmis!** Skanneri on käyttövalmis.
