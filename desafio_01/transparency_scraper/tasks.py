import base64
import logging
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

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            logger.info(f"Navigating to {url}")
            page.goto(url, timeout=max_interaction_timeout)

            logger.info("Clicking 'Consulta Pessoa Física' button")
            page.locator('#button-consulta-pessoa-fisica').click(timeout=max_interaction_timeout)

            logger.info(f"Searching for: '{identifier}'")
            search_box_locator = page.get_by_role('searchbox', name='Busque por Nome, Nis ou CPF (')
            search_box_locator.click(timeout=max_interaction_timeout)
            formated_identifier = f'"{identifier}"'
            search_box_locator.fill(formated_identifier, timeout=max_interaction_timeout)

            logger.info("Clicking 'Enviar dados do formulário de busca'")
            page.get_by_role('button', name='Enviar dados do formulário de busca').click(timeout=max_interaction_timeout)

            logger.info("Clicking the result for: ", identifier)
            page.get_by_role("link", name=identifier).click(timeout=max_interaction_timeout)

            logger.info("Waiting for data section to load")
            page.locator("section.dados-tabelados").wait_for(timeout=existence_check_timeout)

            logger.info("Extracting data fields")

            nome = page.locator("section.dados-tabelados strong:text('Nome') + span").inner_text().strip()
            cpf = page.locator("section.dados-tabelados strong:text('CPF') + span").inner_text().strip()
            localidade = page.locator("section.dados-tabelados strong:text('Localidade') + span").inner_text().strip()

            logger.info("Clicking 'Recebimentos de recursos'")
            time.sleep(5)
            page.get_by_role("button", name="Recebimentos de recursos").click(timeout=existence_check_timeout)

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
                        nis = columns.nth(1).inner_text().strip()

                        benefit_data.append({
                            "nis": nis,
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

            browser.close()
            return scraped_data

    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright timeout during scraping for '{identifier}': {e}")
        if browser and browser.is_connected():
            browser.close()
        return {"error": "A timeout occurred during scraping.", "details": str(e), "identifier": identifier}
    except Exception as e:
        logger.error(f"An unexpected error occurred during scraping for '{identifier}': {e}", exc_info=True)
        if browser and browser.is_connected():
            browser.close()
        return {"error": "An unexpected error occurred.", "details": str(e), "identifier": identifier}