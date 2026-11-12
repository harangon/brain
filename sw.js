// 앱 껍데기만 캐시. 노트 데이터는 항상 GitHub에서.
const C='brain-shell-2026-11-12f'; // 배포할 때마다 바꾼다 → 설치된 앱에 '새 버전' 띠가 뜬다
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(['./','./index.html','./manifest.json','./icon.svg'])));self.skipWaiting();});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k)))));self.clients.claim();});
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(u.origin!==location.origin)return;e.respondWith(fetch(e.request).then(r=>{caches.open(C).then(c=>c.put(e.request,r.clone()));return r;}).catch(()=>caches.match(e.request)));});
