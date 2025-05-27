import base64
import logging
import random
import time
import unicodedata

from celery import shared_task
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


def normalize_string(text):
    normalized_text = unicodedata.normalize("NFKD", text)
    ascii_text = normalized_text.encode("ascii", "ignore").decode("utf-8")
    return ascii_text.casefold()


@shared_task(bind=True, max_retries=1)
def scrape_portal_data(self, identifier: str, search_filter: str = None):
    url = "https://portaldatransparencia.gov.br/pessoa/visao-geral"
    scraped_data = {}
    max_interaction_timeout = 45000
    existence_check_timeout = 15000

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-default-apps",
                    "--disable-translate",
                    "--disable-device-discovery-notifications",
                    "--disable-software-rasterizer",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--disable-features=TranslateUI",
                    "--disable-ipc-flooding-protection",
                    "--disable-hang-monitor",
                    "--disable-client-side-phishing-detection",
                    "--disable-component-update",
                    "--disable-domain-reliability",
                    "--disable-sync",
                    "--disable-background-networking",
                    "--user-agent=" + random.choice(user_agents),
                ],
            )

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=random.choice(user_agents),
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )

            page = context.new_page()

            stealth_script = """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({ query: () => Promise.resolve({ state: 'granted' }) }),
                });
            """

            page.add_init_script(stealth_script)

            logger.info(f"Navigating to {url}")
            page.goto(
                url, timeout=max_interaction_timeout, wait_until="domcontentloaded"
            )

            logger.info(f"Clicking 'Consulta' buton")
            page.locator("#button-consulta-pessoa-fisica").click(
                timeout=max_interaction_timeout
            )
            time.sleep(5)

            logger.info(f"Looking for filter: {search_filter}")
            if search_filter:
                refine_button = page.locator("button.header:has-text('Refine a Busca')")
                if refine_button.count():
                    refine_button.click()
                    time.sleep(5)
                    page.wait_for_timeout(500)

                filter_actions = {
                    normalize_string("Servidores e Pensionistas"): lambda: page.locator(
                        "#box-busca-refinada"
                    )
                    .get_by_text("Servidores e Pensionistas")
                    .click(),
                    normalize_string(
                        "Beneficiário de Programa Social"
                    ): lambda: page.locator("#box-busca-refinada")
                    .get_by_text("Beneficiário de Programa")
                    .click(),
                    normalize_string(
                        "Portador de cartão de pagamento do Governo Federal"
                    ): lambda: page.get_by_text("Portador de cartão de").click(),
                    normalize_string(
                        "Portador de cartão da defesa civil"
                    ): lambda: page.get_by_text("Portador de cartão da defesa").click(),
                    normalize_string("Possui sanção vigente"): lambda: page.get_by_text(
                        "Possui sanção vigente"
                    ).click(),
                    normalize_string(
                        "Ocupante de imóvel funcional"
                    ): lambda: page.get_by_text("Ocupante de imóvel funcional").click(),
                    normalize_string(
                        "Possui Contrato com o Governo Federal"
                    ): lambda: page.get_by_text(
                        "Possui Contrato com o Governo"
                    ).click(),
                    normalize_string(
                        "Favorecido de recurso público"
                    ): lambda: page.locator("#box-busca-refinada")
                    .get_by_text("Favorecido de recurso público")
                    .click(),
                    normalize_string("Emitente NFe"): lambda: page.get_by_text(
                        "Emitente NFe"
                    ).click(),
                }

                normalized_search_filter = normalize_string(search_filter)
                action_to_perform = filter_actions.get(normalized_search_filter)

                if action_to_perform:
                    logger.info(f"Applying filter: {normalized_search_filter}")
                    action_to_perform()
                    time.sleep(5)
                else:
                    logger.warning(
                        f"No action defined for normalized search_filter: '{normalized_search_filter}' (original: '{search_filter}')"
                    )

            logger.info(f"Searching for: '{identifier}'")
            search_box = page.get_by_role(
                "searchbox", name="Busque por Nome, Nis ou CPF ("
            )
            search_box.click(timeout=max_interaction_timeout)
            time.sleep(5)

            logger.info(f"Typing up '{identifier}'")
            for char in f'"{identifier}"':
                search_box.type(char, delay=random.uniform(50, 150))

            logger.info(f"Clicking search button")
            page.get_by_role(
                "button", name="Enviar dados do formulário de busca"
            ).click(timeout=max_interaction_timeout)
            time.sleep(5)

            logger.info(f"Clicking result for: {identifier}")
            try:
                result_links = page.get_by_role("link", name=identifier)
                if result_links.count() == 0:
                    logger.warning(f"No results found for identifier: {identifier}")
                    context.close()
                    browser.close()
                    return {
                        "message": f"Foram encontrados 0 resultados para o termo {identifier}"
                    }
                elif result_links.count() > 1:
                    logger.info(
                        f"Multiple results found for identifier: {identifier}. Clicking the first one."
                    )
                    result_links.first.click(timeout=max_interaction_timeout)
                    time.sleep(5)
                else:
                    result_links.click(timeout=max_interaction_timeout)
                    time.sleep(5)
            except PlaywrightTimeoutError:
                logger.warning(f"No results found for identifier: {identifier}")
                context.close()
                browser.close()
                return {
                    "message": f"Foram encontrados 0 resultados para o termo {identifier}"
                }

            page.locator("section.dados-tabelados").wait_for(
                timeout=existence_check_timeout
            )

            logger.info(f"Scraping person information")
            nome = (
                page.locator("section.dados-tabelados strong:text('Nome') + span")
                .inner_text()
                .strip()
            )
            cpf = (
                page.locator("section.dados-tabelados strong:text('CPF') + span")
                .inner_text()
                .strip()
            )
            localidade = (
                page.locator("section.dados-tabelados strong:text('Localidade') + span")
                .inner_text()
                .strip()
            )

            recebimentos_button = page.get_by_role(
                "button", name="Recebimentos de recursos"
            )
            recebimentos_button.scroll_into_view_if_needed()
            time.sleep(5)

            logger.info(f"Expanding benefits accordion")
            recebimentos_button.click(timeout=existence_check_timeout)
            time.sleep(5)

            page.locator("#tabela-visao-geral-sancoes tbody tr").first.wait_for(
                timeout=existence_check_timeout
            )

            accordion_data = {}

            benefit_blocks = page.locator("div#accordion1 div.br-table")
            block_count = benefit_blocks.count()

            logger.info("Scraping tables")
            for i in range(block_count):
                block = benefit_blocks.nth(i)

                title_el = block.locator("strong")
                if not title_el.count():
                    continue

                title = title_el.first.inner_text().strip()
                benefit_data = []

                table = block.locator("table")
                if not table.count():
                    continue

                rows = table.locator("tbody tr")
                row_count = rows.count()

                for j in range(row_count):
                    row = rows.nth(j)
                    columns = row.locator("td")
                    if columns.count() >= 4:
                        valor = columns.nth(3).inner_text().strip()

                        detail_link = columns.nth(0).locator("a")
                        if detail_link.count() > 0:
                            detail_url = detail_link.get_attribute("href")
                            if detail_url:
                                logger.info(f"Navigating to detail page: {detail_url}")
                                detail_page = context.new_page()
                                detail_page.add_init_script(stealth_script)
                                detail_page.goto(
                                    "https://portaldatransparencia.gov.br" + detail_url,
                                    timeout=max_interaction_timeout,
                                )
                                time.sleep(5)

                                logger.info(
                                    "Scraping detailed data tables from .dados-detalhados"
                                )
                                detailed_data = []

                                detailed_section = detail_page.locator(
                                    "section.dados-detalhados"
                                )
                                tables = detailed_section.locator("table")

                                for k in range(tables.count()):
                                    table = tables.nth(k)
                                    caption_el = table.locator("caption")
                                    caption = (
                                        caption_el.inner_text().strip()
                                        if caption_el.count()
                                        else f"Tabela {k+1}"
                                    )

                                    headers = []
                                    header_cells = table.locator("thead tr th")
                                    for h in range(header_cells.count()):
                                        headers.append(
                                            header_cells.nth(h).inner_text().strip()
                                        )

                                    rows_data = []

                                    while True:
                                        body_rows = table.locator("tbody tr")
                                        row_count = body_rows.count()

                                        for r in range(row_count):
                                            row = body_rows.nth(r)
                                            cells = row.locator("td")
                                            row_dict = {}
                                            for c in range(cells.count()):
                                                key = (
                                                    headers[c]
                                                    if c < len(headers)
                                                    else f"coluna_{c+1}"
                                                )
                                                row_dict[key] = (
                                                    cells.nth(c).inner_text().strip()
                                                )
                                            rows_data.append(row_dict)

                                        next_button = detail_page.locator(
                                            "#tabelaDetalheValoresSacados_paginate .paginate_button.next button"
                                        )

                                        if not next_button.count():
                                            break

                                        next_button_parent = detail_page.locator(
                                            "#tabelaDetalheValoresSacados_paginate .paginate_button.next"
                                        )
                                        is_disabled = (
                                            "disabled"
                                            in next_button_parent.get_attribute("class")
                                        )

                                        if is_disabled:
                                            break

                                        next_button.click()
                                        time.sleep(5)
                                        detail_page.wait_for_timeout(
                                            random.uniform(1000, 2000)
                                        )

                                    detailed_data.append(
                                        {"tabela": caption, "dados": rows_data}
                                    )

                                benefit_data.append(
                                    {
                                        "valor_recebido": valor,
                                        "detalhamento": detailed_data,
                                    }
                                )

                                detail_page.close()

                accordion_data[title] = benefit_data

            screenshot_bytes = page.screenshot(full_page=True)
            screenshot_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")

            scraped_data = {
                "nome": nome,
                "cpf": cpf,
                "localidade": localidade,
                "screenshot_base64": screenshot_base64,
                "recebimentos": accordion_data,
            }

            context.close()
            browser.close()
            return scraped_data

    except PlaywrightTimeoutError as e:
        logger.error(f"Playwright timeout during scraping for '{identifier}': {e}")
        try:
            if "context" in locals():
                context.close()
            if "browser" in locals() and browser.is_connected():
                browser.close()
        except:
            pass
        return {
            "error": "A timeout occurred during scraping.",
            "details": str(e),
            "identifier": identifier,
        }

    except Exception as e:
        logger.error(
            f"Unexpected error during scraping for '{identifier}': {e}", exc_info=True
        )
        try:
            if "context" in locals():
                context.close()
            if "browser" in locals() and browser.is_connected():
                browser.close()
        except:
            pass
        return {
            "error": "An unexpected error occurred.",
            "details": str(e),
            "identifier": identifier,
        }
