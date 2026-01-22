"""
ETL Pipeline - Data Quality and Transformation
Procesa datos de órdenes y aplica reglas de calidad
"""
from datetime import datetime
from typing import Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DecimalType, StringType, TimestampType


class OrdersETL:
    """Pipeline ETL para procesar órdenes"""

    def __init__(self, spark: SparkSession, catalog: str = "main", schema: str = "default"):
        """
        Inicializa el pipeline ETL

        Args:
            spark: SparkSession
            catalog: Catalog de Unity Catalog
            schema: Schema donde están las tablas
        """
        self.spark = spark
        self.catalog = catalog
        self.schema = schema
        self.full_schema = f"{catalog}.{schema}"

    def read_table(self, table_name: str) -> DataFrame:
        """
        Lee una tabla de Delta Lake

        Args:
            table_name: Nombre de la tabla

        Returns:
            DataFrame con los datos
        """
        return self.spark.read.table(f"{self.full_schema}.{table_name}")

    def validate_orders(self, df: DataFrame) -> DataFrame:
        """
        Valida y limpia datos de órdenes

        Args:
            df: DataFrame de órdenes

        Returns:
            DataFrame validado
        """
        # Filtrar órdenes con total_amount positivo
        df = df.filter(F.col("total_amount") > 0)

        # Agregar columna de validación
        df = df.withColumn(
            "is_valid",
            (F.col("total_amount").isNotNull())
            & (F.col("customer_id").isNotNull())
            & (F.col("order_date").isNotNull()),
        )

        # Agregar columna de mes/año para particionamiento
        df = df.withColumn("order_year", F.year("order_date")).withColumn("order_month", F.month("order_date"))

        return df

    def enrich_orders(self, orders_df: DataFrame) -> DataFrame:
        """
        Enriquece órdenes con información de clientes y productos

        Args:
            orders_df: DataFrame de órdenes

        Returns:
            DataFrame enriquecido
        """
        # Leer tablas relacionadas
        customers_df = self.read_table("customers")
        order_items_df = self.read_table("order_items")
        products_df = self.read_table("products")

        # Join con clientes
        enriched_df = orders_df.join(
            customers_df.select("customer_id", "customer_name", "email"),
            on="customer_id",
            how="left",
        )

        # Agregar información de items
        order_summary = (
            order_items_df.join(products_df.select("product_id", "category"), on="product_id", how="left")
            .groupBy("order_id")
            .agg(
                F.count("order_item_id").alias("total_items"),
                F.sum(F.col("quantity") * F.col("unit_price")).alias("calculated_total"),
                F.collect_set("category").alias("product_categories"),
            )
        )

        # Join con resumen de items
        enriched_df = enriched_df.join(order_summary, on="order_id", how="left")

        # Agregar flags de calidad
        enriched_df = enriched_df.withColumn(
            "amount_matches",
            F.when(
                F.abs(F.col("total_amount") - F.col("calculated_total")) < 0.01,
                True,
            ).otherwise(False),
        )

        return enriched_df

    def calculate_metrics(self, enriched_df: DataFrame) -> DataFrame:
        """
        Calcula métricas agregadas

        Args:
            enriched_df: DataFrame enriquecido

        Returns:
            DataFrame con métricas
        """
        metrics_df = enriched_df.groupBy("order_year", "order_month", "status").agg(
            F.count("order_id").alias("total_orders"),
            F.sum("total_amount").alias("total_revenue"),
            F.avg("total_amount").alias("avg_order_value"),
            F.countDistinct("customer_id").alias("unique_customers"),
            F.sum(F.when(F.col("is_valid"), 1).otherwise(0)).alias("valid_orders"),
            F.sum(F.when(F.col("amount_matches"), 1).otherwise(0)).alias("matching_amounts"),
        )

        # Calcular porcentajes
        metrics_df = metrics_df.withColumn(
            "valid_order_pct", (F.col("valid_orders") / F.col("total_orders") * 100).cast(DecimalType(5, 2))
        ).withColumn(
            "matching_amount_pct", (F.col("matching_amounts") / F.col("total_orders") * 100).cast(DecimalType(5, 2))
        )

        return metrics_df

    def write_table(
        self, df: DataFrame, table_name: str, mode: str = "overwrite", partition_by: Optional[list] = None
    ):
        """
        Escribe DataFrame a una tabla Delta

        Args:
            df: DataFrame a escribir
            table_name: Nombre de la tabla destino
            mode: Modo de escritura (overwrite, append, etc.)
            partition_by: Columnas para particionar
        """
        writer = df.write.format("delta").mode(mode)

        if partition_by:
            writer = writer.partitionBy(*partition_by)

        writer.saveAsTable(f"{self.full_schema}.{table_name}")

    def run(self):
        """Ejecuta el pipeline completo"""
        print(f"Iniciando ETL Pipeline - {datetime.now()}")
        print(f"Catalog: {self.catalog}, Schema: {self.schema}")

        # 1. Leer órdenes
        print("\n[1/5] Leyendo órdenes...")
        orders_df = self.read_table("orders")
        print(f"  Total órdenes: {orders_df.count()}")

        # 2. Validar
        print("\n[2/5] Validando órdenes...")
        validated_df = self.validate_orders(orders_df)
        valid_count = validated_df.filter(F.col("is_valid")).count()
        print(f"  Órdenes válidas: {valid_count}/{validated_df.count()}")

        # 3. Enriquecer
        print("\n[3/5] Enriqueciendo datos...")
        enriched_df = self.enrich_orders(validated_df)

        # 4. Calcular métricas
        print("\n[4/5] Calculando métricas...")
        metrics_df = self.calculate_metrics(enriched_df)

        # 5. Guardar resultados
        print("\n[5/5] Guardando resultados...")

        # Guardar órdenes enriquecidas
        self.write_table(
            enriched_df, table_name="orders_enriched", mode="overwrite", partition_by=["order_year", "order_month"]
        )
        print("  ✓ orders_enriched guardada")

        # Guardar métricas
        self.write_table(metrics_df, table_name="orders_metrics", mode="overwrite")
        print("  ✓ orders_metrics guardada")

        # Mostrar resumen de métricas
        print("\n=== Resumen de Métricas ===")
        metrics_df.orderBy("order_year", "order_month").show(truncate=False)

        print(f"\nETL Pipeline completado - {datetime.now()}")


def main():
    """Función principal"""
    # Inicializar Spark
    spark = SparkSession.builder.appName("OrdersETL").getOrCreate()

    # Configurar Unity Catalog
    catalog = spark.conf.get("spark.databricks.catalog", "main")
    schema = spark.conf.get("spark.databricks.schema", "default")

    # Ejecutar pipeline
    pipeline = OrdersETL(spark=spark, catalog=catalog, schema=schema)
    pipeline.run()

    spark.stop()


if __name__ == "__main__":
    main()
