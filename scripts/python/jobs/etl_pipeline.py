"""
Simple ETL - Lee datos, transforma y escribe en Unity Catalog
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def run_etl(spark: SparkSession, catalog: str, schema: str):
    """
    ETL simple: lee orders, filtra validos, escribe resultado.
    """
    table_path = f"{catalog}.{schema}"

    # Leer
    print(f"Leyendo {table_path}.orders...")
    df = spark.read.table(f"{table_path}.orders")

    # Transformar: filtrar validos y agregar columna de mes
    df_clean = (
        df.filter(F.col("total_amount") > 0)
        .filter(F.col("customer_id").isNotNull())
        .withColumn("order_month", F.date_format("order_date", "yyyy-MM"))
    )

    print(f"Registros: {df.count()} -> {df_clean.count()} (limpios)")

    # Escribir
    df_clean.write.format("delta").mode("overwrite").saveAsTable(f"{table_path}.orders_clean")
    print(f"Guardado en {table_path}.orders_clean")


if __name__ == "__main__":
    spark = SparkSession.builder.appName("SimpleETL").getOrCreate()

    catalog = spark.conf.get("spark.databricks.catalog", "main")
    schema = spark.conf.get("spark.databricks.schema", "default")

    run_etl(spark, catalog, schema)
    spark.stop()
