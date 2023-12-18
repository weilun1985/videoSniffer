import json
import re,os
import tools
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse


playwright = sync_playwright().start()
browser = playwright.firefox.launch(headless=False)
log=tools.get_logger()

def get_page(url):
    cur_dir=os.path.dirname(os.path.realpath(__file__))
    host=tools.get_url_host(url)
    state = os.path.join(cur_dir, f'{host.replace(".","_")}.state.txt')
    if os.path.exists(state):
        context = browser.new_context(storage_state=state, ignore_https_errors=True)
    else:
        context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(url)
    log.info(f'goto:{url}')
    page.wait_for_load_state('networkidle')
    context.storage_state(path=state)

if __name__ == '__main__':
    url='http://xhslink.com/jQn5Gw'
    get_page(url)
    input('press any key to close!')