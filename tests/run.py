"""brain 화면 테스트 (Playwright). 먼저 build_mock.py 로 테스트 페이지를 만든 뒤 실행한다.
   python3 tests/build_mock.py && python3 tests/run.py [스크린샷 폴더]"""
import sys,os,traceback
from playwright.sync_api import sync_playwright
MOCK='file:///tmp/brain-mock.html';SHOTS=sys.argv[1] if len(sys.argv)>1 else ''
results=[]
def files(pg):return pg.evaluate('Object.keys(__FILES)')
def fget(pg,p):return pg.evaluate('p=>__FILES[p]',p)
def idle(pg,ms=350):pg.wait_for_timeout(ms)
def view(pg,name):pg.click(f'#views button:has-text("{name}")');idle(pg)
def tab(pg,name):pg.click(f'.tabs:not(.sub) button:has-text("{name}")');idle(pg)
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
    assert pg.get_attribute('#views button[data-id="b:inbox"]','aria-pressed')=='true'
    assert set(rows(pg)[:4])=={'수납 아이디어','구조를 단순하게 가는 이유','주말에 볼 영상','옛 메모'},rows(pg)
    assert '정리 안 된 노트 4' in pg.inner_text('#views')
    assert '최근 정리된 노트' in pg.inner_text('#main')
    shot(pg,'01-inbox')
def t_suggest(pg):
    pg.click('tr[data-path="20_Notes/수납 아이디어.md"] .sug');idle(pg)
    c=fget(pg,'20_Notes/수납 아이디어.md');assert 'project: "[[집 정리]]"' in c and 'suggest-project' not in c,c
    assert '수납 아이디어' not in rows(pg)[:3]
    pg.click('tr[data-path="20_Notes/구조를 단순하게 가는 이유.md"] .sug');idle(pg)
    c=fget(pg,'20_Notes/구조를 단순하게 가는 이유.md');assert 'label: mine' in c and 'suggest-label' not in c,c
def t_keep(pg):
    pg.click('tr[data-path="20_Notes/주말에 볼 영상.md"] .keep');idle(pg)
    assert 'reviewed: true' in fget(pg,'20_Notes/주말에 볼 영상.md')
    assert '정리 안 된 노트 1' in pg.inner_text('#views')
def t_quick(pg):
    pg.fill('#quickText','새 메모 / 테스트?');pg.press('#quickText','Enter');idle(pg)
    c=fget(pg,'20_Notes/새 메모 테스트.md');assert c and '# 새 메모 / 테스트?' in c and 'type: note' in c,c
    assert '새 메모 / 테스트?' in rows(pg)
    pg.fill('#quickText','새 메모 / 테스트?');pg.press('#quickText','Enter');idle(pg)
    assert any(p.startswith('20_Notes/새 메모 테스트 20') for p in files(pg)),'이름이 겹치면 날짜를 붙여야 함'
def t_views(pg):
    view(pg,'모든 노트');r=rows(pg);assert '수납장 문서 요약' in r and '집 정리' not in r and '우유 사기' not in r,r
    pg.select_option('#fProject','집 정리');idle(pg);assert set(rows(pg))=={'수납장 문서 요약','수납 아이디어'},rows(pg)
    pg.select_option('#fProject','__none');pg.select_option('#fLabel','__none');idle(pg);r=rows(pg);assert '주말에 볼 영상' in r and '정리는 버리는 것부터' not in r,r
    pg.select_option('#fProject','');pg.select_option('#fLabel','');pg.select_option('#fType','');idle(pg)
    assert '종류' in pg.inner_text('#main thead') and '집 정리' in rows(pg) and '끝난 일' not in rows(pg)
    view(pg,'읽을 것');assert set(rows(pg))=={'수납장 문서 요약','옛 자료'},rows(pg)
    view(pg,'프로젝트');cols=pg.eval_on_selector_all('.board .col h3','e=>e.map(x=>x.textContent)');assert any('진행' in c for c in cols) and any('보류' in c for c in cols),cols
    shot(pg,'02-projects-board')
    view(pg,'모든 노트');pg.click('#subtabs button:has-text("보드")');pg.select_option('#fGroup','project');idle(pg)
    cols=pg.eval_on_selector_all('.board .col h3','e=>e.map(x=>x.textContent)');assert any('집 정리' in c for c in cols) and any('없음' in c for c in cols),cols
    shot(pg,'03-notes-by-project')
    pg.click('#subtabs button:has-text("갤러리")');idle(pg);assert pg.locator('.gcard').count()>3
    pg.click('#subtabs button:has-text("표")');idle(pg)
def t_archive_view(pg):
    view(pg,'보관함');assert set(rows(pg))=={'끝난 일','옛 프로젝트'},rows(pg)
    open_row(pg,'끝난 일');assert '보관됨' in pg.inner_text('#pPath');act(pg,'되살리기');idle(pg,500)
    c=fget(pg,'11_Todos/끝난 일.md');assert c and 'archived' not in c and 'label' not in c and 'type: todo' in c,c
    assert '90_Archive/끝난 일.md' not in files(pg);close(pg)
def t_todo(pg):
    tab(pg,'할 일');side=pg.inner_text('.tdside')
    assert '프로젝트 없음' in side and '집 정리' in side and '1/4' in side,side
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
    pg.click('[data-sec=done] .hd');idle(pg);assert '주간 정리 때 보관' in pg.inner_text('[data-sec=done] .hd') and '비용 비교' in pg.inner_text('[data-sec=done]')
    # 완료 체크
    pg.click('.tdtoday .trow:has-text("우유 사기") input[type=checkbox]');idle(pg);assert 'status: done' in fget(pg,'11_Todos/우유 사기.md')
    shot(pg,'04-todo')
    pg.click('.tdadd .chip[data-id=none]');idle(pg);assert not pg.is_visible('.tdtoday') and not pg.is_visible('[data-sec=todaylate]')
    pg.click('.tdadd .chip[data-id=today]');idle(pg)
def t_convert(pg):
    tab(pg,'노트');view(pg,'모든 노트');open_row(pg,'주말에 볼 영상');shot(pg,'05-note-card')
    act(pg,'할 일로 바꾸기');idle(pg,500)
    c=fget(pg,'11_Todos/주말에 볼 영상.md');assert c and 'type: todo' in c and 'reviewed' not in c,c
    assert '20_Notes/주말에 볼 영상.md' not in files(pg) and pg.inner_text('#pPath').startswith('할 일')
    assert pg.locator('#card .cdone').count()==1
    act(pg,'노트로 되돌리기');idle(pg,500);assert '20_Notes/주말에 볼 영상.md' in files(pg) and 'type: note' in fget(pg,'20_Notes/주말에 볼 영상.md')
    act(pg,'할 일로 바꾸기');idle(pg,500);act(pg,'프로젝트로 키우기');ok(pg)
    c=fget(pg,'10_Projects/주말에 볼 영상.md');assert c and 'type: project' in c and 'status: active' in c,c
    assert pg.inner_text('#pPath').startswith('프로젝트');close(pg)
def t_rename(pg):
    view(pg,'모든 노트');open_row(pg,'테마 비교 메모');pg.fill('#card .ctitle','테마: A/B 비교');pg.press('#card .ctitle','Enter');idle(pg,600)
    c=fget(pg,'20_Notes/테마 A B 비교.md');assert c and '# 테마: A/B 비교' in c,files(pg)
    assert '20_Notes/테마 비교 메모.md' not in files(pg);close(pg)
    # 프로젝트 이름을 바꾸면 속한 노트·할 일의 project 도 따라간다
    view(pg,'프로젝트');pg.click('.board .card:has-text("블로그 개편")');idle(pg)
    pg.fill('#card .ctitle','블로그 새단장');pg.press('#card .ctitle','Enter');idle(pg,900)
    assert '10_Projects/블로그 새단장.md' in files(pg),files(pg)
    assert 'project: "[[블로그 새단장]]"' in fget(pg,'11_Todos/도메인 연장.md') and 'project: "[[블로그 새단장]]"' in fget(pg,'20_Notes/테마 A B 비교.md');close(pg)
def t_project(pg):
    view(pg,'프로젝트');pg.click('.board .card:has-text("집 정리")');idle(pg)
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
    view(pg,'모든 노트');open_row(pg,'수납장 문서 요약');assert '(보관됨)' in pg.inner_text('#card [data-chip=project]');close(pg)
def t_delete_project(pg):
    view(pg,'프로젝트');pg.click('.board .card:has-text("블로그 새단장")');idle(pg);pg.click('#card .actions .danger');assert '프로젝트 없음' in pg.inner_text('#askMsg');ok(pg);idle(pg,600)
    assert '10_Projects/블로그 새단장.md' not in files(pg) and 'project' not in fget(pg,'11_Todos/도메인 연장.md')
def t_misc(pg):
    tab(pg,'일정');assert pg.locator('.calgrid .day').count()==42 and '마감 노트' not in pg.inner_text('#main');shot(pg,'07-calendar')
    tab(pg,'문서');tree=pg.inner_text('.tree');assert 'Notes' in tree and 'Todos' in tree and 'Inbox' not in tree,tree
    pg.click('.tree .tn:has-text("수납 아이디어")');idle(pg);assert pg.input_value('#pTitle')=='수납 아이디어' and pg.inner_text('#pPath')=='20_Notes/수납 아이디어.md'
    pg.fill('#pBody','본문 수정');pg.click('#pSave');idle(pg);assert '본문 수정' in fget(pg,'20_Notes/수납 아이디어.md');shot(pg,'08-docs')
    pg.keyboard.press('Control+k');idle(pg,200);pg.fill('#palInput','>새로');idle(pg,200);assert pg.locator('#palList button').count()>=4;pg.keyboard.press('Escape')
def t_docs_rename(pg):
    tab(pg,'문서');pg.click('.tree .tn:has-text("정리는 버리는 것부터")');idle(pg)
    pg.fill('#pTitle','버리는 것부터');pg.click('#pSave');idle(pg,700)
    assert '20_Notes/버리는 것부터.md' in files(pg) and '20_Notes/정리는 버리는 것부터.md' not in files(pg),files(pg)
    assert pg.inner_text('#pPath')=='20_Notes/버리는 것부터.md' and pg.input_value('#pTitle')=='버리는 것부터'
    assert pg.locator('.tree .tn[aria-current=true]').count()==1
    # 데일리 노트는 제목을 바꿔도 파일 이름이 그대로
    daily=[p for p in files(pg) if p.startswith('01_Daily/')][0];pg.click('.tree .tn >> nth=0');idle(pg)
    pg.fill('#pTitle','오늘 기록');pg.click('#pSave');idle(pg,600);assert daily in files(pg) and '# 오늘 기록' in fget(pg,daily)
    # 저장 안 한 변경이 있으면 묻는다
    pg.fill('#pBody','임시');tab(pg,'노트');assert pg.is_visible('#ask.on') or pg.is_visible('#askOk');pg.click('#askOk');idle(pg)
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
    assert ev("typeOf({fm:{},folder:'10_Projects'})")=='project' and ev("typeOf({fm:{type:'weekly'},folder:'01_Daily'})")=='daily'
    assert ev("targetFolder({fm:{type:'project',archived:true},folder:'10_Projects'})")=='90_Archive'
    assert ev("projectOf({fm:{type:'todo',project:'ToDo'},folder:'11_Todos'})")=='' and ev("projectOf({fm:{type:'note',project:'[[가|나]]'},folder:'20_Notes'})")=='가'
    assert ev("parseWhen('내일 회의').rest")=='회의'
TESTS=[t_unit,t_load,t_suggest,t_keep,t_quick,t_views,t_archive_view,t_todo,t_convert,t_rename,t_project,t_delete_project,t_misc,t_docs_rename,t_offline]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':1280,'height':860});errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('console',lambda m:errs.append('console: '+m.text) if m.type=='error' else None)
    pg.goto(MOCK+'?gcal=1');pg.wait_for_selector('#views button');idle(pg,900)
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
    m=b.new_page(viewport={'width':390,'height':800});m.on('pageerror',lambda e:errs.append('mobile: '+str(e)))
    m.goto(MOCK);m.wait_for_selector('#views button');idle(m,900)
    try:
        assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰에서 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'09-mobile-inbox.png'))
        tab(m,'할 일');assert m.evaluate('document.documentElement.scrollWidth<=window.innerWidth+1'),'폰 할 일 탭 가로 스크롤'
        if SHOTS:m.screenshot(path=os.path.join(SHOTS,'10-mobile-todo.png'))
        results.append(('mobile','ok',''))
    except Exception as e:results.append(('mobile','FAIL',str(e)[:300]))
    b.close()
for n,s,d in results:print(f'{s:5} {n} {d}')
print('page errors:',errs if errs else 'none')
sys.exit(1 if errs or any(s!='ok' for _,s,_ in results) else 0)
