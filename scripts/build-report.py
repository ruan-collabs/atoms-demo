"""Create a self-contained evidence report from maintained Markdown and test output."""
import base64
import html
import re
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
source=(root/'docs/SELF_TEST.md').read_text()

def markdown(text):
    parts=[];table=False
    for line in text.splitlines():
        if line.startswith('|'):
            if re.fullmatch(r'[| :\-]+',line):continue
            if not table:parts.append('<div class="scroll"><table>');table=True
            cells=line.strip('|').split('|');parts.append('<tr>'+''.join('<td>'+inline(c.strip())+'</td>' for c in cells)+'</tr>');continue
        if table:parts.append('</table></div>');table=False
        if not line.strip():continue
        if line.startswith('### '):parts.append('<h3>'+inline(line[4:])+'</h3>')
        elif line.startswith('## '):parts.append('<h2>'+inline(line[3:])+'</h2>')
        elif line.startswith('# '):parts.append('<h1>'+inline(line[2:])+'</h1>')
        elif line.startswith('- '):parts.append('<p class="bullet">• '+inline(line[2:])+'</p>')
        else:parts.append('<p>'+inline(line)+'</p>')
    if table:parts.append('</table></div>')
    return ''.join(parts)
def inline(text):return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',html.escape(text))
results=[]
for name in ('backend-test-results.xml','frontend-test-results.xml'):
    tree=ET.parse(root/'docs'/name);cases=tree.findall('.//testcase')
    results.append(f'{name}: {len(cases)} tests, {len(tree.findall(".//failure"))} failures')
image=root/'docs/evidence/editor-preview.png'
image_html='<figure><img src="data:image/png;base64,'+base64.b64encode(image.read_bytes()).decode()+'" alt="实际浏览器编辑器预览截图"><figcaption>实际浏览器截图：构建2紫色任务板、保留的完成记录和明确Mock标识。</figcaption></figure>' if image.exists() else ''
evidence=[]
for path in sorted((root/'docs/evidence').glob('*.txt')):
    # Avoid embedding temporary signed preview URLs in shareable report.
    text=re.sub(r'(signature=)[0-9a-f]+',r'\1[redacted]',path.read_text())
    evidence.append('<details><summary>'+html.escape(path.name)+'</summary><pre>'+html.escape(text)+'</pre></details>')
body=markdown(source)+image_html+'<h2>附录：Mock登记</h2>'+markdown((root/'docs/MOCK_REGISTER.md').read_text())+'<h2>附录：原始浏览器DOM证据</h2>'+''.join(evidence)
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Atoms 本地开发与自测报告</title><style>:root{font-family:system-ui,"PingFang SC",sans-serif;color:#243148;background:#f3f5fa}body{margin:0}main{max-width:1060px;margin:35px auto;padding:42px;background:white;border-radius:16px;box-shadow:0 10px 40px #2233530a}h1{font-size:34px;line-height:1.4;margin:0 0 25px}h2{font-size:24px;border-top:1px solid #e5e9f1;padding-top:30px;margin-top:38px}h3{font-size:18px}p{line-height:1.9;font-size:14px;color:#50607a}strong{color:#263b65}table{border-collapse:collapse;width:100%;font-size:12px;line-height:1.8}td{border:1px solid #e0e6f1;padding:10px;vertical-align:top}tr:first-child{background:#edf1ff;font-weight:600}tr:nth-child(even){background:#f9faff}.scroll{overflow:auto}figure{margin:30px 0}img{max-width:100%;max-height:850px;border:1px solid #dbe3f2;border-radius:10px}figcaption{font-size:12px;color:#68768e;margin-top:9px}details{border:1px solid #e0e5f1;border-radius:8px;margin:10px 0;padding:12px}summary{cursor:pointer;font-size:13px;color:#536797}pre{font:12px/1.7 system-ui;white-space:pre-wrap;overflow-wrap:anywhere;background:#f7f9fd;padding:12px}.badge{color:#8b5b12;background:#fff3d8;padding:13px;border-radius:8px}.metrics{background:#eff5ef;padding:14px;border-radius:8px;font-size:12px}@media(max-width:700px){main{margin:0;padding:25px;border-radius:0}h1{font-size:27px}td{min-width:140px}}@media print{details{display:none}main{margin:0;box-shadow:none}}</style></head><body><main><div class="badge">本地Mock辅助闭环通过 ≠ 真实生产全项通过</div><div class="metrics">'''+html.escape(' | '.join(results))+'''</div>'''+body+'''</main></body></html>'''
output=root/'artifacts/Atoms自测报告.html';output.write_text(page,encoding='utf-8');print(output)
