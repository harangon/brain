"""index.html 에 mock.js 를 끼워 넣어 저장소 없이 여는 테스트 페이지를 만든다.  python3 tests/build_mock.py [출력 경로]"""
import sys,re,pathlib
root=pathlib.Path(__file__).resolve().parent.parent
out=pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/brain-mock.html')
s=(root/'index.html').read_text(encoding='utf-8');mock=(root/'tests'/'mock.js').read_text(encoding='utf-8')
mark="/* 새 버전 감지"
assert s.count(mark)==1
s=s.replace(mark,mock+"\n"+mark).replace("if('serviceWorker' in navigator){","if(false){")
out.write_text(s,encoding='utf-8')
js=re.search(r'<script>\n([\s\S]*)</script>',s).group(1)
pathlib.Path(str(out)+'.js').write_text(js,encoding='utf-8')
print(out)
