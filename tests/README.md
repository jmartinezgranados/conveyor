# Tests

Este directorio contiene todas las pruebas del proyecto.

## Estructura

```
tests/
├── unit/                    # Tests unitarios
│   └── test_etl_pipeline.py
└── integration/             # Tests de integración
    └── test_end_to_end.py

# Data quality (Soda Core) - en directorio raiz
soda/
├── configuration.yml        # Conexión a Databricks
└── checks/
    └── orders.yml           # Checks de la tabla orders
```

## Tests Unitarios

Los tests unitarios verifican componentes individuales sin dependencias externas.

```bash
# Ejecutar todos los tests unitarios
pytest tests/unit/ -v

# Ejecutar un test específico
pytest tests/unit/test_etl_pipeline.py::test_validate_orders_filters_negative_amounts -v

# Con cobertura
pytest tests/unit/ --cov=scripts/python --cov=deployment
```

### Escribir Tests Unitarios

Ejemplo:
```python
import pytest
from scripts.python.jobs.etl_pipeline import OrdersETL

def test_validate_orders(spark):
    # Arrange
    pipeline = OrdersETL(spark=spark, catalog="test", schema="test")
    
    # Act
    result = pipeline.validate_orders(df)
    
    # Assert
    assert result.count() > 0
```

## Tests de Integración

Los tests de integración verifican el funcionamiento end-to-end con Databricks real.

```bash
# Ejecutar tests de integración
pytest tests/integration/ -v -m integration

# Requiere variables de entorno
export DATABRICKS_HOST=...
export DATABRICKS_TOKEN=...
export WAREHOUSE_ID=...
```

### Escribir Tests de Integración

```python
import pytest

@pytest.mark.integration
def test_full_pipeline():
    # Test que ejecuta el pipeline completo
    pass
```

## Soda Core

Soda Core valida la calidad de los datos en las tablas de Databricks.

### Ejecutar Validaciones

```bash
# Ejecutar todos los checks
soda scan -d databricks -c soda/configuration.yml soda/checks/

# Ejecutar checks de una tabla específica
soda scan -d databricks -c soda/configuration.yml soda/checks/orders.yml
```

### Checks Disponibles

- **orders.yml**: Valida la tabla `orders`
  - Row count > 0
  - Columnas requeridas presentes
  - Campos no nulos (order_id, customer_id, order_date)
  - order_id único
  - total_amount en rango válido (95% entre 0 y 1M)
  - status en valores permitidos
  - Diversidad de clientes (min 10% únicos)

### Añadir Nuevos Checks

Para añadir validaciones a una nueva tabla:

```yaml
# soda/checks/nueva_tabla.yml
checks for nueva_tabla:
  - row_count > 0
  - missing_count(campo_requerido) = 0
  - duplicate_count(campo_unico) = 0
```

## Markers

Los tests usan markers de pytest para categorización:

```python
@pytest.mark.unit        # Test unitario
@pytest.mark.integration # Test de integración
@pytest.mark.slow        # Test lento
```

Ejecutar por marker:
```bash
pytest -m unit              # Solo unitarios
pytest -m integration       # Solo integración
pytest -m "not slow"        # Excluir lentos
```

## Fixtures

### Fixtures de PySpark

```python
@pytest.fixture(scope="session")
def spark():
    """SparkSession para testing"""
    return SparkSession.builder.master("local[2]").getOrCreate()
```

### Fixtures de Datos

```python
@pytest.fixture
def sample_orders():
    """Datos de ejemplo para tests"""
    return [(1, 101, "2024-01-01", 100.0, "completed")]
```

## Coverage

```bash
# Generar reporte de cobertura
pytest tests/ --cov=scripts/python --cov=deployment --cov-report=html

# Ver reporte
open htmlcov/index.html
```

## CI/CD

Los tests se ejecutan automáticamente en:

- **Pull Requests**: Unit tests + integration tests
- **Merge a develop**: Todos los tests + Soda Core
- **Merge a main**: Todos los tests + Soda Core + deploy

## Best Practices

1. **Nomenclatura**: `test_<nombre_descriptivo>`
2. **Arrange-Act-Assert**: Estructura clara en cada test
3. **Aislamiento**: Cada test debe ser independiente
4. **Mock externos**: No depender de servicios externos en unit tests
5. **Documentación**: Docstrings explicando qué se prueba

## Troubleshooting

### Error: "No module named 'pyspark'"

```bash
pip install pyspark
```

### Error: Soda Core no encuentra datasource

Verifica las variables de entorno:
```bash
export DATABRICKS_HOST=...
export DATABRICKS_TOKEN=...
export CATALOG=...
export SCHEMA=...
```

### Tests de integración fallan

Asegúrate de tener acceso al warehouse de Databricks:
```bash
databricks workspace list --profile dev
```

## Recursos

- [Pytest Documentation](https://docs.pytest.org/)
- [Soda Core](https://docs.greatexpectations.io/)
- [PySpark Testing](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html)
