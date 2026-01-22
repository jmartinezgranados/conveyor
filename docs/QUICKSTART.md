# 🚀 Guía de Inicio Rápido

Esta guía te ayudará a empezar a trabajar con el proyecto en menos de 10 minutos.

## 📋 Prerequisitos

- Python 3.10 o superior
- Acceso a un workspace de Databricks
- Token de Databricks con permisos necesarios
- Git

## ⚡ Setup en 3 Pasos

### 1. Clonar e instalar

```bash
# Clonar el repositorio
git clone <tu-repo-url>
cd conveyor

# Ejecutar setup automático
chmod +x setup.sh
./setup.sh

# O manualmente:
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar credenciales

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus credenciales
nano .env
```

Configurar en `.env`:
```bash
DATABRICKS_HOST=https://dbc-xxxxx.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
WAREHOUSE_ID=abc123...
CATALOG=main
SCHEMA=default
```

### 3. Validar instalación

```bash
# Verificar linters
make lint

# Ejecutar tests
make test

# Ver comandos disponibles
make help
```

## 🎯 Primeros Pasos

### Ejecutar un script SQL

```bash
# Opción 1: Usando Make
make execute-migration

# Opción 2: Manualmente
cd deployment
python sql_executor.py ../scripts/sql/migrations/V001__create_base_tables.sql \
  --warehouse-id abc123 \
  --catalog main \
  --schema default
```

### Validar código antes de commit

```bash
# SQL
make lint-sql

# Python
make lint-python

# Todo
make lint
```

### Ejecutar tests

```bash
# Solo unitarios
make test-unit

# Solo integración
make test-integration

# Todos con cobertura
make test-coverage
```

## 📝 Workflow Típico

### 1. Crear nueva rama

```bash
git checkout -b feature/nueva-funcionalidad
```

### 2. Escribir código

```bash
# Crear script SQL
nano scripts/sql/migrations/V003__mi_nueva_tabla.sql

# O script Python
nano scripts/python/jobs/mi_pipeline.py
```

### 3. Validar localmente

```bash
# Lint
make lint

# Tests
make test

# Ejecutar en dev
make deploy-dev
```

### 4. Commit y Push

```bash
git add .
git commit -m "feat: añadir nueva tabla/pipeline"
git push origin feature/nueva-funcionalidad
```

### 5. Crear Pull Request

El CI/CD se ejecutará automáticamente y validará:
- ✅ Linting de SQL y Python
- ✅ Tests unitarios
- ✅ Tests de integración (en PR)
- ✅ Ejecución de scripts (en merge a main/develop)
- ✅ Validación con Great Expectations

## 🔧 Comandos Útiles

### Gestión de tokens

```bash
# Listar tokens temporales
make list-tokens

# Limpiar tokens temporales
make clean-tokens
```

### Great Expectations

```bash
# Inicializar (solo primera vez)
make ge-init

# Ejecutar validaciones
make ge-validate
```

### Formateo automático

```bash
# Formatear Python con Black
black scripts/python/ deployment/

# Formatear SQL con SQLFluff
sqlfluff fix scripts/sql/ --dialect databricks
```

## 📚 Estructura de Archivos

```
databricks-cicd/
├── scripts/
│   ├── sql/
│   │   └── migrations/          # Scripts SQL versionados
│   └── python/
│       ├── jobs/                # Jobs de Spark
│       └── notebooks/           # Notebooks
├── tests/
│   ├── unit/                    # Tests unitarios
│   ├── integration/             # Tests de integración
│   └── great_expectations/      # Validaciones de calidad
├── deployment/
│   ├── token_manager.py         # Gestión de tokens
│   └── sql_executor.py          # Executor de SQL
└── config/
    ├── dev.yml                  # Config desarrollo
    └── prod.yml                 # Config producción
```

## 🐛 Troubleshooting

### Error: "Profile not found in .databrickscfg"

```bash
# Configurar manualmente
mkdir -p ~/.databricks
cat > ~/.databrickscfg << EOF
[dev]
host = https://dbc-xxxxx.cloud.databricks.com
token = dapi...
EOF
```

### Error: "WAREHOUSE_ID is required"

```bash
# Asegúrate de tener el WAREHOUSE_ID en .env
echo "WAREHOUSE_ID=tu-warehouse-id" >> .env
```

### Error en tests: "No module named 'deployment'"

```bash
# Activar el entorno virtual
source venv/bin/activate

# Reinstalar en modo desarrollo
pip install -e .
```

## 📖 Próximos Pasos

1. Lee la [documentación completa](../README.md)
2. Revisa los [ejemplos de SQL](../scripts/sql/)
3. Estudia los [pipelines de ejemplo](../scripts/python/jobs/)
4. Configura [Great Expectations](../tests/great_expectations/)

## 💡 Tips

- Usa `make help` para ver todos los comandos disponibles
- Ejecuta `make lint` antes de cada commit
- Revisa los logs en caso de errores
- Los tokens se limpian automáticamente después de cada ejecución

## 🆘 Ayuda

¿Problemas? Consulta:
- README principal: [README.md](../README.md)
- Documentación de Databricks: https://docs.databricks.com
- Great Expectations: https://docs.greatexpectations.io

---

¡Listo! Ya puedes empezar a trabajar con el proyecto 🎉
