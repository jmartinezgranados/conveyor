#!/usr/bin/env python3
"""
Conveyor CLI - Script de automatización para el proyecto.

Uso:
    python run.py <comando> [opciones]

Ejemplos:
    python run.py setup          # Configuración inicial
    python run.py test           # Ejecutar todos los tests
    python run.py lint           # Verificar código
    python run.py format         # Formatear código
"""

import subprocess
import sys
import os
from pathlib import Path

# Colores para la terminal
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_header(msg: str) -> None:
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}\n")


def print_success(msg: str) -> None:
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")


def print_error(msg: str) -> None:
    print(f"{Colors.RED}✗ {msg}{Colors.END}")


def print_info(msg: str) -> None:
    print(f"{Colors.YELLOW}→ {msg}{Colors.END}")


def run_cmd(cmd: str, check: bool = True, shell: bool = True) -> int:
    """Ejecuta un comando y retorna el código de salida."""
    print_info(f"Ejecutando: {cmd}")
    result = subprocess.run(cmd, shell=shell)
    if result.returncode != 0 and check:
        print_error(f"Comando falló con código {result.returncode}")
    return result.returncode


# =============================================================================
# COMANDOS DISPONIBLES
# =============================================================================

def cmd_setup():
    """Configuración inicial del proyecto."""
    print_header("Setup del proyecto")

    # Crear venv si no existe
    venv_path = Path("venv")
    if not venv_path.exists():
        print_info("Creando entorno virtual...")
        run_cmd(f"{sys.executable} -m venv venv")

    # Determinar el ejecutable de pip según el SO
    if os.name == "nt":  # Windows
        pip_path = "venv\\Scripts\\pip"
        activate_cmd = ".\\venv\\Scripts\\activate"
    else:  # Linux/Mac
        pip_path = "venv/bin/pip"
        activate_cmd = "source venv/bin/activate"

    print_info("Instalando dependencias...")
    run_cmd(f"{pip_path} install --upgrade pip")
    run_cmd(f"{pip_path} install -r requirements.txt")

    # Verificar si existe .env
    if not Path(".env").exists() and Path(".env.example").exists():
        print_info("Creando archivo .env desde .env.example...")
        import shutil
        shutil.copy(".env.example", ".env")
        print_info("Edita el archivo .env con tus credenciales de Databricks")

    print_success("Setup completado!")
    print_info(f"Activa el entorno con: {activate_cmd}")


def cmd_test(args: list):
    """Ejecuta tests."""
    print_header("Ejecutando tests")

    if not args:
        # Todos los tests
        run_cmd("pytest tests/ -v --cov=scripts/python --cov=deployment")
    elif args[0] == "unit":
        run_cmd("pytest tests/unit/ -v")
    elif args[0] == "integration":
        run_cmd("pytest tests/integration/ -v -m integration")
    elif args[0] == "coverage":
        run_cmd("pytest tests/ -v --cov=scripts/python --cov=deployment --cov-report=html")
        print_success("Reporte generado en htmlcov/index.html")
    else:
        # Pasar argumentos directamente a pytest
        run_cmd(f"pytest {' '.join(args)}")


def cmd_lint():
    """Ejecuta todos los linters."""
    print_header("Verificando código")

    errors = 0

    print_info("Verificando formato Python (black)...")
    errors += run_cmd("black --check scripts/python/ deployment/", check=False)

    print_info("Verificando imports (isort)...")
    errors += run_cmd("isort --check-only scripts/python/ deployment/", check=False)

    print_info("Verificando estilo Python (flake8)...")
    errors += run_cmd("flake8 scripts/python/ deployment/ --max-line-length=120", check=False)

    print_info("Verificando SQL (sqlfluff)...")
    errors += run_cmd("sqlfluff lint scripts/sql/ --dialect databricks", check=False)

    if errors == 0:
        print_success("Todo el código está correcto!")
    else:
        print_error("Se encontraron problemas. Ejecuta 'python run.py format' para corregir.")

    return errors


def cmd_lint_python():
    """Ejecuta linters solo de Python."""
    print_header("Verificando código Python")
    run_cmd("black --check scripts/python/ deployment/", check=False)
    run_cmd("isort --check-only scripts/python/ deployment/", check=False)
    run_cmd("flake8 scripts/python/ deployment/ --max-line-length=120", check=False)


def cmd_lint_sql():
    """Ejecuta linter de SQL."""
    print_header("Verificando código SQL")
    run_cmd("sqlfluff lint scripts/sql/ --dialect databricks")


def cmd_format():
    """Formatea el código automáticamente."""
    print_header("Formateando código")

    print_info("Formateando Python...")
    run_cmd("black scripts/python/ deployment/")
    run_cmd("isort scripts/python/ deployment/")

    print_info("Formateando SQL...")
    run_cmd("sqlfluff fix scripts/sql/ --dialect databricks")

    print_success("Código formateado!")


def cmd_clean():
    """Limpia archivos temporales."""
    print_header("Limpiando archivos temporales")

    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        "htmlcov",
        ".coverage",
        ".sqlfluff_cache",
    ]

    import shutil
    for pattern in patterns:
        for path in Path(".").glob(pattern):
            print_info(f"Eliminando {path}")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()

    print_success("Limpieza completada!")


def cmd_ci():
    """Simula el pipeline de CI completo."""
    print_header("Simulando CI completo")

    errors = cmd_lint()
    if errors > 0:
        print_error("Lint falló")
        return 1

    print_info("Ejecutando tests...")
    result = run_cmd("pytest tests/unit/ -v", check=False)

    if result == 0:
        print_success("CI completado correctamente!")
    else:
        print_error("CI falló")

    return result


def cmd_execute_sql(args: list):
    """Ejecuta scripts SQL en Databricks."""
    print_header("Ejecutando SQL")

    profile = "dev"
    path = "scripts/sql/migrations/"

    for i, arg in enumerate(args):
        if arg == "--profile" and i + 1 < len(args):
            profile = args[i + 1]
        elif not arg.startswith("--"):
            path = arg

    os.chdir("deployment")
    run_cmd(f"python sql_executor.py ../{path} --profile {profile}")
    os.chdir("..")


def cmd_info():
    """Muestra información del proyecto."""
    print_header("Información del proyecto")

    print(f"Python: {sys.version}")
    print(f"Directorio: {os.getcwd()}")

    # Verificar dependencias
    print("\nDependencias:")
    for pkg in ["databricks-sdk", "pytest", "sqlfluff", "black", "soda-core-spark"]:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            version = [l for l in result.stdout.split("\n") if l.startswith("Version:")][0]
            print(f"  ✓ {pkg}: {version.split(': ')[1]}")
        else:
            print(f"  ✗ {pkg}: No instalado")


def cmd_help():
    """Muestra la ayuda."""
    help_text = """
Conveyor CLI - Comandos disponibles:

  SETUP Y CONFIG
    setup              Configuración inicial (venv + dependencias)
    info               Muestra información del proyecto

  TESTING
    test               Ejecuta todos los tests
    test unit          Ejecuta solo tests unitarios
    test integration   Ejecuta tests de integración
    test coverage      Genera reporte de cobertura HTML

  CÓDIGO
    lint               Verifica todo el código (Python + SQL)
    lint-python        Verifica solo Python
    lint-sql           Verifica solo SQL
    format             Formatea código automáticamente
    clean              Limpia archivos temporales

  CI/CD
    ci                 Simula pipeline CI completo
    execute-sql [path] Ejecuta scripts SQL (--profile dev|prod)

  AYUDA
    help               Muestra esta ayuda

Ejemplos:
    python run.py setup
    python run.py test unit
    python run.py lint
    python run.py format
    python run.py ci
"""
    print(help_text)


# =============================================================================
# MAIN
# =============================================================================

def main():
    if len(sys.argv) < 2:
        cmd_help()
        return

    command = sys.argv[1].lower().replace("-", "_")
    args = sys.argv[2:]

    commands = {
        "setup": lambda: cmd_setup(),
        "test": lambda: cmd_test(args),
        "lint": lambda: cmd_lint(),
        "lint_python": lambda: cmd_lint_python(),
        "lint_sql": lambda: cmd_lint_sql(),
        "format": lambda: cmd_format(),
        "clean": lambda: cmd_clean(),
        "ci": lambda: cmd_ci(),
        "execute_sql": lambda: cmd_execute_sql(args),
        "info": lambda: cmd_info(),
        "help": lambda: cmd_help(),
    }

    if command in commands:
        result = commands[command]()
        sys.exit(result if isinstance(result, int) else 0)
    else:
        print_error(f"Comando desconocido: {command}")
        print_info("Usa 'python run.py help' para ver los comandos disponibles")
        sys.exit(1)


if __name__ == "__main__":
    main()
