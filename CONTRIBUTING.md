# Guía de Contribución

¡Gracias por contribuir al proyecto Conveyor CI/CD! Este documento proporciona las directrices para contribuir efectivamente.

## 🚀 Cómo Contribuir

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub

# Clonar tu fork
git clone https://github.com/tu-usuario/conveyor.git
cd databricks-cicd

# Agregar upstream
git remote add upstream https://github.com/org/conveyor.git
```

### 2. Crear una Rama

```bash
# Actualizar main
git checkout main
git pull upstream main

# Crear rama para tu feature/fix
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/nombre-del-bug
```

### 3. Hacer Cambios

- Escribe código limpio y bien documentado
- Sigue las convenciones de estilo del proyecto
- Agrega tests para nueva funcionalidad
- Actualiza la documentación si es necesario

### 4. Validar Localmente

```bash
# Lint
make lint

# Tests
make test

# Verificar cobertura
make test-coverage
```

### 5. Commit

Usa [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: añadir validación de esquemas SQL"
# o
git commit -m "fix: corregir timeout en ejecución de queries"
```

Tipos de commits:
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo, sin cambios en código
- `refactor`: Refactorización de código
- `test`: Añadir o modificar tests
- `chore`: Cambios en build, CI, etc.

### 6. Push y Pull Request

```bash
# Push a tu fork
git push origin feature/nombre-descriptivo

# Crear Pull Request en GitHub
```

## 📋 Checklist de Pull Request

Antes de crear un PR, verifica:

- [ ] El código pasa todos los linters (`make lint`)
- [ ] Todos los tests pasan (`make test`)
- [ ] La cobertura de tests no disminuye
- [ ] La documentación está actualizada
- [ ] Los commits siguen Conventional Commits
- [ ] El PR tiene una descripción clara
- [ ] Se agregaron tests para nueva funcionalidad

## 🎨 Estándares de Código

### Python

- **Estilo**: PEP 8, Black con línea de 120 caracteres
- **Type hints**: Usar type hints cuando sea posible
- **Docstrings**: Formato Google style
- **Imports**: Ordenados con isort

Ejemplo:
```python
"""
Módulo para procesamiento de datos.
"""
from typing import List, Optional

def process_data(
    data: List[dict],
    filter_nulls: bool = True
) -> Optional[List[dict]]:
    """
    Procesa una lista de datos aplicando filtros.

    Args:
        data: Lista de diccionarios con datos
        filter_nulls: Si True, filtra valores nulos

    Returns:
        Lista de datos procesados o None si está vacía

    Raises:
        ValueError: Si data no es una lista
    """
    if not isinstance(data, list):
        raise ValueError("data debe ser una lista")

    if filter_nulls:
        data = [d for d in data if d is not None]

    return data if data else None
```

### SQL

- **Dialecto**: Databricks SQL
- **Mayúsculas**: Keywords en mayúsculas
- **Indentación**: 4 espacios
- **Nombres**: snake_case para tablas y columnas

Ejemplo:
```sql
-- Crear tabla de clientes
CREATE TABLE IF NOT EXISTS customers (
    customer_id BIGINT,
    customer_name STRING NOT NULL,
    email STRING NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
COMMENT 'Tabla de clientes registrados';
```

## 🧪 Tests

### Tests Unitarios

- Cobertura mínima: 80%
- Usar fixtures de pytest
- Mockear dependencias externas

```python
def test_validate_email():
    """Test que valida formato de email"""
    assert is_valid_email("user@example.com")
    assert not is_valid_email("invalid-email")
```

### Tests de Integración

- Marcar con `@pytest.mark.integration`
- Usar entorno de desarrollo
- Limpiar datos de prueba

```python
@pytest.mark.integration
def test_full_pipeline():
    """Test end-to-end del pipeline"""
    # Setup
    # Execute
    # Assert
    # Cleanup
```

## 📝 Documentación

### Código

- Docstrings en todas las funciones públicas
- Comentarios para lógica compleja
- Type hints para mejorar claridad

### README y Docs

- Actualizar README si cambia funcionalidad
- Agregar ejemplos de uso
- Incluir diagramas si es necesario

## 🔄 Proceso de Review

1. **Automated checks**: CI/CD ejecuta automáticamente
2. **Code review**: Al menos 1 aprobación requerida
3. **Tests**: Todos los tests deben pasar
4. **Documentation**: Verificar que esté actualizada
5. **Merge**: Squash and merge a main/develop

## 🐛 Reportar Bugs

Al reportar un bug, incluye:

1. **Descripción**: Qué esperabas vs qué ocurrió
2. **Pasos para reproducir**:
   ```
   1. Ejecutar comando X
   2. Con parámetros Y
   3. Ver error Z
   ```
3. **Entorno**:
   - OS: macOS 13.0
   - Python: 3.10.5
   - Databricks Runtime: 13.3
4. **Logs**: Incluir logs relevantes
5. **Screenshots**: Si aplica

Template de issue:
```markdown
## Descripción
Breve descripción del bug

## Pasos para Reproducir
1. ...
2. ...

## Comportamiento Esperado
Qué debería ocurrir

## Comportamiento Actual
Qué ocurre realmente

## Entorno
- OS: 
- Python: 
- Databricks: 

## Logs
```
logs aquí
```
```

## 💡 Sugerir Features

Para proponer nuevas funcionalidades:

1. **Buscar**: Verifica que no exista ya
2. **Describir**: Caso de uso y beneficios
3. **Detallar**: Implementación propuesta (opcional)
4. **Discutir**: Espera feedback antes de implementar

Template:
```markdown
## Feature Request

### Problema
Qué problema resuelve esta feature

### Solución Propuesta
Cómo funcionaría

### Alternativas
Otras opciones consideradas

### Beneficios
- Beneficio 1
- Beneficio 2
```

## 🏗️ Arquitectura

### Principios

- **Simplicidad**: Código simple y legible
- **Modularidad**: Componentes independientes
- **Testabilidad**: Fácil de testear
- **Documentación**: Código auto-documentado

### Estructura

```
databricks-cicd/
├── deployment/         # Lógica de deployment
├── scripts/
│   ├── sql/           # Scripts SQL
│   └── python/        # Scripts Python/PySpark
├── tests/             # Tests
└── config/            # Configuración por entorno
```

## 📞 Contacto

- Issues: GitHub Issues
- Discusiones: GitHub Discussions
- Email: team@example.com

## 📜 Licencia

Al contribuir, aceptas que tus contribuciones estarán bajo la licencia MIT del proyecto.

---

¡Gracias por contribuir! 🎉
