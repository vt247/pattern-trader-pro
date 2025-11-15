"""
Database module for storing signals in PostgreSQL
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

class Database:
    """PostgreSQL database for trade signals"""

    def __init__(self):
        # Get database URL from environment
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            # Fallback to local JSON files
            self.use_postgres = False
            print("WARNING: No DATABASE_URL found, using local JSON files")
        else:
            self.use_postgres = True
            # Fix postgres:// to postgresql:// for psycopg2
            if self.database_url.startswith('postgres://'):
                self.database_url = self.database_url.replace('postgres://', 'postgresql://', 1)
            self._init_tables()

    def _get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url)

    def _init_tables(self):
        """Initialize database tables"""
        if not self.use_postgres:
            return

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Create signals table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    pattern_type VARCHAR(50) NOT NULL,
                    market VARCHAR(20) NOT NULL,
                    timeframe VARCHAR(10) NOT NULL,
                    entry DECIMAL(10, 2) NOT NULL,
                    stop DECIMAL(10, 2) NOT NULL,
                    target DECIMAL(10, 2) NOT NULL,
                    risk_reward DECIMAL(10, 2) NOT NULL,
                    chart_path TEXT,
                    status VARCHAR(20) DEFAULT 'open',
                    exit_price DECIMAL(10, 2),
                    exit_date TIMESTAMP,
                    pnl_r DECIMAL(10, 2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create account state table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS account_state (
                    id SERIAL PRIMARY KEY,
                    balance DECIMAL(10, 2) NOT NULL,
                    initial_balance DECIMAL(10, 2) NOT NULL,
                    equity DECIMAL(10, 2) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create index on timestamp
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_signals_timestamp
                ON signals(timestamp DESC)
            """)

            conn.commit()
            cur.close()
            conn.close()
            print("✓ Database tables initialized")

        except Exception as e:
            print(f"Error initializing database: {e}")

    def save_signal(self, signal: Dict):
        """Save a trade signal"""
        if not self.use_postgres:
            # Fallback to JSON
            self._save_to_json(signal)
            return

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO signals (
                    timestamp, pattern_type, market, timeframe,
                    entry, stop, target, risk_reward, chart_path,
                    status, exit_price, exit_date, pnl_r
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                signal['timestamp'],
                signal['pattern_type'],
                signal['market'],
                signal['timeframe'],
                signal['entry'],
                signal['stop'],
                signal['target'],
                signal['risk_reward'],
                signal.get('chart_path', ''),
                signal.get('status', 'open'),
                signal.get('exit_price'),
                signal.get('exit_date'),
                signal.get('pnl_r', 0)
            ))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error saving signal: {e}")

    def get_all_signals(self, limit: int = 100) -> List[Dict]:
        """Get all signals"""
        if not self.use_postgres:
            return self._load_from_json()

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT * FROM signals
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))

            signals = cur.fetchall()
            cur.close()
            conn.close()

            # Convert to regular dicts and format timestamps
            result = []
            for s in signals:
                signal = dict(s)
                signal['timestamp'] = signal['timestamp'].isoformat() if signal['timestamp'] else None
                signal['exit_date'] = signal['exit_date'].isoformat() if signal['exit_date'] else None
                # Convert Decimal to float
                for key in ['entry', 'stop', 'target', 'risk_reward', 'exit_price', 'pnl_r']:
                    if signal[key] is not None:
                        signal[key] = float(signal[key])
                result.append(signal)

            return result

        except Exception as e:
            print(f"Error loading signals: {e}")
            return []

    def update_signal_status(self, signal_id: int, status: str,
                           exit_price: float, pnl_r: float):
        """Update signal status when closed"""
        if not self.use_postgres:
            return

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE signals
                SET status = %s, exit_price = %s, exit_date = %s, pnl_r = %s
                WHERE id = %s
            """, (status, exit_price, datetime.now(), pnl_r, signal_id))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error updating signal: {e}")

    def save_account_state(self, balance: float, initial_balance: float, equity: float):
        """Save account state"""
        if not self.use_postgres:
            self._save_account_json(balance, initial_balance, equity)
            return

        try:
            conn = self._get_connection()
            cur = conn.cursor()

            # Delete old state and insert new
            cur.execute("DELETE FROM account_state")
            cur.execute("""
                INSERT INTO account_state (balance, initial_balance, equity)
                VALUES (%s, %s, %s)
            """, (balance, initial_balance, equity))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error saving account state: {e}")

    def get_account_state(self) -> Dict:
        """Get current account state"""
        if not self.use_postgres:
            return self._load_account_json()

        try:
            conn = self._get_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT * FROM account_state ORDER BY updated_at DESC LIMIT 1")
            state = cur.fetchone()

            cur.close()
            conn.close()

            if state:
                result = dict(state)
                # Convert Decimal to float
                for key in ['balance', 'initial_balance', 'equity']:
                    if result[key] is not None:
                        result[key] = float(result[key])
                return result
            else:
                return {'balance': 1000, 'initial_balance': 1000, 'equity': 1000}

        except Exception as e:
            print(f"Error loading account state: {e}")
            return {'balance': 1000, 'initial_balance': 1000, 'equity': 1000}

    # Fallback JSON methods
    def _save_to_json(self, signal: Dict):
        """Fallback: save to JSON file"""
        try:
            signals = []
            if os.path.exists('trade_signals.json'):
                with open('trade_signals.json', 'r') as f:
                    signals = json.load(f)
            signals.append(signal)
            with open('trade_signals.json', 'w') as f:
                json.dump(signals, f, indent=2)
        except:
            pass

    def _load_from_json(self) -> List[Dict]:
        """Fallback: load from JSON file"""
        try:
            if os.path.exists('trade_signals.json'):
                with open('trade_signals.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def _save_account_json(self, balance: float, initial_balance: float, equity: float):
        """Fallback: save account to JSON"""
        try:
            with open('account_state.json', 'w') as f:
                json.dump({
                    'balance': balance,
                    'initial_balance': initial_balance,
                    'equity': equity
                }, f, indent=2)
        except:
            pass

    def _load_account_json(self) -> Dict:
        """Fallback: load account from JSON"""
        try:
            if os.path.exists('account_state.json'):
                with open('account_state.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return {'balance': 1000, 'initial_balance': 1000, 'equity': 1000}
