# Triangular Arbitrage: VVV/DIEM/USDC on Base

## Concept: Cross-Token Arbitrage Opportunities

Instead of just monitoring **VVV → DIEM mint arbitrage**, we can monitor **triangular arbitrage** across three tokens to capture price inefficiencies in decentralized exchanges.

---

## The Opportunity

### Traditional Arbitrage (Current)
```
VVV → Mint DIEM → Sell DIEM
Profit when: DIEM market price > Mint cost
Current: -76.53% (not profitable)
```

### Triangular Arbitrage (New)
```
Path 1: USDC → VVV → DIEM → USDC
Path 2: USDC → DIEM → VVV → USDC
Profit when: Exchange rate discrepancies exist across pairs
```

---

## How Triangular Arbitrage Works

### Example Scenario

**Starting Capital:** 1000 USDC

**Step 1:** USDC → VVV
- Price: 1 VVV = $3.00 USDC
- Buy: 333.33 VVV

**Step 2:** VVV → DIEM
- Mint rate: 312.5 sVVV per DIEM
- Mint: 1.067 DIEM (333.33 / 312.5)

**Step 3:** DIEM → USDC
- Price: 1 DIEM = $385 USDC
- Sell: 410.79 USDC

**Profit:** 410.79 - 1000 = **-589.21 USDC loss** (current market)

---

## When It Becomes Profitable

### Scenario 1: VVV Price Drops
If VVV drops to $2.00 while DIEM stays at $381:
- Buy VVV cheaper
- Mint DIEM at lower cost ($625 instead of $938)
- Sell DIEM at market ($381)
- **Still negative, but less so**

### Scenario 2: DIEM Price Spikes
If DIEM spikes to $650 while VVV stays at $3:
- Mint cost: $938
- Sell price: $650
- **Still negative**

### Scenario 3: Mint Rate Drops
If mint rate drops to 90 sVVV per DIEM (launch rate):
- Mint cost: 90 × $3 = $270
- Sell price: $381
- **Profit: +$111 per DIEM** ✅

### Scenario 4: Market Inefficiencies
If Aerodrome has DIEM at $400 but Uniswap has it at $450:
- Mint at $938 (still negative)
- But: Buy on Aerodrome at $400, sell on Uniswap at $450
- **Profit: +$50 per DIEM (minus gas)** ✅

---

## Real Arbitrage Opportunities

### 1. Cross-DEX Arbitrage
Monitor price differences between:
- **Aerodrome** (Base DEX)
- **Uniswap V3** (Base)
- **Sushiswap** (Base)
- **CoinMarketCap** (CEX aggregate)

**Example:**
```
Aerodrome: DIEM = $380
Uniswap:   DIEM = $390
Arbitrage: Buy on Aerodrome, sell on Uniswap
Profit:    $10 per DIEM (minus gas ~$1-2)
Net:       ~$8 per DIEM
```

### 2. Triangular Path Arbitrage
Monitor multiple paths:

**Path A:** USDC → VVV → DIEM → USDC
**Path B:** USDC → DIEM → VVV → USDC

If exchange rates are misaligned, one path becomes profitable.

**Example:**
```
Path A: 1000 USDC → 333 VVV → 1.07 DIEM → 407 USDC = -593 USDC
Path B: 1000 USDC → 2.62 DIEM → 819 VVV → 2457 USDC = +1457 USDC ✅
```

*(This requires USDC/DIEM pair to exist and have different pricing than implied by VVV prices)*

### 3. Mint vs Buy Arbitrage
Monitor:
- **Mint cost:** 312.5 VVV × $3.01 = $940.31
- **Market price:** $381.48
- **Spread:** -558.83 (-59.4%)

When mint cost < market price:
- Mint DIEM
- Sell immediately
- Profit = spread

---

## Implementation Strategy

### Phase 1: Data Collection (Immediate)
**Add to Venice Monitor:**
- Track VVV/USDC price on Aerodrome
- Track DIEM/USDC price on Aerodrome
- Track DIEM prices across multiple DEXs
- Calculate implied prices and detect discrepancies

### Phase 2: Triangular Path Calculator
**New Module:** `venice_monitor/analysis/triangular_arbitrage.py`

```python
class TriangularArbitrage:
    def calculate_paths(self, capital_usdc: float):
        # Path 1: USDC → VVV → DIEM → USDC
        path1 = self.path_usdc_vvv_diem_usdc(capital_usdc)

        # Path 2: USDC → DIEM → VVV → USDC
        path2 = self.path_usdc_diem_vvv_usdc(capital_usdc)

        # Path 3: Direct mint arbitrage
        path3 = self.path_mint_and_sell(capital_usdc)

        return {
            'path1': path1,
            'path2': path2,
            'path3': path3,
            'best_path': max([path1, path2, path3], key=lambda x: x['profit'])
        }
```

### Phase 3: Cross-DEX Monitor
**Track prices on:**
- Aerodrome (Base)
- Uniswap V3 (Base)
- Velodrome (Optimism - if VVV/DIEM listed)

**Alert when:**
- Cross-DEX spread > 2% (profitable after gas)
- Triangular path profit > 1%

### Phase 4: Automated Execution (Advanced)
**Warning:** This requires:
- Base wallet with USDC
- Gas reserves (ETH on Base)
- Flash loan capability (optional for larger capital)
- MEV protection

---

## CoinMarketCap API Integration

Based on the [CMC API docs](https://coinmarketcap.com/api/documentation/v1/), we can use:

### 1. Multiple Cryptocurrency Quotes
**Endpoint:** `/v2/cryptocurrency/quotes/latest`
```bash
# Get VVV and DIEM prices in one call
curl -H "X-CMC_PRO_API_KEY: $API_KEY" \
  "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest?id=35509,38186&convert=USD"
```

**Benefit:** Reduce API calls (1 instead of 2)

### 2. OHLCV Historical Data
**Endpoint:** `/v2/cryptocurrency/ohlcv/historical`
```bash
# Get price history for technical analysis
curl -H "X-CMC_PRO_API_KEY: $API_KEY" \
  "https://pro-api.coinmarketcap.com/v2/cryptocurrency/ohlcv/historical?id=35509&time_start=2025-12-01&convert=USD"
```

**Benefit:** Build price history faster (bootstrap initial database)

### 3. Price Performance Stats
**Endpoint:** `/v2/cryptocurrency/quotes/latest` (includes percent_change)
```json
{
  "percent_change_1h": 0.5,
  "percent_change_24h": -2.3,
  "percent_change_7d": -15.2,
  "percent_change_30d": 25.8
}
```

**Benefit:** Instant volatility signals without calculating ourselves

---

## Profitability Analysis

### Current State (2026-01-18)
```
VVV: $3.01
DIEM: $381.48
Mint Cost: $940.31

Triangular Arbitrage:
Path 1 (USDC→VVV→DIEM→USDC): -59.4% LOSS
Path 2 (Direct buy DIEM): N/A (no USDC/DIEM pair found)
Path 3 (Mint & sell): -59.4% LOSS

Verdict: NO PROFITABLE PATHS CURRENTLY
```

### When It Becomes Profitable

**Condition 1: Mint rate drops**
- Mint rate: 312.5 → 90 sVVV per DIEM
- Mint cost: $938 → $271
- Market price: $381
- **Arbitrage: +$110 per DIEM** ✅

**Condition 2: DIEM price spikes**
- Mint cost: $938 (fixed)
- Market price: $381 → $1,000
- **Arbitrage: +$62 per DIEM** ✅

**Condition 3: Cross-DEX spread**
- Aerodrome: $380
- Uniswap: $395
- **Arbitrage: +$15 per DIEM** ✅
- (Requires DIEM liquidity on both DEXs)

---

## Risks and Considerations

### 1. Gas Costs
- Base chain: ~$0.50-2 per transaction
- Triangular arbitrage: 3 transactions = $1.50-6
- **Minimum profitable spread: 2-3%**

### 2. Slippage
- Low liquidity pools have high slippage
- Large trades move price against you
- **Need to check pool depth before executing**

### 3. MEV (Maximal Extractable Value)
- Frontrunning bots can steal arbitrage
- **Solution:** Use private mempools or MEV protection

### 4. Lock-up Risk
- Minting DIEM locks VVV
- Must burn DIEM to unlock
- **Cannot exit position immediately**

---

## Recommended Next Steps

### Immediate (This Week)
1. ✅ **Monitor current VVV/DIEM prices** (already running)
2. ⏳ **Add USDC price tracking** (need Aerodrome API)
3. ⏳ **Track cross-DEX DIEM prices** (Aerodrome vs Uniswap)
4. ⏳ **Implement triangular path calculator**

### Short-term (This Month)
5. ⏳ **Build historical price database** (use CMC OHLCV endpoint)
6. ⏳ **Backtest arbitrage signals** against historical data
7. ⏳ **Set up Base wallet** for potential execution
8. ⏳ **Calculate optimal position sizing** (gas vs profit)

### Long-term (Future)
9. ⏳ **Automated execution** (with safety limits)
10. ⏳ **Flash loan integration** (for larger capital)
11. ⏳ **Cross-chain arbitrage** (Base ↔ Optimism)
12. ⏳ **MEV protection** (private mempools)

---

## Code Enhancement: Triangular Arbitrage Module

**File:** `venice_monitor/analysis/triangular_arbitrage.py`

```python
"""Triangular arbitrage path analysis."""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TriangularArbitrageAnalyzer:
    """Analyze triangular arbitrage opportunities."""

    def __init__(self, gas_cost_usd: float = 5.0):
        """Initialize analyzer.

        Args:
            gas_cost_usd: Estimated gas cost per transaction in USD
        """
        self.gas_cost_usd = gas_cost_usd

    def analyze_paths(
        self,
        vvv_price: float,
        diem_price: float,
        mint_rate: float,
        usdc_amount: float = 1000.0
    ) -> Dict[str, any]:
        """Analyze all triangular arbitrage paths.

        Args:
            vvv_price: Current VVV price in USD
            diem_price: Current DIEM price in USD
            mint_rate: Current mint rate (sVVV per DIEM)
            usdc_amount: Starting capital in USDC

        Returns:
            Dictionary with all paths and best opportunity
        """
        paths = []

        # Path 1: USDC → VVV → DIEM → USDC
        path1 = self._path_usdc_vvv_diem_usdc(
            usdc_amount, vvv_price, diem_price, mint_rate
        )
        paths.append(path1)

        # Path 2: Direct mint comparison
        path2 = self._path_mint_vs_buy(
            usdc_amount, vvv_price, diem_price, mint_rate
        )
        paths.append(path2)

        # Find best path
        best_path = max(paths, key=lambda x: x['profit_usd'])

        return {
            'all_paths': paths,
            'best_path': best_path,
            'is_profitable': best_path['profit_usd'] > 0,
        }

    def _path_usdc_vvv_diem_usdc(
        self, usdc: float, vvv_price: float, diem_price: float, mint_rate: float
    ) -> Dict:
        """Calculate Path 1: USDC → VVV → DIEM → USDC."""
        # Step 1: USDC → VVV
        vvv_amount = usdc / vvv_price
        gas1 = self.gas_cost_usd

        # Step 2: VVV → DIEM (mint)
        diem_amount = vvv_amount / mint_rate
        gas2 = self.gas_cost_usd * 1.5  # Minting is more expensive

        # Step 3: DIEM → USDC
        final_usdc = diem_amount * diem_price
        gas3 = self.gas_cost_usd

        total_gas = gas1 + gas2 + gas3
        profit = final_usdc - usdc - total_gas
        profit_pct = (profit / usdc) * 100

        return {
            'name': 'USDC → VVV → DIEM → USDC',
            'steps': [
                f'Buy {vvv_amount:.2f} VVV',
                f'Mint {diem_amount:.4f} DIEM',
                f'Sell for {final_usdc:.2f} USDC'
            ],
            'start_usdc': usdc,
            'end_usdc': final_usdc,
            'gas_cost_usd': total_gas,
            'profit_usd': profit,
            'profit_pct': profit_pct,
        }

    def _path_mint_vs_buy(
        self, usdc: float, vvv_price: float, diem_price: float, mint_rate: float
    ) -> Dict:
        """Compare minting DIEM vs buying directly."""
        mint_cost = mint_rate * vvv_price

        # How much DIEM can we get?
        diem_by_minting = usdc / mint_cost
        diem_by_buying = usdc / diem_price

        # Sell all DIEM
        final_usdc_mint = diem_by_minting * diem_price
        final_usdc_buy = diem_by_buying * diem_price  # Same as usdc

        # Gas costs
        gas_mint = self.gas_cost_usd * 2  # Mint + sell
        gas_buy = self.gas_cost_usd * 2   # Buy + sell

        profit_mint = final_usdc_mint - usdc - gas_mint
        profit_buy = final_usdc_buy - usdc - gas_buy

        return {
            'name': 'Mint vs Buy Comparison',
            'mint_path': {
                'diem_amount': diem_by_minting,
                'profit_usd': profit_mint,
            },
            'buy_path': {
                'diem_amount': diem_by_buying,
                'profit_usd': profit_buy,
            },
            'better_option': 'mint' if profit_mint > profit_buy else 'buy',
            'profit_usd': max(profit_mint, profit_buy),
            'profit_pct': (max(profit_mint, profit_buy) / usdc) * 100,
        }
```

---

## Integration with Current Monitor

**Add to `venice_monitor/main.py`:**

```python
from venice_monitor.analysis.triangular_arbitrage import TriangularArbitrageAnalyzer

# In VeniceMonitor.__init__:
self.triangular_analyzer = TriangularArbitrageAnalyzer(gas_cost_usd=5.0)

# In check_prices():
triangular_analysis = self.triangular_analyzer.analyze_paths(
    vvv_price, diem_price, mint_rate, usdc_amount=1000.0
)

if triangular_analysis['is_profitable']:
    logger.warning(f"🔺 TRIANGULAR ARBITRAGE OPPORTUNITY: {triangular_analysis['best_path']}")
    if self.notifier:
        self.notifier.send_triangular_arbitrage_alert(triangular_analysis)
```

---

## Summary

**Current State:**
- ❌ No profitable triangular arbitrage paths exist
- Mint arbitrage: -59.4% loss
- VVV/DIEM spread: Deeply negative

**Monitoring Strategy:**
1. ✅ Continue current price monitoring
2. ⏳ Add triangular arbitrage calculator
3. ⏳ Track cross-DEX prices
4. ⏳ Alert when any path becomes profitable (>2% after gas)

**When Profitable:**
- Mint rate drops significantly
- DIEM price spikes above mint cost
- Cross-DEX price discrepancies appear
- VVV price drops while DIEM stays stable

**The monitor will alert you the moment any of these conditions trigger a profitable arbitrage opportunity!**
