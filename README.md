# Web Scraper: Portal da Transparência

Esta aplicação realiza a extração automatizada de dados do Portal da Transparência, por meio de uma API desenvolvida em Django, que utiliza Playwright para navegação web e Celery para execução assíncrona de tarefas.

## Acesso em Produção

A API está disponível em ambiente de produção no seguinte endereço:

- Endpoint da API: [https://desafio-most-production-production.up.railway.app/api/scrape-person/](https://desafio-most-production-production.up.railway.app/api/scrape-person/)
- Formulário via **ActivePieces**: [https://cloud.activepieces.com/forms/wpP5G4LYeKKTxOgd900m5](https://cloud.activepieces.com/forms/wpP5G4LYeKKTxOgd900m5)
- - O template para este formulario também pode ser encontrado localmente.

---

## Descrição

A aplicação oferece um endpoint RESTful que permite o envio de requisições `POST` com dados de identificação de uma pessoa. A partir dessas informações, uma tarefa Celery é acionada para executar o scraper no Portal da Transparência, coletando dados públicos sobre benefícios recebidos.

### Tecnologias Utilizadas

- **Django**: Framework web utilizado para construção da API.
- **Playwright**: Ferramenta para automação de navegação web.
- **Celery**: Executor de tarefas assíncronas.
- **Docker/Docker Compose**: Contêineres para ambiente padronizado e fácil execução.

## Setup Local

### Pré-requisitos

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Instruções

1. Clone o repositório:

2. Execute a aplicação com Docker Compose:
   ```bash
   docker-compose up
   ```

O serviço estará disponível em `http://localhost:8000`.

---

## Endpoint `/api/scrape-person/`

### Método: `POST`

#### Parâmetros

- `identifier` (obrigatório): Nome, CPF ou NIS da pessoa.
- `search_filter` (opcional): Filtro de pesquisa, como por exemplo `"BENEFICIÁRIO DE PROGRAMA SOCIAL"`.

#### Exemplo de Requisições

```
curl -X POST \
http://localhost:8000/api/scrape-person/ \
-H 'Content-Type: application/json' \
-d '{
  "identifier": "WANDERLEYSON DE OLIVEIRA SILVA",
  "search_filter": "BENEFICIÁRIO DE PROGRAMA SOCIAL"
}'
```

```
curl -X POST \
http://localhost:8000/api/scrape-person/ \
-H 'Content-Type: application/json' \
-d '{
  "identifier": "JOAO DA SILVA"
}'
```