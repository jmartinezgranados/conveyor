"""
SQL Executor para Databricks
Ejecuta scripts SQL utilizando tokens temporales
"""

import os
import sys
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from token_manager import DatabricksTokenManager

load_dotenv()


class SQLExecutor:
    """Ejecuta scripts SQL en Databricks"""

    def __init__(self, warehouse_id: str = None, profile: str = None):
        """
        Inicializa el executor de SQL

        Args:
            warehouse_id: ID del SQL Warehouse (default: variable de entorno)
            profile: Perfil de Databricks CLI (default: variable de entorno)
        """
        self.warehouse_id = warehouse_id or os.getenv("WAREHOUSE_ID")
        if not self.warehouse_id:
            raise ValueError("warehouse_id is required. Set WAREHOUSE_ID environment variable or pass as argument.")

        self.token_manager = DatabricksTokenManager(profile=profile)
        self.catalog = os.getenv("CATALOG", "main")

        print(f"  📋 SQLExecutor inicializado:")
        print(f"     Warehouse ID: {self.warehouse_id}")
        print(f"     Catalog: {self.catalog} (env: {os.getenv('CATALOG', 'NO DEFINIDO')})")

    def leer_script_sql(self, filepath: str) -> str:
        """
        Lee un archivo SQL y retorna su contenido

        Args:
            filepath: Ruta al archivo SQL

        Returns:
            Contenido del archivo
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"SQL script not found: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def dividir_statements(self, sql_content: str) -> List[str]:
        """
        Divide el contenido SQL en statements individuales

        Args:
            sql_content: Contenido SQL completo

        Returns:
            Lista de statements
        """
        # Dividir por punto y coma, ignorando los que están en comentarios
        statements = []
        current_statement = []
        in_comment = False

        for line in sql_content.split("\n"):
            stripped = line.strip()

            # Ignorar comentarios de una línea
            if stripped.startswith("--"):
                continue

            # Manejar comentarios multi-línea
            if "/*" in line:
                in_comment = True
            if "*/" in line:
                in_comment = False
                continue

            if in_comment:
                continue

            # Agregar línea al statement actual
            if stripped:
                current_statement.append(line)

            # Si encuentra punto y coma, es el final de un statement
            if stripped.endswith(";"):
                statement = "\n".join(current_statement).strip()
                if statement:
                    # Remover el punto y coma final
                    statement = statement.rstrip(";")
                    statements.append(statement)
                current_statement = []

        # Agregar último statement si existe
        if current_statement:
            statement = "\n".join(current_statement).strip()
            if statement:
                statements.append(statement)

        return statements

    def ejecutar_script(self, filepath: str, continue_on_error: bool = False) -> bool:
        """
        Ejecuta un script SQL completo

        Args:
            filepath: Ruta al archivo SQL
            continue_on_error: Si True, continúa ejecutando aunque falle un statement

        Returns:
            True si todos los statements se ejecutaron correctamente
        """
        print(f"\n{'='*60}")
        print(f"Ejecutando script: {filepath}")
        print(f"{'='*60}")

        try:
            # Leer script
            sql_content = self.leer_script_sql(filepath)

            # Añadir USE CATALOG al inicio (el schema se define en cada script)
            use_statement = f"USE CATALOG {self.catalog};\n"
            sql_content = use_statement + sql_content

            # Dividir en statements
            statements = self.dividir_statements(sql_content)

            print(f"\nEncontrados {len(statements)} statements SQL")
            print(f"Catalog: {self.catalog}\n")

            # Ejecutar cada statement
            all_success = True
            for i, statement in enumerate(statements, 1):
                print(f"\n--- Statement {i}/{len(statements)} ---")

                success = self.token_manager.ejecutar_con_token_temporal(
                    warehouse_id=self.warehouse_id, query=statement, max_wait_seconds=300
                )

                if not success:
                    all_success = False
                    if not continue_on_error:
                        print(f"\n✗ Error en statement {i}. Abortando ejecución.")
                        return False
                    else:
                        print(f"\n⚠ Error en statement {i}. Continuando...")

            print(f"\n{'='*60}")
            if all_success:
                print("✓ Script ejecutado completamente")
            else:
                print("⚠ Script ejecutado con errores")
            print(f"{'='*60}")

            return all_success

        except Exception as e:
            print(f"\n✗ Error ejecutando script: {str(e)}")
            return False

    def ejecutar_directorio(self, dirpath: str, pattern: str = "*.sql", continue_on_error: bool = False) -> bool:
        """
        Ejecuta todos los scripts SQL en un directorio

        Args:
            dirpath: Ruta al directorio
            pattern: Patrón de archivos a ejecutar (default: *.sql)
            continue_on_error: Si True, continúa aunque falle un script

        Returns:
            True si todos los scripts se ejecutaron correctamente
        """
        directory = Path(dirpath)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {dirpath}")

        sql_files = sorted(directory.glob(pattern))

        if not sql_files:
            print(f"No se encontraron archivos {pattern} en {dirpath}")
            return True

        print(f"\n{'='*60}")
        print(f"Ejecutando scripts en: {dirpath}")
        print(f"Archivos encontrados: {len(sql_files)}")
        print(f"{'='*60}")

        all_success = True
        for sql_file in sql_files:
            success = self.ejecutar_script(str(sql_file), continue_on_error=continue_on_error)

            if not success:
                all_success = False
                if not continue_on_error:
                    print(f"\n✗ Error en {sql_file.name}. Abortando ejecución.")
                    return False
                else:
                    print(f"\n⚠ Error en {sql_file.name}. Continuando...")

        return all_success


def main():
    """Función principal para CLI"""
    import argparse

    parser = argparse.ArgumentParser(description="Ejecuta scripts SQL en Databricks")
    parser.add_argument("path", help="Ruta al archivo SQL o directorio")
    parser.add_argument("--warehouse-id", help="ID del SQL Warehouse")
    parser.add_argument("--profile", help="Perfil de Databricks CLI", default="dev")
    parser.add_argument("--catalog", help="Catalog a usar")
    parser.add_argument(
        "--continue-on-error", action="store_true", help="Continuar ejecutando aunque falle un statement"
    )
    parser.add_argument("--pattern", default="*.sql", help="Patrón de archivos (para directorios)")

    args = parser.parse_args()

    # Configurar variables de entorno si se pasaron argumentos
    if args.warehouse_id:
        os.environ["WAREHOUSE_ID"] = args.warehouse_id
    if args.catalog:
        os.environ["CATALOG"] = args.catalog

    # Crear executor
    try:
        executor = SQLExecutor(profile=args.profile)
    except ValueError as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)

    # Ejecutar
    path = Path(args.path)
    if path.is_file():
        success = executor.ejecutar_script(str(path), continue_on_error=args.continue_on_error)
    elif path.is_dir():
        success = executor.ejecutar_directorio(
            str(path), pattern=args.pattern, continue_on_error=args.continue_on_error
        )
    else:
        print(f"✗ Ruta no válida: {args.path}")
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
