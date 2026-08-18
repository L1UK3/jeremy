# Reference: Game Rules & Mechanics

This document provides a comprehensive technical reference for all rules, formulas, tables, and engine mechanics of the Kaggriculture environment.

---

## 1. Object Types & Parameters

| Type | Yield Type | Seed / Buy Cost | Base Market Price | Time to First Yield | Time to Max Yield | Subsequent Yields | Max Yield | Action Cost | Base Yield / Tile / Day |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wheat** | One-time | $10 | $25 | 2 days | 4 days | None | 6 (4 unfert.) | 1 | 0.80 |
| **Carrot** | One-time | $20 | $35 | 2 days | 3 days | None | 4 (3 unfert.) | 1 | 0.75 |
| **Tomato** | Ongoing | $50 | $60 | 8 days | 11 days | Every day ×4 | 4 total | 1 | 0.33 |
| **Strawberry** | Ongoing | $100 | $120 | 10 days | 16 days | Every other day ×4 | 4 total | 1 | 0.24 |
| **Melon** | One-time | $80 | $250 | 10 days | 10 days | None | 6 | 1 | 0.55 |
| **Goose / Egg** | Ongoing | $300 | $50 | 4 days | N/A | Every day | 4 held | 1 + 1 (build coop) | 1.00 |
| **Cow / Milk** | Ongoing | $400 | $160 | 8 days | N/A | Every 2 days | 6 held | 1 + 1 (build pasture) | 0.50 |
| **Sheep / Wool** | Ongoing | $500 | $200 | 6 days | N/A | Every 3 days | 6 held | 1 + 1 (build pasture) | 0.33 |
| **Fertilizer** | N/A | $100 | Dynamic | N/A | N/A | N/A | N/A | 1 | N/A |

### Crop Growth & Bonus Watering
* **Bonus Window (One-time crops)**: Begins on day $\lceil \text{max\_yield\_day} / 2 \rceil$. Each day watered during this window adds $+1$ unit to final harvest yield ($+2$ if fertilized).
  * **Wheat**: Days 2–4. Max yield 4 (6 with fertilizer).
  * **Carrot**: Days 2–3. Max yield 3 (4 with fertilizer).
  * **Melon**: Days 6–12 (peaks at day 10 unfertilized, day 8 fertilized). Max yield 6.
* **Ongoing Crops (Tomato, Strawberry)**: Scheduled production yields 1 unit by default, doubled to 2 if both watered and fertilized on that day. Total production is capped at 4 scheduled yields before the plant begins decay.

### Plant & Animal Lifespan, Decay, and Survival
* **Watering & Feeding Requirement**: Must be watered/fed at least once every two days. Two consecutive missed end-of-day refreshes turn plants into weeds and cause animals to escape (unrecoverable).
  * A newly planted seed starts with `consecutive_unwatered = 1` (planting day counts as the first missed day).
  * A newly placed animal starts with `consecutive_unfed = 0`.
* **Crop Decay**: Max lifespan begins 1 day after `max_yield_day` for one-time crops, or 1 day after cumulative production reaches cap for ongoing crops. Unharvested `yield_units` decay by 1 every other turn until reaching 0, at which point the tile converts to a `WEED`.
* **Animal Care**: `CARE` banks $+1$ on days the animal is fed. The entire banked bonus pays out on the next scheduled production day (capped by `max_held`).
* **Fertilizer Collection**: Surviving animals make 1 fertilizer available each day via `COLLECT_FERTILIZER` (does not accumulate past 1).

---

## 2. Farm Map & Quadrants

* **Grid Size**: $10 \times 10$ tiles divided into four $5 \times 5$ quadrants (`NW`, `NE`, `SW`, `SE`).
* **Quadrant Unlocking**: Only `NW` starts unlocked. Neighboring quadrants are unlocked via `BUY_LAND`:
  * First expansion (2nd quadrant): **$1,000**
  * Second expansion (3rd quadrant): **$2,000**
  * Third expansion (4th quadrant): **$4,000**
* **Movement on Locked Tiles**: Units may traverse locked quadrants, but cannot perform tile-modifying actions (`PLANT`, `WATER`, `DIG`, `BUILD_*`) on them.
* **Shed**: Centered at coordinates `(4,4)`, `(5,4)`, `(4,5)`, and `(5,5)`. Capacity is **100 non-seed items**. Items exceeding capacity at end-of-day drop are discarded. Seeds live in an uncapped, separate seed bank.
* **Weeds**: Spontaneously spawn on empty unlocked tiles with probability `weedSpawnChance = 0.005` at end of day. Cleared with `DIG`.

---

## 3. Worker Hiring & Spawn Mechanics

* **Hiring Cost Formula**: $\text{Cost} = \text{farmHandCostMult} \times \text{fib}(n)$, where $n$ is the number of hires already made today.
  * Sequence with default multiplier 1: **$1, $1, $2, $3, $5, $8, $13, $21, ...**
  * Cost resets to $1 at the start of each in-game day.
* **Spawn Position**: Spawned orthogonally adjacent to the shed, selecting the least occupied tile following `NW -> NE -> SW -> SE` tiebreaker preference.

---

## 4. Town Center & Town Shops

Shops unlock every `townShopUnlockInterval = 3` days, drawn uniformly at random **with replacement** (capped at 8 instances).

| Shop Type | Demand Multiplier | Demanded Goods |
| :--- | :--- | :--- |
| **Bakery** | $1\times$ | Eggs, Wheat |
| **Pizza Shop** | $1\times$ | Milk, Tomatoes, Wheat |
| **Brunch Spot** | $1\times$ | Eggs, Wheat, Strawberries |
| **Yarn Store** | $2\times$ | Wool |
| **Ice Cream Shop** | $1\times$ | Strawberries, Milk, Wheat |
| **Pet Cafe** | $2\times$ | Carrots |
| **Smoothie Shop** | $1\times$ | Strawberries, Milk |
| **Farmers Market** | $1\times$ | Wheat, Carrots, Tomatoes, Strawberries |
| **Town Center** | Flat $1\times$ every 24 turns | All produce (excluding Fertilizer) |

* Each shop instance consumes demanded products every `townShopSellInterval = 4` turns.

---

## 5. Market Pricing Function & Parameters

Market prices move dynamically based on inventory $I$ relative to equilibrium $I_0 = 10,000$:

$$\text{price}(I) = \max\left(1, \text{round}\left(\text{base} + \text{sign} \cdot \text{amp} \cdot f(|I - I_0|)\right)\right)$$

Where:
* $\text{sign} = +1$ if $I < I_0$ (scarcity), $-1$ if $I > I_0$ (glut).
* $\text{amp} = \frac{\text{target} \cdot \text{base}}{f(T)}$
* $f \in \{\text{linear}, \text{sq}, \text{sqrt}, \text{log}\}$ where $\text{log}(x) = \ln(1 + x)$.

### Market Price Parameter Table

| Resource | Base | $I_0$ | $T$ | Below Func | Below Target | Above Func | Above Target | $P(I_0 - T)$ | $P(I_0 + T)$ | $P(I_0 + 2T)$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wheat** | $25 | 10,000 | 400 | sqrt | 0.80 | log | 0.20 | $45 | $20 | $19 |
| **Carrot** | $35 | 10,000 | 450 | log | 0.20 | sqrt | 0.70 | $42 | $10 | $1 |
| **Tomato** | $60 | 10,000 | 200 | linear | 0.40 | sqrt | 0.60 | $84 | $24 | $9 |
| **Strawberry**| $120| 10,000 | 100 | sqrt | 0.70 | linear | 1.60 | $204 | $1 | $1 |
| **Melon** | $250| 10,000 | 300 | log | 0.20 | sq | 3.60 | $300 | $1 | $1 |
| **Egg** | $50 | 10,000 | 332 | linear | 0.40 | log | 0.20 | $70 | $40 | $39 |
| **Milk** | $160| 10,000 | 122 | sqrt | 0.60 | linear | 1.60 | $256 | $1 | $1 |
| **Wool** | $200| 10,000 | 105 | log | 0.20 | sq | 3.20 | $240 | $1 | $1 |
| **Fertilizer**| $100| 10,000 | 200 | linear | 0.40 | linear | 0.40 | $140 | $60 | $20 |

---

## 6. Turn Processing Order

Every turn, operations resolve in the following exact sequence:
1. **Action Validation**: Verify action legality and bounds.
2. **Player Actions**: Execute movement, planting, watering, harvesting, building, and shed operations simultaneously for both players.
3. **Market Actions**: Process market order queues in alternating order (one unit at a time, up to `maxMarketOrdersPerTurn = 10` per player).
4. **Town Buy Actions**: Town center and unlocked shops consume product inventory.
5. **Observation & State Refresh**:
   * **Day refresh** (at hour 23): Update plant/animal ages, check missed water/food, bank care bonuses, spawn weeds, discard shed overflow, reset daily hire counters and watered/fed flags.
   * **Market refresh**: Update dynamic market prices based on supply changes.
   * **Bank & Farm update**: Reflect final coin balances and cleared tiles.

---

## 7. Engine Configuration Parameters

| Parameter | Default Value | Description |
| :--- | :--- | :--- |
| `episodeSteps` | `720` | Total turns in match ($24 \text{ turns/day} \times 30 \text{ days}$). |
| `boardSize` | `10` | Grid width and height ($10 \times 10$ with four $5 \times 5$ quadrants). |
| `startingMoney` | `3000` | Starting coin balance per player. |
| `maxMarketOrdersPerTurn` | `10` | Max market transactions processed per turn per player. |
| `turnsPerDay` | `24` | Turns per in-game day. |
| `shedCapacity` | `100` | Maximum non-seed item capacity in player shed. |
| `weedSpawnChance` | `0.005` | Per-empty-tile weed spawn probability at end of day. |
| `townShopUnlockInterval` | `3` | Days between successive shop unlocks (capped at 8). |
| `townShopSellInterval` | `4` | Turns between consumption ticks by unlocked shops. |
| `townCenterSellInterval` | `24` | Turns between consumption ticks by town center. |
| `seed` | `None` | Optional seed for deterministic simulation. |
