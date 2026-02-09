# 📊 REPORTE DE ESTADO DEL PROYECTO
## Bitcoin Mining Farm Calculator

**Fecha:** 8 de Febrero de 2026  
**Proyecto:** BP-8Blocks  
**Ubicación:** Neuquén, Argentina  
**Fase Actual:** Prototipo funcional con arquitectura monolítica

---

## 🎯 RESUMEN EJECUTIVO

El proyecto es una **calculadora web de rentabilidad para granjas de minería de Bitcoin** con un horizonte de 8 años, considerando expansiones progresivas (3 MW → 10 MW → 40 MW). Actualmente implementado como una aplicación Flask monolítica con 668 líneas en un solo archivo.

### Estado General: 🟡 FUNCIONAL PERO REQUIERE REFACTORIZACIÓN CRÍTICA

---

## 📁 ESTRUCTURA ACTUAL DEL PROYECTO

```
BP-8Blocks/
├── app.py                          # 668 líneas - TODA LA LÓGICA (🔴 CRÍTICO)
├── requirements.txt                # 7 dependencias básicas
├── agent.md                        # Recién adaptado para Python
├── ModeloNegocioBitcoin.md         # Documentación del modelo de negocio
├── PreguntasProyectoBitcoin.md     # Especificaciones y requerimientos
├── README.md                       # Documentación básica
├── __pycache__/                    # Cache de Python
└── templates/
    ├── index.html                  # 650 líneas - Formulario principal
    ├── results.html                # Vista de resultados
    └── results_partial.html        # Resultados parciales (AJAX)
```

---

## 🔴 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **ARQUITECTURA MONOLÍTICA (Severidad: ALTA)**

**Problema:**
- Todo el código está en `app.py` (668 líneas)
- Lógica de negocio, persistencia, API y presentación mezcladas
- Datos hardcodeados directamente en el código (35 modelos de ASICs)
- Funciones de cálculo, scraping y rutas en el mismo archivo

**Violaciones contra Clean Architecture:**
```python
# Líneas 13-36: Datos hardcodeados en el código de aplicación
asics_data = [
    {'model': 'Antminer S23 Hyd', 'price': 17400, ...},
    # ... 35 modelos hardcodeados
]

# Líneas 50-668: Todo mezclado
# - Funciones de scraping web (parse_bitmain_models, parse_whatsminer_models)
# - Lógica de negocio (simulate_mining, calculate_roi)
# - Obtención de datos externos (get_btc_price, get_network_difficulty)
# - Rutas HTTP (index, calculate, export_excel)
```

**Impacto:**
- ❌ Imposible de testear unitariamente
- ❌ Difícil de mantener y extender
- ❌ No escalable
- ❌ Riesgo de bugs por acoplamiento

---

### 2. **SEGURIDAD (Severidad: CRÍTICA)**

**Problemas Detectados:**

#### 🚨 No hay validación de entrada
```python
# Línea 40-42: Conversión insegura sin validación
def safe_float(value, default=0):
    try:
        return float(value) if value else default
    except ValueError:
        return default
```
- ❌ No valida rangos (negatives, infinitos)
- ❌ No hay sanitización de inputs
- ❌ Vulnerable a inyección de datos malformados

#### 🚨 Sin autenticación ni autorización
- ❌ Todos los endpoints son públicos
- ❌ No hay rate limiting
- ❌ No hay CORS configurado
- ❌ No hay headers de seguridad

#### 🚨 Datos sensibles expuestos
```python
# Línea 668: Debug habilitado en producción
if __name__ == '__main__':
    app.run(debug=True)  # 🔴 NUNCA EN PRODUCCIÓN
```

#### 🚨 Sin manejo de errores estructurado
- ❌ Try-catch genéricos sin logging
- ❌ Stack traces expuestos al usuario
- ❌ No hay correlation IDs para trazabilidad

---

### 3. **GESTIÓN DE DATOS (Severidad: ALTA)**

**Problemas:**

#### Datos volátiles en memoria
```python
# Línea 36-39: Variable global mutable
asics_data = [...]  # Se pierde al reiniciar
for asic in asics_data:
    asic['usd_per_th'] = ...  # Modificación en runtime
```
- ❌ Datos se pierden al reiniciar el servidor
- ❌ No hay persistencia (ni siquiera JSON)
- ❌ Race conditions en ambientes multi-worker

#### Dependencia de APIs externas sin fallback robusto
```python
# Líneas 50-66: Fallback hardcodeado
def get_btc_price():
    try:
        # CoinGecko
    except:
        try:
            # Binance
        except:
            return 95000  # 🔴 PRECIO HARDCODEADO DEL 2024
```

---

### 4. **LÓGICA DE NEGOCIO (Severidad: MEDIA-ALTA)**

**Problemas:**

#### Simulación simplificada
```python
# Líneas 129-159: simulate_mining()
# - Asume dificultad constante (NO REALISTA)
# - No modela halving adecuadamente
# - No considera expansiones graduales
# - Depreciación muy simplificada
# - No calcula NPV ni IRR correctamente
```

#### Falta de escenarios
- ✅ Histórico mencionado pero NO IMPLEMENTADO
- ❌ No hay escenario óptimo vs pesimista
- ❌ No hay análisis de sensibilidad automatizado
- ❌ No se modelan las expansiones (10 MW, 40 MW)

#### Cálculos incompletos
- ❌ WACC no implementado
- ❌ Impuestos no calculados (variable al 0%)
- ❌ Downtime modelado pero no aplicado correctamente
- ❌ Cash flow proyectado pero sin descuento

---

### 5. **FRONTEND (Severidad: MEDIA)**

**Problemas:**
- 650 líneas de HTML con lógica JavaScript mezclada
- JavaScript vanilla repetitivo (podría usar un framework ligero)
- No hay validación del lado del cliente
- AJAX implementado pero sin manejo de errores
- Sin feedback visual de carga/errores

---

### 6. **TESTING Y CALIDAD (Severidad: ALTA)**

**Estado Actual:**
- ❌ **CERO tests** (ni unitarios, ni integración, ni e2e)
- ❌ Sin linting configurado
- ❌ Sin type hints (Python dinámico usado incorrectamente)
- ❌ Sin documentación de funciones (docstrings)
- ❌ Sin coverage

---

## 🟢 ASPECTOS POSITIVOS

1. ✅ **Documentación del modelo de negocio completa** (ModeloNegocioBitcoin.md)
2. ✅ **Especificaciones claras** (PreguntasProyectoBitcoin.md)
3. ✅ **UI funcional con Bootstrap**
4. ✅ **Integración con APIs reales** (aunque mejorable)
5. ✅ **Base de datos de ASICs completa** (35 modelos)
6. ✅ **Cálculos dinámicos en frontend** (AJAX)
7. ✅ **Exportación a Excel** (básica pero funcional)

---

## 🎯 MODIFICACIONES REQUERIDAS

### FASE 1: FUNDAMENTOS (PRIORIDAD CRÍTICA)

#### 1.1 Reestructurar Arquitectura
```
project/
├── src/
│   ├── domain/                      # CREAR
│   │   ├── entities/
│   │   │   ├── mining_farm.py      # Entidad Farm
│   │   │   ├── asic.py             # Entidad ASIC
│   │   │   └── simulation_params.py
│   │   ├── repositories/            # Interfaces
│   │   │   ├── asic_repository.py
│   │   │   └── price_repository.py
│   │   └── exceptions/
│   │       └── domain_errors.py
│   ├── application/                 # CREAR
│   │   └── use_cases/
│   │       ├── calculate_roi.py
│   │       ├── simulate_mining.py
│   │       └── export_results.py
│   ├── infrastructure/              # CREAR
│   │   ├── persistence/
│   │   │   ├── asic_json_repo.py   # JSON como DB inicial
│   │   │   └── data/asics.json
│   │   ├── external/
│   │   │   ├── coingecko_client.py
│   │   │   ├── blockchain_client.py
│   │   │   └── scraper_service.py
│   │   └── config/
│   │       └── settings.py
│   ├── presentation/                # REFACTORIZAR app.py
│   │   ├── api/
│   │   │   ├── blueprints/
│   │   │   │   ├── mining_bp.py
│   │   │   │   └── asic_bp.py
│   │   │   └── controllers/
│   │   ├── schemas/                 # CREAR con Pydantic
│   │   │   ├── mining_request.py
│   │   │   └── mining_response.py
│   │   └── middleware/              # CREAR
│   │       ├── error_handler.py
│   │       ├── cors.py
│   │       └── rate_limiter.py
│   └── shared/                      # CREAR
│       ├── logging_config.py
│       ├── security.py
│       └── constants.py
├── tests/                           # CREAR
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config.py                        # CREAR
├── app.py                           # SIMPLIFICAR (Application Factory)
└── .env.example                     # CREAR
```

#### 1.2 Implementar Validación con Pydantic
```python
# src/presentation/schemas/mining_request.py
from pydantic import BaseModel, Field, validator

class MiningFarmRequest(BaseModel):
    """CREAR: Validación estricta de entrada"""
    research_cost: float = Field(ge=0, description="Research cost in USD")
    asics_count: int = Field(gt=0, le=10000)
    energy_cost_per_kwh: float = Field(gt=0, le=1.0)
    btc_price_override: Optional[float] = Field(None, gt=0)
    downtime_percent: float = Field(ge=0, le=100)
    
    class Config:
        extra = "forbid"  # Rechazar campos no definidos
```

#### 1.3 Implementar Seguridad
```python
# requirements.txt - AGREGAR:
flask-talisman==1.0.0
flask-cors==4.0.0
flask-limiter==3.5.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
structlog==23.2.0
pydantic==2.5.0
```

```python
# src/presentation/middleware/ - CREAR
from flask_talisman import Talisman
from flask_cors import CORS
from flask_limiter import Limiter

def configure_security(app):
    Talisman(app, force_https=False)  # True en producción
    CORS(app, origins=["http://localhost:5000"])
    Limiter(app, default_limits=["100 per hour"])
```

---

### FASE 2: LÓGICA DE NEGOCIO (PRIORIDAD ALTA)

#### 2.1 Implementar Simulación Completa
- [ ] Modelar ajuste de dificultad cada 2016 bloques
- [ ] Implementar halvings (próximo en ~2028)
- [ ] Calcular NPV con WACC real
- [ ] Implementar IRR
- [ ] Modelar expansiones (3MW → 10MW → 40MW)
- [ ] Depreciación realista (lineal + acelerada)
- [ ] Impuestos configurables

#### 2.2 Implementar Escenarios
```python
# src/application/use_cases/scenario_simulator.py - CREAR
class ScenarioType(Enum):
    HISTORICAL = "historical"
    OPTIMISTIC = "optimistic"
    BREAKEVEN = "breakeven"
    PESSIMISTIC = "pessimistic"

def simulate_scenario(params: SimulationParams, scenario: ScenarioType):
    # Implementar lógica para cada escenario
```

#### 2.3 Análisis de Sensibilidad Automatizado
- [ ] BTC Price ±20%
- [ ] Difficulty ±10%
- [ ] Energy Cost ±15%
- [ ] Downtime ±5%
- [ ] Generar matriz de sensibilidad

---

### FASE 3: PERSISTENCIA Y DATOS (PRIORIDAD MEDIA)

#### 3.1 Migrar Datos a JSON/SQLite
```json
// src/infrastructure/persistence/data/asics.json - CREAR
{
  "asics": [
    {
      "id": "antminer-s23-hyd",
      "manufacturer": "Bitmain",
      "model": "Antminer S23 Hyd",
      "price_usd": 17400,
      "hashrate_th": 580,
      "consumption_w": 5510,
      "updated_at": "2026-02-08T00:00:00Z"
    }
  ]
}
```

#### 3.2 Implementar Caché de APIs
```python
# AGREGAR: flask-caching==2.1.0
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 300})

@cache.cached(timeout=300, key_prefix='btc_price')
def get_btc_price():
    # ...
```

#### 3.3 Logging Estructurado
```python
# src/shared/logging_config.py - CREAR
import structlog

logger = structlog.get_logger()
logger.info("calculation_started", 
            correlation_id="...", 
            user_id="...", 
            hashrate=580)
```

---

### FASE 4: FRONTEND Y UX (PRIORIDAD BAJA)

#### 4.1 Mejorar UI/UX
- [ ] Loading spinners
- [ ] Error messages visibles
- [ ] Validación del lado del cliente
- [ ] Tooltips explicativos
- [ ] Gráficos interactivos (Plotly mejorado)

#### 4.2 Considerar Framework Moderno
- Evaluar migrar JS vanilla a **Alpine.js** o **HTMX** (ligero)
- O mantener vanilla pero modularizado

---

### FASE 5: TESTING Y CI/CD (PRIORIDAD MEDIA)

#### 5.1 Implementar Tests
```python
# tests/unit/test_simulation.py - CREAR
import pytest
from src.application.use_cases.simulate_mining import simulate_mining

def test_simulate_mining_basic():
    result = simulate_mining(...)
    assert result.roi > 0
    assert result.daily_btc > 0
```

#### 5.2 Configurar CI/CD
```yaml
# .github/workflows/ci.yml - CREAR
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest --cov=src tests/
```

---

## 🔧 MEJORAS PARA EL AGENTE

El agente recién adaptado necesita **contexto específico del dominio de minería Bitcoin**:

### Agregar Sección al agent.md:

```markdown
## 10. Contexto del Dominio: Minería de Bitcoin

### Términos Clave
- **Hashrate**: Potencia de cómputo medida en TH/s (Terahashes por segundo)
- **Difficulty**: Ajuste automático cada 2016 bloques (~2 semanas) para mantener bloques cada 10 min
- **Block Reward**: Actualmente 3.125 BTC (reducido por halving en 2024)
- **Halving**: Reducción del 50% en block reward cada 210,000 bloques (~4 años)
- **J/TH**: Joules por Terahash - eficiencia energética del ASIC
- **$/TH**: Costo por Terahash - métrica de eficiencia de capital

### Entidades del Dominio
```python
class MiningFarm:
    """Entidad raíz - Representa una granja de minería"""
    capacity_mw: float
    location: Location
    asics: List[ASIC]
    energy_source: EnergySource

class ASIC:
    """Value Object - Hardware de minería"""
    model: str
    hashrate_th: float
    consumption_w: float
    price_usd: float
    efficiency_j_per_th: float  # Calculado

class SimulationResult:
    """Value Object - Resultado de simulación"""
    daily_btc: Decimal
    daily_revenue_usd: Decimal
    daily_cost_usd: Decimal
    roi_percent: float
    payback_months: int
    npv_usd: Decimal
    irr_percent: float
```

### Reglas de Negocio Críticas
1. **Daily BTC Reward** = (Hashrate Farm / Hashrate Network) × 144 blocks × 3.125 BTC
2. **Effective Hashrate** = Hashrate Nominal × (1 - Downtime%)
3. **Daily Energy Cost** = (Total Consumption kW × 24h) × $/kWh
4. **ROI** = (Total Profits / Initial Investment) × 100
5. **NPV** = Σ(Cash Flow_t / (1 + WACC)^t) - Initial Investment

### Casos de Uso Principales
1. **Calculate Mining ROI** - Entrada: Parámetros farm → Salida: Métricas financieras
2. **Simulate 8-Year Projection** - Modelar expansiones y cambios de mercado
3. **Compare ASIC Models** - Análisis de eficiencia de diferentes hardware
4. **Export Business Report** - Generar Excel con proyecciones completas
5. **Update Market Data** - Fetch real-time BTC price, difficulty, hashrate

### APIs Externas
- **Precio BTC**: CoinGecko, Binance, CoinMarketCap
- **Difficulty**: Blockchain.info, Mempool.space
- **Network Hashrate**: Hashrate.no, Glassnode
- **ASIC Pricing**: Bitmain shop, WhatsMiner shop (scraping)

### KPIs del Negocio
- ROI (Return on Investment)
- Payback Period (meses)
- NPV (Net Present Value)
- IRR (Internal Rate of Return)
- COGS (Cost of Goods Sold)
- Daily/Monthly/Annual Cash Flow (USD y BTC)
- Network Share (% del hashrate de la red)
```

---

## 📊 MÉTRICAS DE REFACTORIZACIÓN

| Métrica | Actual | Objetivo | Prioridad |
|---------|--------|----------|-----------|
| Archivos Python | 1 (668 líneas) | 25+ archivos modulares | 🔴 CRÍTICA |
| Cobertura de Tests | 0% | >80% | 🔴 CRÍTICA |
| Complejidad Ciclomática | >50 (app.py) | <10 por función | 🟡 ALTA |
| Type Hints | 0% | 100% | 🟡 ALTA |
| Validación de Entrada | 0% | 100% con Pydantic | 🔴 CRÍTICA |
| Seguridad Headers | 0/10 | 10/10 | 🔴 CRÍTICA |
| Documentación (docstrings) | <10% | 100% | 🟡 MEDIA |
| Performance APIs (cache) | No | Sí (5min TTL) | 🟢 BAJA |

---

## 🚀 PLAN DE ACCIÓN RECOMENDADO

### Sprint 1 (1-2 semanas): FUNDAMENTOS
1. ✅ Crear estructura de carpetas completa
2. ✅ Implementar Application Factory Pattern
3. ✅ Migrar datos de ASICs a JSON
4. ✅ Implementar Pydantic schemas
5. ✅ Configurar seguridad básica (Talisman, CORS, Rate Limiting)
6. ✅ Implementar logging estructurado

### Sprint 2 (1-2 semanas): DOMINIO Y APLICACIÓN
1. ✅ Crear entidades de dominio
2. ✅ Implementar repositorios (interfaces + implementaciones)
3. ✅ Refactorizar lógica de cálculo en use cases
4. ✅ Implementar simulación completa (difficulty, halving, expansiones)
5. ✅ Calcular NPV e IRR correctamente

### Sprint 3 (1 semana): ESCENARIOS Y SENSIBILIDAD
1. ✅ Implementar 4 escenarios (histórico, óptimo, breakeven, pesimista)
2. ✅ Análisis de sensibilidad automatizado
3. ✅ Mejorar exportación a Excel con todos los datos

### Sprint 4 (1 semana): TESTING
1. ✅ Tests unitarios (domain + application)
2. ✅ Tests de integración (APIs externas con mocks)
3. ✅ Tests e2e (Selenium/Playwright básico)
4. ✅ Configurar CI/CD

### Sprint 5 (1 semana): FRONTEND Y PULIDO
1. ✅ Mejorar UX (loading, errors, tooltips)
2. ✅ Optimizar performance (cache, lazy loading)
3. ✅ Documentación completa (README, API docs)
4. ✅ Deploy a cloud (Railway, Render, o similar)

---

## 💰 ESTIMACIÓN DE ESFUERZO

| Fase | Horas | Complejidad |
|------|-------|-------------|
| Sprint 1 | 20-30h | Media |
| Sprint 2 | 30-40h | Alta |
| Sprint 3 | 15-20h | Media |
| Sprint 4 | 20-25h | Media |
| Sprint 5 | 15-20h | Baja |
| **TOTAL** | **100-135h** | *~3-4 semanas a tiempo completo* |

---

## 🎓 RECURSOS DE APRENDIZAJE RECOMENDADOS

1. **Clean Architecture en Python**:
   - "Arquitectura Limpia" - Robert C. Martin
   - "Cosmic Python" (https://www.cosmicpython.com/)

2. **Flask + Pydantic**:
   - Flask Mega-Tutorial - Miguel Grinberg
   - Pydantic docs (v2)

3. **Testing Python**:
   - "Testing Python" - Brian Okken
   - pytest documentation

4. **Minería Bitcoin**:
   - Bitcoin whitepaper (Satoshi Nakamoto)
   - Braiins Academy (https://braiins.com/academy)

---

## ⚠️ RIESGOS Y MITIGACIONES

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| Breaking changes durante refactor | Alto | Media | Tests + feature flags |
| APIs externas caídas | Alto | Media | Fallbacks + caché extenso |
| Complejidad subestimada | Media | Alta | Sprints cortos + revisión continua |
| Scope creep (agregar features) | Media | Alta | Adherirse estrictamente al plan |
| Falta de documentación de negocio | Baja | Baja | Ya existe documentación completa ✅ |

---

## 📝 CONCLUSIÓN

El proyecto tiene **bases sólidas** (documentación, UI funcional, integraciones reales) pero requiere una **refactorización arquitectónica profunda** para pasar de prototipo a aplicación productiva.

**Próximo paso inmediato:** Ejecutar Sprint 1 para establecer fundamentos arquitectónicos antes de agregar más funcionalidad.

---

**Preparado por:** GitHub Copilot (Claude Sonnet 4.5)  
**Fecha:** 8 de Febrero de 2026
