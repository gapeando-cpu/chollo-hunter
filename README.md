# Chollo Hunter Cloud

Bot gratuito que consulta fuentes RSS públicas de ofertas y envía a Telegram las publicaciones que anuncian un descuento igual o superior al 60% y coinciden con las categorías configuradas.

## Importante: qué verifica y qué no

- El porcentaje se extrae del texto publicado por la fuente.
- No se consulta un histórico independiente de Amazon.
- No se garantiza que el precio actual siga disponible al abrir el enlace.
- Las fuentes RSS pueden cambiar, limitar acceso o dejar de funcionar.
- El proyecto no realiza scraping directo de páginas de Amazon.

## Configuración

1. Crea un bot con @BotFather y copia su token.
2. Abre una conversación con el bot y pulsa Start.
3. Obtén tu Chat ID con `https://api.telegram.org/bot<TOKEN>/getUpdates`.
4. Crea un repositorio público en GitHub y sube estos archivos.
5. En Settings > Secrets and variables > Actions > New repository secret, crea:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
6. En Settings > Actions > General, permite que los workflows puedan leer y escribir en el repositorio (Read and write permissions).
7. En Actions, ejecuta manualmente `Chollo Hunter` con Run workflow.

## Frecuencia y coste

El workflow está programado cada 30 minutos. GitHub puede retrasar ejecuciones programadas. GitHub Actions es gratuito para runners estándar en repositorios públicos, sujeto a sus condiciones vigentes.

## Personalizar categorías

Edita `CATEGORY_KEYWORDS` en `main.py`. Añade o quita palabras en cada categoría. Una oferta debe coincidir con al menos una palabra de una categoría.

## Fuentes RSS

Por defecto:
- Ofertitas: `https://www.ofertitas.es/etiqueta/amazon-espana/feed/`
- Chollometro: `https://chollometro.com/rss`

Puedes cambiar las fuentes en la variable de repositorio `RSS_FEEDS` (separadas por comas). La primera fuente de Ofertitas se considera dedicada a Amazon España; para otras fuentes se exige que el contenido mencione Amazon.

## Seguridad

No introduzcas tokens en el código ni en archivos versionados. Usa exclusivamente GitHub Actions Secrets. No actives workflows para pull requests externos con acceso a esos secretos.
