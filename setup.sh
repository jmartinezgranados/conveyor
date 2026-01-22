#!/bin/bash

# Setup script for Databricks Conveyor Project
# Este script configura el entorno local para trabajar con el proyecto

set -e

echo "==================================="
echo "Databricks CI/CD Project - Setup"
echo "==================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 no está instalado${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION encontrado${NC}"

# Create virtual environment
echo ""
echo "Creando entorno virtual..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}⚠ El entorno virtual ya existe${NC}"
    read -p "¿Deseas recrearlo? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ Entorno virtual recreado${NC}"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
fi

# Activate virtual environment
echo ""
echo "Activando entorno virtual..."
source venv/bin/activate
echo -e "${GREEN}✓ Entorno virtual activado${NC}"

# Upgrade pip
echo ""
echo "Actualizando pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓ Pip actualizado${NC}"

# Install dependencies
echo ""
echo "Instalando dependencias..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# Create .env file if it doesn't exist
echo ""
if [ ! -f ".env" ]; then
    echo "Creando archivo .env..."
    cp .env.example .env
    echo -e "${GREEN}✓ Archivo .env creado${NC}"
    echo -e "${YELLOW}⚠ Por favor, edita .env con tus credenciales de Databricks${NC}"
else
    echo -e "${YELLOW}⚠ El archivo .env ya existe${NC}"
fi

# Configure Databricks CLI
echo ""
read -p "¿Deseas configurar Databricks CLI ahora? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Configurando Databricks CLI..."
    echo "Por favor, ingresa la información de tu workspace:"
    
    read -p "Host (ej: https://dbc-xxxxx.cloud.databricks.com): " DATABRICKS_HOST
    read -p "Token: " DATABRICKS_TOKEN
    read -p "Perfil (default: dev): " DATABRICKS_PROFILE
    DATABRICKS_PROFILE=${DATABRICKS_PROFILE:-dev}
    
    mkdir -p ~/.databricks
    
    if [ -f ~/.databrickscfg ]; then
        echo -e "${YELLOW}⚠ El archivo .databrickscfg ya existe${NC}"
        read -p "¿Deseas agregar/actualizar el perfil '$DATABRICKS_PROFILE'? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Configuración de Databricks CLI omitida"
        else
            # Backup existing config
            cp ~/.databrickscfg ~/.databrickscfg.backup
            
            # Update or add profile
            if grep -q "^\[$DATABRICKS_PROFILE\]" ~/.databrickscfg; then
                # Update existing profile
                sed -i.bak "/^\[$DATABRICKS_PROFILE\]/,/^\[/ { /^host/c\host = $DATABRICKS_HOST
                /^token/c\token = $DATABRICKS_TOKEN
                }" ~/.databrickscfg
            else
                # Add new profile
                echo "" >> ~/.databrickscfg
                echo "[$DATABRICKS_PROFILE]" >> ~/.databrickscfg
                echo "host = $DATABRICKS_HOST" >> ~/.databrickscfg
                echo "token = $DATABRICKS_TOKEN" >> ~/.databrickscfg
            fi
            
            echo -e "${GREEN}✓ Databricks CLI configurado${NC}"
        fi
    else
        # Create new config file
        cat > ~/.databrickscfg << EOF
[$DATABRICKS_PROFILE]
host = $DATABRICKS_HOST
token = $DATABRICKS_TOKEN
EOF
        echo -e "${GREEN}✓ Databricks CLI configurado${NC}"
    fi
fi

# Initialize Great Expectations (optional)
echo ""
read -p "¿Deseas inicializar Great Expectations? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ ! -d "tests/great_expectations" ]; then
        echo "Inicializando Great Expectations..."
        cd tests
        great_expectations init --no-view
        cd ..
        echo -e "${GREEN}✓ Great Expectations inicializado${NC}"
    else
        echo -e "${YELLOW}⚠ Great Expectations ya está inicializado${NC}"
    fi
fi

# Install pre-commit hooks (optional)
echo ""
read -p "¿Deseas instalar pre-commit hooks? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install pre-commit --quiet
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks instalados${NC}"
fi

# Create necessary directories
echo ""
echo "Creando directorios necesarios..."
mkdir -p logs
mkdir -p tests/great_expectations/uncommitted/validations
mkdir -p tests/great_expectations/checkpoints
echo -e "${GREEN}✓ Directorios creados${NC}"

# Summary
echo ""
echo "==================================="
echo "Setup completado!"
echo "==================================="
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Edita el archivo .env con tus credenciales:"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Verifica la configuración de Databricks:"
echo "   ${YELLOW}databricks workspace list --profile dev${NC}"
echo ""
echo "3. Ejecuta los linters para verificar el código:"
echo "   ${YELLOW}make lint${NC}"
echo ""
echo "4. Ejecuta los tests:"
echo "   ${YELLOW}make test${NC}"
echo ""
echo "5. Para ver todos los comandos disponibles:"
echo "   ${YELLOW}make help${NC}"
echo ""
echo "El entorno virtual está activado. Para desactivarlo ejecuta:"
echo "   ${YELLOW}deactivate${NC}"
echo ""
echo -e "${GREEN}¡Listo para empezar a trabajar!${NC}"
