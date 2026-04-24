import os, datetime, sys

from kivy.config import Config
Config.set("graphics", "allow_screensaver", "0")
Config.set("kivy",     "log_level",        "warning")

from kivy.app               import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout     import BoxLayout
from kivy.uix.gridlayout    import GridLayout
from kivy.uix.scrollview    import ScrollView
from kivy.uix.label         import Label
from kivy.uix.button        import Button
from kivy.uix.textinput     import TextInput
from kivy.uix.widget        import Widget
from kivy.uix.modalview     import ModalView
from kivy.graphics          import Color, RoundedRectangle, Rectangle
from kivy.clock             import Clock
from kivy.metrics           import dp, sp
from kivy.core.window       import Window
from kivy.core.text         import LabelBase
from kivy.animation         import Animation
from kivy.utils             import platform

IS_ANDROID = (platform == "android")
IS_WIN     = (platform == "win")

def _reg():
    try:    base = os.path.dirname(os.path.abspath(__file__))
    except: base = os.getcwd()

    PREFERRED = os.path.join(base, "NanumBarunGothicBold.ttf")
    fallbacks = [
        "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "/system/fonts/NotoSansCJK-Regular.ttc",
    ]

    for p in [PREFERRED] + fallbacks:
        if p and os.path.exists(p):
            try:
                LabelBase.register("KR", fn_regular=p)
                return "KR"
            except: pass
    return None
KF = _reg()

_S = [1.0]

def _init_scale(*_):
    w, h = Window.width, Window.height
    sw, sh = w / 1920.0, h / 1080.0
    s  = min(sw, sh)
    _S[0] = max(1.1, min(s, 2.8))

def S():    return _S[0]
def fs(b):  return max(13, int(b * _S[0]))
def rp(b):  return dp(max(2, b * _S[0]))
def rq(b):  return dp(max(2, b * _S[0]))

C = {
    "surf":  (1,   1,   1,   1),
    "surf2": (.94, .96, 1,   1),
    "pri_l": (.92, .94, 1,   1),
    "pri":   (.23, .44, .91, 1),
    "ok":    (.13, .77, .37, 1),
    "dang":  (.93, .26, .26, 1),
    "warn":  (.96, .62, .04, 1),
    "t1":    (.12, .16, .24, 1),
    "t2":    (.39, .45, .55, 1),
    "t3":    (.58, .63, .72, 1),
    "clk":   (.12, .23, .54, 1),
    "white": (1,   1,   1,   1),
    "amb2":  (.82, .92, .60, 1), 
    "prep":  (.99, .96, .88, 1),
    "prep2": (.99, .92, .70, 1),
}

def h2r(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2],16)/255 for i in (0,2,4)) + (1,)

EXAM_TYPES = ["1학기 중간시험","1학기 기말시험","2학기 중간시험","2학기 기말시험"]
GRADES     = ["1학년","2학년","3학년"]
CLASSES    = [f"{i}반" for i in range(1,16)]
SUBJECTS   = ["수업","국어","수학","영어","사회","과학","역사","도덕","기술가정","한문",]
NOTICES    = [
    "모든 전자기기(휴대폰,태블릿,이어폰,스마트워치 등)는 담임선생님께 제출",
    "예비종이 울리면 자기 자리에 앉기",
    "지필평가 답안은 OMR카드에 컴퓨터용 수성 사인펜만 사용",
    "OMR카드 예비마킹 금지 (중복답안으로 불이익 발생)",
    "서술형 답안은 검정색 볼펜, 틀린 경우 두 줄 긋기",
    "서술형 답을 모를 경우 빈칸으로 두지 않고 '모름'이라고 작성",
    "부정행위 절대 금지!! (협조자도 0점 처리됨.)",
    "고사 중 화장실 사용 금지 → 쉬는 시간에 꼭 다녀오기",
]
N = 3

# 알림 중복 방지를 위한 셋
_notified_periods = set()

def make_sched(subjects, sh_=9, sm_=5, lesson=45, brk=20, prep=5):
    rows = []; cur = datetime.datetime(2000,1,1,sh_,sm_)
    for i in range(1, N+1):
        if i == 1:
            ps = cur - datetime.timedelta(minutes=prep)
            rows.append({"label":"1교시 준비","disp":"준비시간","time":f"{ps:%H:%M}~{cur:%H:%M}","subject":"","is_break":True,"period":1})
        
        end = cur + datetime.timedelta(minutes=lesson)
        rows.append({"label":f"{i}교시","disp":f"{i}교시","time":f"{cur:%H:%M}~{end:%H:%M}","subject":subjects[i-1] if i-1<len(subjects) else "","is_break":False,"period":i})
        
        if i < N:
            ns_start = end
            ns_end = end + datetime.timedelta(minutes=brk)
            rows.append({"label":f"{i+1}교시 쉬는시간","disp":"쉬는시간","time":f"{ns_start:%H:%M}~{ns_end:%H:%M}","subject":"","is_break":True,"period":i+1})
            cur = ns_end
    return rows

def time_status(tstr, now=None):
    if now is None: now = datetime.datetime.now()
    try:
        s,e = tstr.split("~")
        sh2,sm2 = map(int,s.split(":")); eh,em = map(int,e.split(":"))
        sd = now.replace(hour=sh2,minute=sm2,second=0,microsecond=0)
        ed = now.replace(hour=eh, minute=em, second=0,microsecond=0)
        rem = int((ed-now).total_seconds())
        if sd<=now<ed and rem>0: return True,rem,sd,ed
        return False,None,sd,ed
    except: return False,None,None,None

def get_curr(sched):
    now = datetime.datetime.now()
    for it in sched:
        c,r,s,e = time_status(it["time"],now)
        if c: return it,r
    return None,None

class St:
    se=None; sg=None; sc=None; st=None
    ss=[None]*N; sn=list(range(len(NOTICES))); sx=""; absent=[]; sched=[]
st = St()

class Card(BoxLayout):
    def __init__(self, bg="surf", r=12, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            self._c  = Color(*C[bg])
            self._rr = RoundedRectangle(pos=self.pos,size=self.size,radius=[r])
        self.bind(pos=self._u,size=self._u)
    def _u(self,*_): self._rr.pos=self.pos; self._rr.size=self.size
    def recolor(self,rgba): self._c.rgba=rgba

def L(text, bfs=13, bold=True, col="t1", ha="left", va="middle", **kw):
    w = Label(text=text, font_size=fs(bfs), bold=bold,
              color=C[col] if isinstance(col,str) else col,
              halign=ha, valign=va, **kw)
    if KF: w.font_name = KF
    w.bind(size=w.setter("text_size"))
    return w

def Btn(text, bg="pri", fg="white", bfs=13, wd=None, ht=48, cb=None, **kw):
    b = Button(text=text, font_size=fs(bfs), bold=True,
               background_normal="", background_color=C[bg], color=C[fg],
               size_hint=(None,None),
               width=rp(wd or max(80, len(text)*16+24)),
               height=rq(ht), **kw)
    if KF: b.font_name = KF
    if cb: b.bind(on_press=cb)
    return b

def Div():
    w = Widget(size_hint_y=None, height=dp(2))
    with w.canvas:
        Color(.78,.82,.92,1); r = Rectangle(pos=w.pos,size=w.size)
    w.bind(pos=lambda ww,_:setattr(r,"pos",ww.pos),
           size=lambda ww,_:setattr(r,"size",ww.size))
    return w

def CtHdr(text, col="pri"):
    row = BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(36),spacing=rp(6))
    bar = Widget(size_hint=(None,None),width=rp(6),height=rq(24))
    with bar.canvas:
        Color(*C[col]); rc = Rectangle(pos=bar.pos,size=bar.size)
    bar.bind(pos=lambda w,_:setattr(rc,"pos",w.pos),
             size=lambda w,_:setattr(rc,"size",w.size))
    row.add_widget(bar); row.add_widget(L(text,bfs=15,bold=True,col=col))
    return row

def ChipGroup(opts, selected, on_sel, cols=5):
    n_rows = -(-len(opts)//cols)
    row_h, gap = rq(44), rp(5)
    total_h = n_rows*row_h + max(0,n_rows-1)*gap
    g = GridLayout(cols=cols,size_hint=(1,None),height=total_h,spacing=gap)
    all_ = []
    def sel(b,v):
        on_sel(v)
        for c in all_: c.background_color=C["surf2"]; c.color=C["t2"]
        b.background_color=C["pri"]; b.color=C["white"]
    for o in opts:
        c = Button(text=o, font_size=fs(12), bold=True, background_normal="",
                   background_color=C["pri"] if o==selected else C["surf2"],
                   color=C["white"] if o==selected else C["t2"],
                   size_hint_x=1,size_hint_y=None,height=row_h)
        if KF: c.font_name=KF
        c.bind(on_press=lambda b,v=o:sel(b,v))
        all_.append(c); g.add_widget(c)
    return g

_CHOSEONG  = list("ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ")
_JUNGSEONG = list("ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ")
_JONGSEONG = [" ","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
_KN = [["ㅂ","ㅈ","ㄷ","ㄱ","ㅅ","ㅛ","ㅕ","ㅑ","ㅐ","ㅔ"],["ㅁ","ㄴ","ㅇ","ㄹ","ㅎ","ㅗ","ㅓ","ㅏ","ㅣ"],["ㅋ","ㅌ","ㅊ","ㅍ","ㅠ","ㅜ","ㅡ"]]
_KS = [["ㅃ","ㅉ","ㄸ","ㄲ","ㅆ","ㅛ","ㅕ","ㅑ","ㅒ","ㅖ"],["ㅁ","ㄴ","ㅇ","ㄹ","ㅎ","ㅗ","ㅓ","ㅏ","ㅣ"],["ㅋ","ㅌ","ㅊ","ㅍ","ㅠ","ㅜ","ㅡ"]]

def _compose(buf):
    result=""; i=0
    while i<len(buf):
        c=buf[i]
        if c in _CHOSEONG:
            cho=_CHOSEONG.index(c)
            if i+1<len(buf) and buf[i+1] in _JUNGSEONG:
                jung=_JUNGSEONG.index(buf[i+1])
                if i+2<len(buf) and buf[i+2] in _JONGSEONG[1:]:
                    if i+3<len(buf) and buf[i+3] in _JUNGSEONG:
                        result+=chr(0xAC00+cho*21*28+jung*28); i+=2
                    else:
                        jong=_JONGSEONG.index(buf[i+2])
                        result+=chr(0xAC00+cho*21*28+jung*28+jong); i+=3
                else:
                    result+=chr(0xAC00+cho*21*28+jung*28); i+=2
            else: result+=c; i+=1
        else: result+=c; i+=1
    return result

def show_kor_keyboard(init_text="", title="입력", on_done=None):
    mv = ModalView(size_hint=(.45,.32), pos_hint={"center_x":.5,"center_y":.35}, background_color=(0,0,0,0), overlay_color=(0,0,0,.5), auto_dismiss=False)
    root = Card(bg="surf", r=12, orientation="vertical", padding=rp(10), spacing=rq(5), size_hint=(1,1))
    root.add_widget(L(title,bfs=13,bold=True,col="pri",ha="center", size_hint_y=None,height=rq(26)))
    preview = TextInput(text=init_text,font_size=fs(15),multiline=False, readonly=True,size_hint_y=None,height=rq(42), background_color=C["pri_l"],foreground_color=C["t1"])
    if KF: preview.font_name=KF
    root.add_widget(preview)
    jamo=[]; shift=[False]
    def refresh(): preview.text=_compose(jamo)
    def press(key):
        if key=="⌫":
            if jamo: jamo.pop()
        elif key=="공백": jamo.append(" ")
        elif key=="SHIFT": shift[0]=not shift[0]; rebuild(); return
        else: jamo.append(key)
        refresh()
    key_area=BoxLayout(orientation="vertical",spacing=rq(3))
    def rebuild():
        key_area.clear_widgets()
        rows=_KS if shift[0] else _KN
        for row in rows:
            r=BoxLayout(orientation="horizontal",spacing=rp(3), size_hint_y=None,height=rq(38))
            for k in row:
                b=Button(text=k,font_size=fs(12),background_normal="", background_color=C["surf2"],color=C["t1"],bold=True)
                if KF: b.font_name=KF
                b.bind(on_press=lambda b,k=k:press(k))
                r.add_widget(b)
            key_area.add_widget(r)
        last=BoxLayout(orientation="horizontal",spacing=rp(3), size_hint_y=None,height=rq(38))
        sb=Button(text="⇧"+(" ON" if shift[0] else ""),font_size=fs(10), background_normal="",size_hint_x=1.4,bold=True, background_color=C["pri"] if shift[0] else C["surf2"], color=C["white"] if shift[0] else C["t1"])
        if KF: sb.font_name=KF
        sb.bind(on_press=lambda b:press("SHIFT"))
        sp_=Button(text="공백",font_size=fs(12),background_normal="",bold=True, background_color=C["surf2"],color=C["t1"],size_hint_x=3.5)
        if KF: sp_.font_name=KF
        sp_.bind(on_press=lambda b:press("공백"))
        bs=Button(text="⌫",font_size=fs(13),background_normal="",bold=True, background_color=C["dang"],color=C["white"],size_hint_x=1.4)
        if KF: bs.font_name=KF
        bs.bind(on_press=lambda b:press("⌫"))
        last.add_widget(sb); last.add_widget(sp_); last.add_widget(bs)
        key_area.add_widget(last)
    rebuild(); root.add_widget(key_area)
    btns=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(40),spacing=rp(10))
    btns.add_widget(Btn("취소",bg="surf2",fg="t2",bfs=11,wd=80,ht=36, cb=lambda *_:mv.dismiss()))
    def done(*_):
        txt=_compose(jamo); (on_done(txt) if on_done else None); mv.dismiss()
    btns.add_widget(Btn("완료",bg="pri",fg="white",bfs=11,wd=80,ht=36,cb=done))
    root.add_widget(btns)
    mv.add_widget(root); mv.open()

# 요구사항: 예비령 알림 팝업
class PrepAlertPopup(ModalView):
    def __init__(self, period_label, **kw):
        super().__init__(size_hint=(.8, .45), background_color=(0,0,0,0), overlay_color=(0,0,0,.7), auto_dismiss=False, **kw)
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        content = Card(bg="warn", r=20, orientation="vertical", padding=rp(30), spacing=rq(20))
        
        content.add_widget(L(f"[{period_label} 예비령]", bfs=30, bold=True, col="white", ha="center"))
        content.add_widget(L("시험 시작 5분전입니다.", bfs=26, bold=True, col="white", ha="center"))
        content.add_widget(L("모두 자신의 자리에 앉아 시험을 준비합니다.", bfs=22, bold=True, col="white", ha="center"))
        content.add_widget(L(f"현재 시각: {now_str}", bfs=18, bold=True, col="pri_l", ha="center"))
        
        btn = Btn("종료", bg="white", fg="dang", bfs=20, wd=200, ht=60, cb=lambda *_: self.dismiss())
        btn.pos_hint = {"center_x": .5}
        content.add_widget(btn)
        
        self.add_widget(content)
        # 1분(60초) 뒤 자동 종료
        Clock.schedule_once(lambda dt: self.dismiss(), 60)

def show_exit_popup():
    mv=ModalView(size_hint=(.6,None),height=rq(200), background_color=(0,0,0,0),overlay_color=(0,0,0,.55),auto_dismiss=True)
    card=Card(bg="surf",r=14,orientation="vertical", padding=rp(22),spacing=rq(16),size_hint=(1,1))
    card.add_widget(L("프로그램을 종료하시겠습니까?",bfs=16,bold=True, col="t1",ha="center",size_hint_y=None,height=rq(32)))
    btns=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(48),spacing=rp(12))
    btns.add_widget(Btn("취소",bg="surf2",fg="t2",bfs=14,wd=110,ht=44, cb=lambda *_:mv.dismiss()))
    btns.add_widget(Btn("종료",bg="dang",fg="white",bfs=14,wd=110,ht=44, cb=lambda *_: (App.get_running_app().stop(), Window.close())))
    card.add_widget(btns); mv.add_widget(card); mv.open()

class DashScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        self._last_min=-1; self._sched_status_lbls=[]
        Clock.schedule_once(lambda dt: self._init_and_build(), 0)
        Clock.schedule_interval(self._tick,1)

    def _init_and_build(self, *_):
        _init_scale(); self._build()

    def _build(self):
        self.clear_widgets()
        root=BoxLayout(orientation="vertical",spacing=0)

        top=Card(bg="pri",r=0,orientation="horizontal", size_hint_y=None,height=rq(64), padding=(rp(16),rq(6)),spacing=rp(10))
        info_str = f"{st.se or '시험 정보'} / {st.sg or ''} {st.sc or ''} / {datetime.datetime.now().strftime('%Y년 %m월 %d일')}"
        top.add_widget(L(info_str, bfs=22, bold=True, col="white", size_hint_x=1))
        top.add_widget(Btn("설정",bg="white",fg="pri",bfs=14,wd=100,ht=44, cb=lambda *_:self.manager.go_settings()))
        top.add_widget(Btn("종료",bg="dang",fg="white",bfs=14,wd=100,ht=44, cb=lambda *_:show_exit_popup()))
        root.add_widget(top)

        body=BoxLayout(orientation="horizontal", spacing=rp(8),padding=(rp(8),rq(7),rp(8),rq(8)))
        left=BoxLayout(orientation="vertical",spacing=rq(6),size_hint_x=.55)
        left.add_widget(self._sched_card()) 
        left.add_widget(self._attend_card()) 
        body.add_widget(left)
        right=BoxLayout(orientation="vertical",spacing=rq(6),size_hint_x=.45)
        right.add_widget(self._clock_card()) 
        right.add_widget(self._notice_card()) 
        body.add_widget(right)
        root.add_widget(body)
        self.add_widget(root)

    def _sched_card(self):
        card=Card(bg="surf",r=10,orientation="vertical", padding=rp(10),spacing=rq(4),size_hint_y=.55)
        card.add_widget(CtHdr("시험 시간표"))
        content_box = BoxLayout(orientation="vertical")
        if not st.sched:
            content_box.add_widget(L("설정에서 과목을 선택하세요", bfs=12,bold=True,col="warn",ha="center"))
            card.add_widget(content_box)
            return card
        table_container = BoxLayout(orientation="vertical", size_hint_y=None, spacing=rq(4))
        hdr=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(28))
        for t,sx in [("교시",.18),("시간",.32),("과목",.22),("상태",.28)]:
            hdr.add_widget(L(t,bfs=12,bold=True,col="pri",ha="center",size_hint_x=sx))
        table_container.add_widget(hdr); table_container.add_widget(Div())
        now=datetime.datetime.now()
        self._sched_status_lbls=[]
        total_rows_height = rq(28) + dp(2)
        for item in st.sched:
            ib=item["is_break"]; curr,rem,sd,ed=time_status(item["time"],now)
            rbg=("prep2" if ib else "amb2") if curr else ("prep" if ib else "surf2")
            if curr: st_txt="쉬는시간" if ib else "진행중"; st_col=C["warn"]
            elif ed and now>ed: st_txt="종료"; st_col=C["ok"]
            else: st_txt="대기중"; st_col=C["t3"]
            pd_fs = 13 if ib else 18
            sub_fs = 13 if ib else 20
            time_fs = 12 if ib else 16
            st_fs = 13 if ib else 16
            row_h = rq(44) if curr else rq(42)
            total_rows_height += row_h + rq(4)
            row=Card(bg=rbg,r=5,orientation="horizontal",size_hint_y=None,height=row_h)
            l_pd=L(("▶" if curr and not ib else "")+item["disp"],bfs=pd_fs,bold=True,col=C["pri"],ha="center",size_hint_x=.18)
            l_st=L(st_txt,bfs=st_fs,bold=True,col=st_col,ha="center",size_hint_x=.28)
            row.add_widget(l_pd)
            row.add_widget(L(item["time"].replace("~"," ~ "),bfs=time_fs,bold=True,col="t2",ha="center",size_hint_x=.32))
            row.add_widget(L(item.get("subject",""),bfs=sub_fs,bold=True,col="t1",ha="center",size_hint_x=.22))
            row.add_widget(l_st)
            table_container.add_widget(row)
            self._sched_status_lbls.append((item,l_st,l_pd))
        table_container.height = total_rows_height
        content_box.add_widget(Widget()) 
        content_box.add_widget(table_container)
        content_box.add_widget(Widget()) 
        card.add_widget(content_box)
        return card

    def _attend_card(self):
        card=Card(bg="surf",r=10,orientation="vertical", padding=rp(12),spacing=rq(8),size_hint_y=.45)
        card.add_widget(CtHdr("응시 현황"))
        total=st.st; na=len(st.absent); np_=(total-na) if total is not None else None
        stats=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(85),spacing=rp(10))
        for val,lbl_,bgc,fc in [(total,"재적",C["surf2"],C["t1"]),(np_,"응시",h2r("F0FDF4"),C["ok"]),(na,"결시",h2r("FFF5F5"),C["dang"])]:
            pill=Card(bg="surf",r=8,orientation="vertical",padding=rp(5)); pill.recolor(bgc)
            pill.add_widget(L(lbl_,bfs=14,bold=True,col="t3",ha="center"))
            pill.add_widget(L(str(val) if val is not None else "-", bfs=32,bold=True,col=fc,ha="center"))
            stats.add_widget(pill)
        card.add_widget(stats)
        card.add_widget(L("결시자 명단",bfs=15,bold=True,col="t2",size_hint_y=None,height=rq(26)))
        sv=ScrollView(do_scroll_x=False)
        box=GridLayout(cols=2, size_hint_y=None, spacing=rp(6))
        box.bind(minimum_height=box.setter("height"))
        if st.absent:
            tc2={"질병결시":C["pri"],"미인정결시":C["warn"],"출석인정결시":C["ok"],"기타결시":C["t3"]}
            for idx,a in enumerate(st.absent):
                bgc2=h2r("FFF5F5") if idx%2==0 else h2r("FEE2E2")
                row=Card(bg="surf",r=5,orientation="horizontal",size_hint_y=None,height=rq(38),padding=(rp(6),0))
                row.recolor(bgc2)
                row.add_widget(L(f"{a.get('num','')}번",bfs=15,bold=True,col="dang",ha="center",size_hint_x=None,width=rp(50)))
                row.add_widget(L(a.get('name','-'),bfs=15,bold=True,col="t1",ha="left",size_hint_x=None,width=rp(80)))
                row.add_widget(L(f"[{a.get('type','질병결시')}]",bfs=14,bold=True,col=tc2.get(a.get('type','질병결시'),C["t3"]),ha="left"))
                box.add_widget(row)
        else:
            empty_lbl = L("결시자 없음",bfs=15,bold=True,col="t3",ha="center",size_hint_y=None,height=rq(50))
            box.add_widget(empty_lbl)
        sv.add_widget(box); card.add_widget(sv)
        return card

    def _clock_card(self):
        card=Card(bg="clk",r=10,orientation="vertical", padding=rp(15),spacing=rq(2),size_hint_y=.55)
        upper = BoxLayout(orientation="vertical", size_hint_y=.7)
        upper.add_widget(L("현재 시각",bfs=20,bold=True,col=(.75,.88,1,1), ha="center",size_hint_y=None,height=rq(34)))
        self._lbl_clock=Label(text="00:00", font_size=sp(180), bold=True, color=(1,1,1,1), halign="center", valign="middle",
                              size_hint_y=1, outline_width=2, outline_color=(0.06,0.14,0.40,1))
        if KF: self._lbl_clock.font_name = KF
        self._lbl_clock.bind(size=self._lbl_clock.setter("text_size"))
        upper.add_widget(self._lbl_clock)
        card.add_widget(upper)

        sep=Widget(size_hint_y=None,height=dp(2))
        with sep.canvas: Color(.18,.31,.60,1); sr=Rectangle(pos=sep.pos,size=sep.size)
        sep.bind(pos=lambda w,_:setattr(sr,"pos",w.pos), size=lambda w,_:setattr(sr,"size",w.size))
        card.add_widget(sep)

        lower = BoxLayout(orientation="vertical", size_hint_y=.3, spacing=rq(2))
        self._lbl_remain=L("대기 중",bfs=32,bold=True,col="t3", ha="center")
        lower.add_widget(self._lbl_remain)
        card.add_widget(lower)
        return card

    def _notice_card(self):
        card=Card(bg="surf",r=10,orientation="vertical", padding=rp(12),spacing=rq(4),size_hint_y=.45)
        card.add_widget(CtHdr("시험 유의사항"))
        sv=ScrollView(do_scroll_x=False)
        box=BoxLayout(orientation="vertical",size_hint_y=None,spacing=0)
        box.bind(minimum_height=box.setter("height"))
        items=[NOTICES[i] for i in st.sn if i<len(NOTICES)]
        n = len(items) + len([l for l in st.sx.split("\n") if l.strip()])
        item_bfs = 17 if n <= 6 else 15
        row_h_val = 32 if n <= 6 else 26 
        for txt in items:
            row=BoxLayout(orientation="horizontal", size_hint_y=None,height=rq(row_h_val),spacing=rp(6))
            row.add_widget(L("•",bfs=item_bfs,bold=True,col="pri", ha="center",size_hint_x=None,width=rp(20)))
            row.add_widget(L(txt,bfs=item_bfs,bold=True,col="t1",ha="left"))
            box.add_widget(row)
        for line in [l for l in st.sx.split("\n") if l.strip()]:
            row2=BoxLayout(orientation="horizontal", size_hint_y=None,height=rq(row_h_val),spacing=rp(6))
            row2.add_widget(L("*",bfs=item_bfs,bold=True,col="warn", ha="center",size_hint_x=None,width=rp(20)))
            row2.add_widget(L(line.strip(),bfs=item_bfs,bold=True,col="warn",ha="left"))
            box.add_widget(row2)
        sv.add_widget(box); card.add_widget(sv)
        return card

    def _tick(self,dt):
        now=datetime.datetime.now()
        self._lbl_clock.text=now.strftime("%H:%M")
        
        # 교시 정보와 남은 시간 체크
        item,rem=get_curr(st.sched)
        if item and rem is not None:
            mm,ss2=divmod(rem,60)
            if item["is_break"]: 
                self._lbl_remain.text=f"{item['period']}교시 시작까지 {mm:02d}:{ss2:02d}"
                self._lbl_remain.color=(.99,.82,.20,1)
                
                # 요구사항: 시험 시작 5분 전(300초 전) 알림 (오차범위 고려하여 299~300초 사이 체크)
                if 295 <= rem <= 300:
                    period_key = f"P{item['period']}"
                    if period_key not in _notified_periods:
                        PrepAlertPopup(f"{item['period']}교시").open()
                        _notified_periods.add(period_key)
            else: 
                self._lbl_remain.text=f"{item['label']} 종료까지 {mm:02d}:{ss2:02d}"
                self._lbl_remain.color=(.58,.76,.99,1)
        else: 
            self._lbl_remain.text="대기 중"; self._lbl_remain.color=C["t3"]
            
        if now.hour*60+now.minute != self._last_min: 
            self._last_min=now.hour*60+now.minute
            self._upd_sched(now)

    def _upd_sched(self,now):
        for item,lbl_st,lbl_pd in self._sched_status_lbls:
            ib=item["is_break"]; curr,rem,sd,ed=time_status(item["time"],now)
            if curr: st_txt="쉬는시간" if ib else "진행중"; st_col=C["warn"]
            elif ed and now>ed: st_txt="종료"; st_col=C["ok"]
            else: st_txt="대기중"; st_col=C["t3"]
            lbl_st.text=st_txt; lbl_st.color=st_col

    def refresh(self):
        _init_scale(); self._build()

class SettingsPopup(ModalView):
    def __init__(self, dash_ref, **kw):
        super().__init__(size_hint=(.70, .84), pos_hint={"center_x": .5, "center_y": .5}, background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0,.55), auto_dismiss=False, **kw)
        self._dash, self._tab = dash_ref, "basic"; self._build()

    def _build(self):
        self.clear_widgets(); outer = Card(bg="surf", r=14, orientation="vertical", size_hint=(1, 1))
        hdr = Card(bg="pri", r=0, orientation="horizontal", size_hint_y=None, height=rq(52), padding=(rp(14), rq(6)), spacing=rp(10))
        hdr.add_widget(L("시험 설정", bfs=16, bold=True, col="white")); hdr.add_widget(Widget())
        hdr.add_widget(Btn("적용", bg="white", fg="pri", bfs=13, wd=80, ht=38, cb=self._apply))
        hdr.add_widget(Btn("닫기", bg="surf2", fg="t2", bfs=13, wd=70, ht=38, cb=lambda *_: self.dismiss()))
        outer.add_widget(hdr)
        tb = BoxLayout(orientation="horizontal", size_hint_y=None, height=rq(44)); self._tbs = {}
        for key, name in [("basic","기본정보"), ("sched","시간표"), ("notice","유의사항"), ("absent","결시자")]:
            on = (key == self._tab); b = Button(text=name, font_size=fs(13), bold=True, background_normal="", background_color=C["pri_l"] if on else C["surf2"], color=C["pri"] if on else C["t3"])
            if KF: b.font_name = KF
            b.bind(on_press=lambda btn, k=key: self._sw(k)); tb.add_widget(b); self._tbs[key] = b
        outer.add_widget(tb); outer.add_widget(Div()); self._tbody = BoxLayout(orientation="vertical")
        outer.add_widget(self._tbody); self.add_widget(outer); self._render()

    def _sw(self,key):
        self._tab=key
        for k,b in self._tbs.items(): (setattr(b, "background_color", C["pri_l"]) if k==key else setattr(b, "background_color", C["surf2"])); (setattr(b, "color", C["pri"]) if k==key else setattr(b, "color", C["t3"]))
        self._render()

    def _render(self): self._tbody.clear_widgets(); getattr(self,f"_t_{self._tab}")()

    def _t_basic(self):
        sv=ScrollView(do_scroll_x=False); b=BoxLayout(orientation="vertical",size_hint_y=None,spacing=rq(9),padding=rp(12)); b.bind(minimum_height=b.setter("height"))
        b.add_widget(SecHdr("시험 종류")); b.add_widget(ChipGroup(EXAM_TYPES,st.se,lambda v:setattr(st,"se",v),cols=2)); b.add_widget(Div())
        b.add_widget(SecHdr("학년")); b.add_widget(ChipGroup(GRADES,st.sg,lambda v:setattr(st,"sg",v),cols=3)); b.add_widget(Div())
        b.add_widget(SecHdr("반")); b.add_widget(ChipGroup(CLASSES,st.sc,lambda v:setattr(st,"sc",v),cols=5)); b.add_widget(Div())
        b.add_widget(SecHdr("재적 인원")); b.add_widget(ChipGroup([f"{n}명" for n in range(15,43)], f"{st.st}명" if st.st else None, lambda v:setattr(st,"st",int(v.replace("명",""))),cols=7))
        sv.add_widget(b); self._tbody.add_widget(sv)

    def _t_sched(self):
        sv=ScrollView(do_scroll_x=False); b=BoxLayout(orientation="vertical",size_hint_y=None,spacing=rq(10),padding=rp(12)); b.bind(minimum_height=b.setter("height"))
        b.add_widget(SecHdr(f"교시별 과목 선택")); n_cols=5; chip_h=rq(44)*2+rp(5)
        for i in range(N):
            cur=st.ss[i]; card_h=rq(66)+chip_h
            pc=Card(bg="surf",r=8,orientation="vertical",size_hint_y=None,height=card_h,padding=rp(10),spacing=rq(6))
            ph=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(28)); ph.add_widget(L(f"{i+1}교시",bfs=15,bold=True,col="pri",width=rp(70),size_hint_x=None))
            cur_lbl=L(f"선택: {cur}" if cur else "과목 선택",bfs=13,bold=True,col="t1" if cur else "t3"); ph.add_widget(cur_lbl); pc.add_widget(ph)
            sg=GridLayout(cols=n_cols,size_hint_y=None,height=chip_h,spacing=rp(5)); cm={}
            def mk_s(idx,val,m,l):
                def _sel(b_):
                    st.ss[idx]=val; [setattr(cc, "background_color", C["surf2"]) for cc in m.values()]; [setattr(cc, "color", C["t2"]) for cc in m.values()]
                    b_.background_color=C["pri"]; b_.color=C["white"]; l.text=f"선택: {val}"; l.color=C["t1"]
                return _sel
            for s in SUBJECTS:
                c=Button(text=s,font_size=fs(13),bold=True,background_normal="", background_color=C["pri"] if cur==s else C["surf2"], color=C["white"] if cur==s else C["t2"], size_hint_x=1,height=rq(44),size_hint_y=None)
                if KF: c.font_name=KF
                c.bind(on_press=mk_s(i,s,cm,cur_lbl)); sg.add_widget(c); cm[s]=c
            pc.add_widget(sg); b.add_widget(pc)
        sv.add_widget(b); self._tbody.add_widget(sv)

    def _t_notice(self):
        sv=ScrollView(do_scroll_x=False); b=BoxLayout(orientation="vertical",size_hint_y=None,spacing=rq(7),padding=rp(12)); b.bind(minimum_height=b.setter("height"))
        b.add_widget(SecHdr("표시 항목 체크"))
        for i,txt in enumerate(NOTICES):
            on=i in st.sn; row=Card(bg="pri_l" if on else "surf",r=7,orientation="horizontal",size_hint_y=None,height=rq(52),padding=rp(10))
            row.add_widget(L(txt,bfs=13,bold=True,col="pri" if on else "t2"))
            chk=Button(text="✓" if on else " ",font_size=fs(14),bold=True,background_normal="", background_color=C["pri"] if on else C["surf2"], color=C["white"] if on else C["t3"], size_hint=(None,None),width=rp(36),height=rq(36))
            if KF: chk.font_name=KF
            def _tog(b_, idx=i, r=row, c=chk):
                (st.sn.remove(idx) if idx in st.sn else st.sn.append(idx)); on2=idx in st.sn
                r._c.rgba=C["pri_l"] if on2 else C["surf"]; c.background_color=C["pri"] if on2 else C["surf2"]; c.text="✓" if on2 else " "
            chk.bind(on_press=_tog); row.add_widget(chk); b.add_widget(row)
        b.add_widget(SecHdr("추가 유의사항"))
        self._notice_ti=TextInput(text=st.sx,hint_text="터치입력",multiline=True,font_size=fs(13),readonly=True,size_hint_y=None,height=rq(80),background_color=C["surf"])
        if KF: self._notice_ti.font_name=KF
        self._notice_ti.bind(on_touch_down=self._on_notice_ti_touch); b.add_widget(self._notice_ti)
        sv.add_widget(b); self._tbody.add_widget(sv)

    def _on_notice_ti_touch(self, w, t):
        if not w.collide_point(*t.pos): return False
        show_kor_keyboard(w.text, title="추가 유의사항", on_done=lambda v:(setattr(st,"sx",v), setattr(w,"text",v)))
        return True

    def _t_absent(self):
        sv=ScrollView(do_scroll_x=False); b=BoxLayout(orientation="vertical",size_hint_y=None,spacing=rq(8),padding=rp(12)); b.bind(minimum_height=b.setter("height"))
        b.add_widget(SecHdr("결시자 추가")); ATYPES=["질병결시","미인정결시","출석인정결시","기타결시"]; self._atype=[ATYPES[0]]
        type_row=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(42),spacing=rp(6)); type_row.add_widget(L("종류:",bfs=13,bold=True,width=rp(50),size_hint_x=None))
        tchips=[]
        def mk_ts(v,cs):
            def _s(b_):
                self._atype[0]=v
                for c in cs: (setattr(c,"background_color",C["pri"]) if c.text==v else setattr(c,"background_color",C["surf2"])); (setattr(c,"color",C["white"]) if c.text==v else setattr(c,"color",C["t2"]))
            return _s
        for t in ATYPES:
            c=Button(text=t,font_size=fs(12),bold=True,background_normal="", background_color=C["pri"] if t==self._atype[0] else C["surf2"], color=C["white"] if t==self._atype[0] else C["t2"], size_hint=(None,None),width=rp(85),height=rq(38))
            if KF: c.font_name=KF
            tchips.append(c); type_row.add_widget(c); c.bind(on_press=mk_ts(c.text,tchips))
        b.add_widget(type_row); b.add_widget(SecHdr("번호/이름")); self._sel_num=[None]
        sel_lbl=L("번호 선택",bfs=13,bold=True,col="t3",height=rq(24),size_hint_y=None); b.add_widget(sel_lbl)
        num_grid=GridLayout(cols=10,size_hint_y=None,height=rq(130),spacing=rp(4)); num_chips={}
        used={a.get("num") for a in st.absent}
        def mk_ns(v,cs,l):
            def _s(b_):
                self._sel_num[0]=v
                for nv,nc in cs.items(): (setattr(nc,"background_color",C["dang"]) if nv in used else setattr(nc,"background_color",C["surf2"]))
                b_.background_color=C["pri"]; l.text=f"선택: {v}번"; l.color=C["pri"]
            return _s
        for n in [str(x) for x in range(1, (st.st or 30)+1)]:
            c=Button(text=n,font_size=fs(12),bold=True,background_normal="", background_color=C["dang"] if n in used else C["surf2"], color=C["t1"], size_hint_y=None,height=rq(38))
            if KF: c.font_name=KF
            c.bind(on_press=mk_ns(n,num_chips,sel_lbl)); num_chips[n]=c; num_grid.add_widget(c)
        b.add_widget(num_grid); nm_row=BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(48),spacing=rp(8))
        self._nm=TextInput(hint_text="이름",multiline=False,font_size=fs(14),readonly=True,background_color=C["surf"])
        if KF: self._nm.font_name=KF
        self._nm.bind(on_touch_down=lambda w,t:(show_kor_keyboard(w.text, "이름", lambda v:setattr(w,"text",v)) if w.collide_point(*t.pos) else None))
        def add_a(*_):
            if not self._sel_num[0]: return
            st.absent.append({"num":self._sel_num[0],"name":self._nm.text.strip(),"type":self._atype[0]})
            self._sel_num[0]=None; self._nm.text=""; self._draw_ab(); self._render()
        nm_row.add_widget(self._nm); nm_row.add_widget(Btn("추가",bg="pri",wd=80,ht=44,cb=add_a)); b.add_widget(nm_row)
        self._ab_box=BoxLayout(orientation="vertical",size_hint_y=None,spacing=rq(3)); self._ab_box.bind(minimum_height=self._ab_box.setter("height"))
        self._draw_ab(); b.add_widget(self._ab_box); sv.add_widget(b); self._tbody.add_widget(sv)

    def _draw_ab(self):
        self._ab_box.clear_widgets()
        tc={"질병결시":C["pri"],"미인정결시":C["warn"],"출석인정결시":C["ok"],"기타결시":C["t3"]}
        for idx,a in enumerate(st.absent):
            row=Card(bg="surf2",r=4,size_hint_y=None,height=rq(36),padding=(rp(5),0))
            row.add_widget(L(f"{a['num']}번 {a['name']}",bfs=13,bold=True))
            row.add_widget(L(f"[{a['type']}]",bfs=12,col=tc.get(a['type'],C["t3"]),ha="right"))
            db=Button(text="✕",size_hint_x=None,width=rp(30),background_normal="",background_color=(0,0,0,0),color=C["dang"],bold=True)
            db.bind(on_press=lambda b,i=idx:(st.absent.pop(i), self._draw_ab())); row.add_widget(db); self._ab_box.add_widget(row)

    def _apply(self, *_):
        _notified_periods.clear()
        st.sched = make_sched([s if s else "" for s in st.ss[:N]]) if any(st.ss) else []
        self._dash.refresh(); self.dismiss()

def SecHdr(text):
    row = BoxLayout(orientation="horizontal",size_hint_y=None,height=rq(34),spacing=rp(6))
    bar = Widget(size_hint=(None,None),width=rp(6),height=rq(22))
    with bar.canvas:
        Color(*C["pri"]); rc = Rectangle(pos=bar.pos,size=bar.size)
    bar.bind(pos=lambda w,_:setattr(rc,"pos",w.pos),
             size=lambda w,_:setattr(rc,"size",w.size))
    row.add_widget(bar); row.add_widget(L(text,bfs=13,bold=True,col="t1"))
    return row

class SM(ScreenManager):
    def go_settings(self): SettingsPopup(dash_ref=self.get_screen("dash")).open()

class ExamApp(App):
    def build(self):
        Window.clearcolor=(.91,.93,1.0,1); sm=SM(); sm.add_widget(DashScreen(name="dash")); return sm
    def on_start(self):
        def _li(dt):
            _init_scale()
            if IS_ANDROID:
                try:
                    from jnius import autoclass; View = autoclass("android.view.View"); activity = autoclass("org.kivy.android.PythonActivity").mActivity
                    activity.getWindow().getDecorView().setSystemUiVisibility(0x00000002 | 0x00000004 | 0x00001000)
                except: pass
            else: Window.maximize()
            Clock.schedule_once(lambda d2: self.root.get_screen("dash")._build(), 0.2)
        Clock.schedule_once(_li, 0.1)
    def get_application_name(self): return "시험도우미"

if __name__ == "__main__":
    ExamApp().run()
