"""
Unit tests for Simple ETL Pipeline
"""
import pytest
from datetime import datetime
from decimal import Decimal
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    LongType,
    StringType,
    DecimalType,
    TimestampType,
)
from pyspark.sql import functions as F


@pytest.fixture(scope="session")
def spark():
    """Create a Spark session for testing"""
    return (
        SparkSession.builder.master("local[2]")
        .appName("pytest-pyspark-tests")
        .getOrCreate()
    )


@pytest.fixture
def orders_schema():
    """Schema for orders table"""
    return StructType(
        [
            StructField("order_id", LongType(), False),
            StructField("customer_id", LongType(), True),
            StructField("order_date", TimestampType(), False),
            StructField("total_amount", DecimalType(10, 2), True),
            StructField("status", StringType(), True),
        ]
    )


@pytest.fixture
def sample_orders(spark, orders_schema):
    """Sample orders DataFrame"""
    data = [
        (1, 101, datetime(2024, 1, 15), Decimal("150.50"), "completed"),
        (2, 102, datetime(2024, 1, 16), Decimal("250.75"), "pending"),
        (3, 101, datetime(2024, 2, 10), Decimal("99.99"), "completed"),
        (4, 103, datetime(2024, 2, 12), Decimal("-50.00"), "cancelled"),
        (5, None, datetime(2024, 2, 15), Decimal("200.00"), "processing"),
    ]
    return spark.createDataFrame(data, schema=orders_schema)


def test_filter_negative_amounts(sample_orders):
    """Test that negative amounts are filtered"""
    result = sample_orders.filter(F.col("total_amount") > 0)
    assert result.count() == 4
    assert result.filter("total_amount < 0").count() == 0


def test_filter_null_customer_id(sample_orders):
    """Test that null customer_id are filtered"""
    result = sample_orders.filter(F.col("customer_id").isNotNull())
    assert result.count() == 4


def test_combined_filter(sample_orders):
    """Test combined filters (total_amount > 0 AND customer_id not null)"""
    result = (
        sample_orders.filter(F.col("total_amount") > 0)
        .filter(F.col("customer_id").isNotNull())
    )
    assert result.count() == 3


def test_add_order_month_column(sample_orders):
    """Test that order_month column is added correctly"""
    result = sample_orders.withColumn(
        "order_month", F.date_format("order_date", "yyyy-MM")
    )
    assert "order_month" in result.columns

    jan_orders = result.filter(F.col("order_month") == "2024-01")
    assert jan_orders.count() == 2


class TestTokenManager:
    """Tests for Databricks Token Manager"""

    def test_generate_unique_id_format(self):
        """Test that generated IDs have correct format"""
        from deployment.token_manager import DatabricksTokenManager

        manager = DatabricksTokenManager.__new__(DatabricksTokenManager)
        token_id = manager.generar_id_unico()

        assert token_id.startswith("IOP")
        assert len(token_id) == 9

    def test_generate_unique_ids_are_different(self):
        """Test that generated IDs are unique"""
        from deployment.token_manager import DatabricksTokenManager

        manager = DatabricksTokenManager.__new__(DatabricksTokenManager)
        id1 = manager.generar_id_unico()
        id2 = manager.generar_id_unico()

        assert id1 != id2
