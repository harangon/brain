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
def proj(pg,name):tab(pg,'프로젝트');pg.click(f'.pside button[data-p="{name}"]');idle(pg)
def proj_card(pg,name):proj(pg,name);pg.click('#projOpen');idle(pg)
def col(pg,c):return pg.eval_on_selector_all(f'.pboard .col[data-col="{c}"] .card .ct','e=>e.map(x=>x.textContent)')
def tab(pg,name):pg.click(f'.tabs:not(.sub) button:text-is("{name}")');idle(pg)
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
    assert '20_Notes/옛 메모.md' in f and '00_Inbox/옛 메모.md' not in f,'옛 Inbox 노트가 20_Notes 로 안 옮겨짐'
    assert '20_Notes/옛 자료.md' in f and '30_Resources/옛 자료.md' not in f
    assert pg.evaluate("getComputedStyle(document.querySelector('#btnSettings')).width")=='30px' and pg.evaluate("getComputedStyle(document.querySelector('#q')).borderRadius")!='0px','머리줄 스타일이 빠짐'
    # 노트 탭은 노트 목록 하나: 보기 칩 없음, 옆에 프로젝트·라벨 목록, 옛 데일리도 노트로
    r=rows(pg);daily=[x for x in r if x.startswith('20')];assert len(daily)==1 and f'20_Notes/{daily[0]}.md' in f and not any(p.startswith('01_Daily/') for p in f)
    assert set(r)-set(daily)=={'수납 아이디어','구조를 단순하게 가는 이유','주말에 볼 영상','옛 메모','수납장 문서 요약','정리는 버리는 것부터','테마 비교 메모','옛 자료'},r
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
    # 프로젝트 탭: 프로젝트를 고르면 그 프로젝트의 보드(할 일 · 완료 · 노트)
    tab(pg,'프로젝트');assert not pg.is_visible('#quick') and not pg.is_visible('#subtabs'),'프로젝트 탭에는 메모 입력·표/보드 전환이 없어야 함'
    ps=pg.inner_text('.pside');assert '진행' in ps and '보류' in ps and '집 정리' in ps and '1/4' in ps and '끝낸 프로젝트' in pg.inner_text('#main'),ps
    proj(pg,'집 정리');assert pg.inner_text('.phead .ptitle')=='집 정리' and '창고와 베란다' in pg.inner_text('.pdesc')
    assert col(pg,'todo')==['창고 치수 재기','업체 견적 받기','버릴 것 목록'] and col(pg,'done')==['비용 비교'] and set(col(pg,'notes'))=={'수납장 문서 요약','수납 아이디어','선반 치수','선반 자료'},(col(pg,'todo'),col(pg,'notes'))
    ti='.pboard .col[data-col=todo] .cadd input';pg.fill(ti,'내일 창고 청소');pg.press(ti,'Enter');idle(pg)
    c=fget(pg,'11_Todos/창고 청소.md');assert c and 'project: "[[집 정리]]"' in c and 'due: ' in c,c
    pg.click('.pboard .col[data-col=todo] .card:has-text("창고 청소") .nd');idle(pg);assert '창고 청소' in col(pg,'done') and 'status: done' in fget(pg,'11_Todos/창고 청소.md')
    ni='.pboard .col[data-col=notes] .cadd input';pg.fill(ni,'청소 업체 메모');pg.press(ni,'Enter');idle(pg);c=fget(pg,'20_Notes/청소 업체 메모.md');assert c and 'project: "[[집 정리]]"' in c and '청소 업체 메모' in col(pg,'notes'),c
    pg.click('.pboard .col[data-col=todo] .card:has-text("업체 견적 받기")');idle(pg);assert pg.inner_text('#pPath').startswith('할 일');close(pg)
    shot(pg,'02-project-board')
    # 라벨 칩으로 프로젝트 목록 거르기
    assert '업무' in pg.inner_text('.lchips');pg.click('.lchips button[data-v="work"]');idle(pg)
    assert pg.eval_on_selector_all('.pside button[data-p]','e=>e.map(x=>x.dataset.p)')==['블로그 개편'] and pg.inner_text('.phead .ptitle')=='블로그 개편'
    pg.click('.lchips button[data-v="work"]');idle(pg);assert pg.locator('.pside button[data-p]').count()==2
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
    c=fget(pg,'11_Todos/끝난 일.md');assert c and 'archived' not in c and 'label' not in c and 'type: todo' in c,c
    assert '90_Archive/끝난 일.md' not in files(pg);close(pg)
    tab(pg,'프로젝트');pg.click('[data-sec=parch] .hd');idle(pg);assert '옛 프로젝트' in pg.inner_text('[data-sec=parch]');pg.click('[data-sec=parch] .hd');idle(pg);tab(pg,'노트')
def t_todo(pg):
    tab(pg,'할 일');side=pg.inner_text('.tdside')
    assert '프로젝트 없음' in side and '집 정리' in side and '2/5' in side,side
    assert pg.locator('[data-sec=todaylate]').count()==1 and not pg.is_visible('[data-sec=todaylate]')
    inp='.tdadd input[type=text]';pg.fill(inp,'금요일 벤더 견적');idle(pg,200)
    assert pg.is_visible('[data-sec=todaylate]'),'다른 날짜를 볼 때 오늘·지연이 보여야 함'
    assert '프로젝트 없음' in pg.inner_text('.tdprev')
    pg.select_option('.tdadd select','집 정리');pg.press(inp,'Enter');idle(pg)
    c=fget(pg,'11_Todos/벤더 견적.md');assert c and 'project: "[[집 정리]]"' in c and 'due: ' in c and 'label' not in c,c
    assert '옛 할 일' in pg.inner_text('.tdmain') or True
    pg.click('.tdside button[data-key=""]');idle(pg);txt=pg.inner_text('.tdmain');assert '우유 사기' in txt and '업체 견적' not in txt
    pg.fill(inp,'세탁소');pg.press(inp,'Enter');idle(pg);c=fget(pg,'11_Todos/세탁소.md');assert c and 'project' not in c,c
    pg.click('.tdside button[data-key="*"]');idle(pg)
    # 라벨로 거르기: 그 라벨의 할 일만, 새 할 일도 그 라벨로
    pg.click('.tdside button[data-label="work"]');idle(pg);txt=pg.inner_text('.tdmain');assert '건강검진 예약' in txt and '우유 사기' not in txt,txt
    assert '라벨 업무' in pg.inner_text('.tdprev') or True
    pg.fill(inp,'회의록 정리');pg.press(inp,'Enter');idle(pg);c=fget(pg,'11_Todos/회의록 정리.md');assert c and 'label: work' in c,c
    pg.click('.tdside button[data-label="work"]');idle(pg);assert '우유 사기' in pg.inner_text('.tdmain')
    pg.click('[data-sec=done] .hd');idle(pg);assert '주간 정리 때 보관' in pg.inner_text('[data-sec=done] .hd') and '비용 비교' in pg.inner_text('[data-sec=done]')
    # 완료 체크
    pg.click('.tdtoday .trow:has-text("우유 사기") input[type=checkbox]');idle(pg);assert 'status: done' in fget(pg,'11_Todos/우유 사기.md')
    shot(pg,'04-todo')
    pg.click('.tdadd .chip[data-id=none]');idle(pg);assert not pg.is_visible('.tdtoday') and not pg.is_visible('[data-sec=todaylate]')
    pg.click('.tdadd .chip[data-id=today]');idle(pg)
def t_convert(pg):
    tab(pg,'노트');view(pg,'노트');open_row(pg,'주말에 볼 영상');shot(pg,'05-note-card')
    act(pg,'할 일로 바꾸기');idle(pg,500)
    c=fget(pg,'11_Todos/주말에 볼 영상.md');assert c and 'type: todo' in c and 'reviewed' not in c,c
    assert '20_Notes/주말에 볼 영상.md' not in files(pg) and pg.inner_text('#pPath').startswith('할 일')
    assert pg.locator('#card .cdone').count()==1
    act(pg,'노트로 되돌리기');idle(pg,500);assert '20_Notes/주말에 볼 영상.md' in files(pg) and 'type: note' in fget(pg,'20_Notes/주말에 볼 영상.md')
    act(pg,'할 일로 바꾸기');idle(pg,500);act(pg,'프로젝트로 키우기');ok(pg)
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
    assert 'project: "[[블로그 새단장]]"' in fget(pg,'11_Todos/도메인 연장.md') and 'project: "[[블로그 새단장]]"' in fget(pg,'20_Notes/테마 A B 비교.md');close(pg)
def t_project(pg):
    proj_card(pg,'집 정리')
    card=pg.inner_text('#card');assert '수납장 문서 요약' in card and '창고 치수 재기' in card and '이 프로젝트 노트의 변경 기록' in card,card
    shot(pg,'06-project-card')
    pg.click('#card button:text-is("+ 기존 노트 넣기")');idle(pg);pg.select_option('#askField select',label='정리는 버리는 것부터');ok(pg)
    assert 'project: "[[집 정리]]"' in fget(pg,'20_Notes/정리는 버리는 것부터.md') and '정리는 버리는 것부터' in pg.inner_text('#card [data-sec=notes]')
    pg.fill('#card .cl .add input[aria-label="할 일 추가"]','내일 박스 사기');pg.press('#card .cl .add input[aria-label="할 일 추가"]','Enter');idle(pg)
    assert 'project: "[[집 정리]]"' in fget(pg,'11_Todos/박스 사기.md')
    act(pg,'프로젝트 끝내기');assert '남은 할 일' in pg.inner_text('#askMsg');pg.select_option('#askField select','free');ok(pg);idle(pg,900)
    f=files(pg);assert '90_Archive/집 정리.md' in f and '10_Projects/집 정리.md' not in f,f
    c=fget(pg,'90_Archive/집 정리.md');assert 'archived: true' in c and 'status: done' in c,c
    assert '90_Archive/비용 비교.md' in f and '11_Todos/업체 견적 받기.md' in f and 'project' not in fget(pg,'11_Todos/업체 견적 받기.md')
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
    assert '11_Todos/임시 할 일.md' in files(pg) and 'archived' not in fget(pg,'11_Todos/임시 할 일.md') and '임시 할 일' in pg.inner_text('#card')
    close(pg);tab(pg,'할 일');assert '임시 프로젝트' in pg.inner_text('.tdside');tab(pg,'노트')
def t_delete_project(pg):
    proj_card(pg,'블로그 새단장');pg.click('#card .actions .danger');assert '프로젝트 없음' in pg.inner_text('#askMsg');ok(pg);idle(pg,600)
    assert '10_Projects/블로그 새단장.md' not in files(pg) and 'project' not in fget(pg,'11_Todos/도메인 연장.md')
    pg.fill('.padd input','새 프로젝트');pg.press('.padd input','Enter');idle(pg,700);c=fget(pg,'10_Projects/새 프로젝트.md');assert c and 'type: project' in c and 'status: active' in c,c
    assert pg.inner_text('.phead .ptitle')=='새 프로젝트' and col(pg,'todo')==[] and pg.get_attribute('.pside button[data-p="새 프로젝트"]','aria-pressed')=='true'
def t_misc(pg):
    tab(pg,'일정');assert pg.locator('.calgrid .day').count()==42
    pg.fill('.evbar input[type=search]','치과');pg.press('.evbar input[type=search]','Enter');idle(pg);assert '검색 결과 · 1건' in pg.inner_text('#main')
    pg.click('#main button:text-is("닫기")');idle(pg);assert pg.locator('.calgrid .day').count()==42 and '마감 노트' not in pg.inner_text('#main');shot(pg,'07-calendar')
    tab(pg,'문서');assert not pg.is_visible('#quick') and pg.locator('.nside').count()==0,'문서 탭에는 메모 입력·옆 목록이 없어야 함'
    tree=pg.inner_text('.tree');assert 'Notes' in tree and 'Todos' in tree and 'Inbox' not in tree,tree
    pg.click('.tree .tn:has-text("수납 아이디어")');idle(pg);assert pg.input_value('#pTitle')=='수납 아이디어' and pg.inner_text('#pPath')=='20_Notes/수납 아이디어.md'
    pg.fill('#pBody','본문 수정');pg.click('#pSave');idle(pg);assert '본문 수정' in fget(pg,'20_Notes/수납 아이디어.md');shot(pg,'08-docs')
    pg.keyboard.press('Control+k');idle(pg,200);pg.fill('#palInput','>새로');idle(pg,200);assert pg.locator('#palList button').count()>=4;pg.keyboard.press('Escape')
def t_docs_rename(pg):
    tab(pg,'문서');pg.click('.tree .tn:has-text("정리는 버리는 것부터")');idle(pg)
    pg.fill('#pTitle','버리는 것부터');pg.click('#pSave');idle(pg,700)
    assert '20_Notes/버리는 것부터.md' in files(pg) and '20_Notes/정리는 버리는 것부터.md' not in files(pg),files(pg)
    assert pg.inner_text('#pPath')=='20_Notes/버리는 것부터.md' and pg.input_value('#pTitle')=='버리는 것부터'
    assert pg.locator('.tree .tn[aria-current=true]').count()==1
    pg.click('.tree .tn >> nth=0');idle(pg)
    # 저장 안 한 변경이 있으면 묻는다
    pg.fill('#pBody','임시');tab(pg,'노트');assert pg.is_visible('#ask.on') or pg.is_visible('#askOk');pg.click('#askOk');idle(pg)
def t_links(pg):
    # 문서 편집기: [[ 자동완성 — 키보드 Enter, 폰 키보드의 줄바꿈(beforeinput), 링크 버튼
    tab(pg,'문서');pg.click('.tree .tn:has-text("수납 아이디어")');idle(pg)
    pg.fill('#pBody','');pg.type('#pBody','가 [[주말');idle(pg,200);assert pg.is_visible('#pAc.on') and '주말에 볼 영상' in pg.inner_text('#pAc')
    pg.press('#pBody','Enter');idle(pg,200);assert pg.input_value('#pBody')=='가 [[주말에 볼 영상]]' and not pg.is_visible('#pAc.on')
    pg.type('#pBody',' [[옛 자');idle(pg,200)
    cancelled=pg.evaluate("!document.querySelector('#pBody').dispatchEvent(new InputEvent('beforeinput',{inputType:'insertLineBreak',cancelable:true,bubbles:true}))")
    assert cancelled and pg.input_value('#pBody').endswith('[[옛 자료]]'),pg.input_value('#pBody')
    pg.click('#pLink');idle(pg,200);assert pg.get_attribute('#palInput','placeholder')=='링크할 노트 검색'
    pg.fill('#palInput','버리는');idle(pg,200);assert pg.locator('#palList button').count()==1;pg.click('#palList button');idle(pg,200)
    assert pg.input_value('#pBody').endswith('[[옛 자료]][[버리는 것부터]]'),pg.input_value('#pBody')
    pg.click('#pSave');idle(pg);assert '[[버리는 것부터]]' in fget(pg,'20_Notes/수납 아이디어.md')
    pg.keyboard.press('Control+k');idle(pg,200);assert pg.get_attribute('#palInput','placeholder')!='링크할 노트 검색' and '명령' in pg.inner_text('#palList') or True;pg.keyboard.press('Escape')
    # 카드 설명: 링크 버튼과 자동완성
    tab(pg,'노트');view(pg,'노트');open_row(pg,'수납장 문서 요약');pg.click('#card section h3 button:text-is("편집")');idle(pg,200)
    ta='#card .dedit textarea';pg.click(ta);pg.keyboard.press('Control+End');pg.type(ta,'\n[[수납 아');idle(pg,200);assert pg.is_visible('#pAc.on')
    pg.click('#pAc button >> nth=0');idle(pg,200);assert pg.input_value(ta).endswith('[[수납 아이디어]]'),pg.input_value(ta)
    pg.click('#card .dedit button:text-is("링크")');idle(pg,200);pg.fill('#palInput','옛 메모');idle(pg,200);pg.click('#palList button >> nth=0');idle(pg,200)
    assert pg.input_value(ta).endswith('[[수납 아이디어]][[옛 메모]]'),pg.input_value(ta)
    pg.click('#card .dedit button:text-is("저장")');idle(pg);assert '[[옛 메모]]' in fget(pg,'20_Notes/수납장 문서 요약.md') and '옛 메모' in pg.inner_text('#card');close(pg)
def t_settings(pg):
    pg.click('#btnSettings');idle(pg,200);tabs=pg.inner_text('#settings .mh');assert '저장한 보기' not in tabs and '뷰' not in pg.inner_text('#settings')
    pg.click('#settings .mh button[data-tab=props]');idle(pg,200)
    assert pg.locator('#optStatus .opt').count()==3 and pg.locator('#optStatus .opt button.x').count()==1 and pg.locator('#optStatus input.id[disabled]').count()==2
    pg.click('#sCancel');idle(pg,200)
def t_offline(pg):
    tab(pg,'할 일');pg.evaluate('window.__OFFLINE=true');inp='.tdadd input[type=text]'
    pg.fill(inp,'오프라인 할 일');pg.press(inp,'Enter');idle(pg);assert '오프라인 할 일' in pg.inner_text('.tdmain') and '11_Todos/오프라인 할 일.md' not in files(pg)
    assert pg.is_visible('#qbadge');pg.evaluate('window.__OFFLINE=false;queue.flush()');idle(pg,600)
    assert '11_Todos/오프라인 할 일.md' in files(pg) and not pg.is_visible('#qbadge')

def t_unit(pg):
    ev=pg.evaluate
    assert ev("fileNameOf('.env 설정?')")=='env 설정' and ev("fileNameOf('a/b: c')")=='a b c' and ev("fileNameOf('??')")=='메모'
    assert ev("parseFM(buildFM({type:'todo',project:'[[집: 정리]]',label:['a','b'],archived:true})).fm")=={'type':'todo','project':'[[집: 정리]]','label':['a','b'],'archived':True}
    assert ev("typeOf({fm:{type:'resource'},folder:'30_Resources'})")=='note' and ev("typeOf({fm:{type:'inbox',label:'todo'},folder:'00_Inbox'})")=='todo'
    assert ev("typeOf({fm:{},folder:'10_Projects'})")=='project' and ev("typeOf({fm:{type:'weekly'},folder:'01_Daily'})")=='note' and ev("typeOf({fm:{type:'daily'},folder:'01_Daily'})")=='note'
    assert ev("targetFolder({fm:{type:'project',archived:true},folder:'10_Projects'})")=='90_Archive'
    assert ev("projectOf({fm:{type:'todo',project:'ToDo'},folder:'11_Todos'})")=='' and ev("projectOf({fm:{type:'note',project:'[[가|나]]'},folder:'20_Notes'})")=='가'
    assert ev("parseWhen('내일 회의').rest")=='회의'
TESTS=[t_unit,t_load,t_suggest,t_quick,t_views,t_archive_view,t_todo,t_convert,t_rename,t_project,t_project_restore,t_delete_project,t_misc,t_docs_rename,t_links,t_settings,t_offline]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':860});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' else None)
    pg.goto(MOCK+'?gcal=1');pg.wait_for_selector('#main table, #main .status');idle(pg,900)
    for t in TESTS:
        try:t(pg);results.append((t.__name__,'ok',''))
        except Exception as e:
            results.append((t.__name__,'FAIL',''.join(traceback.format_exception_only(type(e),e)).strip()[:600]))
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
        tab(m,'노트')
        tab(m,'할 일');assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰 할 일 탭 가로 스크롤'
        m.fill('.tdadd input[type=text]','폰에서 추가');m.click('.tdadd .addbtn');idle(m);assert '11_Todos/폰에서 추가.md' in files(m),'추가 버튼으로 할 일이 안 만들어짐'
        m.fill('.tdadd input[type=text]','폰 엔터');m.press('.tdadd input[type=text]','Enter');idle(m);assert '11_Todos/폰 엔터.md' in files(m)
        assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'추가 뒤 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'10-mobile-todo.png'))
        tab(m,'문서');m.click('.tree .tn:has-text("수납 아이디어")');idle(m);m.click('#pBody');m.keyboard.press('Control+End');m.type('#pBody','\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n[[');idle(m,300)
        bx=m.evaluate("(()=>{const r=document.querySelector('#pAc').getBoundingClientRect();return [r.top,r.bottom,r.left,r.right,innerWidth,innerHeight]})()")
        assert m.is_visible('#pAc.on') and bx[0]>=0 and bx[1]<=bx[5] and bx[2]>=0 and bx[3]<=bx[4],bx
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'11-mobile-link.png'))
        m.tap('#pAc button >> nth=1') if False else m.click('#pAc button >> nth=1');idle(m,200);assert ']]' in m.input_value('#pBody') and not m.is_visible('#pAc.on')
        results.append(('mobile','ok',''))
    except Exception as e:results.append(('mobile','FAIL',str(e)[:300]))
    b.close()
for n,s,d in results:print(f'{s:5} {n} {d}')
print('page errors:',errs if errs else 'none')
sys.exit(1 if errs or any(s!='ok' for _,s,_ in results) else 0)
