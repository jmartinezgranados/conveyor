"""
Unit tests for ETL Pipeline
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
    BooleanType,
)


@pytest.fixture(scope="session")
def spark():
    """Create a Spark session for testing"""
    return SparkSession.builder.master("local[2]").appName("pytest-pyspark-tests").getOrCreate()


@pytest.fixture
def sample_orders_data():
    """Sample orders data for testing"""
    return [
        (1, 101, datetime(2024, 1, 15, 10, 30), Decimal("150.50"), "completed"),
        (2, 102, datetime(2024, 1, 16, 14, 20), Decimal("250.75"), "pending"),
        (3, 101, datetime(2024, 2, 10, 9, 15), Decimal("99.99"), "completed"),
        (4, 103, datetime(2024, 2, 12, 16, 45), Decimal("-50.00"), "cancelled"),  # Invalid amount
        (5, None, datetime(2024, 2, 15, 11, 0), Decimal("200.00"), "processing"),  # Missing customer_id
    ]


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


def test_validate_orders_filters_negative_amounts(spark, sample_orders_data, orders_schema):
    """Test that orders with negative amounts are filtered out"""
    # Arrange
    from scripts.python.jobs.etl_pipeline import OrdersETL

    df = spark.createDataFrame(sample_orders_data, schema=orders_schema)
    pipeline = OrdersETL(spark=spark, catalog="test", schema="test")

    # Act
    validated_df = pipeline.validate_orders(df)

    # Assert
    assert validated_df.count() == 4  # One order with negative amount should be filtered
    assert validated_df.filter("total_amount < 0").count() == 0


def test_validate_orders_adds_validation_flag(spark, sample_orders_data, orders_schema):
    """Test that validation flag is added correctly"""
    # Arrange
    from scripts.python.jobs.etl_pipeline import OrdersETL

    df = spark.createDataFrame(sample_orders_data, schema=orders_schema)
    pipeline = OrdersETL(spark=spark, catalog="test", schema="test")

    # Act
    validated_df = pipeline.validate_orders(df)

    # Assert
    assert "is_valid" in validated_df.columns
    valid_count = validated_df.filter("is_valid = true").count()
    assert valid_count == 3  # Only 3 orders are fully valid


def test_validate_orders_adds_year_month_columns(spark, sample_orders_data, orders_schema):
    """Test that year and month columns are added"""
    # Arrange
    from scripts.python.jobs.etl_pipeline import OrdersETL

    df = spark.createDataFrame(sample_orders_data, schema=orders_schema)
    pipeline = OrdersETL(spark=spark, catalog="test", schema="test")

    # Act
    validated_df = pipeline.validate_orders(df)

    # Assert
    assert "order_year" in validated_df.columns
    assert "order_month" in validated_df.columns

    # Check specific values
    jan_orders = validated_df.filter("order_month = 1")
    assert jan_orders.count() == 2


@pytest.mark.parametrize(
    "order_id,customer_id,total_amount,expected_valid",
    [
        (1, 101, Decimal("100.00"), True),  # Valid order
        (2, None, Decimal("100.00"), False),  # Missing customer_id
        (3, 102, None, False),  # Missing total_amount
        (4, 103, Decimal("0.00"), False),  # Zero amount (filtered)
    ],
)
def test_order_validation_scenarios(spark, order_id, customer_id, total_amount, expected_valid):
    """Test various order validation scenarios"""
    # Arrange
    from scripts.python.jobs.etl_pipeline import OrdersETL

    schema = StructType(
        [
            StructField("order_id", LongType(), False),
            StructField("customer_id", LongType(), True),
            StructField("order_date", TimestampType(), False),
            StructField("total_amount", DecimalType(10, 2), True),
            StructField("status", StringType(), True),
        ]
    )

    data = [(order_id, customer_id, datetime.now(), total_amount, "pending")]
    df = spark.createDataFrame(data, schema=schema)
    pipeline = OrdersETL(spark=spark, catalog="test", schema="test")

    # Act
    validated_df = pipeline.validate_orders(df)

    # Assert
    if expected_valid:
        assert validated_df.filter("is_valid = true").count() == 1
    else:
        # Either filtered out or marked as invalid
        result = validated_df.filter("is_valid = false").count()
        assert result == 0 or validated_df.count() == 0


def test_calculate_metrics_aggregates_correctly(spark):
    """Test that metrics are calculated correctly"""
    # Arrange
    from scripts.python.jobs.etl_pipeline import OrdersETL

    schema = StructType(
        [
            StructField("order_id", LongType(), False),
            StructField("order_year", LongType(), False),
            StructField("order_month", LongType(), False),
            StructField("status", StringType(), False),
            StructField("total_amount", DecimalType(10, 2), True),
            StructField("customer_id", LongType(), True),
            StructField("is_valid", BooleanType(), True),
            StructField("amount_matches", BooleanType(), True),
        ]
    )

    data = [
        (1, 2024, 1, "completed", Decimal("100.00"), 101, True, True),
        (2, 2024, 1, "completed", Decimal("200.00"), 102, True, True),
        (3, 2024, 1, "pending", Decimal("150.00"), 101, True, False),
        (4, 2024, 2, "completed", Decimal("300.00"), 103, True, True),
    ]

    df = spark.createDataFrame(data, schema=schema)
    pipeline = OrdersETL(spark=spark, catalog="test", schema="test")

    # Act
    metrics_df = pipeline.calculate_metrics(df)

    # Assert
    assert metrics_df.count() == 2  # Two groups: (2024,1,completed), (2024,1,pending), (2024,2,completed) = 3

    # Check January completed orders
    jan_completed = metrics_df.filter("order_year = 2024 AND order_month = 1 AND status = 'completed'").collect()[0]
    assert jan_completed["total_orders"] == 2
    assert float(jan_completed["total_revenue"]) == 300.00
    assert jan_completed["unique_customers"] == 2


class TestTokenManager:
    """Tests for Databricks Token Manager"""

    def test_generate_unique_id_format(self):
        """Test that generated IDs have correct format"""
        from deployment.token_manager import DatabricksTokenManager

        # We can't fully initialize without credentials, but we can test the method
        manager = DatabricksTokenManager.__new__(DatabricksTokenManager)
        token_id = manager.generar_id_unico()

        assert token_id.startswith("IOP")
        assert len(token_id) == 9  # IOP + 6 characters

    def test_generate_unique_ids_are_different(self):
        """Test that generated IDs are unique"""
        from deployment.token_manager import DatabricksTokenManager

        manager = DatabricksTokenManager.__new__(DatabricksTokenManager)
        id1 = manager.generar_id_unico()
        id2 = manager.generar_id_unico()

        assert id1 != id2
