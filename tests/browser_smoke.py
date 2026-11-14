"""Conferência visual opcional: python tests/browser_smoke.py (Playwright e Chrome)."""
import json, os, shutil, sys, threading, tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from doguia_usage.panel import servidor
from doguia_usage.model import Ctx
from playwright.sync_api import sync_playwright
with tempfile.TemporaryDirectory() as tmp:
 s=servidor(ctx=Ctx(home=Path(tmp),env={},platform='linux'))
 threading.Thread(target=s.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path=os.environ.get('DOGUIA_CHROME') or shutil.which('google-chrome') or shutil.which('chromium') or None,args=['--no-sandbox'])
   page=browser.new_page(viewport={'width':1360,'height':1000})
   errors=[]
   page.on('pageerror',lambda e: errors.append(str(e)))
   page.goto(f'http://127.0.0.1:{s.server_port}')
   page.get_by_role('button',name='Verificar ambiente').click()
   page.get_by_text('O computador está pronto para configurar o Display.',exact=True).wait_for()
   assert page.evaluate("document.fonts.check('16px Inter')")
   page.get_by_label('Endereço IP do Display').fill('192.168.31.15')
   page.get_by_role('button',name='Salvar e continuar').click()
   page.get_by_role('heading',name='Suas IAs, juntas na tela.').wait_for()
   page.get_by_role('button',name='Salvar e continuar').click()
   page.get_by_role('heading',name='Do seu jeito, a cada atualização.').wait_for()
   page.screenshot(path='/tmp/doguia-painel-desktop.png',full_page=True)
   page.set_viewport_size({'width':390,'height':844})
   page.screenshot(path='/tmp/doguia-painel-mobile.png',full_page=True)
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
   page.get_by_role('button',name='Salvar e continuar').click()
   page.get_by_role('heading',name='Pronto para acompanhar você.').wait_for()
   page.get_by_role('button',name='Salvar e continuar').click()
   page.get_by_role('button',name='Testar conexão e envio').wait_for()
   # O navegador exercita edição e aplicação sem enviar nada a um aparelho físico.
   gravados=[]
   def responder(route):
    action=route.request.url.rsplit('/',1)[-1]
    data=json.loads(route.request.post_data or '{}')
    if action.startswith('gravar-'):
     gravados.append((action,data))
    route.fulfill(json={'bri':55,'pet_x':70} if action in ('config','custom') else {'ok':True})
   page.route('**/api/config', responder)
   page.route('**/api/custom', responder)
   page.route('**/api/gravar-*', responder)
   page.get_by_role('button',name='Personalizar Display',exact=True).click()
   page.get_by_role('button',name='Ajustes do produto').click()
   page.get_by_label('Buscar ajuste').fill('Brilho')
   assert page.locator('[data-field="bri"]').is_visible()
   assert not page.locator('[data-field="name"]').is_visible()
   page.get_by_label('Buscar ajuste').fill('')
   page.locator('[data-edit="bri"]').fill('55')
   page.get_by_role('button',name='Aplicar alterações ao Display').click()
   page.get_by_role('status').filter(has_text='Alterações aplicadas').wait_for()
   assert gravados==[('gravar-config',{'bri':'55'})], gravados
   page.get_by_role('button',name='Estúdio da tela').click()
   assert page.locator('[data-edit="pet_act_name"]').is_disabled()
   page.locator('[data-edit="pet_x"]').fill('70')
   page.get_by_role('button',name='Aplicar alterações ao Display').click()
   page.get_by_role('status').filter(has_text='Alterações aplicadas').wait_for()
   assert gravados[-1]==('gravar-custom',{'pet_x':'70'}), gravados
   assert not errors, errors
   browser.close()
  print('Wizard desktop e mobile: ok; sem erros JavaScript ou overflow horizontal.')
 finally:
  s.shutdown();s.server_close()
