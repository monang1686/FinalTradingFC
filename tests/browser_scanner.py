"""Optional browser checks: run from repo root after generating work/scanner-demo.json.
Requires Playwright and Chromium; no third-party network calls.
"""
import json
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
server=ThreadingHTTPServer(("127.0.0.1",0),SimpleHTTPRequestHandler)
Thread(target=server.serve_forever,daemon=True).start()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    for width in (375,390,1280):
        page=browser.new_page(viewport={'width':width,'height':844})
        page.goto('http://127.0.0.1:'+str(server.server_port)+'/experimental/scanner.html')
        page.set_input_files('#file','work/scanner-demo.json')
        page.wait_for_function("document.querySelectorAll('article').length === 3")
        assert '0 segnali reali' in page.locator('#status').inner_text()
        page.select_option('#filter','candidates')
        assert page.locator('article').count()==1
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        data=json.loads(Path('work/scanner-demo.json').read_text());data['rows'][0]['name']='<img src=x onerror=alert(1)>'
        page.set_input_files('#file',{'name':'xss.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
        page.wait_for_function("document.querySelector('article h2').textContent.includes('<img')")
        assert page.locator('article img').count()==0
        data['data_kind']='production'
        page.set_input_files('#file',{'name':'real.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Errore:')")
        assert page.locator('article').count()==0
        page.click('#clear')
        assert 'Nessun report' in page.locator('#status').inner_text()
        page.close()
    browser.close()
print('PASS: 375/390/1280px, labels, candidate filter, no overflow, escaped HTML, reject production, clear')
