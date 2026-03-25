# Estructura recomendada (Clean Code + Clean Architecture)

> Objetivo: mantener reglas de negocio aisladas, dependencias dirigidas hacia adentro y módulos por contexto de negocio.

## Árbol propuesto

```text
search-orchestrator/
├─ pyproject.toml
├─ README.md
├─ src/
│  └─ search_orchestrator/
│     ├─ domain/
│     │  ├─ common/
│     │  │  ├─ errors.py
│     │  │  └─ value_objects.py
│     │  ├─ users/
│     │  │  ├─ entities/
│     │  │  │  └─ user.py
│     │  │  └─ repositories/
│     │  │     └─ user_repository.py          # Port (interfaz)
│     │  ├─ products/
│     │  │  ├─ entities/
│     │  │  │  └─ product.py
│     │  │  └─ repositories/
│     │  │     └─ product_repository.py       # Port (opcional)
│     │  └─ pricing/
│     │     ├─ entities/
│     │     │  ├─ price_snapshot.py
│     │     │  └─ watch.py
│     │     ├─ events/
│     │     │  └─ price_dropped.py
│     │     └─ repositories/
│     │        ├─ price_snapshot_repository.py # Port
│     │        └─ watch_repository.py          # Port
│     │
│     ├─ application/
│     │  ├─ auth/
│     │  │  ├─ commands/
│     │  │  │  ├─ login_command.py
│     │  │  │  └─ refresh_token_command.py
│     │  │  ├─ services/
│     │  │  │  └─ auth_service.py
│     │  │  └─ ports/
│     │  │     ├─ token_provider.py
│     │  │     └─ password_hasher.py
│     │  ├─ users/
│     │  │  ├─ commands/
│     │  │  │  └─ register_user_command.py
│     │  │  ├─ queries/
│     │  │  │  └─ get_user_query.py
│     │  │  └─ services/
│     │  │     └─ user_service.py
│     │  ├─ search/
│     │  │  ├─ commands/
│     │  │  │  └─ orchestrate_search_command.py
│     │  │  ├─ services/
│     │  │  │  └─ search_orchestrator_service.py
│     │  │  └─ ports/
│     │  │     ├─ scraper_adapter.py
│     │  │     ├─ normalizer.py
│     │  │     ├─ ranker.py
│     │  │     └─ cache.py
│     │  └─ pricing/
│     │     ├─ commands/
│     │     │  ├─ track_prices_command.py
│     │     │  └─ create_watch_command.py
│     │     ├─ services/
│     │     │  └─ price_tracker_service.py
│     │     └─ ports/
│     │        └─ notifier.py
│     │
│     ├─ infrastructure/
│     │  ├─ persistence/
│     │  │  ├─ repositories/
│     │  │  │  ├─ redis_user_repository.py
│     │  │  │  ├─ redis_price_snapshot_repository.py
│     │  │  │  └─ redis_watch_repository.py
│     │  │  └─ models/
│     │  ├─ cache/
│     │  │  └─ redis_cache.py
│     │  ├─ adapters/
│     │  │  ├─ amazon_scraper_adapter.py
│     │  │  └─ mercadolibre_scraper_adapter.py
│     │  ├─ normalization/
│     │  │  ├─ engine.py
│     │  │  └─ mappings/
│     │  ├─ ranking/
│     │  │  └─ weighted_scorer.py
│     │  ├─ security/
│     │  │  ├─ jwt_token_provider.py
│     │  │  └─ bcrypt_password_hasher.py
│     │  ├─ notifications/
│     │  │  └─ email_notifier.py
│     │  └─ scheduling/
│     │     └─ price_tracker_job.py
│     │
│     ├─ interfaces/
│     │  ├─ api/
│     │  │  ├─ routes/
│     │  │  │  ├─ auth_routes.py
│     │  │  │  ├─ users_routes.py
│     │  │  │  ├─ search_routes.py
│     │  │  │  └─ pricing_routes.py
│     │  │  ├─ schemas/
│     │  │  │  ├─ auth_schemas.py
│     │  │  │  ├─ user_schemas.py
│     │  │  │  ├─ search_schemas.py
│     │  │  │  └─ pricing_schemas.py
│     │  │  └─ dependencies.py
│     │  └─ cli/
│     │     └─ run_price_tracking.py
│     │
│     ├─ bootstrap/
│     │  ├─ container.pya
│     │  └─ settings.py
│     │
│     └─ main.py
│
├─ tests/
│  ├─ domain/
│  ├─ application/
│  ├─ infrastructure/
│  └─ interfaces/
└─ docs/
   ├─ architecture.md
      └─ 0001-clean-architecture.md
```

## Reglas clean code (clave)

1. `domain` no depende de framework ni librerías de infraestructura.
2. `application` depende de puertos (interfaces), no de implementaciones.
3. `infrastructure` implementa puertos y puede depender de librerías externas.
4. `interfaces` traduce HTTP/CLI ↔ casos de uso, sin lógica de negocio compleja.
5. Módulos por contexto (`auth`, `users`, `search`, `pricing`) para evitar acoplamiento accidental.

## Ubicación recomendada para `UserRepository`

- **Contrato (puerto):** `src/search_orchestrator/domain/users/repositories/user_repository.py`
- **Implementación:** `src/search_orchestrator/infrastructure/persistence/repositories/redis_user_repository.py`

## Auth: nombres de carpetas recomendados

- `application/auth/commands`
- `application/auth/services`
- `application/auth/ports`
- `interfaces/api/routes/auth_routes.py`
- `interfaces/api/schemas/auth_schemas.py`
- `infrastructure/security`

> `auth` no debe contener repositorios de dominio de usuario salvo que sean estrictamente de sesión/token.

## Si agregas Price Tracker

- Entidades y repos de precio en `domain/pricing`.
- Caso de uso en `application/pricing/services/price_tracker_service.py`.
- Job programado en `infrastructure/scheduling/price_tracker_job.py`.
- Endpoint de watchlist/alertas en `interfaces/api/routes/pricing_routes.py`.

---

Este árbol está optimizado para crecer sin mezclar responsabilidades y facilita pruebas unitarias por capa.