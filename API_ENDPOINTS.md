# Guia de Endpoints - Search Orchestrator

Base URL local:
- http://127.0.0.1:8000

Documentacion interactiva:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## 1) Health Check

Metodo y ruta:
- GET /health

Ejemplo PowerShell:
- Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/health"

Respuesta esperada:
- {"status":"ok"}

## 2) Buscar productos

Metodo y ruta:
- POST /search

Body JSON:
- query: string obligatorio
- weights: objeto opcional con pesos

Claves permitidas en weights:
- price
- in_stock
- months_without_interest
- delivery_days

Reglas para weights:
- cada valor debe estar entre 0.0 y 1.0

Ejemplo PowerShell:
- $body = @{
    query = "laptop"
    weights = @{
      price = 0.6
      months_without_interest = 0.2
      in_stock = 0.2
      delivery_days = 0.0
    }
  } | ConvertTo-Json -Depth 4
- Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/search" -ContentType "application/json" -Body $body

Respuesta:
- lista de productos normalizados y ordenados

Header util:
- X-Cache = HIT o MISS

## 3) Registro de usuario

Metodo y ruta:
- POST /auth/register

Body JSON:
- email: correo valido
- password: minimo 8 caracteres, al menos 1 mayuscula y 1 digito

Ejemplo PowerShell:
- $body = @{
    email = "tu_correo@example.com"
    password = "Password123"
  } | ConvertTo-Json
- Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/auth/register" -ContentType "application/json" -Body $body

Respuesta:
- {"id":"...","email":"..."}

## 4) Login

Metodo y ruta:
- POST /auth/login

Body JSON:
- email
- password

Ejemplo PowerShell:
- $body = @{
    email = "tu_correo@example.com"
    password = "Password123"
  } | ConvertTo-Json
- $login = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/auth/login" -ContentType "application/json" -Body $body
- $accessToken = $login.access_token
- $refreshToken = $login.refresh_token

Respuesta:
- access_token
- refresh_token
- token_type

## 5) Refresh de access token

Metodo y ruta:
- POST /auth/refresh

Body JSON:
- refresh_token

Ejemplo PowerShell:
- $body = @{ refresh_token = $refreshToken } | ConvertTo-Json
- $newAccess = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/auth/refresh" -ContentType "application/json" -Body $body
- $accessToken = $newAccess.access_token

## 6) Crear alerta (requiere auth)

Metodo y ruta:
- POST /alerts

Header:
- Authorization: Bearer <access_token>

Body JSON:
- query: string
- condition: PRICE_BELOW o IN_STOCK
- interval_minutes: entero mayor a 0
- weights: mismo formato de /search
- threshold: requerido para PRICE_BELOW, opcional en IN_STOCK

Ejemplo PowerShell:
- $headers = @{ Authorization = "Bearer $accessToken" }
- $body = @{
    query = "iphone"
    condition = "PRICE_BELOW"
    interval_minutes = 30
    threshold = 18000
    weights = @{ price = 1.0 }
  } | ConvertTo-Json -Depth 4
- Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8000/alerts" -Headers $headers -ContentType "application/json" -Body $body

Respuesta:
- {"id":"..."}

## 7) Listar alertas (requiere auth)

Metodo y ruta:
- GET /alerts

Header:
- Authorization: Bearer <access_token>

Ejemplo PowerShell:
- Invoke-RestMethod -Method GET -Uri "http://127.0.0.1:8000/alerts" -Headers $headers

Respuesta:
- lista con id, query, condition, active, last_error

## 8) Eliminar alerta (requiere auth)

Metodo y ruta:
- DELETE /alerts/{alert_id}

Header:
- Authorization: Bearer <access_token>

Ejemplo PowerShell:
- $alertId = "id_de_alerta"
- Invoke-RestMethod -Method DELETE -Uri "http://127.0.0.1:8000/alerts/$alertId" -Headers $headers

Respuesta:
- 204 No Content

## Errores comunes

- 400 Bad Request:
  - query vacio
  - password no cumple reglas
  - weights con claves invalidas o valores fuera de rango

- 401 Unauthorized:
  - token faltante
  - token invalido o expirado
  - usuario inactivo o no autorizado

- 404 Not Found:
  - alerta no encontrada al intentar eliminarla

## Flujo recomendado rapido

1. Registrar usuario en /auth/register
2. Hacer login en /auth/login
3. Guardar access_token y refresh_token
4. Usar access_token para /alerts
5. Usar /search sin auth para pruebas de busqueda
