## Singular person with filter
```
curl -X POST \
  http://localhost:8000/api/scrape-person/ \
  -H 'Content-Type: application/json' \
  -d '{
    "identifier": "WANDERLEYSON DE OLIVEIRA SILVA",
    "search_filter": "BENEFICIÁRIO DE PROGRAMA SOCIAL"
  }'
```

## Multiple people with filter
```
curl -X POST \
  http://localhost:8000/api/scrape-person/ \
  -H 'Content-Type: application/json' \
  -d '{
    "identifier": "JOAO DA SILVA",
    "search_filter": "BENEFICIÁRIO DE PROGRAMA SOCIAL"
  }'
```

## Singular Person without filter:
```
curl -X POST \
  http://localhost:8000/api/scrape-person/ \
  -H 'Content-Type: application/json' \
  -d '{
    "identifier": "WANDERLEYSON DE OLIVEIRA SILVA"
  }'
```

## Multiple people with filter:
```
curl -X POST \
  http://localhost:8000/api/scrape-person/ \
  -H 'Content-Type: application/json' \
  -d '{
    "identifier": "JOAO DA SILVA"
  }'
```
