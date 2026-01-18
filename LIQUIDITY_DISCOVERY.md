# Liquidity Discovery & Simulation Strategy

## The Challenge

**Problem:** Not all token pairs have liquidity on DEXs.

For triangular arbitrage to work, we need:
1. **VVV/USDC** pair with sufficient liquidity
2. **DIEM/USDC** pair with sufficient liquidity
3. Or: **VVV/DIEM** direct pair

**Current Reality (Base Chain):**
- VVV/USDC: Need to verify
- DIEM/USDC: Need to verify
- VVV/DIEM: Unlikely (DIEM is minted, not traded directly)

---

## Phase 1: Liquidity Discovery

### Step 1: Query DEX Subgraphs

**Aerodrome (Primary DEX on Base):**
```graphql
# Query all pools with VVV or DIEM
{
  pools(where: {
    or: [
      { token0: "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf" }  # VVV
      { token1: "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf" }
      { token0: "0xf4d97f2da56e8c3098f3a8d538db630a2606a024" }  # DIEM
      { token1: "0xf4d97f2da56e8c3098f3a8d538db630a2606a024" }
    ]
  }) {
    id
    token0 { symbol }
    token1 { symbol }
    reserve0
    reserve1
    volumeUSD
  }
}
```

**Uniswap V3 (Base):**
```graphql
{
  pools(where: {
    or: [
      { token0: "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf" }
      { token1: "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf" }
      { token0: "0xf4d97f2da56e8c3098f3a8d538db630a2606a024" }
      { token1: "0xf4d97f2da56e8c3098f3a8d538db630a2606a024" }
    ]
  }) {
    id
    token0 { symbol }
    token1 { symbol }
    liquidity
    volumeUSD
    feeTier
  }
}
```

### Step 2: Liquidity Thresholds

**Minimum Requirements for Profitable Arbitrage:**

| Metric | Minimum Value | Reason |
|--------|--------------|---------|
| **Total Liquidity** | $10,000 USD | Prevent high slippage |
| **24h Volume** | $1,000 USD | Ensure active trading |
| **Trade Size** | <5% of liquidity | Keep slippage under 1% |

**Slippage Calculation:**
```python
def calculate_slippage(trade_amount_usd: float, pool_liquidity_usd: float) -> float:
    """Estimate slippage based on constant product formula."""
    # Simplified: slippage ≈ (trade_amount / liquidity) * 100
    slippage_pct = (trade_amount_usd / pool_liquidity_usd) * 100
    return slippage_pct

# Example:
# Trade: $1,000 USDC
# Pool: $50,000 liquidity
# Slippage: ~2%
```

### Step 3: Discover Available Paths

**Code Implementation:**

```python
# venice_monitor/analysis/liquidity_discovery.py

import logging
from typing import List, Dict, Optional
import requests

logger = logging.getLogger(__name__)


class LiquidityDiscovery:
    """Discover available trading pairs and liquidity."""

    AERODROME_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/aerodrome-finance/base"
    UNISWAP_SUBGRAPH = "https://api.thegraph.com/subgraphs/name/uniswap/base-v3"

    # Token addresses on Base
    VVV_ADDRESS = "0xacfE6019Ed1A7Dc6f7B508C02d1b04ec88cC21bf"
    DIEM_ADDRESS = "0xf4d97f2da56e8c3098f3a8d538db630a2606a024"
    USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

    def __init__(self, min_liquidity_usd: float = 10000):
        """Initialize liquidity discovery.

        Args:
            min_liquidity_usd: Minimum liquidity threshold
        """
        self.min_liquidity = min_liquidity_usd

    def discover_pools(self) -> Dict[str, List[Dict]]:
        """Discover all pools with VVV/DIEM on Base DEXs.

        Returns:
            Dictionary of pools by DEX
        """
        aerodrome_pools = self._query_aerodrome()
        uniswap_pools = self._query_uniswap()

        return {
            'aerodrome': aerodrome_pools,
            'uniswap': uniswap_pools,
        }

    def find_triangular_paths(self) -> List[Dict]:
        """Find all possible triangular arbitrage paths.

        Returns:
            List of viable paths with liquidity info
        """
        pools = self.discover_pools()
        paths = []

        # Check Path 1: USDC → VVV → DIEM → USDC
        vvv_usdc_pool = self._find_pool(pools, self.VVV_ADDRESS, self.USDC_ADDRESS)
        diem_usdc_pool = self._find_pool(pools, self.DIEM_ADDRESS, self.USDC_ADDRESS)

        if vvv_usdc_pool and diem_usdc_pool:
            paths.append({
                'path': 'USDC → VVV → DIEM → USDC',
                'pools': [vvv_usdc_pool, None, diem_usdc_pool],  # None = minting
                'liquidity_score': self._calculate_path_liquidity([vvv_usdc_pool, diem_usdc_pool]),
                'viable': True
            })

        # Check Path 2: USDC → DIEM → VVV → USDC
        if diem_usdc_pool and vvv_usdc_pool:
            paths.append({
                'path': 'USDC → DIEM → VVV → USDC',
                'pools': [diem_usdc_pool, None, vvv_usdc_pool],  # None = burning DIEM
                'liquidity_score': self._calculate_path_liquidity([diem_usdc_pool, vvv_usdc_pool]),
                'viable': True
            })

        # Check for direct VVV/DIEM pool (rare)
        vvv_diem_pool = self._find_pool(pools, self.VVV_ADDRESS, self.DIEM_ADDRESS)
        if vvv_diem_pool:
            paths.append({
                'path': 'VVV ↔ DIEM direct swap',
                'pools': [vvv_diem_pool],
                'liquidity_score': vvv_diem_pool['liquidity_usd'],
                'viable': vvv_diem_pool['liquidity_usd'] > self.min_liquidity
            })

        logger.info(f"Found {len(paths)} potential arbitrage paths")
        return paths

    def _find_pool(self, pools: Dict, token0: str, token1: str) -> Optional[Dict]:
        """Find pool for token pair across all DEXs."""
        for dex_name, dex_pools in pools.items():
            for pool in dex_pools:
                if self._is_token_pair(pool, token0, token1):
                    return {**pool, 'dex': dex_name}
        return None

    def _is_token_pair(self, pool: Dict, token0: str, token1: str) -> bool:
        """Check if pool contains both tokens."""
        pool_tokens = {pool['token0'].lower(), pool['token1'].lower()}
        target_tokens = {token0.lower(), token1.lower()}
        return pool_tokens == target_tokens

    def _calculate_path_liquidity(self, pools: List[Dict]) -> float:
        """Calculate minimum liquidity across path."""
        return min(pool['liquidity_usd'] for pool in pools)

    def _query_aerodrome(self) -> List[Dict]:
        """Query Aerodrome subgraph for pools."""
        # Implementation would use GraphQL queries
        # For now, return placeholder
        return []

    def _query_uniswap(self) -> List[Dict]:
        """Query Uniswap V3 subgraph for pools."""
        # Implementation would use GraphQL queries
        return []
```

---

## Phase 2: Simulation Engine

### Step 1: Build Backtest Framework

**File:** `venice_monitor/simulation/backtest.py`

```python
"""Backtesting engine for arbitrage strategies."""

import logging
from datetime import datetime
from typing import List, Dict
import pandas as pd

logger = logging.getLogger(__name__)


class ArbitrageBacktester:
    """Backtest arbitrage strategies against historical data."""

    def __init__(self, price_history_db):
        """Initialize backtester.

        Args:
            price_history_db: PriceHistoryDB instance
        """
        self.db = price_history_db
        self.trades = []

    def backtest_mint_arbitrage(
        self,
        start_date: str,
        end_date: str,
        min_profit_pct: float = 5.0
    ) -> Dict:
        """Backtest mint-and-sell arbitrage strategy.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            min_profit_pct: Minimum profit to trigger trade

        Returns:
            Backtest results with P&L
        """
        # Get historical data
        vvv_prices = self.db.get_vvv_history_range(start_date, end_date)
        diem_prices = self.db.get_diem_history_range(start_date, end_date)
        mint_rates = self.db.get_mint_rate_history_range(start_date, end_date)

        # Align timestamps
        df = pd.merge(vvv_prices, diem_prices, on='timestamp')
        df = pd.merge(df, mint_rates, on='timestamp')

        total_profit = 0
        winning_trades = 0
        losing_trades = 0

        for _, row in df.iterrows():
            mint_cost = row['vvv_price'] * row['mint_rate']
            market_price = row['diem_price']
            spread_pct = ((market_price - mint_cost) / mint_cost) * 100

            if spread_pct >= min_profit_pct:
                # Simulate trade
                profit_per_diem = market_price - mint_cost
                gas_cost = 5.0  # $5 gas estimate

                # Assume 1 DIEM trade
                net_profit = profit_per_diem - gas_cost

                self.trades.append({
                    'timestamp': row['timestamp'],
                    'mint_cost': mint_cost,
                    'sell_price': market_price,
                    'spread_pct': spread_pct,
                    'gross_profit': profit_per_diem,
                    'net_profit': net_profit,
                })

                total_profit += net_profit
                if net_profit > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1

        return {
            'total_trades': len(self.trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': winning_trades / len(self.trades) if self.trades else 0,
            'total_profit_usd': total_profit,
            'avg_profit_per_trade': total_profit / len(self.trades) if self.trades else 0,
            'trades': self.trades,
        }
```

### Step 2: Paper Trading Mode

**File:** `venice_monitor/simulation/paper_trading.py`

```python
"""Paper trading simulator for live testing without capital risk."""

import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperTrader:
    """Simulate trades without real capital."""

    def __init__(self, starting_capital_usd: float = 10000):
        """Initialize paper trader.

        Args:
            starting_capital_usd: Starting virtual capital
        """
        self.capital = starting_capital_usd
        self.starting_capital = starting_capital_usd
        self.positions = {}
        self.trade_history = []

    def execute_arbitrage(
        self,
        path: str,
        entry_price: float,
        exit_price: float,
        amount_usd: float,
        gas_cost: float = 5.0
    ) -> Dict:
        """Execute simulated arbitrage trade.

        Args:
            path: Trade path description
            entry_price: Entry price
            exit_price: Exit price
            amount_usd: Trade size in USD
            gas_cost: Estimated gas cost

        Returns:
            Trade result
        """
        if amount_usd > self.capital:
            logger.warning(f"Insufficient capital: {self.capital} < {amount_usd}")
            return {'executed': False, 'reason': 'insufficient_capital'}

        # Calculate profit/loss
        gross_profit = ((exit_price - entry_price) / entry_price) * amount_usd
        net_profit = gross_profit - gas_cost

        # Update capital
        self.capital += net_profit

        trade = {
            'timestamp': datetime.utcnow().isoformat(),
            'path': path,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'amount_usd': amount_usd,
            'gross_profit': gross_profit,
            'gas_cost': gas_cost,
            'net_profit': net_profit,
            'capital_after': self.capital,
            'roi_pct': (net_profit / amount_usd) * 100,
        }

        self.trade_history.append(trade)
        logger.info(f"Paper trade executed: {net_profit:+.2f} USD (Capital: ${self.capital:.2f})")

        return {'executed': True, 'trade': trade}

    def get_performance(self) -> Dict:
        """Get overall performance metrics.

        Returns:
            Performance summary
        """
        if not self.trade_history:
            return {'total_trades': 0}

        total_profit = self.capital - self.starting_capital
        roi_pct = (total_profit / self.starting_capital) * 100

        winning_trades = [t for t in self.trade_history if t['net_profit'] > 0]
        losing_trades = [t for t in self.trade_history if t['net_profit'] <= 0]

        return {
            'total_trades': len(self.trade_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trade_history),
            'starting_capital': self.starting_capital,
            'current_capital': self.capital,
            'total_profit': total_profit,
            'roi_pct': roi_pct,
            'avg_profit_per_trade': total_profit / len(self.trade_history),
        }
```

---

## Phase 3: Integration with PassiveIncomeMaximizer

### PIM Crypto Component Architecture

```
PassiveIncomeMaximizer/
├── engine/
│   ├── agents/
│   │   └── crypto_arbitrage_agent.py  ← NEW
│   ├── modules/
│   │   ├── crypto_liquidity.py        ← NEW
│   │   ├── crypto_execution.py        ← NEW
│   │   └── crypto_risk_manager.py     ← NEW
│   └── services/
│       └── venice_arbitrage_service.py ← Bridge to venice-monitor
```

### Crypto Arbitrage Agent

**File:** `PassiveIncomeMaximizer/engine/agents/crypto_arbitrage_agent.py`

```python
"""Crypto arbitrage agent for PIM."""

from agents.base_agent import BaseAgent
import requests


class CryptoArbitrageAgent(BaseAgent):
    """Agent for monitoring and executing crypto arbitrage trades."""

    def __init__(self, config):
        super().__init__(config)
        self.venice_monitor_url = "http://localhost:8091"  # Venice monitor API
        self.paper_trading = config.get('paper_trading', True)

    def analyze_opportunities(self):
        """Query Venice monitor for current opportunities."""
        response = requests.get(f"{self.venice_monitor_url}/api/opportunities")
        opportunities = response.json()

        for opp in opportunities:
            if opp['profit_pct'] > self.config.get('min_profit_pct', 5.0):
                self.log(f"Opportunity found: {opp['path']} - {opp['profit_pct']:.2f}%")

                if self.paper_trading:
                    self.execute_paper_trade(opp)
                else:
                    # Real execution (requires approval)
                    self.request_trade_approval(opp)

    def execute_paper_trade(self, opportunity):
        """Execute simulated trade."""
        response = requests.post(
            f"{self.venice_monitor_url}/api/paper_trade",
            json=opportunity
        )
        result = response.json()
        self.log(f"Paper trade: {result['net_profit']:+.2f} USD")

    def get_performance(self):
        """Get trading performance metrics."""
        response = requests.get(f"{self.venice_monitor_url}/api/performance")
        return response.json()
```

### Venice Monitor API Extension

**File:** `venice_monitor/api/server.py`

```python
"""REST API for Venice monitor integration with PIM."""

from flask import Flask, jsonify, request
from venice_monitor.simulation.paper_trading import PaperTrader

app = Flask(__name__)
paper_trader = PaperTrader(starting_capital_usd=10000)


@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """Get current arbitrage opportunities."""
    # Return current analysis from monitor
    return jsonify([
        {
            'path': 'USDC → VVV → DIEM → USDC',
            'profit_pct': -59.4,
            'profit_usd': -594.00,
            'viable': False,
        }
    ])


@app.route('/api/paper_trade', methods=['POST'])
def execute_paper_trade():
    """Execute paper trade."""
    opp = request.json
    result = paper_trader.execute_arbitrage(
        path=opp['path'],
        entry_price=opp.get('entry_price', 0),
        exit_price=opp.get('exit_price', 0),
        amount_usd=opp.get('amount_usd', 1000),
    )
    return jsonify(result)


@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get trading performance."""
    return jsonify(paper_trader.get_performance())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8091)
```

---

## Implementation Roadmap

### Week 1: Liquidity Discovery
- [ ] Query Aerodrome subgraph for VVV/USDC pool
- [ ] Query for DIEM/USDC pool
- [ ] Calculate liquidity scores
- [ ] Identify viable arbitrage paths

### Week 2: Simulation
- [ ] Build backtest engine
- [ ] Download historical price data (CMC API)
- [ ] Run backtest for past 6 months
- [ ] Analyze if profitable opportunities existed

### Week 3: Paper Trading
- [ ] Implement paper trading module
- [ ] Add REST API to Venice monitor
- [ ] Test with live prices but simulated capital
- [ ] Track performance metrics

### Week 4: PIM Integration
- [ ] Create CryptoArbitrageAgent
- [ ] Connect to Venice monitor API
- [ ] Add crypto dashboard to PIM UI
- [ ] Set up approval workflow for real trades

### Month 2: Live Trading (If Profitable)
- [ ] Set up Base wallet
- [ ] Fund with small capital ($100-500)
- [ ] Execute first live arbitrage trade
- [ ] Monitor slippage and gas costs
- [ ] Gradually increase position sizes

---

## Success Metrics

### Simulation Phase
- **Target ROI:** >20% annually in backtests
- **Win Rate:** >60% of trades profitable
- **Max Drawdown:** <10% of capital
- **Minimum Trade Frequency:** 1+ opportunity per week

### Paper Trading Phase
- **Duration:** 30 days minimum
- **Target:** Positive P&L over period
- **Consistency:** Profitable in ≥3 of 4 weeks

### Live Trading Phase
- **Starting Capital:** $100-500 USD
- **Position Size:** Max 10% of capital per trade
- **Stop Loss:** Exit if capital drops 20%
- **Scale-up Trigger:** 50% profit with <5% max drawdown

---

## Risk Management

### Capital Allocation
- **Paper Trading:** Unlimited virtual capital
- **Live Trading Tier 1:** $100-500 (learning phase)
- **Live Trading Tier 2:** $500-2000 (proven strategy)
- **Live Trading Tier 3:** $2000+ (scaled operations)

### Trade Size Limits
- **Maximum per trade:** 20% of capital
- **Maximum daily exposure:** 50% of capital
- **Reserve for gas:** 10% of capital (never trade)

### Circuit Breakers
- **Daily loss limit:** -5% of capital → Pause trading
- **Weekly loss limit:** -10% of capital → Stop for 1 week
- **Monthly loss limit:** -20% of capital → Strategy review

---

## Next Steps

1. **Immediate:**
   - ✅ Document strategy (done)
   - ⏳ Implement liquidity discovery module
   - ⏳ Query DEX subgraphs for pool data

2. **This Week:**
   - ⏳ Build backtest engine
   - ⏳ Download historical prices
   - ⏳ Run simulation on past 6 months

3. **Next Week:**
   - ⏳ Implement paper trading
   - ⏳ Add REST API to monitor
   - ⏳ Start live paper trading

4. **This Month:**
   - ⏳ Integrate with PIM as CryptoArbitrageAgent
   - ⏳ Build crypto dashboard
   - ⏳ If profitable in paper trading → Plan live deployment

**The goal: Transform Venice monitor from a passive watcher into an active profit generator integrated with PassiveIncomeMaximizer!**
