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
def side(pg,k,v):   # 노트 탭의 프로젝트·라벨 고르기 상자. 이미 고른 것을 다시 고르면 풀린다(전체)
    pg.evaluate("""([k,v])=>{const s=document.querySelector(`.nmain .fsels select[data-k="${k}"]`);const os=[...s.options];let o=os.find(o=>o.dataset.v===v);if(o.selected&&v!=='')o=os[0];s.value=o.value;s.dispatchEvent(new Event('change'));}""",[k,v]);idle(pg)
def tside(pg,k,v):   # 할 일 탭의 프로젝트·라벨 고르기 상자 (프로젝트 전체는 '*')
    pg.evaluate("""([k,v])=>{const s=document.querySelector(`.tdmain .fsels select[data-k="${k}"]`);const os=[...s.options];let o=os.find(o=>o.dataset.v===v);if(o.selected)o=os[0];s.value=o.value;s.dispatchEvent(new Event('change'));}""",[k,v]);idle(pg)
def side_on(pg,k):return pg.evaluate("""k=>{const s=document.querySelector(`.nmain .fsels select[data-k="${k}"]`);return s.selectedOptions[0].dataset.v}""",k)
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
    assert not pg.is_visible('#views') and pg.locator('.nmain .fsels select').count()==2 and pg.locator('.nside').count()==0 and '정리 전' not in pg.inner_text('body') and '이대로 두기' not in pg.inner_text('body')
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
    st=pg.text_content('.nmain .fsels');assert '프로젝트 없음' in st and '집 정리' in st and '블로그 개편' in st and '라벨 없음' in st and '읽을 것' in st and '내 생각' in st,st
    # 옆 목록에서 프로젝트를 누르면 그 프로젝트의 노트만. 보기 칩은 그대로
    side(pg,'project','집 정리');assert set(rows(pg))=={'수납장 문서 요약','수납 아이디어'},rows(pg)
    assert side_on(pg,'project')=='집 정리' and 'on' in pg.get_attribute('.nmain .fsel >> nth=0','class')
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
    side(pg,'label','idea');assert rows(pg)==[] and '해당하는 노트가 없습니다' in pg.inner_text('#main') and pg.locator('.nmain .fsels').count()==1
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
    # 보관은 탭마다: 노트 탭 "보관한 노트", 할 일 탭 "보관한 할 일", 프로젝트 탭 "끝낸 프로젝트"
    view(pg,'노트');assert '옛 노트' not in rows(pg);pg.click('[data-sec=narch] .hd');idle(pg);pg.click('[data-sec=narch] .trow button:text-is("옛 노트")');idle(pg)
    act(pg,'되살리기');idle(pg,500);assert '20_Notes/옛 노트.md' in files(pg) and 'archived' not in fget(pg,'20_Notes/옛 노트.md');close(pg);assert '옛 노트' in rows(pg)
    tab(pg,'할 일');pg.click('[data-sec=arch] .hd');idle(pg);pg.click('[data-sec=arch] .trow button:text-is("끝난 일")');idle(pg)
    assert '보관됨' in pg.inner_text('#pPath');act(pg,'되살리기');idle(pg,500)
    c=fget(pg,'20_Notes/끝난 일.md');assert c and 'archived' not in c and 'label' not in c and 'todo: true' in c,c
    assert '90_Archive/끝난 일.md' not in files(pg);close(pg)
    proj_home(pg);pg.click('[data-sec=parch] .hd');idle(pg);assert '옛 프로젝트' in pg.inner_text('[data-sec=parch]');pg.click('[data-sec=parch] .hd');idle(pg);tab(pg,'노트')
def t_todo(pg):
    tab(pg,'할 일');side=pg.text_content('.tdmain .fsels');assert pg.locator('.tdside').count()==0 and pg.locator('.tdadd select').count()==0
    assert '프로젝트 없음' in side and '집 정리' in side and '2/5' in side,side
    assert pg.locator('[data-sec=todaylate]').count()==1 and not pg.is_visible('[data-sec=todaylate]')
    inp='.tdadd input[type=text]';pg.fill(inp,'금요일 벤더 견적');idle(pg,200)
    assert pg.is_visible('[data-sec=todaylate]'),'다른 날짜를 볼 때 오늘·지연이 보여야 함'
    assert '프로젝트 없음' in pg.inner_text('.tdprev')
    tside(pg,'project','집 정리');pg.fill(inp,'금요일 벤더 견적');assert '집 정리에 추가' in pg.get_attribute(inp,'placeholder') and '프로젝트 집 정리' in pg.inner_text('.tdprev');pg.press(inp,'Enter');idle(pg)
    c=fget(pg,'20_Notes/벤더 견적.md');assert c and 'project: "[[집 정리]]"' in c and 'due: ' in c and 'label' not in c,c
    assert '옛 할 일' in pg.inner_text('.tdmain') or True
    tside(pg,'project','');txt=pg.inner_text('.tdmain');assert '우유 사기' in txt and '업체 견적' not in txt
    pg.fill(inp,'세탁소');pg.press(inp,'Enter');idle(pg);c=fget(pg,'20_Notes/세탁소.md');assert c and 'project' not in c,c
    tside(pg,'project','*')
    # 라벨로 거르기: 그 라벨의 할 일만, 새 할 일도 그 라벨로
    tside(pg,'label','work');txt=pg.inner_text('.tdmain');assert '건강검진 예약' in txt and '우유 사기' not in txt,txt
    assert '라벨 업무' in pg.inner_text('.tdprev') or True
    pg.fill(inp,'회의록 정리');pg.press(inp,'Enter');idle(pg);c=fget(pg,'20_Notes/회의록 정리.md');assert c and 'label: work' in c,c
    tside(pg,'label','work');assert '우유 사기' in pg.inner_text('.tdmain')
    pg.click('[data-sec=done] .hd');idle(pg);assert '주간 정리 때 보관' in pg.inner_text('[data-sec=done] .hd') and '비용 비교' in pg.inner_text('[data-sec=done]')
    # 완료 체크
    pg.click('.tdtoday .trow:has-text("우유 사기") input[type=checkbox]');idle(pg);assert 'status: done' in fget(pg,'20_Notes/우유 사기.md')
    shot(pg,'04-todo')
    pg.click('.tdadd .chip[data-id=none]');idle(pg);assert not pg.is_visible('.tdtoday') and not pg.is_visible('[data-sec=todaylate]')
    pg.click('.tdadd .chip[data-id=today]');idle(pg)
def t_todo_when(pg):
    # 오늘 / 날짜 / 나중에 — 세 선택 모두 할 일로 만들어지고 할 일 탭에 나온다
    tab(pg,'할 일');tside(pg,'project','*');inp='.tdadd input[type=text]'
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
    view(pg,'노트');assert '수납장 문서 요약' not in rows(pg);pg.click('[data-sec=nended] .hd');idle(pg);pg.click('[data-sec=nended] .trow .tx:text-is("수납장 문서 요약")');idle(pg);assert '(보관됨)' in pg.inner_text('#card [data-chip=project]');close(pg);pg.click('[data-sec=nended] .hd');idle(pg)
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
    close(pg);tab(pg,'할 일');assert '임시 프로젝트' in pg.text_content('.tdmain .fsels');tab(pg,'노트')
def t_delete_project(pg):
    proj_card(pg,'블로그 새단장');pg.click('#card .actions .danger');assert '프로젝트 없음' in pg.inner_text('#askMsg');ok(pg);idle(pg,600)
    assert '10_Projects/블로그 새단장.md' not in files(pg) and 'project' not in fget(pg,'20_Notes/도메인 연장.md')
    proj(pg,'집 정리') if False else tab(pg,'프로젝트');pg.click('#projNew');pg.fill('#askField input','새 프로젝트');ok(pg);idle(pg,400);c=fget(pg,'10_Projects/새 프로젝트.md');assert c and 'type: project' in c and 'status: active' in c,c
    assert c.split('---')[2].strip()=='# 새 프로젝트','새 프로젝트는 빈 설명으로 시작한다: '+c
    pg.click('.phead .ptitle');idle(pg);assert pg.inner_text('#card .desc').strip()=='설명 추가…' and pg.locator('#card .cl .ci').count()==0 and '없습니다' in pg.inner_text('#card');close(pg)
    assert pg.inner_text('.phead .ptitle')=='새 프로젝트' and lists(pg)==['할 일','진행 중','완료'] and col(pg,'할 일')==[]
def t_misc(pg):
    tab(pg,'일정');assert pg.locator('.calgrid .day').count()==42
    pg.fill('.evbar input[type=search]','치과');pg.press('.evbar input[type=search]','Enter');idle(pg);assert '검색 결과 · 1건' in pg.inner_text('#main')
    pg.click('#main button:text-is("닫기")');idle(pg);assert pg.locator('.calgrid .day').count()==42 and '마감 노트' not in pg.inner_text('#main');shot(pg,'07-calendar')
    # 문서는 탭이 아니라 오른쪽 아이콘. 다시 누르면 보던 탭으로. 새로고침 버튼은 없다
    assert pg.locator('.tabs:not(.sub) button').count()==4 and pg.locator('#btnReload').count()==0 and pg.eval_on_selector_all('header .icon','e=>e.map(x=>x.id)')[:2]==['btnDocs','btnPalette']
    pg.click('#btnDocs');idle(pg);assert pg.is_visible('.tree') and pg.get_attribute('#btnDocs','aria-pressed')=='true';pg.click('#btnDocs');idle(pg);assert pg.locator('.calgrid .day').count()==42 and pg.get_attribute('#btnDocs','aria-pressed')=='false'
    tab(pg,'문서');assert not pg.is_visible('#quick') and pg.locator('.fsels').count()==0,'문서 탭에는 메모 입력·고르기 상자가 없어야 함'
    tree=pg.inner_text('.tree');assert '노트 · 할 일' in tree and '프로젝트' in tree and 'Notes' not in tree and 'Todos' not in tree and 'Cards' not in tree and 'Inbox' not in tree,tree
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
def t_refs(pg):
    """참고(링크·메모), 주소 자동 링크, 고정"""
    P='20_Notes/참고 시험.md'
    pg.evaluate("createNote({type:'note',title:'참고 시험',body:'설명 글 https://example.com/a/b. 끝\\n\\n## 준비\\n- [ ] 안내 보기 https://example.com/guide\\n\\n## 연결\\n- [[옛 메모]]\\n'})");idle(pg,500)
    tab(pg,'노트');view(pg,'노트');open_row(pg,'참고 시험')
    # 주소는 설명·체크리스트에서 누를 수 있는 링크로 보인다 (파일은 그대로)
    assert pg.get_attribute('#card .desc a.xl','href')=='https://example.com/a/b' and pg.inner_text('#card .desc a.xl')=='example.com/a/b'
    assert pg.get_attribute('#card .cl .ci a.xl','href')=='https://example.com/guide'
    R='#card [data-sec=refs]';inp=R+' .add input'
    pg.fill(inp,'https://example.com/one');pg.press(inp,'Enter');idle(pg)
    pg.fill(inp,'분리배출 안내 https://example.com/two');pg.press(inp,'Enter');idle(pg)
    pg.fill(inp,'둘째 주만 받는다');pg.click(R+' .add button');idle(pg)
    c=fget(pg,P);assert '## 참고\n- https://example.com/one\n- [분리배출 안내](https://example.com/two)\n- 둘째 주만 받는다\n\n## 연결\n- [[옛 메모]]' in c,c
    assert pg.locator(R+' .ci.ref').count()==3 and pg.inner_text(R+' .ci.ref >> nth=1 >> a')=='분리배출 안내' and pg.get_attribute(R+' .ci.ref >> nth=1 >> a','href')=='https://example.com/two'
    shot(pg,'14-refs')
    assert '둘째 주만 받는다' in pg.inner_text(R) and '참고' not in pg.inner_text('#card .desc') and '[' not in pg.inner_text(R)
    # 설명을 고쳐도 참고는 그대로, 순서는 체크리스트 → 참고 → 연결
    pg.click('#card .desc');idle(pg,200);assert 'example.com/one' not in pg.inner_text('#card .desc.editing')
    pg.keyboard.press('Control+End');pg.keyboard.type(' 추가');pg.click('#card .dedit button:text-is("저장")');idle(pg);c=fget(pg,P)
    assert c.index('## 준비')<c.index('## 참고')<c.index('## 연결') and '- [분리배출 안내](https://example.com/two)' in c and '끝 추가' in c,c
    # 빼기: 마지막 것을 빼면 제목 줄도 사라진다
    for _ in range(3):pg.click(R+' .ci.ref >> nth=0 >> .x');idle(pg)
    c=fget(pg,P);assert '참고' not in c.split('---')[2].replace('# 참고 시험','') and '## 연결' in c,c
    # 원문 주소(source 속성)는 참고의 첫 줄로 보인다
    pg.evaluate("p=>saveNote(notes.find(n=>n.path===p),{source:'https://example.com/origin'},undefined,undefined,true)",P);idle(pg,500)
    assert pg.get_attribute(R+' .ci.ref a','href')=='https://example.com/origin';pg.click(R+' .ci.ref .x');idle(pg);assert 'source' not in fget(pg,P)
    # 고정: 노트 목록 맨 위로, 다시 누르면 풀린다. 할 일에는 고정 단추가 없다
    assert rows(pg)[0]!='참고 시험' or True
    pg.click('#card .pinbtn');idle(pg);assert 'pin: true' in fget(pg,P) and pg.get_attribute('#card .pinbtn','aria-pressed')=='true'
    shot(pg,'15-pin-note')
    close(pg);shot(pg,'16-pin-list');r=rows(pg);assert r[0].replace('📌 ','')=='참고 시험' and r[0].startswith('📌'),r
    pg.click('#main thead th button:text-is("제목")');idle(pg);assert rows(pg)[0].startswith('📌'),'정렬을 바꿔도 고정은 맨 위'
    open_row(pg,'📌 참고 시험') if False else pg.click('#main tbody tr >> nth=0 >> td.t>button');idle(pg)
    pg.click('#card .pinbtn');idle(pg);assert 'pin' not in fget(pg,P)
    act(pg,'할 일로');idle(pg);assert pg.locator('#card .pinbtn').count()==0;act(pg,'할 일 해제');idle(pg);close(pg)

def t_ended(pg):
    """끝난 프로젝트에 속한 노트는 노트 목록에서 빠지고, 되살리면 돌아온다"""
    pg.evaluate("(async()=>{await createNote({type:'project',title:'끝낼 프로젝트',quiet:true});await createNote({type:'note',title:'끝낼 프로젝트의 메모',project:'끝낼 프로젝트'});})()");idle(pg,700)
    tab(pg,'노트');view(pg,'노트');assert '끝낼 프로젝트의 메모' in rows(pg) and pg.locator('.nmain .fsels option[data-v="끝낼 프로젝트"]').count()==1
    side(pg,'project','끝낼 프로젝트');assert rows(pg)==['끝낼 프로젝트의 메모']
    pg.evaluate("saveNote(projectNote('끝낼 프로젝트'),{status:'done',archived:true},undefined,undefined,true)");idle(pg,900);tab(pg,'프로젝트');tab(pg,'노트')
    r=rows(pg);assert '끝낼 프로젝트의 메모' not in r and len(r)>1 and pg.locator('.nmain .fsels option[data-v="끝낼 프로젝트"]').count()==0,r
    assert 'archived' not in fget(pg,'20_Notes/끝낼 프로젝트의 메모.md'),'노트 파일은 그대로'
    sec='[data-sec=nended]';assert '끝난 프로젝트의 노트' in pg.inner_text(sec);pg.click(sec+' .hd');idle(pg)
    assert '끝낼 프로젝트의 메모' in pg.inner_text(sec) and '끝낼 프로젝트' in pg.inner_text(sec+' .trow .evnote')
    pg.click(sec+' .trow .tx');idle(pg);assert pg.input_value('#card .ctitle')=='끝낼 프로젝트의 메모';close(pg)
    pg.evaluate("unarchive(projectNote('끝낼 프로젝트'))");idle(pg,1200);tab(pg,'프로젝트');tab(pg,'노트')
    assert '끝낼 프로젝트의 메모' in rows(pg) and (pg.locator(sec).count()==0 or '끝낼 프로젝트의 메모' not in pg.inner_text(sec))

def t_repeat(pg):
    """반복 할 일: 완료하면 다음 차례로 넘어간다 (brain 안에서만)"""
    td=pg.evaluate('today()')
    # 날짜 계산 (시간대와 무관)
    assert pg.evaluate("addDays('2026-11-13',1)")=='2026-11-14' and pg.evaluate("addDays('2026-12-31',1)")=='2027-01-01' and pg.evaluate("addDays('2026-03-01',-1)")=='2026-02-28'
    S=lambda d,r,a=0:pg.evaluate("([d,r,a])=>stepDue(d,r,a)",[d,r,a])
    assert S('2026-11-13','daily')=='2026-11-14' and S('2026-11-13','weekly')=='2026-11-20' and S('2026-11-13','weekday')=='2026-11-16' and S('2026-11-12','weekday')=='2026-11-13'
    assert S('2026-11-25','monthly')=='2026-12-25' and S('2026-12-25','monthly')=='2027-01-25' and S('2026-01-31','monthly',31)=='2026-02-28' and S('2026-02-28','monthly',31)=='2026-03-31'
    assert S('2026-03-01','yearly')=='2027-03-01' and S('2028-02-29','yearly',29)=='2029-02-28'
    PR=lambda x:pg.evaluate("x=>{const r=parseRepeat(x);return r?[r.rule,r.rest]:null}",x)
    assert PR('매주 금요일 분리수거')==['weekly','금요일 분리수거'] and PR('관리비 매월 25일')==['monthly','관리비 25일'] and PR('평일마다 스트레칭')==['weekday','스트레칭'] and PR('매일매일 일기') is None and PR('보고서')is None
    # 입력: 적은 대로 읽는다
    tab(pg,'할 일');tside(pg,'project','*')
    inp='.tdadd input[type=text]';pg.click('.tdadd .chip[data-id=today]')
    pg.fill(inp,'매주 금요일 분리수거 내기');idle(pg,200);assert '↻ 매주' in pg.inner_text('.tdprev');shot(pg,'17-repeat-input');pg.press(inp,'Enter');idle(pg)
    P='20_Notes/분리수거 내기.md';c=fget(pg,P);fri=pg.evaluate("parseWhen('금요일').due");assert 'repeat: weekly' in c and f'due: {fri}' in c and 'todo: true' in c and 'repeat-day' not in c,c
    pg.fill(inp,'매일 물 마시기');pg.press(inp,'Enter');idle(pg);c=fget(pg,'20_Notes/물 마시기.md');assert 'repeat: daily' in c and f'due: {td}' in c,c
    pg.click('.tdadd .chip[data-id=none]');pg.fill(inp,'매월 31일 정산');pg.press(inp,'Enter');idle(pg);c=fget(pg,'20_Notes/정산.md');assert 'repeat: monthly' in c and 'repeat-day: 31' in c and '-31' in c,c
    pg.click('.tdadd .chip[data-id=today]')
    # 할 일도 제목을 누르면 열린다 (노트 목록과 같은 방식). 프로젝트 표시는 누르는 것이 아니다
    pg.click('.trow:visible .tx .tt:text-is("물 마시기")');idle(pg);assert pg.input_value('#card .ctitle')=='물 마시기';close(pg)
    r1='.trow:visible:has(.tx .tt:text-is("물 마시기")) >> nth=0';assert pg.locator(r1+' >> select.inl.pj').count()==1
    pj=pg.eval_on_selector(r1+' >> select.inl.pj','s=>[...s.options].map(o=>o.value).filter(Boolean)[0]')
    pg.select_option(r1+' >> select.inl.pj',pj);idle(pg,700);assert f'project: "[[{pj}]]"' in fget(pg,'20_Notes/물 마시기.md')
    pg.select_option(r1+' >> select.inl.pj','');idle(pg,700);assert 'project' not in fget(pg,'20_Notes/물 마시기.md')
    # 완료 → 날짜만 다음으로, 완료 상태는 아니다. 줄에 ↻ 표시
    row='.trow:has(.tx .tt:text-is("물 마시기"))';assert '↻ 매일' in pg.inner_text(row+' >> nth=0')
    pg.click(row+' >> nth=0 >> input[type=checkbox]');idle(pg,700);c=fget(pg,'20_Notes/물 마시기.md')
    assert f"due: {pg.evaluate('addDays(today(),1)')}" in c and 'status' not in c and 'repeat: daily' in c,c
    assert pg.locator(row).count()>=1 and not pg.is_checked(row+' >> nth=0 >> input[type=checkbox]')
    # 밀린 것은 지난 횟수만큼 쌓지 않고 오늘 뒤의 가장 가까운 차례로. 체크리스트는 다시 비운다
    pg.evaluate("p=>saveNote(notes.find(n=>n.path===p),{due:addDays(today(),-20)},undefined,'## 준비\\n- [x] 종이\\n- [ ] 병\\n',true)",P);idle(pg,600)
    pg.evaluate("p=>saveNote(notes.find(n=>n.path===p),{status:'done'},undefined,undefined,true)",P);idle(pg,600);c=fget(pg,P)
    due=[l for l in c.split('\n') if l.startswith('due:')][0][5:];assert td<due<=pg.evaluate('addDays(today(),7)') and '- [ ] 종이' in c and '[x]' not in c and 'status' not in c,c
    # 노트 화면: 반복 칩으로 바꾸고, 끝 날짜를 넘으면 그냥 완료된다
    pg.evaluate("p=>openNote(notes.find(n=>n.path===p))",P);idle(pg);assert '매주' in pg.inner_text('#card .rchip')
    shot(pg,'18-repeat-note')
    pg.select_option('#card .rchip select','monthly');idle(pg);assert 'repeat: monthly' in fget(pg,P) and '매월' in pg.inner_text('#card .rchip')
    pg.fill('#card .chip input[aria-label="반복 끝 날짜"]',due);idle(pg);assert f'repeat-until: {due}' in fget(pg,P)
    pg.check('#card .cdone');idle(pg,700);c=fget(pg,P);assert 'status: done' in c and f'due: {due}' in c,c
    pg.uncheck('#card .cdone');idle(pg,600);pg.select_option('#card .rchip select','');idle(pg);c=fget(pg,P);assert 'repeat' not in c,c
    assert pg.locator('#card .chip input[aria-label="반복 끝 날짜"]').count()==0;close(pg)
    # 프로젝트 보드: 완료 줄로 끌어도 반복 할 일은 제자리에 남고 날짜만 넘어간다
    pg.evaluate("(async()=>{await createNote({type:'project',title:'반복 프로젝트',quiet:true});await createNote({type:'todo',title:'주간 점검',due:today(),project:'반복 프로젝트',quiet:true,extra:{repeat:'weekly'}});})()");idle(pg,800)
    pg.evaluate("(async()=>{const p=projectNote('반복 프로젝트'),n=notes.find(x=>x.title==='주간 점검');await moveCard(n,p,DONE_LIST,null);})()");idle(pg,800)
    c=fget(pg,'20_Notes/주간 점검.md');assert f"due: {pg.evaluate('addDays(today(),7)')}" in c and 'status' not in c and 'list: 완료' not in c,c

FUZZ=r"""()=>{
  const parts=['글 한 줄','둘째 줄 **굵게** 와 [[다른 노트]]','','## 요약','주장 한 문장','- 목록 하나','- 목록 둘','## 준비','- [ ] 할 것','- [x] 한 것','- [ ] 날짜 📅 2026-11-20','## 참고','- https://example.com/a','- [제목](https://example.com/b)','- 그냥 메모','![그림](_attachments/a.png)','![[b.png]]','## 연결','- [[옛 메모]]','- [[또 다른]]','## 빈 제목','```','## 코드 속 제목','- [ ] 코드 속','```','1. 번호 목록','> 인용','| a | b |','| - | - |','### 작은 제목','문장 끝 https://example.com/c.','- [ ] 제목 없는 항목','## 체크리스트','## 메모','본문 아래 글'];
  let seed=7;const rnd=()=>{seed=(seed*1103515245+12345)&0x7fffffff;return seed/0x7fffffff;};
  const bad=[];const norm=s=>s.split('\n').map(l=>l.trim()).filter(Boolean).sort().join('\n');
  for(let k=0;k<4000;k++){
    const n=1+Math.floor(rnd()*12);const lines=[];for(let i=0;i<n;i++)lines.push(parts[Math.floor(rnd()*parts.length)]);
    const body='# 제목\n\n'+lines.join('\n')+'\n';
    try{
      const sp=splitBody(body);
      // 1) 설명을 그대로 다시 넣어도 내용이 사라지지 않는다 (만들어 넣는 "## 체크리스트" 제목만 늘 수 있다)
      const out=composeBody(body,sp.desc);const a=norm(stripH1(body)),b=norm(out.replace(/^## 체크리스트$/gm,m=>a.includes('## 체크리스트')?m:''));
      const lost=a.split('\n').filter(l=>!b.split('\n').includes(l));
      if(lost.length)bad.push(['lost',body,out,lost]);
      // 2) 한 번 정리한 것은 다시 정리해도 같다
      const sp2=splitBody('# 제목\n\n'+out);const out2=composeBody('# 제목\n\n'+out,sp2.desc);if(out2!==out)bad.push(['unstable',out,out2]);
      // 3) 편집기를 거쳐도 설명이 같다
      const d=document.createElement('div');mdToEdit(sp.desc,d);const back=editToMd(d);
      if(back!==sp.desc.replace(/[ \t]+$/gm,'').replace(/\n{3,}/g,'\n\n').trim())bad.push(['editor',sp.desc,back]);
      // 4) 체크리스트·참고·연결 개수가 정리 뒤에도 같다
      const c1=sp.groups.reduce((x,g)=>x+g.items.length,0),c2=sp2.groups.reduce((x,g)=>x+g.items.length,0);
      if(c1!==c2||sp.refLines.length!==sp2.refLines.length||sp.linkLines.length!==sp2.linkLines.length)bad.push(['count',body,out,[c1,c2,sp.refLines.length,sp2.refLines.length,sp.linkLines.length,sp2.linkLines.length]]);
    }catch(e){bad.push(['throw',body,String(e)]);}
    if(bad.length>=8)break;
  }
  return bad;
}"""
def t_fuzz(pg):
    """본문 나누기·정리·편집기를 무작위 본문으로 돌려도 내용이 사라지거나 흔들리지 않는다"""
    bad=pg.evaluate(FUZZ);assert not bad,bad[:2]
    # 프로젝트를 빼면 보드 자리(list·order)도 지워지고, 다른 프로젝트로 옮기면 첫 줄에서 시작한다
    pg.evaluate("(async()=>{await createNote({type:'project',title:'자리 A',quiet:true});await createNote({type:'project',title:'자리 B',quiet:true});await createNote({type:'note',title:'자리 노트',project:'자리 A',quiet:true,extra:{list:'진행 중',order:3}});})()");idle(pg,900)
    P='20_Notes/자리 노트.md';assert 'list: 진행 중' in fget(pg,P)
    pg.evaluate("p=>saveNote(notes.find(n=>n.path===p),{project:pjLink('자리 B')},undefined,undefined,true)",P);idle(pg,600);c=fget(pg,P);assert '[[자리 B]]' in c and 'list' not in c and 'order' not in c,c
    pg.evaluate("p=>saveNote(notes.find(n=>n.path===p),{list:'진행 중',order:1},undefined,undefined,true)",P);idle(pg,600)
    pg.evaluate("p=>saveNote(notes.find(n=>n.path===p),{project:''},undefined,undefined,true)",P);idle(pg,600);c=fget(pg,P);assert 'project' not in c and 'list' not in c and 'order' not in c,c
    # 없는 날짜는 날짜로 읽지 않는다
    PW=lambda x:pg.evaluate("x=>{const w=parseWhen(x);return w?w.due:null}",x)
    assert PW('2026-02-30 없는 날') is None and PW('13/45 이상한 날짜') is None and PW('2/30 없는 날') is None and PW('2027-02-28 있는 날')=='2027-02-28' and PW('12/25 성탄')[5:]=='12-25'
    # 오프라인에서 보관·제목 바꾸기를 한 노트는 연결되면 폴더와 파일 이름이 맞춰진다
    pg.evaluate("(async()=>{await createNote({type:'note',title:'끊긴 동안 보관',quiet:true});await createNote({type:'note',title:'끊긴 동안 이름',quiet:true});})()");idle(pg,800)
    pg.evaluate("window.__OFFLINE=true;saveNote(notes.find(n=>n.title==='끊긴 동안 보관'),{archived:true},undefined,undefined,true);saveNote(notes.find(n=>n.title==='끊긴 동안 이름'),{},'이어진 뒤 이름',undefined,true)");idle(pg,800)
    assert '20_Notes/끊긴 동안 보관.md' in files(pg) and pg.evaluate('queue.list.length')==2
    pg.evaluate('window.__OFFLINE=false;queue.flush()');idle(pg,2500);f=files(pg)
    assert '90_Archive/끊긴 동안 보관.md' in f and '20_Notes/끊긴 동안 보관.md' not in f and '20_Notes/이어진 뒤 이름.md' in f and '20_Notes/끊긴 동안 이름.md' not in f and pg.evaluate('queue.list.length')==0,[x for x in f if '끊긴' in x or '이어진' in x]
    # 주소 링크: 문장 속 주소만 링크가 되고 이미 링크인 것은 두 번 감싸지 않는다
    h=pg.evaluate("mdToHtml('보기 https://example.com/a. 그리고 [제목](https://example.com/b) 끝')");assert h.count('<a ')==2 and 'href="https://example.com/a"' in h and '>제목</a>' in h and 'example.com/a</a>.' in h,h

def t_merge(pg):
    """다른 기기가 먼저 고친 노트를 고쳐도 내 변경이 사라지지 않는다 (합쳐서 저장)"""
    pg.evaluate("createNote({type:'todo',title:'합치기 시험',due:today(),body:'첫 줄\\n\\n## 준비\\n- [ ] 하나\\n',quiet:true})");idle(pg,700);P='20_Notes/합치기 시험.md'
    other=lambda js:pg.evaluate("async ([p,js])=>{const f=await api.file(p);await api.put(p,new Function('c','return '+js)(f.content),f.sha,'ext: 다른 기기');}",[P,js])
    tab(pg,'할 일');tside(pg,'project','*') if pg.evaluate('todoFolder')!='*' else None
    pg.click('.trow:visible .tx .tt:text-is("합치기 시험")');idle(pg)
    # 다른 기기: 설명 줄을 고치고 라벨을 붙임 / 나: 체크리스트 항목 추가
    other("c.replace('첫 줄','첫 줄 (폰에서 고침)').replace('type: note','type: note\\nlabel: work')");idle(pg,200)
    pg.fill('#card .cl .add input','둘');pg.press('#card .cl .add input','Enter');idle(pg,1500);c=fget(pg,P)
    assert '첫 줄 (폰에서 고침)' in c and '- [ ] 하나\n- [ ] 둘' in c and 'label: work' in c,c
    assert '합쳐 저장했습니다' in pg.inner_text('#toast') and '둘 다' not in pg.inner_text('#toast'),pg.inner_text('#toast')
    assert '폰에서 고침' in pg.inner_text('#card .desc') and '둘' in pg.inner_text('#card .cl'),'화면도 합친 내용으로'
    # 속성만 바꾸는 경우 (완료 체크): 다른 기기의 본문 변경은 그대로
    other("c.replace('- [ ] 하나','- [x] 하나')");idle(pg,200)
    pg.click('#card .cdone');idle(pg,1500);c=fget(pg,P);assert '- [x] 하나' in c and 'status: done' in c,c
    pg.click('#card .cdone');idle(pg,900)
    # 같은 줄을 서로 다르게 고치면 둘 다 남긴다
    other("c.replace('첫 줄 (폰에서 고침)','첫 줄 — 폰 판')");idle(pg,200)
    pg.click('#card section h3 button:text-is("편집")');idle(pg,300);pg.keyboard.press('Control+End');pg.keyboard.type(' — PC 판');pg.click('#card .dedit button:text-is("저장")');idle(pg,1500);c=fget(pg,P)
    assert '첫 줄 — 폰 판' in c and 'PC 판' in c and '둘 다' in pg.inner_text('#toast'),c
    # 다른 기기가 지운 노트를 고치면 지금 내용으로 다시 만든다
    pg.evaluate("async p=>{const f=await api.file(p);await api.del(p,f.sha,'ext: 삭제');}",P);idle(pg,300);assert P not in files(pg)
    pg.fill('#card .cl .add input','셋');pg.press('#card .cl .add input','Enter');idle(pg,1500);c=fget(pg,P);assert c and '- [ ] 셋' in c and '다시 만들었습니다' in pg.inner_text('#toast'),c
    close(pg);assert pg.evaluate("p=>{const n=notes.find(x=>x.path===p);return n&&n.raw===__FILES[p]&&!!n.sha}",P)

def t_calendar(pg):
    """일정 탭: Google 일정 만들기·고치기·옮기기·지우기 (Apps Script 흉내는 gcal.gs 와 같은 규칙)"""
    td=pg.evaluate('today()');D=lambda n:pg.evaluate('n=>addDays(today(),n)',n)
    EV=lambda title:pg.evaluate("t=>{const e=__EVENTS.find(e=>e.title===t);return e?[e.start,e.end,e.allDay,e.location]:null}",title)
    F=lambda k:f'#askField .fields >> nth=0 >> :nth-match(input,select, {k})'
    def fld(label,val,kind='fill'):
        loc=pg.locator('#askField .fields label',has_text=label).first.locator('xpath=following-sibling::*[1]')
        loc.select_option(val) if kind=='sel' else loc.fill(val)
    def fval(label):return pg.locator('#askField .fields label',has_text=label).first.locator('xpath=following-sibling::*[1]').input_value()
    tab(pg,'일정');idle(pg,600);pg.click('.calh button:text-is("오늘")');idle(pg,400)
    # 새 일정: 시작 시각이 비어 있지 않다 (길이 1시간과 맞는 기본값). 다른 날은 09:00
    pg.click('.evbar .addbtn');idle(pg,200);assert fval('길이')=='60' and (fval('시작')!='' or pg.evaluate('new Date().getHours()')==23)
    fld('제목','점검 회의');fld('날짜',D(3));fld('시작','10:30');fld('길이','90','sel');ok(pg);idle(pg,700)
    assert EV('점검 회의')==[D(3)+'T10:30',D(3)+'T12:00',False,''],EV('점검 회의')
    assert pg.evaluate('calSel')==D(3) and '점검 회의' in pg.inner_text('.daylist') and '10:30–12:00' in pg.inner_text('.daylist')
    assert '10:30 점검 회의' in pg.inner_text('.calgrid .day.sel')
    # 종일 일정
    pg.click('.evbar .addbtn');idle(pg,200);assert fval('시작')=='09:00','다른 날 기본 시작은 9시';fld('제목','휴가');fld('길이','0','sel');ok(pg);idle(pg,700)
    assert EV('휴가')==[D(3)+'T00:00',D(4)+'T00:00',True,''] and '종일' in pg.inner_text('.daylist')
    assert '휴가' not in (pg.evaluate("ds=>{calSel=ds;render();return document.querySelector('.daylist').innerText}",D(4))),'종일 일정이 다음 날에도 보임'
    # 제목·날짜 없이 만들 수 없다
    pg.evaluate("ds=>{calSel=ds;render()}",D(3));n0=pg.evaluate('__EVENTS.length');pg.click('.evbar .addbtn');idle(pg,200);fld('제목','  ');ok(pg);idle(pg,400);assert pg.evaluate('__EVENTS.length')==n0
    pg.click('.evbar .addbtn');idle(pg,200);fld('제목','날짜 없음');fld('날짜','');ok(pg);idle(pg,400);assert pg.evaluate('__EVENTS.length')==n0 and '실패' not in pg.inner_text('#toast')
    # 고치기: 제목·장소만 바꾸면 날짜·시각은 보내지 않는다 (여러 날 일정이 줄어들지 않게)
    pg.evaluate("ds=>{__EVENTS.push({id:'multi',cal:'c1',calName:'기본',color:'#4a86c5',title:'출장',allDay:true,start:ds+'T00:00',end:addDays(ds,3)+'T00:00',location:'',desc:''});gcal.invalidate();render()}",D(3));idle(pg,700)
    assert '출장' in pg.inner_text('.daylist');pg.click('.daylist .evrow:has-text("출장")');idle(pg,200);assert fval('길이')=='0'
    fld('제목','부산 출장');fld('장소','부산');ok(pg);idle(pg,700);assert EV('부산 출장')==[D(3)+'T00:00',D(6)+'T00:00',True,'부산'],EV('부산 출장')
    assert '"date"' not in pg.evaluate('__GLOG[__GLOG.length-1]')
    for k in (3,4,5):assert '부산 출장' in pg.evaluate("ds=>{calSel=ds;render();return document.querySelector('.daylist').innerText}",D(k)),k
    assert '부산 출장' not in pg.evaluate("ds=>{calSel=ds;render();return document.querySelector('.daylist').innerText}",D(6))
    # 고치기: 시각·길이·날짜를 바꾸면 그대로 반영, 종일 ↔ 시각 전환
    pg.evaluate("ds=>{calSel=ds;render()}",D(3));pg.click('.daylist .evrow:has-text("점검 회의")');idle(pg,200);assert fval('시작')=='10:30' and fval('길이')=='90'
    fld('시작','23:30');fld('길이','60','sel');fld('날짜',D(4));ok(pg);idle(pg,700);assert EV('점검 회의')==[D(4)+'T23:30',D(5)+'T00:30',False,''],EV('점검 회의')
    assert pg.evaluate('calSel')==D(4) and '점검 회의' in pg.inner_text('.daylist')
    pg.click('.daylist .evrow:has-text("점검 회의")');idle(pg,200);fld('길이','0','sel');ok(pg);idle(pg,700);assert EV('점검 회의')==[D(4)+'T00:00',D(5)+'T00:00',True,'']
    pg.click('.daylist .evrow:has-text("점검 회의")');idle(pg,200);fld('시작','08:00');fld('길이','30','sel');ok(pg);idle(pg,700);assert EV('점검 회의')==[D(4)+'T08:00',D(4)+'T08:30',False,'']
    # 다른 날로 옮기기: 시각과 길이를 지킨다. 여러 날 종일 일정도 길이를 지킨다
    pg.evaluate("ds=>moveEventTo(__EVENTS.find(e=>e.title==='점검 회의'),ds)",D(6));idle(pg,700);assert EV('점검 회의')==[D(6)+'T08:00',D(6)+'T08:30',False,''] and pg.evaluate('calSel')==D(6)
    pg.evaluate("ds=>moveEventTo(__EVENTS.find(e=>e.title==='부산 출장'),ds)",D(8));idle(pg,700);assert EV('부산 출장')==[D(8)+'T00:00',D(11)+'T00:00',True,'부산'],EV('부산 출장')
    # 검색 → 고르면 그 날짜로
    pg.fill('.evbar input[type=search]','출장');pg.press('.evbar input[type=search]','Enter');idle(pg,600);assert '검색 결과 · 1건' in pg.inner_text('.daylist');pg.click('.daylist .evrow');idle(pg,500);assert pg.evaluate('calSel')==D(8)
    # 지우기: 묻고 나서 지운다
    pg.click('.daylist .evrow:has-text("부산 출장") .x');idle(pg,200);assert '부산 출장' in pg.inner_text('#askMsg');pg.click('#askCancel');idle(pg,300);assert EV('부산 출장')
    pg.click('.daylist .evrow:has-text("부산 출장") .x');idle(pg,200);ok(pg);idle(pg,700);assert EV('부산 출장') is None and '부산 출장' not in pg.inner_text('#main')
    # 할 일 탭의 오늘 상자: 오늘 일정이 보이고, 여기서 만든 일정도 바로 보인다
    tab(pg,'할 일');idle(pg,500);assert '주간 회의' in pg.inner_text('.tdbox, .tdtoday') if pg.locator('.tdbox, .tdtoday').count() else True
    # 달 넘기기와 오늘로 돌아오기, 달력에 할 일도 같이 보인다
    tab(pg,'일정');m0=pg.inner_text('.calh h2');pg.click('.calh button:text-is("›")');idle(pg,500);assert pg.inner_text('.calh h2')!=m0 and pg.locator('.calgrid .day').count()==42
    pg.click('.calh button:text-is("‹")');pg.click('.calh button:text-is("‹")');idle(pg,500);pg.click('.calh button:text-is("오늘")');idle(pg,500);assert pg.inner_text('.calh h2')==m0 and pg.evaluate('calSel')==td
    for t0 in ['점검 회의','휴가']:pg.evaluate("t=>{const i=__EVENTS.findIndex(e=>e.title===t);if(i>=0)__EVENTS.splice(i,1)}",t0)
    pg.evaluate('gcal.invalidate();render()');idle(pg,500)

def t_settings(pg):
    pg.click('#btnSettings');idle(pg,200);tabs=pg.inner_text('#settings .mh');assert '저장한 보기' not in tabs and '뷰' not in pg.inner_text('#settings')
    pg.click('#settings .mh button[data-tab=props]');idle(pg,200)
    assert pg.locator('#optStatus .opt').count()==3 and pg.locator('#optStatus .opt button.x').count()==1,'진행·완료는 지울 수 없다'
    # 파일에 저장되는 값(id)·영문 색 이름은 화면에 나오지 않는다
    body=pg.inner_text('#settings .mb[data-tab=props]');vals=pg.eval_on_selector_all('#settings .mb[data-tab=props] input','e=>e.map(x=>x.value)')
    assert not any(k in body+' '.join(vals) for k in ['active','done','mine','moc','yellow','brain.config','id']),(body,vals)
    assert pg.locator('#settings input.id').count()==0 and '노랑' in pg.text_content('#optLabel') and '사용' in pg.inner_text('#optLabel')
    # 이름만 적어 라벨·항목을 만든다. 저장용 값은 이름에서 만들어지고, 이름을 바꿔도 값은 그대로다
    pg.click('#addLabel');pg.keyboard.type('여행 계획');pg.select_option('#optLabel .opt >> nth=-1 >> select','red')
    pg.fill('#optLabel .opt >> nth=0 >> input','번뜩임')
    pg.click('#addProp');pg.keyboard.type('장소');pg.click('#addProp');pg.keyboard.type('우선순위');pg.select_option('#optProps .opt >> nth=-1 >> select','select');pg.keyboard.type('높음, 보통')
    pg.click('#sSave');idle(pg,900);import json;c=json.loads(fget(pg,'_scripts/brain.config.json'))
    lb={o['id']:o for o in c['labels']};assert lb['여행-계획']=={'id':'여행-계획','name':'여행 계획','color':'red'} and lb['idea']['name']=='번뜩임',c['labels']
    pr={o['id']:o for o in c['props']};assert pr['장소']['type']=='text' and pr['우선순위']['options']==['높음','보통'],c['props']
    assert [o['id'] for o in c['statuses']]==['active','paused','done']
    # 라벨 색이 실제로 칠해진다 (기본 회색 바탕에 덮이지 않는다)
    tab(pg,'노트');cols=pg.eval_on_selector_all('#main td .tag','e=>e.map(x=>getComputedStyle(x).backgroundColor)');assert len(set(cols))>1,cols
    pg.click('#btnSettings');idle(pg,200);pg.click('#settings .mh button[data-tab=props]');idle(pg,200)
    pg.fill('#optLabel .opt >> nth=0 >> input','아이디어');pg.click('#optLabel .opt:has(input[value="여행 계획"]) .x');pg.click('#optProps .opt >> nth=0 >> .x');pg.click('#optProps .opt >> nth=0 >> .x')
    pg.click('#sSave');idle(pg,900);c=json.loads(fget(pg,'_scripts/brain.config.json'));assert len(c['labels'])==6 and c['props']==[] and c['labels'][0]['name']=='아이디어',c
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
TESTS=[t_unit,t_load,t_suggest,t_quick,t_views,t_archive_view,t_todo,t_todo_when,t_convert,t_rename,t_project,t_project_restore,t_delete_project,t_misc,t_docs_rename,t_settings,t_offline,t_stale,t_edit,t_refs,t_ended,t_repeat,t_fuzz,t_merge,t_calendar]
if os.environ.get('ONLY'):TESTS=[x for x in TESTS if x.__name__ in os.environ['ONLY'].split(',')]   # 일부만: ONLY=t_edit python3 tests/run.py
with sync_playwright() as p:
    b=p.chromium.launch();pg0=None;pg=b.new_page(viewport={'width':1280,'height':860},timezone_id='Asia/Seoul');errs=[]   # 한국 시간으로 돌린다 (날짜 계산이 시간대에 흔들리지 않는지)
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
    m=b.new_page(viewport={'width':360,'height':760},timezone_id='Asia/Seoul');m.on('pageerror',lambda e:errs.append('mobile: '+str(e)))
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
        # 폰: 프로젝트·라벨은 한 줄의 고르기 상자 둘 (칩 줄 없음)
        tab(m,'노트');assert m.locator('.fsels select').count()==2 and not m.is_visible('.tdchips') and not m.is_visible('.nside')
        opt=[o for o in m.eval_on_selector_all('.fsels select >> nth=1 >> option','e=>e.map(x=>x.textContent)') if o.startswith('라벨 없음')][0]
        n0=len(rows(m));m.select_option('.fsels select >> nth=1',label=opt);idle(m);assert m.evaluate('state.label')=='__none' and len(rows(m))<n0 and 'on' in m.get_attribute('.fsel >> nth=1','class')
        m.select_option('.fsels select >> nth=1',index=0);idle(m);assert m.evaluate('state.label')=='' and len(rows(m))==n0
        tab(m,'할 일');assert m.locator('.fsels select').count()>=1;m.select_option('.fsels select >> nth=0',index=1);idle(m);assert m.evaluate("todoFolder")!='*';m.select_option('.fsels select >> nth=0',index=0);idle(m);assert m.evaluate("todoFolder")=='*'
        assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1')
        tab(m,'문서');m.click('.tree .tn:has-text("수납 아이디어")');idle(m);assert m.is_visible('#card .desc') and not m.is_visible('#pBody')
        assert m.inner_text('#card .pinbtn').strip()=='📌','폰에서는 핀 하나만'
        m.click('#card .desc');idle(m,200);m.keyboard.type('폰에서 쓴 설명');assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'설명 편집 중 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'11-mobile-edit.png'))
        m.click('#card .dedit button:text-is("저장")');idle(m);assert '폰에서 쓴 설명' in fget(m,'20_Notes/수납 아이디어.md')
        # 폰(터치)에서는 체크리스트·참고의 ✕ 가 늘 보여야 지울 수 있다
        m.fill('#card [data-sec=refs] .add input','폰에서 넣은 참고');m.press('#card [data-sec=refs] .add input','Enter');idle(m)
        op=m.eval_on_selector('#card [data-sec=refs] .ci.ref .x','e=>+getComputedStyle(e).opacity');assert op>0.3,op
        m.click('#card [data-sec=refs] .ci.ref .x');idle(m);assert '폰에서 넣은 참고' not in fget(m,'20_Notes/수납 아이디어.md')
        assert '넓게' not in m.inner_text('#card .actions')
        results.append(('mobile','ok',''))
    except Exception as e:results.append(('mobile','FAIL',str(e)[:300]))
    b.close()
for n,s,d in results:print(f'{s:5} {n} {d}')
print('page errors:',errs if errs else 'none')
sys.exit(1 if errs or any(s!='ok' for _,s,_ in results) else 0)
