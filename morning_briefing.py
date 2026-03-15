import os
import json
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_USER_ID = os.getenv('TELEGRAM_USER_ID')
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS')

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Multiple calendar IDs
CALENDAR_IDS = [
          'styletech.jp@gmail.com',
]

# Add additional calendars from environment if configured
ADDITIONAL_CALENDARS = os.getenv('ADDITIONAL_CALENDAR_IDS', '')
if ADDITIONAL_CALENDARS:
          CALENDAR_IDS.extend([cal.strip() for cal in ADDITIONAL_CALENDARS.split(',')])

# Japanese holidays for 2024-2026
JAPANESE_HOLIDAYS = {
          '01-01': '元日',
          '01-09': '成人の日',
          '02-11': '建国記念の日',
          '02-12': '休日（建国記念の日のため）',
          '03-20': '春分の日',
          '04-29': '昭和の日',
          '05-03': '憲法記念日',
          '05-04': 'みどりの日',
          '05-05': 'こどもの日',
          '05-06': '振替休日',
          '07-15': '海の日',
          '08-11': '山の日',
          '09-16': '敬老の日',
          '09-22': '秋分の日',
          '09-23': '秋分の日（2024）',
          '10-14': 'スポーツの日',
          '11-03': '文化の日',
          '11-04': '振替休日',
          '11-23': '勤労感謝の日',
}

# Special dates/memorial days
SPECIAL_DATES = {
          '03-11': '東日本大震災の日',
          '06-04': '天皇誕生日（現上皇）',
          '09-01': '防災の日',
          '12-25': 'クリスマス',
}

def get_date_info():
          """Get date with holiday/memorial day infoirmmpaotrito no"s"
      "i
      m p o r tj sjts o=n 
      ZiomnpeoIrntf or(e'qAuseisat/sT
      ofkryoom' )d
      a t e t inmoew  i=m pdoartte tdiamtee.tniomwe(,j stti)m
      e d e l tdaa
      tfer_osmt rz o=n enionwf.os tirmfptoirmte (Z"o%nYe年I%nmf月%od
      日f"r)o
      m   g o odgalyes. o=a u[t"h月"2,  i"m火p"o,r t" 水"s,e r"v木i"c,e _"a金"c,c o"u土n"t,
       f"r日"o]m
         g o o gdlaeya_poifc_lwieeenkt .=d idsacyosv[enroyw .iwmepeokrdta yb(u)i]l
         d

          i m p odratt el_okgegyi n=g 
          n
          olwo.gsgtirnfgt.ibmaes(i"c%Cmo-n%fdi"g)(
          l
          e v e l =dlaotgeg_iinngf.oI N=F Of)"
      {ldoagtgee_rs t=r }l（o{gdgaiyn_go.fg_ewteLeokg}g曜日e）"r
      (
      _ _ n a mief_ _d)a
      t
      eT_EkLeEyG RiAnM _JBAOPTA_NTEOSKEE_NH O=L IoDsA.YgSe:t
      e n v ( ' T E L EhGoRlAiMd_aByO T=_ TJOAKPEANN'E)S
      ET_EHLOELGIRDAAMY_SU[SdEaRt_eI_Dk e=y ]o
      s . g e t e n v (d'aTtEeL_EiGnRfAoM _+U=S EfR"_\InD㊗'️祝)日：
      {GhOoOlGiLdEa_yC}R"E
      D E N T IeAlLiSf_ JdSaOtNe _=k eoys .igne tSePnEvC(I'AGLO_ODGALTEE_SC:R
      E D E N T I A L Ss'p)e
      c
      iSaClO P=E SS P=E C[I'AhLt_tDpAsT:E/S/[wdwawt.eg_okoegyl]e
      a p i s . c o m /daautteh_/icnafloe n+d=a rf."r\ena📅{dsopnelcyi'a]l
      }
      "#

       M u l t irpelteu rcna ldeantdea_ri nIfDos


       CdAeLfE NgDeAtR__eIvDeSn t=s _[f
       r o m _ c'aslteynldeatresc(hm.ojrpn@ignmga=iTlr.uceo)m:'
       , 
        ] 

         "#" "AGdedt  aedvdeinttiso nfarlo mc amluelntdiaprlse  fcraolme nednavrisr"o"n"m
         e n t   itfr yc:o
         n f i g u r e d 
         cArDeDdIeTnItOiNaAlLs__CdAiLcEtN D=A RjSs o=n .olso.agdest(eGnOvO(G'LAED_DCIRTEIDOENNATLI_ACLASL_EJNSDOANR)_
         I D S ' ,   ' ' )c
         riefd eAnDtDiIaTlIsO N=A Ls_eCrAvLiEcNeD_AaRcSc:o
         u n t . CCrAeLdEeNnDtAiRa_lIsD.Sf.reoxmt_esnedr(v[iccael_.asctcroiupn(t)_ ifnofro (c
         a l   i n   A D D I T I OcNrAeLd_eCnAtLiEaNlDsA_RdSi.cstp,l
         i t ( ' , ' ) ] ) 

           #  sJcaoppaense=sSeC OhPoElSi
           d a y s   f o r  )2
           0
           2 4 - 2 0 2 6 
            JsAePrAvNiEcSeE _=H ObLuIiDlAdY(S' c=a l{e
            n d a r '',0 1'-v031'',:  c'r元日e'd,e
            n t i a l's0=1c-r0e9d'e:n t'i成人aの日l's,)


                   ' 0 2 - 1 1j's:t  '=建国 記念Zの日o'n,e
                   I n f o (''0A2s-i1a2/'T:o k'y休日o（建'国記)念の
                   日の ため ）' , 
                           t'o0d3a-y2 0=' :d a't春e分のt日'i,m
                           e . n o w'(0j4s-t2)9.'d:a t'e昭(和の)日'
                           ,

                                    ' 0 5 -i0f3 'm:o r'n憲i法記n念日g':,

                                             ' 0 5 - 0 4 ' :t i'mみどeりの_日'm,i
                                             n   =   d'a0t5e-t0i5m'e:. c'oこmどもbの日i'n,e
                                             ( t o d a'y0,5 -d0a6t'e:t i'm振替e休日.'m,i
                                             n . t i m'e0(7)-)1.5r'e:p l'a海のc日'e,(
                                             t z i n f'o0=8j-s1t1)'.:i s'o山fの日o'r,m
                                             a t ( ) 
                                             ' 0 9 - 1 6 ' :  e'l敬老sの日e':,

                                                      ' 0 9 - 2 2 ' :t i'm秋分eの日_'m,i
                                                      n   =   d'a0t9e-t2i3m'e:. c'o秋分mの日b（2i0n2e4(）t'o,d
                                                      a y ,   d'a1t0e-t1i4m'e:. m'iスポnーツ.の日t'i,m
                                                      e ( ) ) .'r1e1p-l0a3c'e:( h'o文化uの日r'=,1
                                                      2 ,   t z'i1n1f-o0=4j's:t )'.振替i休日s'o,f
                                                      o r m a t'(1)1
                                                      -
                                                      2 3 ' :   ' 勤労 感謝 の日t'i,m
                                                      e}_
                                                      m
                                                      a#x  S=p e(cdiaatle tdiamtee.sc/ommebmionrei(atlo ddaayy,s 
                                                      dSaPtEeCtIiAmLe_.DmAaTxE.St i=m e{(
                                                      ) )   +  't0i3m-e1d1e'l:t a'(東日s本大e震災cの日o'n,d
                                                      s = 1 ) )'.0r6e-p0l4a'c:e ('t天皇z誕生i日（n現上f皇）o'=,j
                                                      s t ) . i's0o9f-o0r1m'a:t (')防災
                                                      の日
                                                      ' , 
                                                               ' 1a2l-l2_5e'v:e n'tクリsスマ ス'=, 
                                                               [}]


                                                                d e f   g e t _cdaalteen_dianrf_on(a)m:e
                                                                s   =   {"}"
      "
      G e t   d a t e  fwoirt hc ahloelniddaary_/imde mionr iCaAlL EdNaDyA Ri_nIfDoSr:m
      a t i o n " " " 
              tjrsyt: 
              =   Z o n e I n f o ( ' A s i a /cTaolkeynod'a)r
              _ i n f on o=w  s=e rdvaitceet.icmael.ennodwa(rjLsits)t
              ( ) . g edta(tcea_lsetnrd a=r Indo=wc.aslternfdtairm_ei(d")%.Ye年x%emc月%udt日e"())

                      d a y s   =   [ " 月" ,   "c火a"l,e n"d水"a,r _"n木a"m,e s"[金"c,a l"e土n"d,a r"_日"i]d
                      ]   =   cdaalye_nodfa_rw_eienkf o=. gdeaty(s'[snuomwm.awreye'k,d acya(l)e]n
                      d
                      a r _ i dd)a
                      t
                      e _ k e y   =   n o w . s t r f teivmeen(t"s%_mr-e%sdu"l)t

                       =   s e rdvaitcee_.ienvfeon t=s (f)".{ldiastte(_
                       s t r } （{ d a y _ o f _ w e e k } 曜 日） " 
                       c
                       a l e n diafr Idda=tcea_lkeenyd airn_ iJdA,P
                       A N E S E _ H O L I D A Y S : 
                                 t i m ehMoilni=dtaiym e=_ mJiAnP,A
                                 N E S E _ H O L I D A Y S [ d a t e _ k etyi]m
                                 e M a x = t i m ed_amtaex_,i
                                 n f o   + =   f " \ n ㊗️ 祝日 ：{ h o l i d a ym}a"x
                                 R e s u letlsi=f2 0d,a
                                 t e _ k e y   i n   S P E C I A L _ D A TsEiSn:g
                                 l e E v e n t s =sTpreucei,a
                                 l   =   S P E C I A L _ D A T E S [ d a toer_dkeeryB]y
                                 = ' s t a r t T idmaet'e
                                 _ i n f o   + =   f " \ n 📅 { s p)e.ceixaelc}u"t
                                 e
                                 ( ) 

                                    r e t u r n   d a t e _ i n f oe
                                    v
                                    ednetfs  g=e te_veevnetnst_sr_efsruolmt_.cgaelte(n'diatresm(sm'o,r n[i]n)g
                                    =
                                    T r u e ) : 
                                             " " " G e tf oerv eenvtesn tf rionm  emvuelnttisp:l
                                             e   c a l e n d a r s " " " 
                                                      t reyv:e
                                                      n t [ ' c a l e ncdraerd_ennatmiea'l]s _=d iccatl e=n djasro_nn.almoeasd[sc(aGlOeOnGdLaEr__CiRdE]D
                                                      E N T I A L S _ J S O N ) 
                                                                    a lclr_eedveennttisa.lasp p=e nsde(revviecnet_)a
                                                                    c
                                                                    c o u n t . C r e d e n teixaclesp.tf rEoxmc_espetrivoinc ea_sa cec:o
                                                                    u n t _ i n f o ( 
                                                                                  l o g g e rc.reerdreonrt(ifa"lEsr_rdoirc tf,e
                                                                                  t c h i n g   f r o m   {sccaolpeensd=aSrC_OiPdE}S:
                                                                                    { e } " ) 
                                                                                        ) 

                                                                                                          s e r vciocnet i=n ubeu
                                                                                                          i
                                                                                                          l d ( ' c a l e nidfa rn'o,t  'avl3l'_,e vcernetdse:n
                                                                                                          t i a l s = c r e d e n trieatlusr)n
                                                                                                           
                                                                                                           " 今 日の スケ ジュ ール :   なしj"s ti f=  mZoornneiInngf oe(l'sAes i"a午後/のスTケジoューkル:y oな'し")
                                                                                                           
                                                                                                           
                                                                                                                           taoldla_ye v=e ndtast.estoirmte(.kneoyw=(ljasmtb)d.ad axt:e (x)[
                                                                                                                           '
                                                                                                                           s t a r t ' ] . gieft (m'odrantienTgi:m
                                                                                                                           e ' ,   x [ ' s t a r t 't]i.mgee_tm(i'nd a=t ed'a,t e't9i9m9e9.'c)o)m)b
                                                                                                                           i
                                                                                                                           n e ( t o d a y ,e vdeantte_ttiemxet. m=i n"."t
                                                                                                                           i m e ( ) ) . r efpolra ceev(etnzti nifno =ajlslt_)e.viesnotfso:r
                                                                                                                           m a t ( ) 
                                                                                                                                         s tealrste :=
                                                                                                                                           e v e n t [ ' s t a r tt'i]m.eg_emti(n' d=a tdeaTtiemtei'm,e .ecvoemnbti[n'es(ttaordta'y],. gdeatt(e'tdiamtee.'m)i)n
                                                                                                                                           . t i m e ( ) ) . r e p lsaucmem(ahroyu r== 1e2v,e nttz[i'nsfuom=mjasrty)'.]i
                                                                                                                                           s o f o r m a t ( ) 
                                                                                                                                            
                                                                                                                                              c a l e n d a rt_inmaem_em a=x  e=v e(ndta.tgeetti(m'ec.acloemnbdianre_(ntaomdea'y,,  'd'a)t
                                                                                                                                              e
                                                                                                                                              t i m e . m a x . t i m ei(f) )' T+'  tiinm esdtealrtta:(
                                                                                                                                              s e c o n d s = 1 ) ) . r e p l adcte (=t zdiantfeot=ijmset.)f.riosmoifsoorfmoartm(a)t
                                                                                                                                              (
                                                                                                                                              s t a r t ) 
                                                                                                                                                  a l l _ e v e n t s   =   [ ]s
                                                                                                                                                  t a r t _ t i m ec a=l edntd.asrt_rnfatmiemse (=" %{H}:
                                                                                                                                                  %
                                                                                                                                                  M " ) 
                                                                                                                                                            f o r   c a l eenldsaer:_
                                                                                                                                                            i d   i n   C A L E N D A R _ I DsSt:a
                                                                                                                                                            r t _ t i m e   =   " 終日 "t
                                                                                                                                                            r
                                                                                                                                                            y : 
                                                                                                                                                                                i f   c a l ecnadlaern_dnaarm_ei nafnod  =c asleernvdiacre_.ncaamlee n!d=a rCLAiLsEtN(D)A.Rg_eItD(Sc[a0l]e:n
                                                                                                                                                                                d a r I d = c a l e n d a r _ i de)v.eenxte_ctuetxet( )+
                                                                                                                                                                                =   f " •  { s t a r t _ t i m e }c a-l e{nsduamrm_anraym}e s([{ccaalleennddaarr__inda]m e=} )c\anl"e
                                                                                                                                                                                n d a r _ i n f o . g e te(l'sseu:m
                                                                                                                                                                                m a r y ' ,   c a l e n d a r _ iedv)e
                                                                                                                                                                                n
                                                                                                                                                                                t _ t e x t   + =   f " •   { s teavretn_ttsi_mree}s u-l t{ s=u msmearrvyi}c\en."e
                                                                                                                                                                                v
                                                                                                                                                                                e n t s ( ) . l irsett(u
                                                                                                                                                                                r n   e v e n t _ t e x t . s t r i p ( )c
                                                                                                                                                                                a
                                                                                                                                                                                l e n d aerxIcde=pcta lEexncdeaprt_iiodn, 
                                                                                                                                                                                a s   e : 
                                                                                                                                                                                                 l o g g e r .teirmreoMri(nf="tEirmreo_rm igne,t
                                                                                                                                                                                                 t i n g   e v e n t s :   { e } " ) 
                                                                                                                                                                                                     t i m e M a xr=ettiumren_ m"aスケxジュ,ール
                                                                                                                                                                                                     取得 エラ ー" 
                                                                                                                                                                                                      
                                                                                                                                                                                                       d e f   g e t _ m o r n i n g _meavxeRnetssu(l)t:s
                                                                                                                                                                                                       = 2 0 , 
                                                                                                                                                                                                       " " " G e t   t o d a y ' s   a l l   e vseinntgsl efEovre nmtosr=nTirnuge ,b
                                                                                                                                                                                                       r i e f i n g " " " 
                                                                                                                                                                                                                r e t u r no rgdeetr_Beyv=e'nsttsa_rftrToimm_ec'a
                                                                                                                                                                                                                l e n d a r s ( m o r n i n g = T)r.ueex)e
                                                                                                                                                                                                                c
                                                                                                                                                                                                                udteef( )g
                                                                                                                                                                                                                e
                                                                                                                                                                                                                t _ a f t e r n o o n _ e v e n tesv(e)n:t
                                                                                                                                                                                                                s   =   e"v"e"nGtest_ raefstuelrtn.ogoent (e'vietnetmss '(,1 2[:]0)0
                                                                                                                                                                                                                 
                                                                                                                                                                                                                 o n w a r d s )   f o r   n o o nf obrr ieevfeinntg "i"n" 
                                                                                                                                                                                                                 e v e n trse:t
                                                                                                                                                                                                                 u r n   g e t _ e v e n t s _ f r o m _ ceavleenntd[a'rcsa(lmeonrdnairn_gn=aFmael's]e )=
                                                                                                                                                                                                                  
                                                                                                                                                                                                                  cdaelfe ngdeatr__bniatmceosi[nc_aplreincdea(r)_:i
                                                                                                                                                                                                                  d ] 
                                                                                                                                                                                                                      " " " G e t   B i t c o i n   p r i cael lf_reovme nCtosi.naGpepceknod (AePvIe"n"t")
                                                                                                                                                                                                                      
                                                                                                                                                                                                                       
                                                                                                                                                                                                                             t r y : 
                                                                                                                                                                                                                                       e x c euprtl  E=x c"ehptttiposn: /a/sa pei:.
                                                                                                                                                                                                                                       c o i n g e c k o . c o m / a p il/ovg3g/esri.meprlreo/rp(rfi"cEer"r
                                                                                                                                                                                                                                       o r   f e t c h ipnagr afmrso m=  {{c
                                                                                                                                                                                                                                       a l e n d a r _ i d } :  '{ied}s"'):
                                                                                                                                                                                                                                         ' b i t c o i n ' , 
                                                                                                                                                                                                                                                   c o n t i n u e'
                                                                                                                                                                                                                                                   v
                                                                                                                                                                                                                                                   s _ c u r r e n ciife sn'o:t  'ajlply_,euvsedn't
                                                                                                                                                                                                                                                   s : 
                                                                                                                                                                                                                                                               } 
                                                                                                                                                                                                                                                                         r e t urrens p"o今日nのスsケジeュー ル:=  なrし"e qiufe smtosr.ngientg( uerlls,e  p"a午r後のaスケmジュsール=:p aなしr"a
                                                                                                                                                                                                                                                                         m
                                                                                                                                                                                                                                                                         s ,   t i m e o uatl=l1_0e)v
                                                                                                                                                                                                                                                                         e n t s . s o r tr(eksepyo=nlsaem.brdaai sxe:_ fxo[r'_ssttaarttu's](.)g
                                                                                                                                                                                                                                                                         e
                                                                                                                                                                                                                                                                         t ( ' d a t e T idmaet'a,  =x [r'esstpaornts'e]..jgseotn((')d
                                                                                                                                                                                                                                                                         a t e ' ,   ' 9 9b9t9c'_)j)p)y
                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                          =   d a t a [ ' beivtecnoti_nt'e]x[t' j=p y"'"]
                                                                                                                                                                                                                                                                          
                                                                                                                                                                                                                                                                                          fbotrc _euvsedn t=  idna taal[l'_beivtecnotisn:'
                                                                                                                                                                                                                                                                                          ] [ ' u s d ' ] 
                                                                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                                                                                 s t a r t  r=e teuvrenn tf["'₿s tBairttc'o]i.ng:e t¥{(b'tdca_tjepTyi:m,e.'0,f }e v/e n$t{[b'tsct_aurstd':],..g2eft}("'
                                                                                                                                                                                                                                                                                                 d a t e 'e)x)c
                                                                                                                                                                                                                                                                                                 e p t   E x c e p t i o ns uamsm aer:y
                                                                                                                                                                                                                                                                                                   =   e v e n t [l'osgugmemra.reyr'r]o
                                                                                                                                                                                                                                                                                                   r ( f " E r r o r   g e tctailnegn dBairt_cnoaimne  p=r iecvee:n t{.eg}e"t)(
                                                                                                                                                                                                                                                                                                   ' c a l e n d a rr_entaumren' ," B'i't)c
                                                                                                                                                                                                                                                                                                   o
                                                                                                                                                                                                                                                                                                   i n 価 格取 得エ ラー " 
                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                     d e f  igfe t'_Tw'e aitnh esrt(a)r:t
                                                                                                                                                                                                                                                                                                     : 
                                                                                                                                                                                                                                                                                                           " " " G e t   T o k y o   wdeta t=h edra tweittihm ed.eftraoimliesdo ftoermmpaetr(asttuarret )i
                                                                                                                                                                                                                                                                                                           n f o r m a t i o n " " " 
                                                                                                                                                                                                                                                                                                                 s ttarryt:_
                                                                                                                                                                                                                                                                                                                 t i m e   =   d tu.rslt r=f t"ihmtet(p"s%:H/:/%aMp"i).
                                                                                                                                                                                                                                                                                                                 o p e n - m e t e o . c oeml/sve1:/
                                                                                                                                                                                                                                                                                                                 f o r e c a s t " 
                                                                                                                                                                                                                                                                                                                               s tpaarrta_mtsi m=e  {=
                                                                                                                                                                                                                                                                                                                                 " 終 日" 
                                                                                                                                                                                                                                                                                                                                  
                                                                                                                                                                                                                                                                                                                                                ' l a t i tiufd ec'a:l e3n5d.a6r7_6n2a,m
                                                                                                                                                                                                                                                                                                                                                e   a n d   c a l e n d a'rl_onnagmiet u!d=e 'C:A L1E3N9D.A6R5_0I3D,S
                                                                                                                                                                                                                                                                                                                                                [ 0 ] : 
                                                                                                                                                                                                                                                                                                                                                                ' c u r r e n t 'e:v e'ntte_mtpeexrta t+u=r ef_"2•m ,{wsetaatrhte_rt_icmoed}e '-, 
                                                                                                                                                                                                                                                                                                                                                                { s u m m a r y }   ( { c'adlaeinldya'r:_ n'atmeem}p)e\rna"t
                                                                                                                                                                                                                                                                                                                                                                u r e _ 2 m _ m a x , t eemlpseer:a
                                                                                                                                                                                                                                                                                                                                                                t u r e _ 2 m _ m i n ' , 
                                                                                                                                                                                                                                                                                                                                                                      e v e n t _ t e x t' h+o=u rfl"y• '{:s t'atretm_pteirmaet}u r-e _{2smu'm,m
                                                                                                                                                                                                                                                                                                                                                                      a r y } \ n " 
                                                                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                                                               ' t i m erzeotnuer'n:  e'vAesnita_/tTeoxkty.os't
                                                                                                                                                                                                                                                                                                                                                                               r i p ( ) 
                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                    } 
                                                                                                                                                                                                                                                                                                                                                                                      e x c e p t   Erxecseppotnisoen  =a sr eeq:u
                                                                                                                                                                                                                                                                                                                                                                                      e s t s . g e t (luorglg,e rp.aerrarmosr=(pfa"rEarmrso,r  tgiemtetoiuntg= 1e0v)e
                                                                                                                                                                                                                                                                                                                                                                                      n t s :   { e } "r)e
                                                                                                                                                                                                                                                                                                                                                                                      s p o n s e . r ariesteu_rfno r"_スsケジtューaル取t得エuラーs"(
                                                                                                                                                                                                                                                                                                                                                                                      )
                                                                                                                                                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                                                                                                                                                      d
                                                                                                                                                                                                                                                                                                                                                                                      e f   g e t _ m odrantian g=_ erveesnptosn(s)e:.
                                                                                                                                                                                                                                                                                                                                                                                      j s o n (")"
      " G e t   t o d acyu'rsr eanltl  =e vdeanttas[ 'fcourr rmeonrtn'i]n
      g   b r i e f i ntge"m"p" 
      =   c u rrreetnutr[n' tgeemtp_eervaetnutrse__f2rmo'm]_
      c
      a l e n d a r s (dmaoirlnyi n=g =dTartuae[)'
      d
      adielfy 'g]e
      t _ a f t e r n otoenm_pe_vmeanxt s=( )d:a
      i l y [ '"t"e"mGpeetr aatfutreer_n2omo_nm aexv'e]n[t0s] 
      ( 1 2 : 0 0   o ntweamrpd_sm)i nf o=r  dnaoiolny [b'rtieemfpienrga"t"u"r
      e _ 2 m _rmeitnu'r]n[ 0g]e
      t
      _ e v e n t s _ fhrooumr_lcya_lteenmdpasr s=( mdoartnai[n'gh=oFuarllsye')]
      [
      'dteefm pgeerta_tbuirtec_o2imn'_]p
      r i c e ( ) : 
        b u s i"n"e"sGse_th oBuirtsc_otienm ppsr i=c eh ofurrolmy _CtoeimnpGse[c9k:o1 8A]P
        I " " " 
                ttermyp:_
                a v g   =   s u mu(rblu s=i n"ehstst_phso:u/r/sa_ptie.mcposi)n g/e clkeon.(cboums/ianpeis/sv_3h/osuirmsp_ltee/mpprsi)c
                e
                " 
                              w epaatrhaemrs_ c=o d{e
                              s   =   { 
                                            ' i d s ' :0 :' b'i晴tれ'c,o i1n:' ,'
                                            晴 れ' ,   2 :   ' 曇 り' ,   3':v s'_曇cり'u,r
                                            r e n c i e s ' :   ' j p4y5,:u s'd霧''
                                            ,   4 8 :   ' 霧' ,}

                                                             r e s p5o1n:s e' 小=雨' ,r e5q3u:e s't小s雨'.,g e5t5(:u r'l小,雨' ,p
                                                             a r a m s = p a r a m s ,6 1t:i m'e雨o'u,t =6130:) 
                                                             ' 雨' ,   6 5 :   'r豪e雨's,p
                                                             o n s e . r a i s e _ f o7r1_:s t'a小t雪'u,s (7)3
                                                             :
                                                               ' 雪 ' ,   7 5 :d a't豪雪a' ,=
                                                                 r e s p o n s e . j s o7n7(:) 
                                                                 ' あら れ' , 
                                                                         b t c _ j p y   =8 0d:a t'a所[々小'雨'b,i t8c1o:i n''所]々雨['',j p8y2':] 
                                                                         ' 所々 豪雨 ' , 
                                                                               b t c _ u s d   =  8d5a:t a'[あら'れ'b,i t8c6o:i n''あ]られ['',u
                                                                               s d ' ] 

                                                                                              9 5r:e t'u雷雨r'n,  f9"6₿:  B'i雷t雨'c,o i9n9::  ¥{'b雷雨t'c
                                                                                              _ j p y : , . 0 f}}

                                                                                               /   $ { b t c _ uwseda:t,h.e2rf }=" 
                                                                                               w e a t heexrc_ecpotd eEsx.cgeeptt(icounr raesn te[:'
                                                                                               w e a t h e r _ cloodgeg'e]r,. e'r不明r'o)r
                                                                                               (
                                                                                               f " E r r o r   greetttuirnng  fB"i🌡️t c{owiena tphreirc}e :/  {気温e }{"t)e
                                                                                               m p } °C （ 最低   { treemtpu_rmni n"}B°Ci、t最高c o{itne価m格取p得エ_ラーm"a
                                                                                               x
                                                                                               }d°eCf、日 中平g均 e{tt_ewmepa_tahvegr:(.)1:f
                                                                                               } ° C ）" 
                                                                                               " " " G eetx cTeopkty oE xwceeaptthieorn  waist he :d
                                                                                               e t a i l e d   tleomgpgeerra.teurrreo ri(nff"oErrmraotri ogne"t"t"i
                                                                                               n g   w etartyh:e
                                                                                               r :   { e } " ) 
                                                                                               u r l   =   " h trteptsu:r/n/ a"p天i気取.得エoラーp"e
                                                                                               n
                                                                                               -dmeeft esoe.ncdo_mt/evl1e/gfroarme_cmaessts"a
                                                                                               g e ( t e x t ) :p
                                                                                               a r a m s" "=" S{e
                                                                                               n d   m e s s a g e   v i'al aTteilteugdrea'm:  B3o5t."6"7"6
                                                                                               2 , 
                                                                                                   t r y : 
                                                                                                               ' l ounrgli t=u dfe"'h:t t1p3s9:./6/5a0p3i,.
                                                                                                               t e l e g r a m . o r g /'bcoutr{rTeEnLtE'G:R A'Mt_eBmOpTe_rTaOtKuErNe}_/2sme,nwdeMaetshsearg_ec"o
                                                                                                               d e ' , 
                                                                                                                       p a y l o a d   =' d{a
                                                                                                                       i l y ' :   ' t e m p e r'acthuarte__i2dm'_:m aTxE,LtEeGmRpAeMr_aUtSuErRe__I2Dm,_
                                                                                                                       m i n ' , 
                                                                                                                                     ' t e x t '':h otuerxlty,'
                                                                                                                                     :   ' t e m p e r a t u r'ep_a2rms'e,_
                                                                                                                                     m o d e ' :   ' p l a i n''t
                                                                                                                                     i m e z o n e ' :} 
                                                                                                                                     ' A s i a / T o kryeos'p
                                                                                                                                     o n s e   =   r e}q
                                                                                                                                     u e s t s . p o srte(suproln,s ej s=o nr=epqauyelsotasd.,g etti(muerolu,t =p1a0r)a
                                                                                                                                     m s = p a r a m sr,e stpiomnesoeu.tr=a1i0s)e
                                                                                                                                     _ f o r _ s t a truess(p)o
                                                                                                                                     n s e . r a i s el_ofgogre_rs.tiantfuos((")M
                                                                                                                                     e
                                                                                                                                     s s a g e   s e ndta tsau c=c ersessfpuolnlsye .tjos oTne(l)e
                                                                                                                                     g r a m " ) 
                                                                                                                                         c u rerxecnetp t=  Edxacteap[t'icounr raesn te':]
                                                                                                                                         
                                                                                                                                                         ltoegmgpe r=. ecrurrorre(nft"[E'rtreomrp esreantduirneg_ 2Tme'l]e
                                                                                                                                                         g
                                                                                                                                                         r a m   m e s s adgaei:l y{ e=} "d)a
                                                                                                                                                         t
                                                                                                                                                         ad[e'fd amialiyn'(])
                                                                                                                                                         : 
                                                                                                                                                                  " " "tMeamipn_ mfauxn c=t idoani ltyo[ 'ctoemmppielrea taunrde _s2emn_dm atxh'e] [b0r]i
                                                                                                                                                                  e f i n g " " " 
                                                                                                                                                                  t e m p _jmsitn  ==  ZdoanielIyn[f'ot(e'mApseiraa/tTuorkey_o2'm)_
                                                                                                                                                                  m i n ' ]n[o0w] 
                                                                                                                                                                  =
                                                                                                                                                                    d a t e t i m eh.onuorwl(yj_stte)m
                                                                                                                                                                    p s   =  hdoautra [=' hnoouwr.lhyo'u]r[
                                                                                                                                                                    ' t e m pmeirnauttuer e=_ 2nmo'w].
                                                                                                                                                                    m i n u t e 
                                                                                                                                                                     
                                                                                                                                                                       b u s ilnoegsgse_rh.oiunrfso_(tfe"mCpusr r=e nhto utrilmye_ t(eJmSpTs)[:9 :{1n8o]w
                                                                                                                                                                       . s t r f t i m et(e'm%pY_-a%vmg- %=d  s%uHm:(%bMu:s%iSn'e)s}s"_)h
                                                                                                                                                                       o
                                                                                                                                                                       u r s _ tdeamtpes_)a n/d _ldeany( b=u sgiente_sdsa_theo_uirnsf_ot(e)m
                                                                                                                                                                       p s ) 
                                                                                                                                                                        
                                                                                                                                                                        w e a t h e r   =w egaetth_ewre_actohdeers( )=
                                                                                                                                                                          { 
                                                                                                                                                                              b i t c o i n   =   g0e:t _'b晴iれ't,c o1i:n _'p晴rれ'i,c e2(:) 
                                                                                                                                                                              '
                                                                                                                                                                              曇 り' ,   3i:f  'h曇oり'u,r
                                                                                                                                                                                = =   6 : 
                                                                                                                                                                                            4 5 :l o'g霧g'e,r .4i8n:f o'(霧'",S
                                                                                                                                                                                            e n d i n g   m o r n i n5g1 :b r'i小e雨'f,i n5g3.:. .'"小)雨'
                                                                                                                                                                                            ,   5 5 :   ' 小 雨'e,v
                                                                                                                                                                                            e n t s   =   g e t _ m o6r1n:i n'g雨_'e,v e6n3t:s (')雨'
                                                                                                                                                                                            ,
                                                                                                                                                                                              6 5 :   ' 豪 雨' ,m
                                                                                                                                                                                              e s s a g e   =   f " " "7☀️1 :おは よう'ござ小い雪ま'す!,
                                                                                                                                                                                               
                                                                                                                                                                                               7{3d:a t'e雪'_,a n7d5_:d a'y豪}雪'
                                                                                                                                                                                               ,
                                                                                                                                                                                               
                                                                                                                                                                                               { w e a t h e r } 
                                                                                                                                                                                                
                                                                                                                                                                                                 { b7i7t:c o'iあnられ}'
                                                                                                                                                                                                 ,
                                                                                                                                                                                                 
                                                                                                                                                                                                 ス ケジ ュー ル: 
                                                                                                                                                                                                  { e v e n t s }8"0":" 
                                                                                                                                                                                                  '
                                                                                                                                                                                                  所々 小雨 ' ,  e8l1i:f  'h所々o雨'u,r  8=2=:  1'2所:々豪
                                                                                                                                                                                                  雨' , 
                                                                                                                                                                                                              l o g g e r .8i5n:f o'(あ"られS'e,n d8i6n:g  'aあらfれ't,e
                                                                                                                                                                                                              r n o o n   b r i e f i n9g5.:. .'"雷)雨'
                                                                                                                                                                                                              ,   9 6 :   ' 雷 雨'e,v e9n9t:s  '=雷 雨'g
                                                                                                                                                                                                              e t _ a f t e r n}o
                                                                                                                                                                                                              o
                                                                                                                                                                                                              n _ e v e n t s (w)e
                                                                                                                                                                                                              a
                                                                                                                                                                                                              t h e r   =   w emaetshsearg_ec o=d efs"."g"e🌤️t (こんcにちuは!r
                                                                                                                                                                                                              r
                                                                                                                                                                                                              e{ndta[t'ew_eaantdh_edra_yc}o
                                                                                                                                                                                                              d
                                                                                                                                                                                                              e{'w]e,a t'h不明e'r)}
                                                                                                                                                                                                              
                                                                                                                                                                                                              
                                                                                                                                                                                                              
                                                                                                                                                                                                               { b i t c o i nr}e
                                                                                                                                                                                                               t
                                                                                                                                                                                                               u午r後のnスケ ジュfール":🌡
                                                                                                                                                                                                               ️ {{ewveeantthse}r"}" "/
                                                                                                                                                                                                                
                                                                                                                                                                                                                気 温  { t eemlps}e°:C
                                                                                                                                                                                                                （最 低  { t e m p _ mliong}g°eCr、最.高 i{ntfeom(pf_"mOauxt} °oCf、日 中平b均 r{iteefmipn_ga vtgi:m.e1 f(}c°uCr）"r
                                                                                                                                                                                                                e n t   heoxucre:p t{ hEoxucre}p)t"i)o
                                                                                                                                                                                                                n   a s   e : 
                                                                                                                                                                                                                  r e t u r n 
                                                                                                                                                                                                                   
                                                                                                                                                                                                                   l o g g elro.gegrerro.ri(nff"oE(rfr"oSre ngdeitntgi nmge swseaagteh eart:  {{neo}w".)s
                                                                                                                                                                                                                   t r f t i m e ( 'r%eHt:u%rMn: %"S天'気取)得エ}ラー"")
                                                                                                                                                                                                                   
                                                                                                                                                                                                                   
                                                                                                                                                                                                                    d e f  lsoegngde_rt.eilnefgor(afm"_
