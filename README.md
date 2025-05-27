# Web Scraper: Portal da Transparência

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2F88D0?style=for-the-badge&logo=playwright&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-33FF33?style=for-the-badge&logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

Este projeto apresenta uma aplicação Django que atua como um **web scraper** especializado no **Portal da Transparência**. Utilizando o poder do **Playwright** para a interação com páginas web e o **Celery** para o processamento assíncrono, esta API permite a extração de dados relevantes sobre benefícios recebidos por indivíduos, diretamente do portal.

---

## Visão Geral

A aplicação é uma **API RESTful** simples, com um único endpoint projetado para ser intuitivo e fácil de usar. Ela foi desenvolvida para automatizar a coleta de informações que, de outra forma, exigiriam uma navegação manual e tediosa no Portal da Transparência.

### Em Produção

Essa aplicação está **disponível em produção** e pode ser acessada através do seguinte URL:

* **Endpoint da API**: [https://desafio-most-production-production.up.railway.app/api/scrape-person/](https://desafio-most-production-production.up.railway.app/api/scrape-person/)

Além disso, para uma integração ainda mais fácil em fluxos de trabalho de automação, ela também está disponível na plataforma de hiperautomação ActivePieces, com um formulário dedicado:

* **Formulário ActivePieces**: [https://cloud.activepieces.com/forms/wpP5G4LYeKKTxOgd900m5](https://cloud.activepieces.com/forms/wpP5G4LYeKKTxOgd900m5)

---

## Como Funciona

Ao receber um request `POST`, a API aciona uma **task no Celery**. Esta task, por sua vez, inicia um web scraper que:

1.  Acessa o Portal da Transparência.
2.  Utiliza o `identifier` fornecido (Nome, CPF ou NIS) para pesquisar a pessoa.
3.  Aplica o `search_filter` (se fornecido) para refinar a busca, por exemplo, por "BENEFICIÁRIO DE PROGRAMA SOCIAL".
4.  Extrai os dados relevantes sobre os benefícios recebidos pela pessoa pesquisada.

---

## Setup Local

Para rodar este projeto em seu ambiente local, você precisará ter o **Docker** e o **Docker Compose** instalados.

### Pré-requisitos

* **Docker**: Certifique-se de que o Docker esteja instalado em seu sistema. Se não estiver, você pode encontrá-lo aqui:
    * [Instalação do Docker](https://docs.docker.com/get-docker/)
* **Docker Compose**: O Docker Compose é geralmente incluído na instalação do Docker Desktop. Caso precise instalá-lo separadamente, consulte:
    * [Instalação do Docker Compose](https://docs.docker.com/compose/install/)

### Comandos de Instalação e Execução

Com o Docker e o Docker Compose configurados, basta executar o seguinte comando na raiz do projeto:

```bash
docker-compose up --build