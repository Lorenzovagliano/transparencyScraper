curl -X POST \
  http://localhost:8000/api/scrape-person/ \
  -H 'Content-Type: application/json' \
  -d '{
    "identifier": "WANDERLEYSON DE OLIVEIRA SILVA",
    "search_filter": "BENEFICIÁRIO DE PROGRAMA SOCIAL"
  }'
