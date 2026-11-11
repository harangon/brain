/* 테스트용 가짜 저장소: GitHub API 와 Apps Script 를 메모리로 흉내 낸다. build_mock.py 가 index.html 에 끼워 넣는다 */
const __T=today(),__D=n=>addDays(__T,n);
const __fm=(o,body)=>'---\n'+Object.entries(o).map(([k,v])=>`${k}: ${v}`).join('\n')+'\n---\n'+body;
const __FILES={
  '_templates/Project.md':'---\ntype: project\nstatus: active\ncreated: <% tp.date.now("YYYY-MM-DD") %>\nupdated: <% tp.date.now("YYYY-MM-DD") %>\n---\n# <% tp.file.title %>\n\n## 목표\n',
  ['01_Daily/'+__T+'.md']:__fm({type:'daily',created:__T},`# ${__T}\n\n## 메모\n`),
  '10_Projects/집 정리.md':__fm({type:'project',status:'active',created:__D(-9),updated:__D(-1),due:__D(10)},'# 집 정리\n\n창고와 베란다를 비운다.\n'),
  '10_Projects/블로그 개편.md':__fm({type:'project',status:'paused',label:'work',created:__D(-20),updated:__D(-5)},'# 블로그 개편\n\n보류 중\n'),
  '11_Todos/창고 치수 재기.md':__fm({type:'todo',project:'"[[집 정리]]"',created:__D(-3),due:__D(2)},'# 창고 치수 재기\n\n## 준비\n- [x] 줄자 찾기\n- [ ] 도면 그리기\n'),
  '11_Todos/업체 견적 받기.md':__fm({type:'todo',project:'"[[집 정리]]"',created:__D(-3),due:__D(3)},'# 업체 견적 받기\n'),
  '11_Todos/버릴 것 목록.md':__fm({type:'todo',project:'"[[집 정리]]"',created:__D(-3)},'# 버릴 것 목록\n'),
  '11_Todos/비용 비교.md':__fm({type:'todo',project:'"[[집 정리]]"',status:'done',created:__D(-6),updated:__D(-2)},'# 비용 비교\n'),
  '11_Todos/건강검진 예약.md':__fm({type:'todo',label:'work',created:__D(-1),due:__T},'# 건강검진 예약\n'),
  '11_Todos/우유 사기.md':__fm({type:'todo',created:__D(-1),due:__T},'# 우유 사기\n'),
  '11_Todos/도메인 연장.md':__fm({type:'todo',project:'"[[블로그 개편]]"',created:__D(-8),due:__D(-2)},'# 도메인 연장\n'),
  '11_Todos/책 반납.md':__fm({type:'todo',created:__D(-1),due:__D(20)},'# 책 반납\n'),
  '11_Todos/2026-11-01-옛-할-일.md':__fm({type:'todo',label:'todo',project:'ToDo',created:__D(-9)},'# 옛 할 일\n'),
  '20_Notes/수납 아이디어.md':__fm({type:'note',created:__D(-1),updated:__D(-1),'suggest-project':'"[[집 정리]]"'},'# 수납 아이디어\n\n벽 선반을 달면 바닥이 빈다.\n'),
  '20_Notes/구조를 단순하게 가는 이유.md':__fm({type:'note',created:__D(-1),updated:__D(-1),'suggest-label':'mine'},'# 구조를 단순하게 가는 이유\n\n분류에 드는 힘이 쓰는 힘보다 크면 안 된다.\n'),
  '20_Notes/주말에 볼 영상.md':__fm({type:'note',created:__D(-2),updated:__D(-2)},'# 주말에 볼 영상\n'),
  '20_Notes/수납장 문서 요약.md':__fm({type:'note',project:'"[[집 정리]]"',label:'[resource, read]',created:__D(-4),updated:__D(-3)},'# 수납장 문서 요약\n\n## 요약\n깊이 40cm 가 기준.\n'),
  '20_Notes/정리는 버리는 것부터.md':__fm({type:'note',label:'mine',created:__D(-5),updated:__D(-4)},'# 정리는 버리는 것부터\n'),
  '20_Notes/테마 비교 메모.md':__fm({type:'note',project:'"[[블로그 개편]]"',created:__D(-6),updated:__D(-6)},'# 테마 비교 메모\n\n[[수납 아이디어]]\n'),
  '00_Inbox/옛 메모.md':__fm({type:'inbox',created:__D(-7)},'옛 구조에서 온 메모\n'),
  '30_Resources/옛 자료.md':__fm({type:'resource',status:'active',label:'read',created:__D(-7),updated:__D(-7)},'# 옛 자료\n'),
  '90_Archive/옛 노트.md':__fm({type:'note',label:'read',archived:'true',created:__D(-40),updated:__D(-35)},'# 옛 노트\n'),
  '90_Archive/끝난 일.md':__fm({type:'todo',label:'todo',status:'archived',created:__D(-30),updated:__D(-20)},'# 끝난 일\n'),
  '90_Archive/옛 프로젝트.md':__fm({type:'project',status:'done',archived:'true',created:__D(-60),updated:__D(-30)},'# 옛 프로젝트\n'),
};
const __SHA={};let __seq=0;window.__LOG=[];window.__OFFLINE=false;window.__FILES=__FILES;
const __sha=p=>__SHA[p]||(__SHA[p]='s'+(++__seq));
const __net=()=>{if(window.__OFFLINE)throw new TypeError('Failed to fetch');};
api.tree=async()=>{__net();return{tree:Object.keys(__FILES).map(p=>({path:p,type:'blob',sha:__sha(p)}))};};
api.file=async(p,a)=>{__net();if(__FILES[p]!==undefined)return{sha:__sha(p),content:__FILES[p]};if(a)return null;throw new Error('GitHub 404 Not Found');};
api.put=async(p,c,sha,m)=>{__net();if(__FILES[p]!==undefined&&sha!==__sha(p))throw new Error(sha?'GitHub 409 does not match':'GitHub 422 sha was not supplied');
  __FILES[p]=c;__SHA[p]='n'+(++__seq);__LOG.push('PUT '+p+' | '+m);return{content:{sha:__SHA[p]}};};
api.del=async(p,sha,m)=>{__net();if(__FILES[p]===undefined)throw new Error('GitHub 404 Not Found');if(sha!==__sha(p))throw new Error('GitHub 409 does not match');delete __FILES[p];delete __SHA[p];__LOG.push('DEL '+p+' | '+m);};
api.req=async u=>{__net();if(u.includes('/commits'))return[{commit:{author:{date:new Date().toISOString()},message:'web: 테스트'}}];throw new Error('mock req '+u);};
api.putB64=async(p,b,sha,m)=>{__net();__FILES[p]='B64:'+b;__LOG.push('PUTB64 '+p);return{content:{sha:__sha(p)}};};
api.fileB64=async p=>__FILES[p]?__FILES[p].slice(4):null;
cfg.token='mock';localStorage.clear();
/* --- Apps Script 흉내 --- */
window.__EVENTS=[{id:'e1',cal:'c1',calName:'기본',color:'#4a86c5',title:'치과',allDay:false,start:__D(2)+'T15:00',end:__D(2)+'T16:00',location:'',desc:''},
 {id:'e2',cal:'c1',calName:'기본',color:'#4a86c5',title:'주간 회의',allDay:false,start:__T+'T13:00',end:__T+'T14:00',location:'',desc:''}];
window.fetch=async(url,opt)=>{const b=JSON.parse(opt.body);let out={};
  if(b.key!=='k')out={error:'unauthorized'};
  else if(b.action==='calendars')out={calendars:[{id:'c1',name:'기본',color:'#4a86c5',mine:true,primary:true}]};
  else if(b.action==='list')out={events:__EVENTS.filter(e=>e.start.slice(0,10)<b.to&&e.end.slice(0,10)>=b.from)};
  else if(b.action==='search')out={events:__EVENTS.filter(e=>e.title.includes(b.q))};
  else out={ok:true};
  return{ok:true,text:async()=>JSON.stringify(out)};};
if(new URLSearchParams(location.search).get('gcal'))cfg.gcal={url:'https://script.invalid/x',key:'k',cals:['c1'],names:{c1:'기본'}};
