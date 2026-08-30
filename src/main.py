from __future__ import annotations

import json
from typing import Any

from board import Board
from economy import Economy
from evaluators import (
    evaluate_expansion,
    evaluate_livestock,
    evaluate_market,
)
from explosion import explosion
from market import Market
from scheduler import Scheduler
from state import GameState

__all__ = [
    "agent",
    "expansion_agent",
    "explosion_agent",
    "main_agent",
    "opening_agent",
]


import base64
import zlib

_ROUTES: dict[int, dict] = {
    int(k): v
    for k, v in json.loads(
        zlib.decompress(
            base64.b85decode(
                "c-pmCO^@0z5dAMcbHE7@*joUvh?*rR2|~LFA*60qsoEZBZ>#<9&4*(<<8f>g^@QalesA8)*w1{DDS7%NKW_Jr_d9tylS5n-<T4>YZ@<6)sV1u7$L;>>{cklslU<Ut>Z#jceSE#f`{X4~$%GU;#tvi>Xb(2oNtrGf+g6jO9g9mciNN#=OS3(hEV}7Ko^6ktQhu<!T)rlRf{>EUx8p&962YCxi4|o-cAw?tt{HI!l<!pT?FW5TP%1$~CFoOGACq)@tq{s%Ba*^I5*VT)7MJg-Tx!S=M4!eR#)EeU)E+{VSs#V#s4NddMPZCDLAbfIjv}K~;Cq>mzMNc>Hn9V+3r8(GthPX#I*Ch`_fengB37C4w;^a`lUA-RgY7^zF&C1*1Q%aw5%okG5>f^y(8N1>Thw4H5DDjv2q%+-2&Y#G_zdFGse6<ITIywD5S3DEpe|~P0>Ra!fvqr{%1~5@r3`6^i`XshD55M8gLX52?eLa{q2nUXhtE4l5tS*6iVGXwDDfg|G-iRcM@kdo+AW>YoFp@K@5((WZD3O@n2uQ7q@e~v$3y_6(-sfLM9?2-Ylr`DZMs+)d>J=2bEEAnSXx`fQ<hafv@t(?>Y3$bk|uAJVy!LgUTv48K3=s-?$+P9wrvQiitpsAZqS6{1`M;8I9ttdu7FuC$~-=;S)RWNUmStD<VS(4Yr{+^VxSQ(WuQzsEti8$F<$CUY4+$YE|x~2EpaUFS)6{hM5{U=&HS~O>m$!PI^sMB?|A4xe_Vf)MXHHqY05U`Rq4@sx)oH{XW^a+0U;a{>>y>cR{8)zjmC5YG~3t+-^r8?8n`{u2%NYb^sp*o3Q<K@-=7rN$2lBgp;YO6bcRYD#xaWP(z-EYz{dMwe?PPom_J$T_AD|h2J+6Jr{AFhLnEh<a|#|zwz3bzTI0xvMRwE=i$2Ghk>iYW4BeBgD~N64zNxiSwC?^ATre{zi!gV{^xQ~s&MAUZ0NuWQ@{Wyox=k*@mohjry4BIlV=XMCl)UVlj-6KIrzF-FR&^y~-ER9cURoVMXYM5~a>pCE0{C-UdDf%O(Cdz(6KpS|(+8ySzZ|XTgV7>?TRCF}R(B!)HNwrDC+OEdKxfVC"
            )
        ).decode("utf-8")
    ).items()
}


def opening_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
) -> dict[str, Any]:
    """Opening phase agent (turns 0-23) executing scripted high-yield trajectories."""
    if state is None:
        state = GameState.from_obs(obs)
    step = state.step
    if step in _ROUTES:
        act = _ROUTES[step]
        return {
            "farmer": act.get("farmer", ["PASS"]),
            "hands": act.get("hands", []),
            "market": act.get("market", []),
        }
    return main_agent(obs, state=state)


def expansion_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
) -> dict[str, Any]:
    """Expansion phase agent executing quadrant expansion trajectories."""
    if state is None:
        state = GameState.from_obs(obs)
    step = state.step
    if step in _ROUTES:
        act = _ROUTES[step]
        return {
            "farmer": act.get("farmer", ["PASS"]),
            "hands": act.get("hands", []),
            "market": act.get("market", []),
        }
    return main_agent(obs, state=state)


def explosion_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
    board: Board | None = None,
) -> dict[str, Any]:
    """Final 8-turn liquidation agent (turns 712-719)."""
    if state is None:
        state = GameState.from_obs(obs)
    if board is None:
        board = Board(state)
    return explosion(state, board)


def main_agent(
    obs: dict[str, Any],
    state: GameState | None = None,
    board: Board | None = None,
    eco: Economy | None = None,
    market: Market | None = None,
    scheduler: Scheduler | None = None,
) -> dict[str, Any]:
    """Dynamic mid-game agent managing crops, livestock, market, and scheduling."""
    if state is None:
        state = GameState.from_obs(obs)
    if board is None:
        board = Board(state)
    if eco is None:
        eco = Economy(state)
    if market is None:
        market = Market(state)
    if scheduler is None:
        scheduler = Scheduler(state)

    crop = eco.best_crop()
    market_orders = evaluate_market(state, board, eco, market, crop)

    if expansion_order := evaluate_expansion(state, eco):
        if len(market_orders) < 10:
            market_orders.append(expansion_order)

    livestock_act = evaluate_livestock(
        state, board, worker_idx=0, worker_pos=state.farmer
    )

    scheduler.populate(board, eco, crop)
    default_farmer_act, hands_acts = scheduler.assign()

    farmer_act = (
        livestock_act if livestock_act is not None else default_farmer_act
    )

    if len(board.needs_feed()) > 0 and len(state.hands) > 0:
        for h_idx, h_pos in enumerate(state.hands, start=1):
            hand_pos = (h_pos[0], h_pos[1])
            hand_livestock = evaluate_livestock(
                state, board, worker_idx=h_idx, worker_pos=hand_pos
            )
            if hand_livestock is not None:
                hands_acts[h_idx - 1] = hand_livestock
                break

    return {
        "farmer": farmer_act,
        "hands": hands_acts,
        "market": market_orders,
    }


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    """Agent wrapper routing turns to specialized phase agents."""
    state = GameState.from_obs(obs)
    step = state.step

    # Opening phase (turns 0-23)
    if step < 24:
        return opening_agent(obs, state=state)

    # Endgame liquidation (turns 712-719)
    if step >= 712:
        return explosion_agent(obs, state=state)

    # Scripted expansion phases (turns 169-192, 265-288)
    if step in _ROUTES:
        return expansion_agent(obs, state=state)

    # Dynamic mid-game operations
    return main_agent(obs, state=state)
