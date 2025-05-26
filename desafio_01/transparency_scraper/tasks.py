import base64
import logging
import random
from celery import shared_task
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=1)
def scrape_portal_data(self, identifier: str, search_filter: str = None):
    url = 'https://portaldatransparencia.gov.br/pessoa/visao-geral'
    scraped_data = {}
    max_interaction_timeout = 45000 
    existence_check_timeout = 15000

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-default-apps',
                    '--disable-translate',
                    '--disable-device-discovery-notifications',
                    '--disable-software-rasterizer',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection',
                    '--disable-hang-monitor',
                    '--disable-client-side-phishing-detection',
                    '--disable-component-update',
                    '--disable-domain-reliability',
                    '--disable-sync',
                    '--disable-background-networking',
                    '--user-agent=' + random.choice(user_agents)
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(user_agents),
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
            )
            
            page = context.new_page()
            
            await_stealth_script = """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'],
                });
                
                window.chrome = {
                    runtime: {},
                };
                
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({ state: 'granted' }),
                    }),
                });
            """
            
            page.add_init_script(await_stealth_script)

            time.sleep(random.uniform(2, 5))

            logger.info(f"Navigating to {url}")
            page.goto(url, timeout=max_interaction_timeout, wait_until='domcontentloaded')

            time.sleep(random.uniform(3, 6))

            logger.info("Clicking 'Consulta Pessoa Física' button")
            page.locator('#button-consulta-pessoa-fisica').click(timeout=max_interaction_timeout)

            time.sleep(random.uniform(2, 4))

            logger.info(f"Searching for: '{identifier}'")
            search_box_locator = page.get_by_role('searchbox', name='Busque por Nome, Nis ou CPF (')
            
            search_box_locator.click(timeout=max_interaction_timeout)
            time.sleep(random.uniform(1, 2))
            
            formated_identifier = f'"{identifier}"'
            for char in formated_identifier:
                search_box_locator.type(char, delay=random.uniform(50, 150))
            
            time.sleep(random.uniform(1, 3))

            logger.info("Clicking 'Enviar dados do formulário de busca'")
            page.get_by_role('button', name='Enviar dados do formulário de busca').click(timeout=max_interaction_timeout)

            time.sleep(random.uniform(3, 5))

            logger.info("Clicking the result for: ", identifier)
            page.get_by_role("link", name=identifier).click(timeout=max_interaction_timeout)

            time.sleep(random.uniform(3, 5))

            logger.info("Waiting for data section to load")
            page.locator("section.dados-tabelados").wait_for(timeout=existence_check_timeout)

            logger.info("Extracting data fields")

            nome = page.locator("section.dados-tabelados strong:text('Nome') + span").inner_text().strip()
            cpf = page.locator("section.dados-tabelados strong:text('CPF') + span").inner_text().strip()
            localidade = page.locator("section.dados-tabelados strong:text('Localidade') + span").inner_text().strip()

            logger.info("Clicking 'Recebimentos de recursos'")
            time.sleep(random.uniform(3, 6))
            
            recebimentos_button = page.get_by_role("button", name="Recebimentos de recursos")
            recebimentos_button.scroll_into_view_if_needed()
            time.sleep(random.uniform(1, 2))
            recebimentos_button.click(timeout=existence_check_timeout)

            page.locator("#tabela-visao-geral-sancoes tbody tr").first.wait_for(timeout=existence_check_timeout)

            logger.info("Scraping accordion content")

            accordion_data = {}
            accordion_section_locator = page.locator("div#accordion1 div.content")

            accordion_ready = page.locator("div#accordion1 div.content div.box-ficha__resultados table").first
            accordion_ready.wait_for(timeout=existence_check_timeout)

            accordion_sections = accordion_section_locator.locator("div.box-ficha__resultados")

            count = accordion_sections.count()
            logger.info(f"Found {count} accordion sections with content")

            for i in range(count):
                section = accordion_sections.nth(i)
                
                title_locator = section.locator("strong").first
                title = title_locator.inner_text().strip()

                benefit_data = []

                rows = section.locator("table tbody tr")
                row_count = rows.count()

                for j in range(row_count):
                    row = rows.nth(j)
                    columns = row.locator("td")
                    if columns.count() >= 4:
                        valor = columns.nth(3).inner_text().strip()

                        benefit_data.append({
                            "valor_recebido": valor
                        })

                accordion_data[title] = benefit_data

            logger.info("Taking screenshot of the final page")
            screenshot_bytes = page.screenshot(full_page=True)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

            scraped_data = {
                "nome": nome,
                "cpf": cpf,
                "localidade": localidade,
                "screenshot_base64": screenshot_base64,
                "recebimentos": accordion_data
            }

            context.close()
            browser.close()
            return scraped_data

    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright timeout during scraping for '{identifier}': {e}")
        try:
            if 'context' in locals():
                context.close()
            if 'browser' in locals() and browser.is_connected():
                browser.close()
        except:
            pass
        return {"error": "A timeout occurred during scraping.", "details": str(e), "identifier": identifier}
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping for '{identifier}': {e}", exc_info=True)
        try:
            if 'context' in locals():
                context.close()
            if 'browser' in locals() and browser.is_connected():
                browser.close()
        except:
            pass
        return {"error": "An unexpected error occurred.", "details": str(e), "identifier": identifier}
    