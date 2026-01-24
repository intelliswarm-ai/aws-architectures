"""Transaction Amount Binning module for Glue ETL jobs.

This module provides functions for binning continuous transaction amounts
into categorical bins using various statistical methods.
"""

from typing import Any

from pyspark.ml.feature import Bucketizer, QuantileDiscretizer
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, StringType
from pyspark.sql.window import Window


class AmountBinner:
    """Transaction amount binning handler for PySpark DataFrames."""

    # Default bin labels
    DEFAULT_LABELS = [
        "micro",
        "small",
        "low",
        "medium",
        "high",
        "large",
        "very_large",
        "extreme",
    ]

    def __init__(self, logger: Any = None) -> None:
        """Initialize the binner.

        Args:
            logger: Optional Glue logger
        """
        self.logger = logger

    def bin_amounts(
        self,
        df: DataFrame,
        column: str = "transaction_amount",
        method: str = "percentile",
        percentiles: list[int] | None = None,
        labels: list[str] | None = None,
        custom_bins: list[float] | None = None,
        n_bins: int = 8,
        handle_negatives: str = "absolute",
    ) -> DataFrame:
        """Bin transaction amounts.

        Args:
            df: Input DataFrame
            column: Column name containing amounts
            method: Binning method (percentile, quantile, custom)
            percentiles: Percentile thresholds for percentile method
            labels: Bin labels
            custom_bins: Custom bin edges for custom method
            n_bins: Number of bins for quantile method
            handle_negatives: How to handle negatives (absolute, separate, error)

        Returns:
            DataFrame with binned amounts
        """
        if column not in df.columns:
            if self.logger:
                self.logger.warn(f"Column {column} not found in DataFrame")
            return df

        # Handle negative values
        df = self._handle_negatives(df, column, handle_negatives)

        # Apply binning method
        if method == "percentile":
            return self._percentile_binning(
                df, column, percentiles or [0, 10, 25, 50, 75, 90, 95, 99, 100], labels
            )
        elif method == "quantile":
            return self._quantile_binning(df, column, n_bins, labels)
        elif method == "custom":
            if not custom_bins:
                raise ValueError("custom_bins required for custom method")
            return self._custom_binning(df, column, custom_bins, labels)
        else:
            raise ValueError(f"Unknown binning method: {method}")

    def _handle_negatives(
        self,
        df: DataFrame,
        column: str,
        method: str,
    ) -> DataFrame:
        """Handle negative transaction amounts.

        Args:
            df: Input DataFrame
            column: Amount column
            method: Handling method

        Returns:
            DataFrame with negatives handled
        """
        if method == "absolute":
            # Take absolute value
            return df.withColumn(f"{column}_original", F.col(column)).withColumn(
                column, F.abs(F.col(column))
            )
        elif method == "separate":
            # Flag negative transactions
            return df.withColumn(
                "is_negative_amount", F.when(F.col(column) < 0, True).otherwise(False)
            ).withColumn(column, F.abs(F.col(column)))
        elif method == "error":
            # Filter out negatives
            negative_count = df.filter(F.col(column) < 0).count()
            if negative_count > 0:
                if self.logger:
                    self.logger.warn(f"Found {negative_count} negative amounts, filtering")
                return df.filter(F.col(column) >= 0)
            return df
        else:
            return df

    def _percentile_binning(
        self,
        df: DataFrame,
        column: str,
        percentiles: list[int],
        labels: list[str] | None,
    ) -> DataFrame:
        """Apply percentile-based binning.

        Args:
            df: Input DataFrame
            column: Amount column
            percentiles: Percentile thresholds
            labels: Bin labels

        Returns:
            DataFrame with percentile bins
        """
        # Calculate percentile values from the data
        percentile_exprs = [
            F.percentile_approx(column, p / 100.0).alias(f"p{p}") for p in percentiles
        ]

        percentile_values = df.select(*percentile_exprs).collect()[0]
        bin_edges = [float(percentile_values[f"p{p}"]) for p in percentiles]

        # Remove duplicates and sort
        bin_edges = sorted(set(bin_edges))

        # Ensure we have valid edges
        if len(bin_edges) < 2:
            if self.logger:
                self.logger.warn("Insufficient unique bin edges, using default")
            bin_edges = [float("-inf"), 0, 100, 1000, float("inf")]

        # Add infinity bounds if not present
        if bin_edges[0] != float("-inf"):
            bin_edges = [float("-inf")] + bin_edges
        if bin_edges[-1] != float("inf"):
            bin_edges = bin_edges + [float("inf")]

        return self._apply_bucketizer(df, column, bin_edges, labels)

    def _quantile_binning(
        self,
        df: DataFrame,
        column: str,
        n_bins: int,
        labels: list[str] | None,
    ) -> DataFrame:
        """Apply quantile-based (equal frequency) binning.

        Args:
            df: Input DataFrame
            column: Amount column
            n_bins: Number of bins
            labels: Bin labels

        Returns:
            DataFrame with quantile bins
        """
        discretizer = QuantileDiscretizer(
            numBuckets=n_bins,
            inputCol=column,
            outputCol=f"{column}_bin_idx",
            relativeError=0.01,
        )

        model = discretizer.fit(df)
        result_df = model.transform(df)

        # Add labels if provided
        if labels:
            result_df = self._add_bin_labels(
                result_df, f"{column}_bin_idx", labels, n_bins
            )
        else:
            result_df = result_df.withColumn(
                f"{column}_bin", F.col(f"{column}_bin_idx").cast(IntegerType())
            )

        return result_df

    def _custom_binning(
        self,
        df: DataFrame,
        column: str,
        custom_bins: list[float],
        labels: list[str] | None,
    ) -> DataFrame:
        """Apply custom bin edges.

        Args:
            df: Input DataFrame
            column: Amount column
            custom_bins: Custom bin edges
            labels: Bin labels

        Returns:
            DataFrame with custom bins
        """
        # Ensure infinity bounds
        bin_edges = custom_bins.copy()
        if bin_edges[0] != float("-inf"):
            bin_edges = [float("-inf")] + bin_edges
        if bin_edges[-1] != float("inf"):
            bin_edges = bin_edges + [float("inf")]

        return self._apply_bucketizer(df, column, bin_edges, labels)

    def _apply_bucketizer(
        self,
        df: DataFrame,
        column: str,
        bin_edges: list[float],
        labels: list[str] | None,
    ) -> DataFrame:
        """Apply Spark Bucketizer to create bins.

        Args:
            df: Input DataFrame
            column: Amount column
            bin_edges: Bin edge values
            labels: Bin labels

        Returns:
            DataFrame with bins applied
        """
        bucketizer = Bucketizer(
            splits=bin_edges,
            inputCol=column,
            outputCol=f"{column}_bin_idx",
            handleInvalid="keep",
        )

        result_df = bucketizer.transform(df)

        # Add labels
        n_bins = len(bin_edges) - 1
        if labels:
            result_df = self._add_bin_labels(
                result_df, f"{column}_bin_idx", labels, n_bins
            )
        else:
            result_df = result_df.withColumn(
                f"{column}_bin", F.col(f"{column}_bin_idx").cast(IntegerType())
            )

        # Add numeric encoding for ML
        result_df = result_df.withColumn(
            f"{column}_bin_encoded", F.col(f"{column}_bin_idx").cast(IntegerType())
        )

        return result_df

    def _add_bin_labels(
        self,
        df: DataFrame,
        bin_idx_column: str,
        labels: list[str],
        n_bins: int,
    ) -> DataFrame:
        """Add string labels to bin indices.

        Args:
            df: Input DataFrame
            bin_idx_column: Column with bin indices
            labels: Label strings
            n_bins: Number of bins

        Returns:
            DataFrame with label column
        """
        # Pad labels if needed
        if len(labels) < n_bins:
            labels = labels + [f"bin_{i}" for i in range(len(labels), n_bins)]

        # Create mapping expression
        label_expr = F.when(F.col(bin_idx_column) == 0, labels[0])
        for i in range(1, n_bins):
            if i < len(labels):
                label_expr = label_expr.when(F.col(bin_idx_column) == i, labels[i])
            else:
                label_expr = label_expr.when(F.col(bin_idx_column) == i, f"bin_{i}")

        label_expr = label_expr.otherwise("unknown")

        col_base = bin_idx_column.replace("_bin_idx", "")
        return df.withColumn(f"{col_base}_bin", label_expr)


def create_binner(logger: Any = None) -> AmountBinner:
    """Factory function to create a binner instance.

    Args:
        logger: Optional Glue logger

    Returns:
        Configured AmountBinner instance
    """
    return AmountBinner(logger=logger)
