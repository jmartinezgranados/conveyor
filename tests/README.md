# Tests

Este directorio contiene todas las pruebas del proyecto.

## Estructura

```
tests/
├── unit/                    # Tests unitarios
│   └── test_etl_pipeline.py
├── integration/             # Tests de integración
│   └── test_end_to_end.py
└── great_expectations/      # Validación de calidad de datos
    ├── expectations/        # Suites de expectativas
    ├── checkpoints/         # Checkpoints configurados
    └── great_expectations.yml
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

## Great Expectations

Great Expectations valida la calidad de los datos en las tablas de Databricks.

### Configuración

```bash
# Inicializar (solo primera vez)
great_expectations init

# Editar configuración
nano tests/great_expectations/great_expectations.yml
```

### Crear Expectation Suite

```bash
# Crear nueva suite
great_expectations suite new

# Editar suite existente
great_expectations suite edit orders_quality_suite
```

### Ejecutar Validaciones

```bash
# Ejecutar checkpoint
great_expectations checkpoint run data_quality_checkpoint

# Ver resultados
great_expectations docs build
```

### Expectation Suites Disponibles

- **orders_quality_suite**: Valida la tabla `orders`
  - Row count > 0
  - Columnas requeridas presentes
  - Tipos de datos correctos
  - Valores en rangos esperados
  - Status en lista de valores permitidos

- **customers_quality_suite**: Valida la tabla `customers`
  - Email único
  - Campos no nulos
  - Formato de email válido

- **products_quality_suite**: Valida la tabla `products`
  - Precios positivos
  - Categorías válidas
  - Nombres únicos

### Checkpoints

Los checkpoints ejecutan múltiples expectation suites y generan reportes.

**data_quality_checkpoint**: Checkpoint principal que ejecuta todas las validaciones

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
- **Merge a develop**: Todos los tests + Great Expectations
- **Merge a main**: Todos los tests + Great Expectations + deploy

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

### Error: Great Expectations no encuentra datasource

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
- [Great Expectations](https://docs.greatexpectations.io/)
- [PySpark Testing](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html)
