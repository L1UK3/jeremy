# Explanation: Decision Cycle & Economic Model

This document explains the mechanics of the 720-turn game loop, action merging, and the economic formulas that drive heuristic decision scoring.

---

## 1. The 720-Turn Game Loop

A standard Kaggriculture game spans **30 in-game days**, with **24 hours (turns) per day**, totaling **720 turns**:

```
Step 0 ────────────── Step 23 ────────────── Step 24 ────────────── Step 719
Day 0, Hour 0         Day 0, Hour 23        Day 1, Hour 0         Day 29, Hour 23
(Morning Start)       (End of Day Drop)     (Daily Reset)         (Final Bank Balance)
```

### End-of-Day Processing (Hour 23)
At the end of each day:
1. **Water / Feed Check**: Any unwatered crop or unfed animal increments its unwatered/unfed counter. Two consecutive days without water/food results in permanent crop loss (turns to weed) or animal escape.
2. **Growth & Production**: Crops increment age. Animals bank care bonuses or yield product.
3. **Fertilizer Accumulation**: Surviving animals produce 1 fertilizer.
4. **Weed Spawning**: Empty unlocked tiles have a small chance (`weedSpawnChance = 0.005`) to spawn a weed.
5. **Daily Reset**: Hired farmhand counters reset; daily watering and feeding flags reset to `False`.

---

## 2. Action Composition & Merging

Each turn, a player may submit:
- **One action for the main farmer**: Movement, Tile interaction (`WATER`, `PLANT`, `HARVEST`, `FERTILIZE`, `DIG`), Shed interaction (`PICKUP`, `PLACE`, `DROP`), or `PASS`.
- **One action per hired farmhand**: Same set of unit actions.
- **Up to 10 market orders**: `BUY_SEED`, `BUY_PRODUCT`, `BUY_ANIMAL`, `SELL`, `BUY_LAND`, `HIRE`.

### How `ActionBuilder.merge()` Works
Because unit movement and market trading operate on independent channels in the Kaggle engine, an agent can walk to water a crop while simultaneously buying seeds and selling harvested produce.

`ActionBuilder.merge(*actions)` resolves candidate actions by:
1. Retaining the highest-priority non-`PASS` farmer action.
2. Concatenating all non-conflicting market orders into the `market` list.
3. Appending all farmhand actions into the `hands` list.

```python
# Merging a water action and a sell order:
action1 = ActionBuilder.water(score=80)
action2 = ActionBuilder.sell("WHEAT", 4, score=50)

merged = ActionBuilder.merge(action1, action2)
# Resulting dictionary sent to engine:
# {
#   "farmer": ["WATER"],
#   "hands": [],
#   "market": [["SELL", "WHEAT", 4]]
# }
```

---

## 3. Crop Economics & ROI Modeling

The agent's [`environment.economy.Economy`](file:///d:/Projects/jeremy/src/environment/economy.py) evaluates crop efficiency dynamically:

$$\text{Profit} = \text{Current Market Price} - \text{Seed Purchase Cost}$$

$$\text{ROI} = \frac{\text{Profit}}{\max(1, \text{Growth Days})}$$

### Crop Reference Parameters

| Crop | Seed Cost | Base Price | Growth Days to Peak | Peak Yield (Unfert.) | Peak Yield (Fert.) | Base Yield / Tile / Day |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Wheat** | $10 | $25 | 4 | 4 | 6 | 0.80 |
| **Carrot** | $20 | $35 | 3 | 3 | 4 | 0.75 |
| **Tomato** | $50 | $60 | 11 | 4 (ongoing) | 8 | 0.33 |
| **Strawberry**| $100 | $120 | 16 | 4 (ongoing) | 8 | 0.24 |
| **Melon** | $80 | $250 | 10 | 6 | 6 (fast) | 0.55 |

### Bonus Watering Window
* **One-time crops (Wheat, Carrot, Melon)**: Watering during the bonus window ($\ge \lceil \text{max\_yield\_day} / 2 \rceil$) adds $+1$ harvestable yield unit per day.
* **Fertilization**: Doubles the bonus added per day for 3 days.

---

## 4. Market Pricing & Supply Elasticity

Market sale prices fluctuate dynamically with global market supply $I$ relative to starting inventory $I_0$:
- When market supply $I < I_0$ (scarcity), prices rise above base price.
- When market supply $I > I_0$ (glut), prices fall toward the $1 floor.
- Goods with steep price curves (Melon, Strawberry, Milk, Wool) experience rapid price collapse during oversupply, whereas staples (Wheat, Carrot) absorb market volume more smoothly.
- Town center and unlocked town shops consume product inventory from the market on fixed turn intervals, creating natural demand sinks.
