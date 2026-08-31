"""Jeremy V2 — Phased Action Path Agent."""

import base64
import json
import zlib
from pathlib import Path
from typing import Any

PASS = ["PASS"]
TRACE_FILE = Path(__file__).resolve().parent / "trace.json"
# MOVESETS: dict[str, list[dict[str, Any]]] = (
#     json.loads(TRACE_FILE.read_text(encoding="utf-8"))
#     if TRACE_FILE.is_file()
#     else {}
# )
MOVESETS = json.loads(
    zlib.decompress(
        base64.b85decode(
            "c-rk<U2|L4k^C=w#)Aluw6t%ugv6}SqKc$~%DPx8m96ZmHm1C?lS)-8|9vSE1TOCM^z_U*mlCyp13>`ye4m+~o}Pd0efZ_w_517p+WU_m{<Zhlw;z9g_wnZC-mBw_i@mGa-haQn{^{47H*Q}3{PyGjy!-9u^$&aBot!Uk{!3qc`}!|$j$fX9e|)+(+k1Yt+MDg0w=ce1E?@1<4(|VPv0T2md3*KU^7wLZb~t+b`{n7`%fZ{P&d*-FettRp!qvZLJH0r0{-@Wk2G8I0=ZC%3^5XKgp_>=$J`cXOY2UE>-ZR#X*nP^&v-8XEZhv(9%06fPRr;KDGu7Yz_Vvl>i#IoaUcUY`A>@ZgpVV7_di;F386-MH>rZ}~g`MBO`Nzx4&CEK_`NMEgu*d9vaA&TMFPG=u?>|2d2I%escwFv#aR1Q3@2)?@#$~k0(9dm~UYJ_@fbGwLWv@@D{oT#4`2!+Pr2YAev)AhZ2jdY=pg+#rg=dGOGJk{C`QxC^pWXA@Q_GHnK7Y&O@$V`FBF`UawlXf^Jc4H5e-{kLT`N+}+<bSt-o|g$nrDZ%%Wh`fZ`sY8A6a*)&n8wzqq3LTAl$y#{kfaJ{`%qL&u@Qw|KYk|^@Nv0xbB{xot`eAU%vUn^8E7T^yEKp8*Oiw)XFVfVyGG92k!5@R71g2!-fW<lWg|=PVPBD@loL3V1<?a`&WMd$`|yN-81oGdHTtb8|;)j{|x(s#$!9WN_kTon<PGYd}qLVU9;LzX1t@_p@ALVze=7pqkgp94%;iT(ok^z!?r6e^zRbf#`x=Im}2X1Z7p;jCNTJTlqwAzTmPv=Fz}%YkG2C`Xu@`YO$+4l1=HpXaM(cRXBLi9Gem{o*o=_<t~x^CNAUoaZ;Ssg->qJCJ9pkLrnx_Q`{MHac=he_{QNI_vqkYT9KGm%DfYS^KhH(kdS%`_tAm+p?TO@y%>Zm!zEbsj!#2(yYj{MO-Kz2R+jLI=zmHzTJvv}O(Ci3-NkqtJ>`N*Z(sp^2es9|_7Y*-ZW_qTFW`tOKVT2GiUA6>69K%t?Mvfr3maFggAL;WWZFWJE$4kz{aq#r_yT6ya+}8M{M_6pL@t=z>n&U`+TD`~Te=b~LU@*xwQ3f3nCJy*f5LT-=$zvB=YK{#Xk>&h3CP8<(H?5O8zWp@zz-=r%>bc;PXLbj1&o{TSG9kK0ZiA!pEJ=Z}N}s>}tNZ@s{^r&guDSUR)k*jM58B8}bx&!0{m(PTK?CG~Y=qbai`~=MQffCiKDUK{9LxtW7YJ3%w;SS9+oOl|9c6zds-qnr!X6tS8fUc+)>hcwmzyi;?nT=s8vkq$SjRy{9suc1xZ*4((Bg`#C|b+4$huh{Qw1)0;2&uU(-<1k1I<8e{dUC_UYwu3+N)p*_eRm#*(sw`uNTmQS__LW%~}|GC=X#MF#jXZPuv`(T~L+$g_wv(FieO69lZt~xT4(=kroyT3U<`(0zIVk07Jj3j61Vz62^%A8N3j}AF{`%SqH@6f~WW5-ut_`cV6tprkw>F(1VB<I?sEdbC;?$=l<zDcYr8kS94f5zr0z7^jX@HCyozHO~95#g6d5&W^Vs+cRTMN?lRuV@*dsm`<eKFfn8c$4FKZE5%yd1_Pc-n^7i`I_aCm`?5F74-i}m~*;3%oyoj*eetChHt`?(_qeBaF1nfU?&wzv8K_&H7FGOhjO8U@*m!xmX&1CXPs)h49>IAaq!jEQbMaAlmxE0$^+6$nvh{h*A?i;~P`q*{BD%!m#(7_Qcr49hHVlqcpV`4p(0(_fcfD>d!t;eX?s2KuXH;=S|uklPZc`;x;-}mvw$sh4zc1I|eZ(|l|xEPG#%PpJogh<;rh}DhS-sGzQrw}YjuqQeYuj~;xvhtKZTe5&gI@A)bW_SyctK0@u!&zYfFwKYecXu{5d1trS&Op3!u#d-AVH-}3x@AmvVeD&hc0+ocvAA}(2se1xR1xf8Qnkn4{PoMn4?q3=$KT%n<K3HIe|-D5cdfqBFc`k|TY7p)Gwhl43{P|a$sicSp61ddMF_<=d?oi}YZKcsYRS%Z9ydJGHv`+?fK)Pl%idgLHX3%%tWh-y93LXk)Jj3NS8Y)c?+(oYq()7=IIJmenq@qqil7BG<z4%=Q`}*DJ2|6}N%d3MuOI~O`p3Cv1+(ZR8SE@+g@Ffbf8bkepJvA14d2I$heb9*<8Ct<EH^drK(vL!b2eN=!0Gc(1L)Ma!bi1}$|q8~@W*C2l=W0SoxtcLdPxt`=lF)61>D*eyP3)RFf6FSfW~3H&PKYgRn+%EaR<6_UB5p${nIDi1<Z84!~RF{x8^8GlSMyw3?6RLGj|{|?kfOiWG~lZ8v=bmvW9c!ad*-I4RJJaS{7Ne5#0LWMc9E2Q(%=uK3{xbSI8%$WlIk4IuM&Ds|dzC8<$=_2Q?YD3%ame8nR=-(g^(n7gWxf(1b+p*c}OEl!*vhWSTG9{Mt~W2OxB#EL4f4A>Tx3DWX$0bQJ5`23Y^xJq{M7A$}!Aa%|KJ1SrHnZ2{4}hvA7gIb5xEVK`_d4u6`tL;bR^;A)?MhfkhAQq7qt%?#>cPV}HS0MYA7BSzVg`phw*?C7eLdN+6~2sUillAT?U)CgsKGU!%4>%=qL6+(YTf)L+yaJs;$sXJXZLy<9bsPP+6+Sa4df~QB|5I4k02Yt?aYa)XymLvIpU}{CTqe#-L;bowi)^GHa?j3Wqu`kvJi}(@S#-|+2km<$(a^i3_`mEIW<Uur`IIhha3q2M*U~3S@+XrP*Sv%LsH3HP03e=riGjenxTyu=>j><Sp1hCV!UBz+Gaz_27lQ|lUiZr#?04JdVI}~)O&5Bt%<C&(y9Ui3x_04{JyO`FgIB;~FG_PfxU9vVCj<9XT2=dQ#emoNPBIlkna(Xn<rHoSOiWGlfbVhj)6eMS`d%ch+T=|MaA7Kh|#*@GLBYJuSeuM@PyWck(#D`G4j*mCPB<q)iIK5$_HfXk+B@hh*;zW)y3Usigem8@uscAWiGqw&GY}m~J)Z1b;MKR(&OHn3Z@_WCC(=;HesK5=08gKu%IUKs7O)X0kv~+oKSp{CYA!bZ~vze;PUxf3Mv0ilD7`9{@d-OmYh91eA4~Y^+GuxdjA(EdVYDdu$HOI6o!L^D?HNtD?)++%7ZTY3W__54Y2ZlF;FDe0TAqll3LqjtnTZk0?#8XR_4`)ImhEX7GUQ&h^wBuMSV>UIhoAK~tdDH3uv-N3lhurd%u!|zG8pI;_jCz@Jv#JC=<%^KVa_Eh5E-K7u<W~EMg|UXdnzR}=46S#YU;xN-6f&r=Zi3)NJM7vvbU<>EL-7Pg<>aMK+JV&--@Qq-B~J&diQp05;s8t_5FsjA-N2mihaVC|V3zho430ca<pJ6-4X6E!^+|VF^mD+XfAYw@R7YhjrGA|kpI!+5Er_`x*-7s8?#vhFxC}os&&h-Adcsey6y^J(FOehKbe1f{{z53pop0piLWq>J%h8aGM~w8g^nCHQ?1q2~Ok?)eR_dyE?pql<eAcMpn}6)?-Z1cOY@%${3IG=|X$*--!+Fdt*&jL&0<wu$#A&V4J$&7CyYghVF%1nz9`I!36cZ1GM~QIG)Z94Coe1O4=)C5s9%bb$f8~OK^{T|ol-e(afeuqN$WrFP<ITc|;?3Zoo`_PFIfWVE#=RnW-_b-9G*XK53TDUk=8|MC^+2TzR&u9-b`~=AK_u2pr8DQrd(1wmG_F+t$wC8602&97mEFYJMI3T@^9*jgc>cYN_2!5-39j?Vg^LID^7R#3LoIP*osu%Y`dm;%zq(epJvjimHHS|A|FgmSZBh0q1}}mnrl@z-E<fO@i>74=`p3_|j9~ef5gFG4j3kEJJN(@<yx64#3%Tucngz`|WXMX2RvAo|X&?hPtJjfeo^LN#S}H|7L(PDQ;F(xrwn1psNQn<^B}O<S!!JOR%R*woU0{&5gy3qiZ~KB}+2zY=%u_NJpfyF#d=7&`Wq~zV&JJ5ffR7mB!0bkgQjM_JY;VgbqF8@t%b(K4wddP*cP@-qe9=SYt@fg`FE)us^F?uuUA?qnq<0w90fGhxkI0jHNZ-nyr@C+D$7=K8++GDrfbRwAM{y{$t?Erl7@*9k?q6BijFZGqmSKENPp(iTr<m=}yP#LxA}%G3+(=PW$zU#RB%Ty3RV7f$t908^Hl7#Cj?EgYLC?#339x3p#kuW`A4+FQ>Rp|JOjRJ6rYgNk`Uy*)m8_-k`U+(|CHaUBjGU5C86V`-gTSY9g?TR~EYTDLaDXR-JjWg~goNo&RqhfjZ0Y=u?;)zp7lcL$G~pBDQ_ckw5FpzG_~EMp$jaK2x??~%PMSU)_!Jyr3W)?;h7pISsb{ZIv?JW17+Wli>6AIAp9}h!V$6v9{>*XTpMD*j?CGf1aolrJ$|ZJa*ilIIppi)3kWCz3F#>OzD`-HFpm$YTnI4^`cn7G*gq3tz#8jblYuf4!3f*p2TaJ{iv6a<!YC8vM*60l#E`VS$<Tn$Mg2It+$`r*WQx8SHT%94VUDaMm(?8lgaw0U#?VH8yWGM$RPnx6Tj0|&=h3o0ef@83>-YH95uA9IrP6>Q>l448GQOq?bphLsTrUOMo`F=FMC?bZQI~;%wcahh`V(jxfyLKo1G%}@RR=O2nvR)=N4yiMr<3*5)PSNp7UbNI|Bl1)<fKyR<Wrf@9;|ayilA9BW*|}B(g!V#M)-KiIGguXXhz~L?&vr+|ekZ|iZdkR?1paL?ak!%=nvW7!747>J|DC&XeGOz?=&CN<|AgZA@LPwK+QTiGRJu=|Q3WD*S)+b@CN`H~(g`kqOE0DiifbZBTCaF4wV@bWA$T4Nit1jLmJH0Y>S83lRg)<ZY7u0wskvVZ<|WwRQUV?et@!?VwlY91<(P@duw7OQy|~V=pYGKyL0Pt?tDA5sX#@rI+LkP58h;JQBf|C%g!gqG7mAW<>B5mmojm?n`fmJFsY!}7wuNh(E-RiBTvR9k6UC|*0L0l|;uxoF7qRG5o4jXb4T`leo>bG)W4+UuIs{~n0B<df-8dh?@q@2qcSPATMoM;0KsiWbRG=t&9AGxBa+i=JCrGj`O6;-oRn4hq_yzH}B<M$)FxEjP_ZC)V3@58g8iB;5$kRQt*1?0NL=*+}<y!Y0*3Wd^=(=_o^8Pf)sviP?2VXS1q${c9;Q%_q|E&A49QB*)8hkBT^dOR@R1hw4V*95x17u3!^)}_^k(`G_ts0VgQZII&SbUtFlz`3(n#qA$PO_~JuiijXm~oG~;I=FkK&Q?qi6b>cOT&LDaJ=fcDb;lQ&WYXG`t%A5swGno`Y(yzgXT1yo{$PgYpnSRg?1kbiC4jv$9EmgB%#iEZ(5&}u$F*Gq7?<_3lEZ##g!D*=s>(@wX3NFzOvixa|Q82=&?x=4uZ8w&XHugq%`1w3shh;Ma7GC8Tx7ho5=dm9((iGyMO-j_WIZNAFkibZ{AA#eM5(C{<MYB@wkNm+63U|pIZPPTw*?tgO-gd9n)gAL1eRPb=q2Z)>6zxJS}M>Nm4|kI+&vD9uQe6vA021U=oeGgwTBqT|S&IpbOpcC{iloo87kx-H5C=7orhj6AkzlQ_REC?m1EeVMw*e8sw9d(%SHhs=!}ONb{oD0ds9Q(cM=dm@Wf7Vvq#*Ws<y5s7rWQ;!3jUwI(;uO4*a_gRu>HcvUHb2IU@o)RXRwho}W9pOFdC59K(k)S)9}B+a{IiUjh7*Hem?#@03QdM^CI>e$)z?^&1;jxxEHzRbH)meYJaveA2J7G%r6`?nvcfybg&*5yuR<V%|J_~ZxI8~>_QRZn(8Q?B&s@$=<SCteIzlZ2~ytamEPbrq;z)iY~8;~Y$12Ef8PgO=ZX<EM8&-?a42j~}l8@$Ta%Sg8UkWip41aK)q5=})6ec^GMO9s&f7j&gDrG#kiGI!TLURO$wVSxPE~6L^WbB!I-%UrD6Fq`+Y&59lEa7We|0Y4A?!;#3rkgmflTQh9Om$51qm>lU<gI;3%QX#j%HE0t-tV^X6JNadX*Y0k)27W4_4W-Omz7u01VwX*EgC((>r?tH=pR(U8=yG8$RCCi1R^&=UPg;#*5aveR&1|(_s3F=2NZ{+?!h*=qo@c^?eJvbw|iYPV5?zZMBBFwQUQ3=P$g<O|hNIaL@s%~yFrqz&9X4^3R6lxhL0>#-Jj{y5$w$K<jHm^rE_%Fh9t~L*8CQ-!CqH0P_R!?<Kq*P^b?Z}6KyQ(|P4u$i{Fj6O{BBCyCh5Y$tfgYMLq%fw;@UeUkf!_uROD-FWzr((t3JxoPj(xn6x+P{6-D0IXpw_`vNU+*JD5<>;e`0ZfF|rYcJ%5b3Ilc6D4h|m(VJnn&Az)DfG!wqnSpOxEZ*@Fi@(rm_Oqa42nHuU^HZCVqageP}Io7>=VpndDK1Gj&s@+DPoK#b1b78h;@23zAW@JdhtoRmQo}Rt@1h7|#Wr2w%(#l}GfONL2xDLUa;w=jGCYjnni8qm&H-hFvp;KQ(qbOVwD7aMkUI!DFh|TR>sqoO&qE^Hn?mo@tct1la5%tIjA&%mXlHXcEB89s+l*!W|JM%SgpcghC>l0WT83C`f0xuXtxZ4`K6tGPgVoaU+q~cOTbdV`T5jeD|T=-`Cb4!(jxRt4maws%`XA(5y7d;q<AmSVJXWSAFe|lK6mLul~0WC9NvLJJ4mnRP_YlYd#+@-NN?0OL^JV@EIu{U;uVxB#@6e!7<nVziZbg^Ufx|P-Enav%!O^Hg{q{2C#4$C4-XPD$<1JS%hbTfq=YHb9d&;+I<K41daV#Fd$orSC)3RX(&SH_X$^j@mDf8P;^rOj*gsW!H=!vF+@q~}k*diEb0-rgyt+e}qO`MOVrY4FT>QA`M$NwCG7sRu7154zpgh-1CQg`;#?mTJfBp(X}mL?n@zRMg=R(oV;>`)q0gB4`}Rv@MF&ItIcdN*?&O3o~p*7E2N=%$<V!jivD-sEOw5W)s&NlUbR892onz!*_D};?2!nb@`gqf~%x?*URk%P8(5(8bATJk=9Q)%#i2>__52WSd>(EHj!@}hNoyzw`qziD^Rj5`m<yO*CN(zL+M^%as$@1J@^<Q%er*C3$1NR{NuoGV_CkQN@;;b3>=IS578b6<6X-X03!JeP4y|3e$NX!2giaaUdgFrA(vcHAc$kBRHHqt;TG0P^kGT@3LGUAv`H-<NYNnBXbh$Sn4qO7g$)35Xpm;5-ycF2K)C%+iZK<MMB9M?h%w}C?Z8m}9C-4~B$*JU2I_7;qo4T2=jp}o7Ne`N)>sQ!-8&BaNg1I7{0FK$>z&xf@<@I<A^a%`ydgvGsGVc?#K})RH0jDu5wbahWBX`p-Az}AJytwB5b!7}irhm_TN5Y?Z%m~)d#^;cw3r!fWtY<2E!E(B{3QyswAB}%3ouJ2LoI+@RH{X%67-pbPay&y7&x?QQDynlTbVE8pwJxn_Y^B$soPj&s;*Kh`UwYuu4<yWq*eKulsc-*cqPEXWvFhHlknEu02E)B@yiZX+gU?+Ohc$HUDSeCvNuB<H%y3}4rcUeV^jly23m}}*l?POG>VXx&2Mf7PxYCHtmgSj71`#)kvSJ=W^Ys>k(~`@Jp`6Sf|7_YS8|adK^a1NPMi{;nS47_3v=VtGFBz69)}1JPZFM$@BdjRId`K;C8x%iPaoO**1}%q1#f1+J|gWa3$|yQSR2V0%~;5)?)wV|&iEP?xF*Fn7Ggr5gm)~sGM5658x8n4KcRDm4^5(DQXu3V-@t6tSf5sKOJytRPEjxJ3u;+TeoN++vcOkoB`(;jf)tl1^S={MYi1`Xuw-%}=9Rkg^Q#1xWy)6z5-L@D3j)*%aV<&;X+}dKs{%Hcksl~bkg&03)FqWu+d;xhl9CH}Rm~{}3bM*3hvIEX<q?wbEgik>n-PqAMI0<3^rA#3Sr$y*juHu_q#B0ZW|lR|w5|$O<ikJ)Jb@6_VGp3Bo?At!9^g~Uc%by<M-CQU8*(&v>D|V(;H8oE0)sUv$B^<tMH2E=<w(*f%_>vs+?eZ=pE9F0UMr!%)x^LaLs=M^R6^zK2zOd>5z<I>-g=0{S2-L@i$Ru_9XMNz+>~8D%nuJiOV>e6m#$wCg|CS2>#@1=G|u}$q10#xIZJmLFp>bfO%rGnN@xbGtwxcy&BzgfHRVMh_U0+NB{*+!70P*#8)#C?9*NFbOY>_O<$f12vqgr31;1R#{bNZBk)<4q*-A9@RO?dd9q9s-N-g!OQI$$fs#CH!pixRwlq*9Pib=+`VZ8b6o@hWJgA^Bw6B!fem0kZh{44vk_-gb&n6plW&B@sYnz~00V2qO@<BsJr&TQfnt6feUyB=<9=y(GS!{{riB53{aXqc1A9Mep>b_t1K+RMdy?Sagol!Xqoy}0kP!>#8^x4ULkYDU=jp~Zx!0}2QDgvYK>59jAbeF#onCF=<eFpu+T`i&NRfk&+*t{JQuP4C3QieP;M4K|#Y=DW&qg_uCc#i)FgPcC<}3P%^$h;?DN8m>!mF&cu;YV{_^jlPOq5&~D+O+$H3iV;CdIWqRf{Z8ev$Rf^-rC)4A*-|A+N**1~50#O0){(;dtZ7HCgkFQBItEiA<Vv}PU3K|+Gbat|KRtDZ?i*Aj^y?Fb%ELPcMGD$}9`0G_1)B<BPj^0<m=IKGYKlD;<(G@uN~?UXSNCd+M75>N3-ehi>HC6_`d5-tu7r`mD=s5^Kd;ccGT9Y+GNPcFq3hZAA&OXu6~?$LQ?+{VK$s61=|*X34$BM0w|{wdD_~wEXXS$COfN^2G-*palL}n1G!5kEb4<wD+;G@aR48;9g^(EQ5nEMs@8Z6w8zFHxfkv0hjO74ey&fG)oE4Pr7$7E$y1xfx#-c=a5bdYdOiZ<gKx8M;fo~P)5e4xjiZMlI<3cN?qupncu=07@%FVE3pbVJKOmd{fb$dotM-CYa(SnJ2aHP%+p_+iVJPl}Jp;+IRl;e}=F07&BPl;mS6vVIf0Aw;M)eFaLpp=Repb|+9D{yprGHs4Ltja2J9|FAQ=xfak%%~3c)j=v06r{*E(Xn17$+#uYl{_{iH`2tp3TY>oHYA<v#$j!5^mKAc#Foib2aM!AdFYdY<I@N*>8_TjUv8$|#wfoiJtoyVU<6+Gf5PmRq?~LdIKhmj#nVz&ZC1mHmiP%v8m{|1N?e+SIvX^vM41z!`2@THrL1VoQVB!<VrS+ZB%#6xcLrJYgQd)qH43iU%rTw_KB<|1PR$9;y;Zmwv_~n+!mgT_ipT>LzK(Vg4{57%Iyw@Vslha)8!q7nDXZ18c6MmV7G_M;D=ATShY``673DZO<fhqKNBnLq^IMH7P0>?<l(1q3g-s3J@JPTA<wTwWxRFFQ01N<AdTjkJjRh{<z&6VaZfs^3!8{&X7eK5H94C;O`P{UHcv-vZ<w2?u%T3A;w}LLQnh^w&aKzc|NAi{p8+b6Rp=Y4cg~Gn}7=8&vE2g#iz3YjmE#?L{J4z^RJ??6EQ)H+uw2}{tIPr{sHxW%*C5lhUNjQ`T)KYLRA@f92T)0kEP&~ME6(*P|FY3lbSb~sE7h8;$uuM5cC`C@mx9g;v1?(s()Tu=2fblP<tL02TxoB@)1d2IS88(`=aD-$fod{J?Ga!Q^RJx8<hqYppb8EK+)v3b+6RHyBhD@ipByvi_k7h)Ki6EZLztI?9%Df_!iWMi5(xQdp&V{Mv7&%o4<mKv1QZbClEF2tCCRXbXUB$IAW4p+@SVA5$QD&h!*fuc{c*%6PRap($EZ(hQj`9sDH;`65sgvd?Bo&-7C?k}NtzY}A%pqYFseH%+^l#ZLg;MrwS;_jAR+Ob;G<oseM&11NxA*`1_xC@&{q6mS>zlXIzV~_~9PT@-;TbO1^+@DmntkoaqrwTyF&AZCN)XahY%22oik?ML?7B5`Mq`rX^oCo_zV>LRl;_(su8wUzEp5j&V|xhP0^_HaB2_HclN3eFO*j`Q%z#vYxQz1uS#1q!3u^{N(tKbs8A$<yb%K+I5@AR^is(xm2T|16T8zB1gm25s=Lkojoi%zE=)QcRh<V8mR#2B^O4Yhpg^cE^CP;Kz>Um>%G|D@T1g0v(6iLJ=vTb1j%L1~(Hg~xDm@Ai&$OG3BDQmvvR+0<^hKQ2m{?Iw@4-zq9A!WdGj!OPG4fHD2l~HBsQZcfWkCV%UXiB>1)(V!p5`=b`TY9uF=vfTxk&bSulnu|~kh}nb*b1oOqUkX(B3sR=WI?&e1jqcku+(aEYXWed(zEoDfzzbuBPH}5GAAFaGpWaKJ;Z>jhG$19mb#3$R+tl0h2odFWPOFm-0X$c=Sq&!r<4G>o`+iKHz#CEq!yXktxn#uOR%ZAgmP{kixEV4NQd4WnMo4AYrwMD-q%4T<|bB3HY9Q%s*~+Tlp6*UHM>$xNM0`$$dxxzA8(<~Hfh(|m5L!u=k1LvW?wL_Kv2MNx3<AkC3drpJ7hA%tsBWaBm1?nv?sIl=La(HvmtP)^aykfsS507`%?kQLs!qRZzv3`tW;HnZF?sQ(S^g`)~r!%^xyvnNJH6|"
        )
    ).decode("utf-8")
)

PHASE_SCHEDULE: tuple[tuple[int, int, str], ...] = (
    (0, 24, "opening"),
    (24, 168, "formation"),
    (168, 192, "expansion_1"),
    (192, 432, "productive_scale"),
    (432, 456, "expansion_2"),
    (456, 672, "demand_conversion"),
    (672, 720, "liquidation"),
)

ACTIONS: tuple[dict[str, Any], ...] = tuple(
    MOVESETS.get(name, [])[step - start]
    for start, end, name in PHASE_SCHEDULE
    for step in range(start, end)
)


def select_phase(step: int) -> tuple[str, int]:
    for start, end, name in PHASE_SCHEDULE:
        if step < end:
            return name, step - start
    return "liquidation", min(47, max(0, step - 672))


def get_path_action(path_name: str, local_index: int) -> dict[str, Any]:
    actions = MOVESETS.get(path_name) or []
    act = (
        actions[local_index]
        if 0 <= local_index < len(actions)
        else {"farmer": PASS, "hands": [], "market": []}
    )
    return {
        "farmer": list(act.get("farmer") or PASS),
        "hands": [list(c) for c in act.get("hands") or []],
        "market": [list(o) for o in act.get("market") or []],
    }


def agent(obs: dict[str, Any]) -> dict[str, Any]:
    farm = (obs.get("farms") or [{}])[obs.get("player", 0)]
    n_hands = len(farm.get("hands") or ())
    try:
        path_name, local_index = select_phase(obs.get("step", 0))
        act = get_path_action(path_name, local_index)
        hands = [list(c) for c in act.get("hands") or []]
        if len(hands) < n_hands:
            hands.extend([PASS] * (n_hands - len(hands)))
        return {
            "farmer": list(act.get("farmer") or PASS),
            "hands": hands[:n_hands],
            "market": [list(o) for o in act.get("market") or []],
        }
    except Exception:
        return {"farmer": PASS, "hands": [PASS] * n_hands, "market": []}
