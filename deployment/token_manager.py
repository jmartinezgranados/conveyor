"""
Token Manager para Databricks
Gestiona la creación, validación y eliminación de tokens temporales
"""
import configparser
import os
import random
import string
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


class DatabricksTokenManager:
    """Gestiona tokens temporales de Databricks"""

    def __init__(self, profile: str = None):
        """
        Inicializa el gestor de tokens

        Args:
            profile: Perfil de Databricks CLI a usar (default: variable de entorno o 'dev')
        """
        self.profile = profile or os.getenv("DATABRICKS_PROFILE", "dev")
        self.token_prefix = os.getenv("TOKEN_PREFIX", "sqlops_temp_")
        self.lifetime_hours = int(os.getenv("TOKEN_LIFETIME_HOURS", "2"))

        # Leer configuración del Databricks CLI
        config = configparser.ConfigParser()
        config_path = Path.home() / ".databrickscfg"

        print(f"  🔧 Buscando configuración...")
        print(f"  🔧 Config path: {config_path}")
        print(f"  🔧 Config exists: {config_path.exists()}")

        if config_path.exists():
            config.read(config_path)
            print(f"  🔧 Profiles disponibles: {list(config.sections())}")
            if self.profile in config:
                self.databricks_host = config[self.profile].get("host")
                self.existing_token = config[self.profile].get("token")
                print(f"  🔧 Usando profile: {self.profile}")
                print(f"  🔧 Host desde config: {self.databricks_host}")
            else:
                raise ValueError(f"Profile '{self.profile}' not found in .databrickscfg")
        else:
            # Usar variables de entorno como fallback
            print(f"  🔧 No hay .databrickscfg, usando variables de entorno")
            self.databricks_host = os.getenv("DATABRICKS_HOST")
            self.existing_token = os.getenv("DATABRICKS_TOKEN")
            print(f"  🔧 Host desde env: {self.databricks_host}")

            if not self.databricks_host or not self.existing_token:
                raise ValueError(
                    "Databricks credentials not found. Configure .databrickscfg or set environment variables."
                )

        self.headers = {
            "Authorization": f"Bearer {self.existing_token}",
            "Content-Type": "application/json",
        }

    def generar_id_unico(self) -> str:
        """Genera un ID único tipo IOPXXXXXX"""
        return f"IOP{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

    def crear_token(self, lifetime_hours: int = None) -> Optional[Dict]:
        """
        Crea un token temporal con nomenclatura

        Args:
            lifetime_hours: Duración del token en horas (default: self.lifetime_hours)

        Returns:
            Dict con información del token o None si falla
        """
        lifetime_hours = lifetime_hours or self.lifetime_hours
        token_id_unico = self.generar_id_unico()
        comment = f"{self.token_prefix}{token_id_unico}"

        payload = {"comment": comment, "lifetime_seconds": lifetime_hours * 60 * 60}

        # Asegurar que el host no termina en /
        host = self.databricks_host.rstrip("/")
        url = f"{host}/api/2.0/token/create"

        print(f"  📡 URL: {url}")
        print(f"  📡 Host configurado: {self.databricks_host}")

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 200:
                token_data = response.json()
                print(f"✓ Token creado: {comment}")
                print(f"  Token ID: {token_data['token_info']['token_id']}")
                return token_data
            else:
                print(f"✗ Error creando token: {response.status_code} - {response.text}")
                print(f"  URL usada: {url}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error de conexión: {str(e)}")
            print(f"  URL usada: {url}")
            return None

    def listar_tokens_por_patron(self, patron: str = None) -> List[Dict]:
        """
        Lista todos los tokens que coincidan con el patrón

        Args:
            patron: Patrón a buscar (default: self.token_prefix)

        Returns:
            Lista de tokens encontrados
        """
        patron = patron or self.token_prefix

        try:
            response = requests.get(
                f"{self.databricks_host}/api/2.0/token/list",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 200:
                tokens = response.json().get("token_infos", [])
                return [token for token in tokens if token.get("comment", "").startswith(patron)]
            else:
                print(f"✗ Error listando tokens: {response.status_code} - {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"✗ Error de conexión: {str(e)}")
            return []

    def borrar_token(self, token_id: str) -> bool:
        """
        Borra un token específico

        Args:
            token_id: ID del token a borrar

        Returns:
            True si se borró correctamente, False si falla
        """
        payload = {"token_id": token_id}

        try:
            response = requests.post(
                f"{self.databricks_host}/api/2.0/token/delete",
                headers=self.headers,
                json=payload,
                timeout=30,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"✗ Error de conexión: {str(e)}")
            return False

    def borrar_tokens_por_patron(self, patron: str = None, confirmar: bool = True) -> int:
        """
        Borra todos los tokens que coincidan con el patrón

        Args:
            patron: Patrón a buscar (default: self.token_prefix)
            confirmar: Si True, pide confirmación antes de borrar

        Returns:
            Número de tokens borrados
        """
        patron = patron or self.token_prefix
        tokens = self.listar_tokens_por_patron(patron)

        if not tokens:
            print(f"No se encontraron tokens con el patrón '{patron}'")
            return 0

        print(f"\nTokens encontrados con patrón '{patron}':")
        for token in tokens:
            expiry_time = token.get("expiry_time", 0)
            if expiry_time:
                expiry = datetime.fromtimestamp(expiry_time / 1000).strftime("%Y-%m-%d %H:%M:%S")
            else:
                expiry = "Sin expiración"

            print(f"  - {token.get('comment', 'Sin comentario')} (ID: {token['token_id']}, Expira: {expiry})")

        if confirmar:
            confirmacion = input(f"\n¿Deseas borrar estos {len(tokens)} tokens? (s/n): ")
            if confirmacion.lower() != "s":
                print("Operación cancelada")
                return 0

        print(f"\nBorrando {len(tokens)} tokens...")
        borrados = 0
        for token in tokens:
            if self.borrar_token(token["token_id"]):
                print(f"  ✓ Borrado: {token.get('comment', token['token_id'])}")
                borrados += 1
            else:
                print(f"  ✗ Error borrando: {token.get('comment', token['token_id'])}")

        print(f"\nTotal borrados: {borrados}/{len(tokens)}")
        return borrados

    def verificar_estado_warehouse(self, warehouse_id: str) -> Optional[str]:
        """
        Verifica el estado de un SQL Warehouse

        Args:
            warehouse_id: ID del warehouse

        Returns:
            Estado del warehouse o None si falla
        """
        # Limpiar warehouse_id si viene con prefijo
        if "/warehouses/" in warehouse_id:
            warehouse_id = warehouse_id.split("/warehouses/")[-1].split("/")[0].split("?")[0]

        try:
            host = self.databricks_host.rstrip("/")
            response = requests.get(
                f"{host}/api/2.0/sql/warehouses/{warehouse_id}",
                headers=self.headers,
                timeout=30,
            )

            if response.status_code == 200:
                warehouse = response.json()
                return warehouse.get("state")
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error de conexión: {str(e)}")
            return None

    def ejecutar_query(
        self, token_value: str, warehouse_id: str, query: str, max_wait_seconds: int = 300
    ) -> bool:
        """
        Ejecuta una query SQL en Databricks y espera a que termine

        Args:
            token_value: Token de autenticación
            warehouse_id: ID del SQL Warehouse
            query: Query SQL a ejecutar
            max_wait_seconds: Tiempo máximo de espera en segundos

        Returns:
            True si la query se ejecutó correctamente, False si falló
        """
        print(f"\n=== Ejecutando query ===")
        print(f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}")

        # Limpiar warehouse_id si viene con prefijo
        original_warehouse_id = warehouse_id
        if "/warehouses/" in warehouse_id:
            # Extraer solo el ID del warehouse
            warehouse_id = warehouse_id.split("/warehouses/")[-1].split("/")[0].split("?")[0]
            print(f"  ⚠️ Warehouse ID limpiado: {original_warehouse_id} -> {warehouse_id}")

        print(f"  📡 Warehouse ID: {warehouse_id}")

        # Verificar estado del warehouse
        estado_warehouse = self.verificar_estado_warehouse(warehouse_id)
        if estado_warehouse:
            print(f"Estado del warehouse: {estado_warehouse}")
            if estado_warehouse == "STOPPED":
                print("⚠ El warehouse está parado. Se iniciará automáticamente (puede tardar 1-2 minutos)...")
            elif estado_warehouse == "STARTING":
                print("⚠ El warehouse se está iniciando...")

        # Headers con el nuevo token
        test_headers = {"Authorization": f"Bearer {token_value}", "Content-Type": "application/json"}

        # Ejecutar la query (sin wait_timeout para obtener el statement_id inmediatamente)
        payload = {"warehouse_id": warehouse_id, "statement": query, "wait_timeout": "0s"}

        try:
            response = requests.post(
                f"{self.databricks_host}/api/2.0/sql/statements/",
                headers=test_headers,
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                print(f"✗ Error ejecutando query: {response.status_code}")
                print(f"  Detalle: {response.text}")
                return False

            result = response.json()
            statement_id = result.get("statement_id")

            if not statement_id:
                print("✗ No se obtuvo el statement_id")
                return False

            print(f"Query enviada. Statement ID: {statement_id}")
            print("Esperando a que la query termine...")

            # Polling para verificar el estado de la query
            start_time = time.time()
            last_status = None

            while True:
                # Verificar timeout
                elapsed = time.time() - start_time
                if elapsed > max_wait_seconds:
                    print(f"\n✗ Timeout alcanzado ({max_wait_seconds}s). La query aún está ejecutándose.")
                    return False

                # Consultar estado de la query
                status_response = requests.get(
                    f"{self.databricks_host}/api/2.0/sql/statements/{statement_id}",
                    headers=test_headers,
                    timeout=30,
                )

                if status_response.status_code != 200:
                    print(f"✗ Error consultando estado: {status_response.status_code}")
                    return False

                status_data = status_response.json()
                current_status = status_data.get("status", {}).get("state")

                # Mostrar cambios de estado
                if current_status != last_status:
                    print(f"  Estado: {current_status}")
                    last_status = current_status

                # Verificar si terminó
                if current_status == "SUCCEEDED":
                    manifest = status_data.get("manifest", {})
                    print(f"\n✓ Query ejecutada correctamente")
                    print(f"  Tiempo total: {elapsed:.2f}s")
                    print(f"  Filas: {manifest.get('total_row_count', 0)}")
                    return True

                elif current_status in ["FAILED", "CANCELED", "CLOSED"]:
                    print(f"\n✗ Query terminó con estado: {current_status}")
                    error = status_data.get("status", {}).get("error")
                    if error:
                        print(f"  Error: {error.get('message', 'Sin detalles')}")
                    return False

                # Esperar antes del siguiente poll
                time.sleep(2)

        except requests.exceptions.RequestException as e:
            print(f"✗ Error de conexión: {str(e)}")
            return False

    def ejecutar_con_token_temporal(
        self, warehouse_id: str, query: str, lifetime_hours: int = None, max_wait_seconds: int = 300
    ) -> bool:
        """
        Flujo completo: Crear token -> Ejecutar query -> Borrar token

        Args:
            warehouse_id: ID del SQL Warehouse
            query: Query SQL a ejecutar
            lifetime_hours: Duración del token en horas
            max_wait_seconds: Tiempo máximo de espera para la query

        Returns:
            True si todo se ejecutó correctamente, False si falló
        """
        print("=" * 60)
        print("FLUJO: Crear Token -> Ejecutar Query -> Borrar Token")
        print("=" * 60)

        token_data = None
        token_id = None

        try:
            # 1. Crear token
            print("\n[1/3] Creando token temporal...")
            token_data = self.crear_token(lifetime_hours=lifetime_hours)

            if not token_data:
                print("✗ No se pudo crear el token. Abortando.")
                return False

            token_value = token_data["token_value"]
            token_id = token_data["token_info"]["token_id"]

            # 2. Ejecutar query
            print("\n[2/3] Ejecutando query con el token...")
            query_success = self.ejecutar_query(
                token_value=token_value, warehouse_id=warehouse_id, query=query, max_wait_seconds=max_wait_seconds
            )

            if not query_success:
                print("✗ La query falló.")

            # 3. Borrar token (siempre se intenta, incluso si la query falló)
            print("\n[3/3] Borrando token temporal...")
            if self.borrar_token(token_id):
                print(f"✓ Token {token_id} eliminado correctamente")
            else:
                print(f"✗ Error al borrar token {token_id}")
                print(f"  El token expirará automáticamente en {self.lifetime_hours} horas")

            print("\n" + "=" * 60)
            print("FLUJO COMPLETADO")
            print("=" * 60)

            return query_success

        except Exception as e:
            print(f"\n✗ Error en el flujo: {str(e)}")

            # Intentar borrar el token si se creó
            if token_id:
                print(f"Intentando limpiar token {token_id}...")
                if self.borrar_token(token_id):
                    print(f"✓ Token {token_id} eliminado")
                else:
                    print(f"✗ No se pudo borrar el token {token_id}")
                    print(f"  El token expirará automáticamente en {self.lifetime_hours} horas")

            return False


if __name__ == "__main__":
    # Ejemplo de uso
    import sys

    if len(sys.argv) < 3:
        print("Uso: python token_manager.py <warehouse_id> <query>")
        print('Ejemplo: python token_manager.py abc123 "SELECT 1"')
        sys.exit(1)

    warehouse_id = sys.argv[1]
    query = sys.argv[2]

    manager = DatabricksTokenManager()
    success = manager.ejecutar_con_token_temporal(warehouse_id=warehouse_id, query=query)

    sys.exit(0 if success else 1)
