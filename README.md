# Web Scraper: Transparency Portal

This application performs automated data extraction from the Transparency Portal through an API developed in Django, which uses Playwright for web navigation and Celery for asynchronous task execution.

## Production Access

The API is available in the production environment:

- API Endpoint: https://desafio-most-production-production.up.railway.app/api/scrape-person/. It's not recommended to use the interface directly—see some examples using `curl` below.
- [**Form**](https://cloud.activepieces.com/forms/wpP5G4LYeKKTxOgd900m5) via **ActivePieces**, which initiates a workflow that calls the above API, generates a file in this [folder](https://drive.google.com/drive/folders/1WiVVUHYE3gwL6Edw502S2g2UJ4GPhTIV?usp=sharing) on Google Drive, and updates this [spreadsheet](https://docs.google.com/spreadsheets/d/1DFn6mmRSj1dLlwgaJ5swvZlkvH5_imMZOm5d14WsJbg/edit?usp=sharing) on Google Sheets.
    - The template for this workflow can also be found locally (`desafio_01/ActivePieces.json`) or on [ActivePieces](https://cloud.activepieces.com/templates/9MoIWskAIlpbPBqVMWWEt).
- Average processing time: up to 2 minutes.

---

## Description

The application provides a RESTful endpoint that allows `POST` requests with a person's identification data. Based on this information, a Celery task is triggered to run the scraper on the Transparency Portal, collecting public data about benefits received.

### Technologies Used

- **Django**: Web framework used to build the API.
- **Playwright**: Tool for automating web navigation.
- **Celery**: Asynchronous task executor.
- **Redis**: Message broker for Celery.
- **Poetry**: Dependency management for Python.
- **Docker/Docker Compose**: Containers for a standardized environment and easy execution.

## Local Setup

### Prerequisites

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

### Instructions

1. Clone the repository:

2. Go to the correct directory: `/desafio_01`

3. Run the application with Docker Compose:
   ```bash
   docker-compose up
