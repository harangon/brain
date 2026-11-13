/**
 * brain ↔ Google Calendar 프록시 (Google Apps Script)
 *
 * 설치: script.google.com → 새 프로젝트 → 이 파일 내용 붙여넣기 → KEY 값을 아무 긴 문자열로 바꾼다
 *       → 배포 → 새 배포 → 유형: 웹 앱, 실행 계정: 나, 액세스 권한: 모든 사용자 → 배포 → 웹 앱 URL(…/exec) 복사
 *       → brain ⚙ → 연결 → Google 캘린더에 URL과 KEY 입력
 * 코드를 고친 뒤에는 "배포 관리 → 새 버전"을 해야 반영된다.
 *
 * 시간대: 프로젝트 설정(⚙) → "appsscript.json 표시" 체크 → timeZone 을 "Asia/Seoul" 로. (기본이 다르면 시간이 어긋난다)
 *
 * 요청(모두 POST, 본문 JSON):
 *   {key, action:"calendars"}
 *   {key, action:"list", from:"2026-11-01", to:"2026-12-01", cals:"id1,id2"}
 *   {key, action:"search", q:"치과", cals:"…"}
 *   {key, action:"create", cal, title, date, time?, minutes?, desc?}
 *   {key, action:"update", cal, id, origDate, title?, date?, time?, minutes?, allDay?, location?}
 *   {key, action:"delete", cal, id, origDate}
 */
var KEY = 'CHANGE-ME-to-a-long-random-string';

// GET은 상태 확인용. 키는 URL에 남지 않도록 POST 본문으로만 받는다
function doGet() { return out_({ ok: true, app: 'brain gcal proxy', tz: Session.getScriptTimeZone() }); }
function doPost(e) {
  var p = {};
  try { p = JSON.parse(e.postData.contents); } catch (err) { return out_({ error: 'bad json' }); }
  return handle_(p);
}

function handle_(p) {
  if (!p.key || p.key !== KEY) return out_({ error: 'unauthorized' });
  try {
    switch (p.action) {
      case 'calendars': return out_(calendars_());
      case 'list':      return out_(list_(p));
      case 'search':    return out_(search_(p));
      case 'create':    return out_(create_(p));
      case 'update':    return out_(update_(p));
      case 'delete':    return out_(remove_(p));
      default:          return out_({ error: 'unknown action' });
    }
  } catch (err) { return out_({ error: String(err) }); }
}

function out_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

function cals_(p) {
  var all = CalendarApp.getAllCalendars();
  if (!p.cals) return all.filter(function (c) { return c.isOwnedByMe(); });
  var want = String(p.cals).split(',');
  return all.filter(function (c) { return want.indexOf(c.getId()) >= 0; });
}

function calendars_() {
  return { calendars: CalendarApp.getAllCalendars().map(function (c) {
    return { id: c.getId(), name: c.getName(), color: c.getColor(), mine: c.isOwnedByMe(), primary: c.getId() === CalendarApp.getDefaultCalendar().getId() };
  }) };
}

function fmt_(ev, cal) {
  var allDay = ev.isAllDayEvent();
  return {
    id: ev.getId(), cal: cal.getId(), calName: cal.getName(), color: cal.getColor(),
    title: ev.getTitle(), allDay: allDay,
    start: iso_(ev.getStartTime()), end: iso_(ev.getEndTime()),
    location: ev.getLocation() || '', desc: (ev.getDescription() || '').slice(0, 500), recurring: ev.isRecurringEvent()
  };
}
function iso_(d) { return Utilities.formatDate(d, Session.getScriptTimeZone(), "yyyy-MM-dd'T'HH:mm"); }

function list_(p) {
  var from = new Date(p.from + 'T00:00:00'), to = new Date(p.to + 'T00:00:00');
  var events = [];
  cals_(p).forEach(function (c) { c.getEvents(from, to).forEach(function (ev) { events.push(fmt_(ev, c)); }); });
  events.sort(function (a, b) { return a.start < b.start ? -1 : 1; });
  return { events: events, tz: Session.getScriptTimeZone() };
}

function search_(p) {
  var q = String(p.q || '').trim(); if (!q) return { events: [] };
  var from = new Date(); from.setFullYear(from.getFullYear() - 2);
  var to = new Date(); to.setFullYear(to.getFullYear() + 2);
  var events = [];
  cals_(p).forEach(function (c) { c.getEvents(from, to, { search: q }).forEach(function (ev) { events.push(fmt_(ev, c)); }); });
  events.sort(function (a, b) { return a.start < b.start ? -1 : 1; });
  return { events: events.slice(0, 100) };
}

function create_(p) {
  var cal = p.cal ? CalendarApp.getCalendarById(p.cal) : CalendarApp.getDefaultCalendar();
  if (!cal) return { error: 'calendar not found' };
  var title = String(p.title || '').trim(); if (!title) return { error: 'title required' };
  var ev;
  if (!p.time) {
    ev = cal.createAllDayEvent(title, new Date(p.date + 'T00:00:00'), { description: p.desc || '' });
  } else {
    var start = new Date(p.date + 'T' + p.time + ':00');
    var end = new Date(start.getTime() + (Number(p.minutes) || 60) * 60000);
    ev = cal.createEvent(title, start, end, { description: p.desc || '' });
  }
  return { event: fmt_(ev, cal) };
}

// 반복 일정의 회차 id는 getEventById로 못 찾을 수 있어, 그날의 일정 중에서 id로 찾는다
function find_(cal, id, origDate) {
  if (origDate) {
    var d = new Date(origDate + 'T00:00:00'), d2 = new Date(d.getTime() + 86400000);
    var hits = cal.getEvents(d, d2).filter(function (e) { return e.getId() === id; });
    if (hits.length) return hits[0];
  }
  return cal.getEventById(id);
}

function update_(p) {
  var cal = CalendarApp.getCalendarById(p.cal); if (!cal) return { error: 'calendar not found' };
  var ev = find_(cal, p.id, p.origDate); if (!ev) return { error: 'event not found' };
  if (p.title !== undefined) ev.setTitle(String(p.title));
  if (p.location !== undefined) ev.setLocation(String(p.location));
  if (p.date) {
    if (p.allDay || !p.time) {
      // 여러 날짜에 걸친 종일 일정은 길이를 지킨 채 옮긴다
      var d0 = new Date(p.date + 'T00:00:00'), days = 1;
      try { if (ev.isAllDayEvent()) days = Math.max(1, Math.round((ev.getAllDayEndDate() - ev.getAllDayStartDate()) / 86400000)); } catch (err) { days = 1; }
      if (days > 1) { try { ev.setAllDayDates(d0, new Date(d0.getTime() + days * 86400000)); } catch (err) { ev.setAllDayDate(d0); } }
      else ev.setAllDayDate(d0);
    }
    else {
      var start = new Date(p.date + 'T' + p.time + ':00');
      var minutes = Number(p.minutes) || Math.round((ev.getEndTime() - ev.getStartTime()) / 60000) || 60;
      ev.setTime(start, new Date(start.getTime() + minutes * 60000));
    }
  }
  return { event: fmt_(ev, cal), recurring: ev.isRecurringEvent() };
}

function remove_(p) {
  var cal = CalendarApp.getCalendarById(p.cal); if (!cal) return { error: 'calendar not found' };
  var ev = find_(cal, p.id, p.origDate); if (!ev) return { error: 'event not found' };
  ev.deleteEvent(); return { ok: true };
}
