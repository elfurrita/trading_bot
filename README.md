# Trading Bot

Este es un bot de trading diseñado para operar con criptomonedas utilizando la API de Binance. El bot incluye funcionalidades para comprar y vender criptomonedas basadas en indicadores técnicos y optimización de parámetros.

## Requisitos

- Python 3.8+
- Cuenta en Binance con API Key y Secret

## Instalación

```bash
git clone https://github.com/elfurrita/trading_bot.git
cd trading_bot
pip install -r requirements.txt
```

## Uso

### Configuración

Asegúrate de configurar correctamente las variables en `config.py`:

```python
SYMBOLS = ['BTCUSDT', 'ETHUSDT']
BUDGET = 1000
DEFAULT_PROFIT_THRESHOLD = 0.05
DEFAULT_TRAILING_STOP = 0.02
REAL_MARKET = False  # Cambiar a True para operar en el mercado real
```

### Ejecución

Para ejecutar el bot:

```bash
python trading.py
```

### Pruebas Unitarias

Para ejecutar las pruebas unitarias:

```bash
pytest tests
```

### CI/CD

El proyecto incluye una configuración de GitHub Actions para CI/CD. Cada push a la rama `main` ejecutará las pruebas automáticamente.

### Monitoreo y Alertas

El proyecto incluye configuraciones de Prometheus y Alertmanager para monitoreo y alertas. Asegúrate de configurar correctamente los archivos `prometheus.yml` y `alertmanager.yml`.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o un pull request para discutir cualquier cambio.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT.