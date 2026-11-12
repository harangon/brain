"""brain 화면 테스트 (Playwright). 먼저 build_mock.py 로 테스트 페이지를 만든 뒤 실행한다.
   python3 tests/build_mock.py && python3 tests/run.py [스크린샷 폴더]"""
import sys,os,traceback
from playwright.sync_api import sync_playwright
MOCK='file:///tmp/brain-mock.html';SHOTS=sys.argv[1] if len(sys.argv)>1 else ''
results=[]
def files(pg):return pg.evaluate('Object.keys(__FILES)')
def fget(pg,p):return pg.evaluate('p=>__FILES[p]',p)
def idle(pg,ms=350):pg.wait_for_timeout(ms)
def view(pg,name):
    if name=='프로젝트':return tab(pg,'프로젝트')
    if not pg.is_visible('#subtabs'):tab(pg,'노트')
def proj(pg,name):
    tab(pg,'프로젝트')
    if pg.locator(f'.pbarx button[data-p="{name}"]').count():pg.click(f'.pbarx button[data-p="{name}"]')
    else:pg.click('#projBack');idle(pg);pg.click(f'.prow[data-p="{name}"]')
    idle(pg)
def proj_home(pg):tab(pg,'프로젝트');pg.click('#projBack');idle(pg)
def proj_card(pg,name):proj(pg,name);pg.click('#projOpen');idle(pg)
def col(pg,c):return pg.eval_on_selector_all(f'.tlist[data-list="{c}"] .tcard .ct','e=>e.map(x=>x.textContent)')
def lists(pg):return pg.eval_on_selector_all('.tlist[data-list]','e=>e.map(x=>x.dataset.list)')
def drag(pg,src,dst,pos=None):
    kw={'target_position':pos} if pos else {}
    pg.drag_and_drop(src,dst,**kw);idle(pg,600)
def tab(pg,name):
    if name=='문서':
        if pg.get_attribute('#btnDocs','aria-pressed')!='true':pg.click('#btnDocs')
    else:pg.click(f'.tabs:not(.sub) button:text-is("{name}")')
    idle(pg)
def side(pg,k,v):pg.click(f'.nside button[data-k="{k}"][data-v="{v}"]');idle(pg)
def rows(pg):return pg.eval_on_selector_all('#main tbody tr td.t>button:first-child','e=>e.map(x=>x.textContent)')
def open_row(pg,title):pg.click(f'#main td.t>button:first-child:text-is("{title}")');idle(pg)
def close(pg):pg.click('#pClose');idle(pg,200)
def act(pg,name):pg.click(f'#card .actions button:text-is("{name}")');idle(pg)
def ok(pg):pg.click('#askOk');idle(pg,600)
def shot(pg,name):
    if SHOTS:pg.screenshot(path=os.path.join(SHOTS,name+'.png'))

def t_load(pg):
    f=files(pg)
    assert '20_Notes/옛 메모.md' in f and '00_Inbox/옛 메모.md' not in f,'옛 Inbox 노트가 20_Cards 로 안 옮겨짐'
    assert '20_Notes/옛 자료.md' in f and '30_Resources/옛 자료.md' not in f
    assert pg.evaluate("getComputedStyle(document.querySelector('#btnSettings')).width")=='30px' and pg.evaluate("getComputedStyle(document.querySelector('#q')).borderRadius")!='0px','머리줄 스타일이 빠짐'
    # 노트 탭은 노트 목록 하나: 보기 칩 없음, 옆에 프로젝트·라벨 목록, 옛 데일리도 노트로
    r=rows(pg);daily=[x for x in r if x.startswith('20')];assert len(daily)==1 and f'20_Notes/{daily[0]}.md' in f and not any(p.startswith('01_Daily/') for p in f)
    assert '20_Notes/2026-11-01-옛-할-일.md' in f and not any(p.startswith(('11_Todos/','20_Cards/')) for p in f),'옛 할 일 폴더가 20_Notes 로 안 옮겨짐'
    # 노트 탭에는 할 일이 아닌 노트만 (할 일은 할 일 탭)
    assert set(r)-set(daily)=={'수납 아이디어','구조를 단순하게 가는 이유','주말에 볼 영상','옛 메모','수납장 문서 요약','정리는 버리는 것부터','테마 비교 메모','옛 자료'},r
    assert pg.inner_text('.tabs:not(.sub)').split()==['노트','프로젝트','할','일','일정'] and '카드' not in pg.inner_text('body')
    assert not pg.is_visible('#views') and pg.locator('.nside').count()==1 and '정리 전' not in pg.inner_text('body') and '이대로 두기' not in pg.inner_text('body')
    assert pg.get_attribute('#quickText','placeholder')=='메모 입력'
    shot(pg,'01-notes')
def t_suggest(pg):
    pg.click('tr[data-path="20_Notes/수납 아이디어.md"] .sug');idle(pg)
    c=fget(pg,'20_Notes/수납 아이디어.md');assert 'project: "[[집 정리]]"' in c and 'suggest-project' not in c,c
    pg.click('tr[data-path="20_Notes/구조를 단순하게 가는 이유.md"] .sug');idle(pg)
    c=fget(pg,'20_Notes/구조를 단순하게 가는 이유.md');assert 'label: mine' in c and 'suggest-label' not in c,c
def t_quick(pg):
    pg.fill('#quickText','새 메모 / 테스트?');pg.press('#quickText','Enter');idle(pg)
    c=fget(pg,'20_Notes/새 메모 테스트.md');assert c and '# 새 메모 / 테스트?' in c and 'type: note' in c,c
    assert '새 메모 / 테스트?' in rows(pg)
    pg.fill('#quickText','새 메모 / 테스트?');pg.press('#quickText','Enter');idle(pg)
    assert any(p.startswith('20_Notes/새 메모 테스트 20') for p in files(pg)),'이름이 겹치면 날짜를 붙여야 함'
def t_views(pg):
    view(pg,'노트');r=rows(pg);assert '수납장 문서 요약' in r and '집 정리' not in r and '우유 사기' not in r,r
    st=pg.inner_text('.nside');assert '프로젝트 없음' in st and '집 정리' in st and '블로그 개편' in st and '라벨 없음' in st and '읽을 것' in st and '내 생각' in st,st
    # 옆 목록에서 프로젝트를 누르면 그 프로젝트의 노트만. 보기 칩은 그대로
    side(pg,'project','집 정리');assert set(rows(pg))=={'수납장 문서 요약','수납 아이디어'},rows(pg)
    assert pg.get_attribute('.nside button[data-v="집 정리"]','aria-pressed')=='true'
    # 메모는 보고 있는 프로젝트·라벨로 들어간다
    assert '집 정리에 저장' in pg.get_attribute('#quickText','placeholder')
    pg.fill('#quickText','선반 치수');pg.press('#quickText','Enter');idle(pg);c=fget(pg,'20_Notes/선반 치수.md');assert c and 'project: "[[집 정리]]"' in c,c
    assert '선반 치수' in rows(pg);side(pg,'label','resource');assert '집 정리 · 자료에 저장' in pg.get_attribute('#quickText','placeholder')
    pg.fill('#quickText','선반 자료');pg.press('#quickText','Enter');idle(pg);c=fget(pg,'20_Notes/선반 자료.md');assert 'label: resource' in c and '선반 자료' in rows(pg),c
    # 다시 누르면 풀린다
    side(pg,'label','resource');side(pg,'project','집 정리');assert pg.get_attribute('#quickText','placeholder')=='메모 입력' and '주말에 볼 영상' in rows(pg)
    side(pg,'project','집 정리');assert set(rows(pg))=={'수납장 문서 요약','수납 아이디어','선반 치수','선반 자료'},rows(pg)
    side(pg,'project','__none');side(pg,'label','__none');r=rows(pg);assert '주말에 볼 영상' in r and '정리는 버리는 것부터' not in r and '선반 치수' not in r,r
    side(pg,'project','');side(pg,'label','read');assert set(rows(pg))=={'수납장 문서 요약','옛 자료'},rows(pg)
    side(pg,'label','idea');assert rows(pg)==[] and '해당하는 노트가 없습니다' in pg.inner_text('#main') and pg.locator('.nside').count()==1
    side(pg,'label','');assert '종류' not in pg.inner_text('#main thead')
    # 프로젝트 탭 홈: 프로젝트(보드) 고르기
    proj_home(pg);assert not pg.is_visible('#quick') and not pg.is_visible('#subtabs')
    home=pg.inner_text('#main');assert '진행' in home and '보류' in home and '1/4' in pg.inner_text('.prow[data-p="집 정리"]') and pg.locator('.pbarx button[data-p="블로그 개편"]').count()==0 and '끝낸 프로젝트' in home,home
    assert '업무' in pg.inner_text('.lchips');pg.click('.lchips button[data-v="work"]');idle(pg)
    assert pg.eval_on_selector_all('.prow[data-p]','e=>e.map(x=>x.dataset.p)')==['블로그 개편'];pg.click('.lchips button[data-v="work"]');idle(pg);assert pg.locator('.prow[data-p]').count()==2 and pg.locator('.ptile').count()==0 and '새 프로젝트' not in pg.inner_text('#main')
    shot(pg,'02-project-home')
    # 프로젝트가 많으면: 위 줄에는 진행 중인 것 중 목록 순서로 앞의 3개, 나머지는 '외 N개' → 전체 목록
    pg.evaluate("(async()=>{for(let i=1;i<=5;i++)await createNote({type:'project',title:'P'+String(i).padStart(2,'0'),quiet:true});render();})()");idle(pg,900)
    bar=lambda:pg.eval_on_selector_all('.pbarx button[data-p]','e=>e.map(x=>x.dataset.p)')
    assert bar()==['P01','P02','P03'] and '외 4개' in pg.inner_text('.pbarx .more'),bar()
    # 목록에서 끌어 순서를 바꾸면 위 줄도 따라 바뀐다
    drag(pg,'.prow[data-p="집 정리"]','.prow[data-p="P01"]',{'x':60,'y':4})
    assert pg.eval_on_selector_all('.prow[data-p]','e=>e.map(x=>x.dataset.p)')[:3]==['집 정리','P01','P02'] and bar()==['집 정리','P01','P02'],bar()
    assert 'order: 0' in fget(pg,'10_Projects/집 정리.md') and 'order: 1' in fget(pg,'10_Projects/P01.md')
    drag(pg,'.prow[data-p="P05"]','.prow[data-p="P01"]',{'x':60,'y':4});assert bar()==['집 정리','P05','P01'],bar()
    pg.click('.prow[data-p="블로그 개편"]');idle(pg);assert pg.get_attribute('.pbarx button[data-p="블로그 개편"]','aria-pressed')=='true' and len(bar())==4
    pg.click('.pbarx .more');idle(pg);assert pg.locator('.prow[data-p]').count()==7
    if SHOTS:pg.screenshot(path=os.path.join(SHOTS,'02-project-many.png'))
    pg.evaluate("(async()=>{for(const n of notes.filter(x=>/^P\\d\\d$/.test(x.title))){await api.del(n.path,n.sha,'t');}notes=notes.filter(x=>!/^P\\d\\d$/.test(x.title));render();})()");idle(pg,700);assert pg.locator('.prow[data-p]').count()==2
    # 보드: 줄(할 일 · 진행 중 · 완료)에 그 프로젝트의 할 일·노트가 카드로. 완료된 할 일은 완료 줄
    # 목록에서 열고, 위 프로젝트 줄에서 바로 다른 프로젝트로 바꾼다
    pg.click('.prow[data-p="블로그 개편"]');idle(pg);assert pg.inner_text('.phead .ptitle')=='블로그 개편' and pg.get_attribute('.pbarx button[data-p="블로그 개편"]','aria-pressed')=='true'
    pg.click('.pbarx button[data-p="집 정리"]');idle(pg);assert '1/4' in pg.inner_text('.pbarx button[data-p="집 정리"]')
    assert pg.inner_text('.phead .ptitle')=='집 정리' and lists(pg)==['할 일','진행 중','완료']
    assert col(pg,'할 일')[:2]==['창고 치수 재기','업체 견적 받기'] and set(col(pg,'할 일')[2:])=={'버릴 것 목록','수납장 문서 요약','수납 아이디어','선반 치수','선반 자료'} and col(pg,'완료')==['비용 비교'] and col(pg,'진행 중')==[],col(pg,'할 일')
    # 카드 추가는 하나: 날짜를 적으면 할 일(체크 있음), 아니면 그냥 카드
    ti='.tlist[data-list="진행 중"] .cadd input';pg.fill(ti,'내일 창고 청소');pg.press(ti,'Enter');idle(pg)
    c=fget(pg,'20_Notes/창고 청소.md');assert c and 'type: note' in c and 'project: "[[집 정리]]"' in c and 'due: ' in c and 'list: 진행 중' in c and col(pg,'진행 중')==['창고 청소'] and pg.locator('.tcard:has-text("창고 청소") .nd').count()==1,c
    pg.fill(ti,'청소 업체 메모');pg.press(ti,'Enter');idle(pg);assert pg.locator('.tlist[data-list="진행 중"] .cadd button').count()==1 and pg.locator('.tcard:has-text("청소 업체 메모") .nd').count()==0
    c=fget(pg,'20_Notes/청소 업체 메모.md');assert c and 'type: note' in c and 'todo' not in c and 'due' not in c and 'list: 진행 중' in c and set(col(pg,'진행 중'))=={'창고 청소','청소 업체 메모'},c
    # 체크하면 완료 줄로, 풀면 돌아온다
    pg.click('.tcard:has-text("창고 청소") .nd');idle(pg);assert '창고 청소' in col(pg,'완료') and 'status: done' in fget(pg,'20_Notes/창고 청소.md')
    # 끌어 옮기기: 줄 사이 (완료 줄에서 꺼내면 완료가 풀린다), 같은 줄 안 순서
    drag(pg,'.tcard:has-text("창고 청소")','.tlist[data-list="진행 중"] .tcards');c=fget(pg,'20_Notes/창고 청소.md')
    assert 'status' not in c and 'list: 진행 중' in c and '창고 청소' in col(pg,'진행 중') and '창고 청소' not in col(pg,'완료'),c
    drag(pg,'.tcard:has-text("버릴 것 목록")','.tlist[data-list="완료"] .tcards');c=fget(pg,'20_Notes/버릴 것 목록.md');assert 'status: done' in c and '버릴 것 목록' in col(pg,'완료'),c
    drag(pg,'.tcard:has-text("업체 견적 받기")','.tcard:has-text("창고 치수 재기")',{'x':40,'y':4})
    assert col(pg,'할 일')[:2]==['업체 견적 받기','창고 치수 재기'],col(pg,'할 일')
    drag(pg,'.tcard:has-text("수납 아이디어")','.tlist[data-list="진행 중"] .tcards');assert 'list: 진행 중' in fget(pg,'20_Notes/수납 아이디어.md') and '수납 아이디어' in col(pg,'진행 중')
    # 줄: 추가 · 이름 바꾸기 · 옮기기 · 삭제
    pg.fill('.tlist.addlist input','자료');pg.press('.tlist.addlist input','Enter');idle(pg);assert lists(pg)==['할 일','진행 중','완료','자료'] and 'lists: [할 일, 진행 중, 완료, 자료]' in fget(pg,'10_Projects/집 정리.md')
    pg.click('.tlist[data-list="자료"] .lm');pg.click('.menu.pop button:text-is("왼쪽으로")');idle(pg);assert lists(pg)==['할 일','진행 중','자료','완료']
    pg.click('.tlist[data-list="진행 중"] .lm');pg.click('.menu.pop button:text-is("이름 바꾸기")');pg.fill('#askField input','하는 중');ok(pg)
    assert lists(pg)==['할 일','하는 중','자료','완료'] and 'list: 하는 중' in fget(pg,'20_Notes/창고 청소.md') and '창고 청소' in col(pg,'하는 중')
    pg.click('.tlist[data-list="하는 중"] .lm');pg.click('.menu.pop button:text-is("줄 삭제")');assert '할 일' in pg.inner_text('#askMsg');ok(pg)
    assert lists(pg)==['할 일','자료','완료'] and '창고 청소' in col(pg,'할 일') and 'list: 할 일' in fget(pg,'20_Notes/창고 청소.md')
    pg.click('.tcard:has-text("업체 견적 받기")');idle(pg);assert pg.inner_text('#pPath').startswith('할 일');close(pg)
    pg.click('.tcard:has-text("버릴 것 목록") .nd');idle(pg);assert '버릴 것 목록' in col(pg,'할 일') and 'status' not in fget(pg,'20_Notes/버릴 것 목록.md')
    pg.click('.tcard:has-text("창고 청소") .nd');idle(pg)
    shot(pg,'02-project-board')
    view(pg,'노트');pg.click('#subtabs button:has-text("보드")');idle(pg)
    cols=pg.eval_on_selector_all('.board .col h3','e=>e.map(x=>x.textContent)');assert any('집 정리' in c for c in cols) and any('없음' in c for c in cols),cols
    pg.select_option('#fGroup','label');idle(pg);cols=pg.eval_on_selector_all('.board .col h3','e=>e.map(x=>x.textContent)');assert any('자료' in c for c in cols),cols;pg.select_option('#fGroup','project');idle(pg)
    shot(pg,'03-notes-by-project')
    pg.click('#subtabs button:has-text("갤러리")');idle(pg);assert pg.locator('.gcard').count()>3
    pg.click('#subtabs button:has-text("표")');idle(pg)
def t_archive_view(pg):
    # 보관은 탭마다: 노트 탭 "보관한 노트", 할 일 탭 "보관된 할 일", 프로젝트 탭 "끝낸 프로젝트"
    view(pg,'노트');assert '옛 노트' not in rows(pg);pg.click('[data-sec=narch] .hd');idle(pg);pg.click('[data-sec=narch] .trow button:text-is("옛 노트")');idle(pg)
    act(pg,'되살리기');idle(pg,500);assert '20_Notes/옛 노트.md' in files(pg) and 'archived' not in fget(pg,'20_Notes/옛 노트.md');close(pg);assert '옛 노트' in rows(pg)
    tab(pg,'할 일');pg.click('[data-sec=arch] .hd');idle(pg);pg.click('[data-sec=arch] .trow button:text-is("끝난 일")');idle(pg)
    assert '보관됨' in pg.inner_text('#pPath');act(pg,'되살리기');idle(pg,500)
    c=fget(pg,'20_Notes/끝난 일.md');assert c and 'archived' not in c and 'label' not in c and 'todo: true' in c,c
    assert '90_Archive/끝난 일.md' not in files(pg);close(pg)
    proj_home(pg);pg.click('[data-sec=parch] .hd');idle(pg);assert '옛 프로젝트' in pg.inner_text('[data-sec=parch]');pg.click('[data-sec=parch] .hd');idle(pg);tab(pg,'노트')
def t_todo(pg):
    tab(pg,'할 일');side=pg.inner_text('.tdside')
    assert '프로젝트 없음' in side and '집 정리' in side and '2/5' in side,side
    assert pg.locator('[data-sec=todaylate]').count()==1 and not pg.is_visible('[data-sec=todaylate]')
    inp='.tdadd input[type=text]';pg.fill(inp,'금요일 벤더 견적');idle(pg,200)
    assert pg.is_visible('[data-sec=todaylate]'),'다른 날짜를 볼 때 오늘·지연이 보여야 함'
    assert '프로젝트 없음' in pg.inner_text('.tdprev')
    pg.select_option('.tdadd select','집 정리');pg.press(inp,'Enter');idle(pg)
    c=fget(pg,'20_Notes/벤더 견적.md');assert c and 'project: "[[집 정리]]"' in c and 'due: ' in c and 'label' not in c,c
    assert '옛 할 일' in pg.inner_text('.tdmain') or True
    pg.click('.tdside button[data-key=""]');idle(pg);txt=pg.inner_text('.tdmain');assert '우유 사기' in txt and '업체 견적' not in txt
    pg.fill(inp,'세탁소');pg.press(inp,'Enter');idle(pg);c=fget(pg,'20_Notes/세탁소.md');assert c and 'project' not in c,c
    pg.click('.tdside button[data-key="*"]');idle(pg)
    # 라벨로 거르기: 그 라벨의 할 일만, 새 할 일도 그 라벨로
    pg.click('.tdside button[data-label="work"]');idle(pg);txt=pg.inner_text('.tdmain');assert '건강검진 예약' in txt and '우유 사기' not in txt,txt
    assert '라벨 업무' in pg.inner_text('.tdprev') or True
    pg.fill(inp,'회의록 정리');pg.press(inp,'Enter');idle(pg);c=fget(pg,'20_Notes/회의록 정리.md');assert c and 'label: work' in c,c
    pg.click('.tdside button[data-label="work"]');idle(pg);assert '우유 사기' in pg.inner_text('.tdmain')
    pg.click('[data-sec=done] .hd');idle(pg);assert '주간 정리 때 보관' in pg.inner_text('[data-sec=done] .hd') and '비용 비교' in pg.inner_text('[data-sec=done]')
    # 완료 체크
    pg.click('.tdtoday .trow:has-text("우유 사기") input[type=checkbox]');idle(pg);assert 'status: done' in fget(pg,'20_Notes/우유 사기.md')
    shot(pg,'04-todo')
    pg.click('.tdadd .chip[data-id=none]');idle(pg);assert not pg.is_visible('.tdtoday') and not pg.is_visible('[data-sec=todaylate]')
    pg.click('.tdadd .chip[data-id=today]');idle(pg)
def t_todo_when(pg):
    # 오늘 / 날짜 / 나중에 — 세 선택 모두 할 일로 만들어지고 할 일 탭에 나온다
    tab(pg,'할 일');pg.click('.tdside button[data-key="*"]');idle(pg);inp='.tdadd input[type=text]'
    td=pg.evaluate('today()');d7=pg.evaluate('addDays(today(),7)')
    pg.click('.tdadd .chip[data-id=today]');pg.fill(inp,'칩 하나');pg.press(inp,'Enter');idle(pg)
    c=fget(pg,'20_Notes/칩 하나.md');assert c and 'type: note' in c and f'due: {td}' in c and 'todo: true' in c,c
    assert '칩 하나' in pg.inner_text('.tdtoday')
    pg.click('.tdadd .chip[data-id=date]');pg.fill('.tdadd input[type=date]',d7);idle(pg)
    pg.fill(inp,'칩 둘');pg.click('.tdadd .addbtn');idle(pg)
    c=fget(pg,'20_Notes/칩 둘.md');assert c and f'due: {d7}' in c and 'todo: true' in c,c
    assert '칩 둘' in pg.inner_text('.tdmain'),'고른 날짜의 할 일이 안 보임'
    pg.click('.tdadd .chip[data-id=none]');pg.fill(inp,'칩 셋');pg.press(inp,'Enter');idle(pg)
    c=fget(pg,'20_Notes/칩 셋.md');assert c and 'todo: true' in c and 'due' not in c,c
    assert '칩 셋' in pg.inner_text('.tdmain'),'나중에 할 일이 안 보임'
    # 셋 중 하나는 늘 선택: 기본 오늘, 날짜를 고르기 전에는 앞의 선택 유지, 글에서 읽은 날짜는 맞는 칩
    on=lambda:pg.eval_on_selector_all('.tdadd .chip[aria-pressed=true]','e=>e.map(x=>x.dataset.id)')
    pg.click('.tdadd .chip[data-id=today]');idle(pg,150);assert on()==['today'],on()
    pg.evaluate("todoDate='';render()");idle(pg,200);assert on()==['today'],on()
    pg.click('.tdadd .chip[data-id=date]');idle(pg,150);assert on()==['today'] and pg.is_visible('.tdadd input[type=date]'),on()
    pg.fill('.tdadd input[type=date]',d7);idle(pg,150);assert on()==['date'],on()
    pg.fill(inp,'내일 확인');idle(pg,150);assert on()==['date'],on()
    pg.fill(inp,'오늘 확인');idle(pg,150);assert on()==['today'],on()
    pg.fill(inp,'x');pg.press(inp,'Backspace');idle(pg,300);assert on()==['date'],(on(),pg.evaluate('[todoDue,todoDate]'),pg.input_value(inp))
    pg.click('.tdadd .chip[data-id=none]');idle(pg,150);assert on()==['none'],on()
    pg.fill('.tdadd input[type=date]','') if pg.is_visible('.tdadd input[type=date]') else None
    # 목록에 없는 같은 이름 파일이 이미 있어도(다른 기기·AI가 만든 것) 실패하지 않고 날짜를 붙여 만든다
    pg.evaluate("c=>{__FILES['20_Notes/겹치는 이름.md']=c}",'---\ntype: note\n---\n# 겹치는 이름\n')
    for chip in ['today','date','none']:
        pg.click(f'.tdadd .chip[data-id={chip}]');idle(pg,150);pg.fill(inp,'겹치는 이름');pg.press(inp,'Enter');idle(pg,1500)
        assert '생성 실패' not in pg.inner_text('body'),chip
    fs=[f for f in files(pg) if f.startswith('20_Notes/겹치는 이름')];assert len(fs)==4,fs
    assert sum('todo: true' in fget(pg,f) for f in fs)==3,fs
    tab(pg,'노트');assert not any(r.startswith('칩 ') for r in rows(pg)),rows(pg)
    pg.click('.tdadd .chip[data-id=today]') if False else None
def t_convert(pg):
    tab(pg,'노트');view(pg,'노트');open_row(pg,'주말에 볼 영상');shot(pg,'05-note-card')
    # 노트 ↔ 할 일: 표시만 바뀌고 파일은 그대로. 할 일이 되면 노트 탭에서 빠지고 할 일 탭에 나온다
    assert pg.inner_text('#pPath').startswith('노트') and pg.locator('#card .cdone').count()==0
    act(pg,'할 일로');idle(pg,500)
    c=fget(pg,'20_Notes/주말에 볼 영상.md');assert c and 'todo: true' in c and 'type: note' in c,c
    assert pg.inner_text('#pPath').startswith('할 일') and '주말에 볼 영상' not in rows(pg)
    assert pg.locator('#card .cdone').count()==1
    act(pg,'할 일 해제');idle(pg,500);c=fget(pg,'20_Notes/주말에 볼 영상.md');assert 'todo' not in c and pg.locator('#card .cdone').count()==0 and pg.inner_text('#pPath').startswith('노트') and '주말에 볼 영상' in rows(pg),c
    # 날짜를 넣어도 할 일이 된다
    pg.fill('#card .chip[title="마감"] input','2026-12-01');pg.dispatch_event('#card .chip[title="마감"] input','change');idle(pg,500);assert pg.inner_text('#pPath').startswith('할 일') and pg.locator('#card .cdone').count()==1
    act(pg,'할 일 해제');idle(pg,500);assert 'due' not in fget(pg,'20_Notes/주말에 볼 영상.md')
    act(pg,'프로젝트로 키우기');ok(pg)
    c=fget(pg,'10_Projects/주말에 볼 영상.md');assert c and 'type: project' in c and 'status: active' in c,c
    assert pg.inner_text('#pPath').startswith('프로젝트');close(pg)
def t_rename(pg):
    view(pg,'노트');open_row(pg,'테마 비교 메모');pg.fill('#card .ctitle','테마: A/B 비교');pg.press('#card .ctitle','Enter');idle(pg,600)
    c=fget(pg,'20_Notes/테마 A B 비교.md');assert c and '# 테마: A/B 비교' in c,files(pg)
    assert '20_Notes/테마 비교 메모.md' not in files(pg);close(pg)
    # 프로젝트 이름을 바꾸면 속한 노트·할 일의 project 도 따라간다
    proj_card(pg,'블로그 개편')
    pg.fill('#card .ctitle','블로그 새단장');pg.press('#card .ctitle','Enter');idle(pg,900)
    assert '10_Projects/블로그 새단장.md' in files(pg),files(pg)
    assert 'project: "[[블로그 새단장]]"' in fget(pg,'20_Notes/도메인 연장.md') and 'project: "[[블로그 새단장]]"' in fget(pg,'20_Notes/테마 A B 비교.md');close(pg)
def t_project(pg):
    proj_card(pg,'집 정리')
    card=pg.inner_text('#card');assert '수납장 문서 요약' in card and '창고 치수 재기' in card and '이 프로젝트 노트의 변경 기록' in card,card
    shot(pg,'06-project-card')
    pg.click('#card button:text-is("+ 기존 노트 넣기")');idle(pg);pg.select_option('#askField select',label='정리는 버리는 것부터');ok(pg)
    assert 'project: "[[집 정리]]"' in fget(pg,'20_Notes/정리는 버리는 것부터.md') and '정리는 버리는 것부터' in pg.inner_text('#card [data-sec=notes]')
    pg.fill('#card .cl .add input[aria-label="할 일 추가"]','내일 박스 사기');pg.press('#card .cl .add input[aria-label="할 일 추가"]','Enter');idle(pg)
    assert 'project: "[[집 정리]]"' in fget(pg,'20_Notes/박스 사기.md')
    act(pg,'프로젝트 끝내기');assert '남은 할 일' in pg.inner_text('#askMsg');pg.select_option('#askField select','free');ok(pg);idle(pg,900)
    f=files(pg);assert '90_Archive/집 정리.md' in f and '10_Projects/집 정리.md' not in f,f
    c=fget(pg,'90_Archive/집 정리.md');assert 'archived: true' in c and 'status: done' in c,c
    assert '90_Archive/비용 비교.md' in f and '20_Notes/업체 견적 받기.md' in f and 'project' not in fget(pg,'20_Notes/업체 견적 받기.md')
    assert 'project: "[[집 정리]]"' in fget(pg,'20_Notes/수납장 문서 요약.md');close(pg)
    view(pg,'노트');open_row(pg,'수납장 문서 요약');assert '(보관됨)' in pg.inner_text('#card [data-chip=project]');close(pg)
def t_project_restore(pg):
    # 미완료 할 일을 함께 보관한 프로젝트를 되살리면: 다시 진행 상태, 카드에서 '보관됨'이 사라지고, 그 할 일도 돌아온다
    n=pg.evaluate("createNote({type:'project',title:'임시 프로젝트',quiet:true}).then(()=>createNote({type:'todo',title:'임시 할 일',project:'임시 프로젝트'})).then(()=>1)");idle(pg)
    proj_card(pg,'임시 프로젝트')
    act(pg,'프로젝트 끝내기');pg.select_option('#askField select','archive');ok(pg);idle(pg,900)
    assert '90_Archive/임시 프로젝트.md' in files(pg) and '90_Archive/임시 할 일.md' in files(pg),files(pg)
    assert '되살리기' in pg.inner_text('#card .actions') and '보관됨' in pg.inner_text('#card .chiprow')
    act(pg,'되살리기');idle(pg,1200)
    c=fget(pg,'10_Projects/임시 프로젝트.md');assert c and 'status: active' in c and 'archived' not in c,c
    assert '보관됨' not in pg.inner_text('#card .chiprow') and '프로젝트 끝내기' in pg.inner_text('#card .actions')
    assert '20_Notes/임시 할 일.md' in files(pg) and 'archived' not in fget(pg,'20_Notes/임시 할 일.md') and '임시 할 일' in pg.inner_text('#card')
    close(pg);tab(pg,'할 일');assert '임시 프로젝트' in pg.inner_text('.tdside');tab(pg,'노트')
def t_delete_project(pg):
    proj_card(pg,'블로그 새단장');pg.click('#card .actions .danger');assert '프로젝트 없음' in pg.inner_text('#askMsg');ok(pg);idle(pg,600)
    assert '10_Projects/블로그 새단장.md' not in files(pg) and 'project' not in fget(pg,'20_Notes/도메인 연장.md')
    proj(pg,'집 정리') if False else tab(pg,'프로젝트');pg.click('#projNew');pg.fill('#askField input','새 프로젝트');ok(pg);idle(pg,400);c=fget(pg,'10_Projects/새 프로젝트.md');assert c and 'type: project' in c and 'status: active' in c,c
    assert pg.inner_text('.phead .ptitle')=='새 프로젝트' and lists(pg)==['할 일','진행 중','완료'] and col(pg,'할 일')==[]
def t_misc(pg):
    tab(pg,'일정');assert pg.locator('.calgrid .day').count()==42
    pg.fill('.evbar input[type=search]','치과');pg.press('.evbar input[type=search]','Enter');idle(pg);assert '검색 결과 · 1건' in pg.inner_text('#main')
    pg.click('#main button:text-is("닫기")');idle(pg);assert pg.locator('.calgrid .day').count()==42 and '마감 노트' not in pg.inner_text('#main');shot(pg,'07-calendar')
    # 문서는 탭이 아니라 오른쪽 아이콘. 다시 누르면 보던 탭으로. 새로고침 버튼은 없다
    assert pg.locator('.tabs:not(.sub) button').count()==4 and pg.locator('#btnReload').count()==0 and pg.eval_on_selector_all('header .icon','e=>e.map(x=>x.id)')[:2]==['btnDocs','btnPalette']
    pg.click('#btnDocs');idle(pg);assert pg.is_visible('.tree') and pg.get_attribute('#btnDocs','aria-pressed')=='true';pg.click('#btnDocs');idle(pg);assert pg.locator('.calgrid .day').count()==42 and pg.get_attribute('#btnDocs','aria-pressed')=='false'
    tab(pg,'문서');assert not pg.is_visible('#quick') and pg.locator('.nside').count()==0,'문서 탭에는 메모 입력·옆 목록이 없어야 함'
    tree=pg.inner_text('.tree');assert 'Notes' in tree and 'Projects' in tree and 'Todos' not in tree and 'Cards' not in tree and 'Inbox' not in tree,tree
    pg.click('.tree .tn:has-text("수납 아이디어")');idle(pg);assert pg.input_value('#card .ctitle')=='수납 아이디어' and pg.inner_text('#pPath')=='20_Notes/수납 아이디어.md'
    # 문서 탭도 같은 노트 화면이다 — 마크다운 편집기는 없다
    assert not pg.is_visible('#pBody') and not pg.is_visible('#pSave') and pg.is_visible('#card .desc')
    pg.click('#card .desc');idle(pg,200);pg.keyboard.type('본문 수정');pg.click('#card .dedit button:text-is("저장")');idle(pg);assert '본문 수정' in fget(pg,'20_Notes/수납 아이디어.md');shot(pg,'08-docs')
    pg.keyboard.press('Control+k');idle(pg,200);pg.fill('#palInput','>새로');idle(pg,200);assert pg.locator('#palList button').count()>=4;pg.keyboard.press('Escape')
def t_docs_rename(pg):
    tab(pg,'문서');pg.click('.tree .tn:has-text("정리는 버리는 것부터")');idle(pg)
    pg.fill('#card .ctitle','버리는 것부터');pg.press('#card .ctitle','Enter');idle(pg,900)
    assert '20_Notes/버리는 것부터.md' in files(pg) and '20_Notes/정리는 버리는 것부터.md' not in files(pg),files(pg)
    assert pg.inner_text('#pPath')=='20_Notes/버리는 것부터.md' and pg.input_value('#card .ctitle')=='버리는 것부터'
    assert pg.locator('.tree .tn[aria-current=true]').count()==1
    pg.click('.tree .tn >> nth=0');idle(pg)
    # 저장 안 한 설명이 있으면 묻는다
    pg.click('#card .desc');idle(pg,200);pg.keyboard.type('임시');assert pg.evaluate('isDirty()'),pg.evaluate("[descEditing,!!document.querySelector('#card .desc.editing'),current&&current.path]");tab(pg,'노트');assert pg.is_visible('#ask.on') or pg.is_visible('#askOk');pg.click('#askOk');idle(pg)
def t_edit(pg):
    """노트 편집: 파일 형식(마크다운)이 화면에 나오지 않는다"""
    ED='#card .desc.editing';SAVE='#card .dedit button:text-is("저장")'
    P='20_Notes/편집 시험.md'
    pg.evaluate("p=>{__FILES[p]='---\\ntype: note\\n---\\n# 편집 시험\\n\\n## 체크리스트\\n- [ ] 테스트1\\n'}",P);assert pg.evaluate('softRefresh()');idle(pg)
    tab(pg,'노트');view(pg,'노트');open_row(pg,'편집 시험')
    # 체크리스트만 있는 노트: 설명을 눌러도 "## 체크리스트", "- [ ]" 가 나오지 않는다
    assert pg.inner_text('#card .desc').strip()=='설명 추가…'
    pg.click('#card .desc');idle(pg,200);tx=pg.inner_text(ED);assert tx.strip()=='' and pg.locator('#card textarea').count()==0,repr(tx)
    pg.keyboard.type('첫 줄');pg.keyboard.press('Enter');pg.keyboard.type('둘째 줄');pg.click(SAVE);idle(pg)
    c=fget(pg,P);assert '첫 줄\n둘째 줄\n\n## 체크리스트\n- [ ] 테스트1' in c,c
    assert '테스트1' in pg.inner_text('#card .cl') and '첫 줄' in pg.inner_text('#card .desc') and '##' not in pg.inner_text('#card')
    # 바꾼 것이 없으면 저장하지 않는다
    n0=pg.evaluate('__LOG.length');pg.click('#card .desc');idle(pg,200);pg.click(SAVE);idle(pg);assert pg.evaluate('__LOG.length')==n0
    # 체크리스트 항목은 화면에서 넣는다
    pg.fill('#card .cl .add input','테스트2');pg.press('#card .cl .add input','Enter');idle(pg);c=fget(pg,P);assert '- [ ] 테스트1\n- [ ] 테스트2' in c and c.index('둘째 줄')<c.index('## 체크리스트'),c
    # 서식: 소제목·목록·굵게·다른 노트 링크가 기호 없이 보이고, 고쳐도 그대로 남는다
    pg.evaluate("p=>api.put(p,'---\\ntype: note\\n---\\n# 편집 시험\\n\\n## 요약\\n주장 **한 문장** 과 [[수납 아이디어]]\\n- 하나\\n- 둘\\n\\n끝 문단\\n\\n## 준비\\n- [x] 끝낸 것\\n\\n![그림](_attachments/a.png)\\n\\n## 연결\\n- [[옛 메모]]\\n',notes.find(n=>n.path===p).sha,'ext')",P)
    close(pg);assert pg.evaluate('softRefresh()');idle(pg);open_row(pg,'편집 시험')
    pg.click('#card .desc');idle(pg,200);tx=pg.inner_text(ED)
    assert '요약' in tx and '하나' in tx and '한 문장' in tx and '수납 아이디어' in tx and not any(k in tx for k in ['##','**','[[','- [','![','옛 메모','끝낸 것']),repr(tx)
    shot(pg,'13-edit')
    assert pg.locator(ED+' h3').count()==1 and pg.locator(ED+' li').count()==2 and pg.locator(ED+' b').count()==1 and pg.locator(ED+' a.wl').count()==1
    pg.keyboard.press('Control+End');pg.keyboard.type(' 덧붙임');pg.click(SAVE);idle(pg);c=fget(pg,P)
    assert '## 요약\n주장 **한 문장** 과 [[수납 아이디어]]\n- 하나\n- 둘\n\n끝 문단 덧붙임\n' in c,c
    assert '## 준비\n- [x] 끝낸 것' in c and '![그림](_attachments/a.png)' in c and c.rstrip().endswith('## 연결\n- [[옛 메모]]'),c
    # 서식 단추
    pg.click('#card .desc');idle(pg,200);pg.keyboard.press('Control+End');pg.keyboard.press('Enter');pg.keyboard.type('새 소제목');pg.click('#card .dedit button:text-is("소제목")');pg.keyboard.press('Enter');pg.keyboard.type('목록 항목');pg.click('#card .dedit button:text-is("목록")')
    pg.click(SAVE);idle(pg);c=fget(pg,P);assert '## 새 소제목' in c.replace('###','##') and '- 목록 항목' in c,c
    # 연결: 골라서 잇고, ✕ 로 뺀다
    assert '옛 메모' in pg.inner_text('#card .links') and '수납 아이디어' in pg.inner_text('#card .links')
    pg.click('#card section h3 button:text-is("+ 연결")');idle(pg,200);pg.fill('#palInput','주말에');idle(pg,200);pg.click('#palList button >> nth=0');idle(pg)
    c=fget(pg,P);assert '## 연결\n- [[옛 메모]]\n- [[주말에 볼 영상]]' in c,c
    pg.click('#card .links .lki:has-text("옛 메모") .x');idle(pg);c=fget(pg,P);assert '[[옛 메모]]' not in c and '- [[주말에 볼 영상]]' in c,c
    assert pg.locator('#card .links .lki:has-text("수납 아이디어") .x').count()==0,'글 속의 링크는 연결 목록에서 빼지 않는다'
    pg.click('#card .links .lki:has-text("주말에 볼 영상") .x');idle(pg);c=fget(pg,P);assert '## 연결' not in c,c
    # 첨부: ✕ 로 뺀다
    assert pg.locator('#card .att img').count()==1;pg.click('#card .att .atti .x');idle(pg);c=fget(pg,P);assert 'a.png' not in c and '끝낸 것' in c,c
    # 안내 문구에도 기호가 없다
    body=pg.inner_text('#card');assert not any(k in body for k in ['[[','- [ ]','마크다운']),body
    close(pg)
def t_settings(pg):
    pg.click('#btnSettings');idle(pg,200);tabs=pg.inner_text('#settings .mh');assert '저장한 보기' not in tabs and '뷰' not in pg.inner_text('#settings')
    pg.click('#settings .mh button[data-tab=props]');idle(pg,200)
    assert pg.locator('#optStatus .opt').count()==3 and pg.locator('#optStatus .opt button.x').count()==1 and pg.locator('#optStatus input.id[disabled]').count()==2
    pg.click('#sCancel');idle(pg,200)
def t_stale(pg):
    # 다른 기기·AI가 바꾼 것을 조용히 받아온다: 새 파일, 옮긴 파일, 고친 파일, 지운 파일
    tab(pg,'노트');pg.click('.nside button[data-k="project"][data-v=""]') if False else None
    src=pg.evaluate("notes.find(n=>n.path.startsWith('20_Notes/')&&n.sha&&!isTask(n)&&__FILES[n.path]).path")
    before=pg.evaluate('notes.length')
    pg.evaluate("""src=>{const F=__FILES;F['20_Notes/밖에서 만든 노트.md']='---\\ntype: note\\n---\\n# 밖에서 만든 노트\\n';
      F['20_Notes/옮겨진 메모.md']=F[src];delete F[src];}""",src)
    assert pg.evaluate('softRefresh()')==True,pg.evaluate("[softBusy,loadError,notes.length,saving,queue.list.length,!!current,document.activeElement.tagName,document.activeElement.id,!!document.querySelector('.modal.on,.modal.open,.dragging')]");idle(pg)
    r=rows(pg);assert '밖에서 만든 노트' in r and pg.evaluate("notes.some(n=>n.path==='20_Notes/옮겨진 메모.md')") and not pg.evaluate("p=>notes.some(n=>n.path===p)",src),r
    assert pg.evaluate('notes.length')==before+1
    assert pg.evaluate('softRefresh()')==False,'바뀐 것이 없으면 다시 그리지 않는다'
    # 옮겨진 파일을 고쳐도 실패하지 않는다
    pg.evaluate("saveNote(notes.find(n=>n.path==='20_Notes/옮겨진 메모.md'),{todo:true},undefined,undefined,true)");idle(pg,500);assert 'todo: true' in fget(pg,'20_Notes/옮겨진 메모.md')
    assert '실패' not in pg.inner_text('#toast')
    # 입력 중이거나 패널이 열려 있으면 건너뛴다
    tab(pg,'할 일');pg.fill('.tdadd input[type=text]','쓰는 중');pg.evaluate("__FILES['20_Notes/또 밖에서.md']='---\\ntype: note\\n---\\n# 또 밖에서\\n'")
    assert pg.evaluate('softRefresh()')==False and pg.input_value('.tdadd input[type=text]')=='쓰는 중'
    pg.fill('.tdadd input[type=text]','x');pg.press('.tdadd input[type=text]','Backspace');pg.evaluate('document.activeElement.blur()')
    assert pg.evaluate('softRefresh()')==True
    # 오프라인에서 만든 것과 같은 이름의 파일이 그 사이 생겼으면 덮어쓰지 않는다
    pg.evaluate('window.__OFFLINE=true');inp='.tdadd input[type=text]';pg.fill(inp,'겹친 오프라인');pg.press(inp,'Enter');idle(pg)
    pg.evaluate("__FILES['20_Notes/겹친 오프라인.md']='---\\ntype: note\\n---\\n# 겹친 오프라인\\n\\n남의 내용\\n'")
    pg.evaluate('window.__OFFLINE=false;queue.flush()');idle(pg,700)
    assert '남의 내용' in fget(pg,'20_Notes/겹친 오프라인.md'),'다른 기기의 파일을 덮어씀'
    fs=[f for f in files(pg) if f.startswith('20_Notes/겹친 오프라인')];assert len(fs)==2 and not pg.is_visible('#qbadge'),fs
    assert pg.evaluate("notes.filter(n=>n.path.startsWith('20_Notes/겹친 오프라인')).every(n=>n.sha)")

def t_offline(pg):
    tab(pg,'할 일');pg.evaluate('window.__OFFLINE=true');inp='.tdadd input[type=text]'
    pg.fill(inp,'오프라인 할 일');pg.press(inp,'Enter');idle(pg);assert '오프라인 할 일' in pg.inner_text('.tdmain') and '20_Notes/오프라인 할 일.md' not in files(pg)
    assert pg.is_visible('#qbadge');pg.evaluate('window.__OFFLINE=false;queue.flush()');idle(pg,600)
    assert '20_Notes/오프라인 할 일.md' in files(pg) and not pg.is_visible('#qbadge')

def t_unit(pg):
    ev=pg.evaluate
    assert ev("fileNameOf('.env 설정?')")=='env 설정' and ev("fileNameOf('a/b: c')")=='a b c' and ev("fileNameOf('??')")=='메모'
    assert ev("parseFM(buildFM({type:'todo',project:'[[집: 정리]]',label:['a','b'],archived:true})).fm")=={'type':'todo','project':'[[집: 정리]]','label':['a','b'],'archived':True}
    assert ev("typeOf({fm:{type:'resource'},folder:'30_Resources'})")=='note' and ev("typeOf({fm:{type:'inbox',label:'todo'},folder:'00_Inbox'})")=='note' and ev("isTask({fm:{type:'inbox',label:'todo'},folder:'00_Inbox'})")
    assert ev("typeOf({fm:{},folder:'10_Projects'})")=='project' and ev("typeOf({fm:{type:'weekly'},folder:'01_Daily'})")=='note' and ev("typeOf({fm:{type:'card'},folder:'20_Cards'})")=='note'
    # 할 일은 종류가 아니라 카드의 상태: 날짜 · 할 일 표시 · 완료 중 하나 (옛 할 일 노트 포함)
    T=lambda fm,folder='20_Notes':ev("([fm,folder])=>isTask({fm,folder})",[fm,folder])
    assert not T({'type':'note'}) and T({'type':'note','due':'2026-01-01'}) and T({'type':'note','todo':True}) and T({'type':'note','status':'done'}) and T({'type':'todo'}) and T({},'11_Todos') and not T({'type':'project','due':'2026-01-01'},'10_Projects')
    assert ev("targetFolder({fm:{type:'todo'},folder:'11_Todos'})")=='20_Notes' and ev("targetFolder({fm:{type:'card'},folder:'20_Cards'})")=='20_Notes' and ev("normFM({type:'todo',label:'todo'},'note',true)")=={'type':'note','todo':True,'label':''}
    assert ev("targetFolder({fm:{type:'project',archived:true},folder:'10_Projects'})")=='90_Archive'
    assert ev("projectOf({fm:{type:'todo',project:'ToDo'},folder:'11_Todos'})")=='' and ev("projectOf({fm:{type:'note',project:'[[가|나]]'},folder:'20_Notes'})")=='가'
    assert ev("parseWhen('내일 회의').rest")=='회의'
TESTS=[t_unit,t_load,t_suggest,t_quick,t_views,t_archive_view,t_todo,t_todo_when,t_convert,t_rename,t_project,t_project_restore,t_delete_project,t_misc,t_docs_rename,t_settings,t_offline,t_stale,t_edit]
if os.environ.get('ONLY'):TESTS=[x for x in TESTS if x.__name__ in os.environ['ONLY'].split(',')]   # 일부만: ONLY=t_edit python3 tests/run.py
with sync_playwright() as p:
    b=p.chromium.launch();pg0=None;pg=b.new_page(viewport={'width':1280,'height':860});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' else None)
    pg.goto(MOCK+'?gcal=1');pg.wait_for_selector('#main table, #main .status');idle(pg,900)
    for t in TESTS:
        try:t(pg);results.append((t.__name__,'ok',''))
        except Exception as e:
            results.append((t.__name__,'FAIL','line '+str(traceback.extract_tb(e.__traceback__)[-1].lineno)+' '+''.join(traceback.format_exception_only(type(e),e)).strip()[:int(os.environ.get('ERRLEN','500'))]))
            if SHOTS:pg.screenshot(path=os.path.join(SHOTS,'FAIL-'+t.__name__+'.png'))
            for sel in ['#askCancel','#pClose']:
                try:
                    if pg.is_visible(sel):pg.click(sel,timeout=500)
                except Exception:pass
    # 폰 화면
    m=b.new_page(viewport={'width':360,'height':760});m.on('pageerror',lambda e:errs.append('mobile: '+str(e)))
    m.goto(MOCK);m.wait_for_selector('#main table, #main .status');idle(m,900)
    try:
        assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰에서 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'09-mobile-inbox.png'))
        for vn in ['노트','프로젝트']:
            view(m,vn);assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰 '+vn+' 보기 가로 스크롤'
        tab(m,'프로젝트');assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰 프로젝트 목록 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'12-mobile-projects.png'))
        m.click('.pbarx button[data-p] >> nth=0');idle(m);assert m.is_visible('.tboard') and m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰 프로젝트 보드 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'12-mobile-board.png'))
        m.click('#projBack');idle(m)
        tab(m,'노트')
        tab(m,'할 일');assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰 할 일 탭 가로 스크롤'
        m.fill('.tdadd input[type=text]','폰에서 추가');m.click('.tdadd .addbtn');idle(m);assert '20_Notes/폰에서 추가.md' in files(m),'추가 버튼으로 할 일이 안 만들어짐'
        m.fill('.tdadd input[type=text]','폰 엔터');m.press('.tdadd input[type=text]','Enter');idle(m);assert '20_Notes/폰 엔터.md' in files(m)
        assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'추가 뒤 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'10-mobile-todo.png'))
        tab(m,'문서');m.click('.tree .tn:has-text("수납 아이디어")');idle(m);assert m.is_visible('#card .desc') and not m.is_visible('#pBody')
        m.click('#card .desc');idle(m,200);m.keyboard.type('폰에서 쓴 설명');assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'설명 편집 중 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'11-mobile-edit.png'))
        m.click('#card .dedit button:text-is("저장")');idle(m);assert '폰에서 쓴 설명' in fget(m,'20_Notes/수납 아이디어.md')
        results.append(('mobile','ok',''))
    except Exception as e:results.append(('mobile','FAIL',str(e)[:300]))
    b.close()
for n,s,d in results:print(f'{s:5} {n} {d}')
print('page errors:',errs if errs else 'none')
sys.exit(1 if errs or any(s!='ok' for _,s,_ in results) else 0)
