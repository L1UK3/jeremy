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

_ROUTES = json.loads(
    zlib.decompress(
        base64.b85decode(
            "dm=C*Iv{%@W?^z|WpW}qAX_3(K~qyAT`V9XXkl(-b0Rt*TU{(5B5h%EYh`pIIv`tHB1lP6MIv1+AX_3xNm4~3T`VA5B1lP6MIv1+AX_3xNm4~3T`VA5B1lP6MIv1+AX_3rRasv_PDxEcOd>2GB2!33MNlFvATnJnAX_3rRasv_PDxEcOd>2GB12DCA}k;>T`VA5B0^PJUsFXzL?SF8B3DR7K~y3vAU9nsAX_3rRaswCMMXp+EFdCHMNCglA}k;_T`VA5B0^PJUr<s{L{&pnA}k;xS4c%cR3a=OI9*+REFdB=B03;@B4%N7ZDn#IIv`sjP)S2eRZt=<AR<FgS0XGRGF>bnB4}Z5WOE`qAX{4^S4C4)B3&#XTOv+RQdCGHT`VA5B2Yn7QzBg~AX_3(NkdCjP$DcKB2!33MNlFvATnJnAX_3=MN?EFU0p07B5h%EYh`pIIv`tHB0^PJUr<s{L{&pnA}k;xS4c%cR3a=OGF@GLEFdB>B03;@B4%N7ZDn#IIv`sjLRCpjL|;%rQ&d$_MIv1+AR=gCZe(*JIv`tHB2G_IR7fISEFfDVPES%)NFrS<AX_3(K~qyAT`VA5B2Y;~OI1)JEFdCRNJT+ZA}k;>T`VA5B2G_IR7fIST`V9XZDDe2WppAsAX{C1EFdB?B03;@B4%N7ZDn#IIv`sjP)tEXMItO9B12DCB3&#XB4}Z5WOE`qAX{4^PES%)NFrS<AX_3%Pf}D!B3&#XTOv?FQ&S>cEFfDVPES%)NFrS<AX_3%Pf}D!B3)f9AR=vHa%*LDB03;jU41MdA~Yg8AbTQaVRCI{aw0k)TOwCQQ&b{dEFdCiVQyq|B03;jTOvYLNlZjvP(f2vRZ>MFT`VA5B2G_IR7fISEFfDVP(f2uB3&#XTOvYLNlZjvP(f2vRZ>MFT`VA5B2G_IR7fIST`V9XZDDe2WppAsAX{C1EFdB^B03;@B4%N7ZDn#IIv`sjLRCpjL|;%rQ&d$_MIv1+AR=gCZe(*JIv`tHB3DIIR3cq0AX_3(OhHamA}k;xS4c%cR3cq0AX_3(K~qyAT`VA5B2Y|0Lq#GiAR<#pMMY2|T`VA5B2G_IR7fIST`V9XZDDe2WppAsAX{C1EFdB_B03;@B4%N7ZDn#IIv`sjP)tEXMItO9B12DCB3&#XB4}Z5WOE`qAX{4^P)tEiR3a=OB27h1Pfj9TEFfDVS3y)oQX*X}AX_3(K~qyAT`VA5B1T0;L?T@*AX_3(OhHamA}k;xO+`#kP9j}hEFdCnVRCC_bRs$+TU~uDAR;#+Iv{%@W?^z|WpW}qAX_3=MN?EFT`V9XXkl(-b0Rt*TU#PmK~zOjB3&#XTOwCQQ&b{dEFfDVP(f2uB3&#XTOvb2Qbi(NEFfDVS3y)oQX*YlEFdCnVRCC_bRs$+TU~uDAR;&-Iv{%@W?^z|WpW}qAX_3(OhHamA}k;xS4c%cR3cq0AR=gCZe(*JIv`tHB3DIIR3cq0AX_3(OhHamA}k;xO+`#kP9j|_AX_3(K~qyAT`VA5B3DIIR3cq0AX_3=MN?EFU0p07B5h%EYh`pIIv`tJeJmg%IU+hBdm?6Ga&2XDB03;jB3D6FMN%SNEFdCiVQyq|B03;jTOv?QK~7X6EFdCRNJT+ZB3&#XTOwCMR7FxET`VA5B2Yn7QzBg~AX_3rRY^=lUr<3)R8>+%B3&#XTOv?QK~7X6EFdCRNJT+ZB3)f9AR=vHa%*LDB03;jU41MdA~7%`Iv{%@W?^z|WpW}qAX_3(OhHamA}k;xS4c%cR3cq0AR=gCZe(*JIv`tHB3D6FMN%SNEFfDVS4C4)B3&#XTOv?FQ&S>cEFfDVP)tEXMItO9B2!33MNlGLEFfDVS3y)oQX*YlEFdCnVRCC_bRs$+TU~uDAR;j_B03;@B4%N7ZDn#IIv`sjS3y)oQX*X}AR=gCZe(*JIv`tHB3DIIR3cq0AX_3(OhHamA}k;xO+`#kP9j|_AX_3(K~qyAT`VA5B1T0;L?T@*AX_3=MN?EFU0p07B5h%EYh`pIIv`tJeJmg%F)|`LAbTQaVRCI{aw0k)TOwCQQ&b{dEFdCiVQyq|B03;jTOv?QK~7X6EFdCHMNCglB3&#XTOwCMR7FxET`VA5B2Yn7QzBg~AX_3sK~hB`T`VA5B2Y|0PE;Z+AR<jgOixZCU0p07B5h%EYh`pIIv`tJeJmg%F*71MAbTQaVRCI{aw0k)TOv?QK~7X6EFdCHMNCglB3&#XB4}Z5WOE`qAX{4^S3y)oQX*X}AX_3=MN?EFT`VA5B2Yn7QzBg~AX_3=MN?EFT`VA5B3D6FMN%SNT`V9XZDDe2WppAsAX{C1EFdB=G$J}6dm?6Ga&2XDB03;jB3D6FMN%SNEFdCiVQyq|B03;jTOwCQQ&b{dEFfDVP)tEiR3a=OB3DR7K~y4LEFfDVP(f2uB3&#XTOv?QK~7X6EFdCHMNCglB3&#XTOwCQQ&b{dT`V9XZDDe2WppAsAX{C1EFdB=H6l77dm?6Ga&2XDB03;jB2Yn7QzBg~AR=gCZe(*JIv`tHB2Y|0PE;Z+AR<jgOixZCT`VA5B3D6FMN%SNEFfDVP(f2uB3&#XTOwCMR7FxET`VA5B2Y|0PE;Z+AR<jgOixZCU0p07B5h%EYh`pIIv`tJeJmg%F*YJPAbTQaVRCI{aw0k)TOv?FQ&S>cEFdCiVQyq|B03;jTOwCMR7FxET`VA5B3DIIR3cq0AX_3(K~qyAT`VA5B3DIIR3cq0AX_3=K~zOjB3)f9AR=vHa%*LDB03;jU41MdA~822Iv{%@W?^z|WpW}qAX_3(K~qyAT`V9XXkl(-b0Rt*TU#PfK~qyAT`VA5B2Y|0PE;Z+AR<jgOixZCT`VA5B2Yn7QzBg~AX_3(OhHamA}k;xS4c%cR3cq0AX_3=MN?EFU0p07B5h%EYh`pIIv`tJeJmg%F*qVRAbTQaVRCI{aw0k)TOv?FQ&S>cEFdCiVQyq|B03;jTOv?FQ&S>cEFfDVS3y)oQX*X}AX_3(K~qyAT`VA5B3D6FMN%SNEFfDVP)tEiR3a=OB3DR7K~y4LT`V9XZDDe2WppAsAX{C1EFdB=IU+hBdm?6Ga&2XDB03;jB2Yn7QzBg~AR=gCZe(*JIv`tHB2Yn7QzBg~AX_3(K~qyAT`VA5B2Yn7QzBg~AX_3=MN?EFT`VA5B3D6FMN%SNT`V9XZDDe2WppAsAX{C1EFdB>Fd{l2dm?6Ga&2XDB03;jB2Yn7QzBg~AR=gCZe(*JIv`tHB2Yn7QzBg~AX_3(K~qyAT`VA5B2Yn7QzBg~AX_3(OhHamA}k;xO+`#kP9j|_AX_3(K~qyAU0p07B5h%EYh`pIIv`tJeJmg%GBF}LAbTQaVRCI{aw0k)TOv?FQ&S>cEFdCiVQyq|B03;jTOv?FQ&S>cEFfDVP(f2uB3&#XTOv?FQ&S>cEFfDVS3y)oQX*X}AX_3(K~qyAU0p07B5h%EYh`pIIv`tJeJmg%GBP4MAbTQaVRCI{aw0k)TOv?FQ&S>cEFdCiVQyq|B03;jTOv?FQ&S>cEFfDVP(f2uB3&#XTOv?FQ&S>cEFfDVP(f2uB3&#XTOv?FQ&S>cT`V9XZDDe2WppAsAX{C1EFdB>Ga@=5dm?6Ga&2XDB03;jB2Yn7QzBg~AR=gCZe(*JIv`tHB2Yn7QzBg~AX_3(K~qyAT`VA5B2Yn7QzBg~AX_3(K~qyAT`VA5B2Yn7QzBhmEFdCnVRCC_bRs$+TU~uDAR;j~IU+hBdm?6Ga&2XDB03;jB2Y;~OI1)JEFdCRNJT+ZA}k;^T`V9XXkl(-b0Rt*TU{(5B5h%EYh`pIIv`tHB2z_7Od>2GB3DmOOd>2GF*02&AX_3+MNCX0EFdCAMN(8rOi5ZrQX(uMHeD<rTOw0MOiUsyAR<>tML|>|EFdvmEFfDVNJ&yfB3&#XTOvqFQbi(NEFfDVNJ&yfB3&#XTOvqFQbi(NEFfDVLRDE`OhHaWB3&#XTOvYLSzkd;NligaA}k;xQ%FTcP$DcKGF>bnTOvYLSzkd;NligaA}k;xLr+&CEFdynU41MdA~82GB03;@B4%N7ZDn#IIv`sjMny$LB3&#XB4}Z5WOE`qAX{4^P)S2eRZt=<AR<FgS0XGRGF>bnTOv+RQdCGHT`VA5B2G_IR7fISEFfDVS4C4)B3)f9AR=vHa%*LDB03;jTOvqFQbi(NEFfDVNJ&yfB3&#XTOvYLSzl06PefHiR3a=OB3DR7K~y3vAURzuAX_3rRaswCMMXp+EFdCNR8m1#LPb(iSt2YTI9*+REFdB=H!&hQAbTQaVRCI{aw0k)TOvb2Qbi(NEFdCiVQyq|B03;jTOvYLNlZjvP(f2vRZ>MFT`VA5B2G_IR7fISEFfDVP)S2eRZt=<AR<>tML|>|EFdynEFfDVS4C4)B3&#XTOv+RQdCGHT`VA5B2G_IR7fIST`V9XZDDe2WppAsAX{4^LRDE`P*P7sRYO!FEFdCRNJT+ZA}k;=U0r=FAR;k0G9o%4dm?6Ga&2XDB03;jB3DIIR3cq0AR=gCZe(*JIv`tHB2Y|0Lq#GiAR<FgS0Y_3AX_3=MN?EFT`VA5B2Y;~OI1)JEFdCNNJT|ZA}k;>T`VA5B3DIIR3cq0AX_3%Pf}D!B3&#XTOv+RQdCGHU0p07B5h%EYh`pIIv`tJeJmg%F*h?JIv{%@W?^z|WpW}qAX_3vMMXp+T`V9XXkl(-b0Rt*TU#PUK~q#BT`VA5B3DIIR3cq0AX_3%Pf}D!B3&#XTOwCMR7FxET`VA5B2G_IR7fISEFfDVPES%)NFrTbEFdCnVRCC_bRs$+TU~uDAR;k0G$J}6dm?6Ga&2XDB03;jB11t^MIv1+AR=gCZe(*JIv`tHB0^P3OhjK$K~q#!Qbi(NEFfDVS3y)oQX*X}AX_3rRY^=lUr<3)R8>+%B3&#XTOwCQQ&b{dEFfDVLqSqSB3&#XTOvYLNlZjvP(f2vRZ>MFU0p07B5h%EYh`pIIv`tHB0^PJUr<s{L{&pnA}k;xS4c%cR3a=OF<o7KEFdB=H#H(UAbTQaVRCI{aw0k)TOwCQQ&b{dEFdCiVQyq|B03;jTOv?QK|@6%EFdC7Pgf#cEFfDVS4C4)B3&#XTOv?QK|@6%EFdCNNJT|ZB3&#XTOwCMR7FxET`VA5B12D1OhrRfUq(ezR7p%pT18SKT`VA5B1J({R3cqnEFdCnVRCC_bRs$+TU~uDAR;k0HX=G8dm?6Ga&2XDB03;jB1T0;L?T@*AR=gCZe(*JIv`tHB1J({R3cq0AX_3=K~zOjB3&#XTOvk9MMNT9EFfDVPES%)NFrS<AX_3=MN?EFT`VA5B2Y|0PE;Z+AR<##QbAWjMN(2(B3)f9AR=vHa%*LDB03;jU41MdA~82NB03;@B4%N7ZDn#IIv`sjLqSqSB3&#XB4}Z5WOE`qAX{4^LRCpjL|;%rQ&d$_MIv1+AX_3%Pf}D!B3&#XTOvb2Qbi(NEFfDVS3y)oQX*X}AX_3=K~zOjB3&#XTOwCMR7FxEU0p07B5h%EYh`pIIv`tHB2z_7Od>2GB3DR7K~y3vATnJnAX_3rRasw9QcpxxLsTLxAR<>tML|>|EFdynU41MdA~82OB03;@B4%N7ZDn#IIv`sjPES%)NFrS<AR=gCZe(*JIv`tHB1J({R3cq0AX_3=K~zOjB3&#XTOvh4Q&b{dEFfDVPES%)NFrS<AX_3=MN?EFT`VA5B1J({R3cqnEFdCnVRCC_bRs$+TU#PiMNCX0EFdCRNJT+ZA}k;>T`VA5B0^PJUr<s{L{&pnA}k;xS4c%cR3a=OGF@GLEFdB=H#s6YAbTQaVRCI{aw0k)TOvh4Q&b{dEFdCiVQyq|B03;jTOv?QK~7X6EFdCNR8m1#LPb(iSt4C5AX_3%Pf}D!B3&#XTOvYLNlZjvP(f2vRZ>MFT`VA5B3D6FMN%SNEFfDVS3y)oQX*X}AX_3uK~q#BU0p07B5h%EYh`pIIv`tHB2z_7Od>2GB3DR7K~y3vATnJnAX_3rRasw9QcpxxLsTLxAR<>tML|>|EFdynU41MdA~85HB03;@B4%N7ZDn#IIv`sjMny$LB3&#XB4}Z5WOE`qAX{4^S3y)oQX*X}AX_3=K~zOjB3&#XTOv?QK|@6%EFdCNNJT|ZB3&#XTOv+RQdCGHT`VA5B2G_IR7fISEFfDVP)tEiR3a=OB2!dSL03XWQc_tWU0p07B5h%EYh`pIIv`tHB2z_7Od>2GB3DR7K~y3vATnJnAX_3rRasw9QcpxxLsTLxAR<>tML|>|EFdynU41MdA~85IB03;@B4%N7ZDn#IIv`sjLqSqSB3&#XB4}Z5WOE`qAX{4^ML|<kB3&#XTOvh4Q&b{dEFfDVMny$LB3&#XTOwCMR7FxET`VA5B1J({R3cq0AX_3=K~zOjB3)f9AR=vHa%*LDB03;jTOw0MOiUsyAR<>tML|>|EFd#oEFfDVLRDE`P*P7sRYO!FEFdCRNJT+ZA}k;?U0r=FAR;k1G9o%4dm?6Ga&2XDB03;jB1J({R3cq0AR=gCZe(*JIv`tHB2Y|0PE;Z+AR<##QbAWjMN(2(B3&#XTOwCMR7FxET`VA5B11t^MIv1+AX_3%Pf}D!B3&#XTOwCMR7FxET`VA5B2!OQR7fIST`V9XZDDe2WppAsAX{4^Q$<WnA}k;xS4c%cR3a=OG+itpTOvYLSzl06PefHiR3a=OB3DR7K~y3vAT(WFeJmg%F*q|KIv{%@W?^z|WpW}qAX_3vMMXp+T`V9XXkl(-b0Rt*TU#PmK~zOjB3&#XTOvh4Q&b{dEFfDVML|<kB3&#XTOwCMR7FxET`VA5B2G_IR7fISEFfDVP)tEiR3a=OB2!dSL03XWQc_tWU0p07B5h%EYh`pIIv`tHB2z_7Od>2GB3DR7K~y3vAT(VpAX_3rRasw9QcpxxLsTLxAR<>tML|>|EFd&pU41MdA~85LB03;@B4%N7ZDn#IIv`sjLqSqSB3&#XB4}Z5WOE`qAX{4^PES%)NFrS<AX_3uK~q#BT`VA5B2Y|0PE;Z+AR<##QbAWjMN(2(B3&#XTOvh4Q&b{dEFfDVS3y)oQX*X}AX_3=K~zOjB3)f9AR=vHa%*LDB03;jTOw0MOiUsyAR<>tML|>|EFd*qEFfDVLRDE`P*P7sRYO!FEFdCRNJT+ZA}k;^U0r=FAR;k1H6l77dm?6Ga&2XDB03;jB12D1OhrRfUq(ezR7p%pT18SKT`V9XXkl(-b0Rt*TU#PfOhHamA}k;xQ&dtxS3*TnQduHhEFfDVS3y)oQX*X}AX_3=K~zOjB3&#XTOwCMR7FxET`VA5B2!OQR7fISEFfDVPES%)NFrTbEFdCnVRCC_bRs$+TU#PiMNCX0EFdCRNJT+ZA}k;^T`VA5B0^PJUr<s{L{&pnA}k;xS4c%cR3a=OHC<hOEFdB=I5r|WAbTQaVRCI{aw0k)TOw0WRa8hKT`V9XXkl(-b0Rt*TU#PmK~zOjB3&#XTOv+RQdCGHT`VA5B2G_IR7fISEFfDVML|<kB3&#XTOw0WRa8hKT`VA5B1J({R3cqnEFdCnVRCC_bRs$+TU#PiMNCX0EFdCRNJT+ZA}k;^T`VA5B0^PJUr<s{L{&pnA}k;xS4c%cR3a=OHC<hOEFdB=I5#3XAbTQaVRCI{aw0k)TOvbGOiV>XR9{9#QdCJyNm@lxB3&#XB4}Z5WOE`qAX{4^PES%)NFrS<AX_3=K~zOjB3&#XTOv?QK~7X6EFdCNR8m1#LPb(iSt4C5AX_3=K~zOjB3&#XTOw0WRa8hKT`VA5B2Yn7QzBhmEFdCnVRCC_bRs$+TU#PiMNCX0EFdCRNJT+ZA}k;^T`VA5B0^PJUr<s{L{&pnA}k;xS4c%cR3a=OHC<hOEFdB=I5;9YAbTQaVRCI{aw0k)TOwCQQ&b{dEFdCiVQyq|B03;jTOv?FQ&S>cEFfDVQ%_Y?NFrS<AX_3=K~zOjB3&#XTOv?FQ&S>cEFfDVP(f2uB3&#XTOv?FQ&S>cT`V9XZDDe2WppAsAX{4^Q$<WnA}k;xS4c%cR3a=OHC-$qTOvYLSzl06PefHiR3a=OB3DR7K~y3vAT?cGeJmg%F*rFQIv{%@W?^z|WpW}qAX_3sPfScjLsVZzMN(8rOi5ZrQX*X}AR=gCZe(*JIv`tHB2Yn7QzBg~AX_3+PgPV%B3&#XTOv?FQ&S>cEFfDVP(f2uB3&#XTOv?FQ&S>cEFfDVP(f2uB3)f9AR=vHa%*LDB03;jTOw0MOiUsyAR<>tML|>|EFd*qU41MdA~88IB03;@B4%N7ZDn#IIv`sjS4C4)B3&#XB4}Z5WOE`qAX{4^P(f2uB3&#XTOw0WRa8hKT`VA5B2Yn7QzBg~AX_3(K~qyAT`VA5B2Yn7QzBg~AX_3(K~qyAU0p07B5h%EYh`pIIv`tJeJmg%F*z|JIv{%@W?^z|WpW}qAX_3sPfScjLsVZzMN(8rOi5ZrQX*X}AR=gCZe(*JIv`tHB2Yn7QzBg~AX_3=MN?EFT`VA5B2Yn7QzBg~AX_3(K~qyAT`VA5B2Yn7QzBg~AX_3(K~qyAU0p07B5h%EYh`pIIv`tJeJmg%F*!0KIv{%@W?^z|WpW}qAX_3%Pf}D!B3&#XB4}Z5WOE`qAX{4^P(f2uB3&#XTOvbGOiV>XR9{9#QdCJyNm@lxB3&#XTOv?FQ&S>cEFfDVP(f2uB3&#XTOv?FQ&S>cEFfDVP(f2uB3)f9AR=vHa%*LDB03;jU44B"
        )
    ).decode("utf-8")
)


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
