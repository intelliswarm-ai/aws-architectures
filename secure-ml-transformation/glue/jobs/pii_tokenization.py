"""PII Tokenization module for Glue ETL jobs.

This module provides functions for tokenizing personally identifiable information
using various methods: deterministic hashing, format-preserving encryption, and redaction.
"""

import hashlib
import hmac
from typing import Any, Callable

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType


class PIITokenizer:
    """PII tokenization handler for PySpark DataFrames."""

    def __init__(self, salt: str, logger: Any = None) -> None:
        """Initialize the tokenizer.

        Args:
            salt: Salt for deterministic tokenization
            logger: Optional Glue logger
        """
        self.salt = salt
        self.logger = logger

    def tokenize_column(
        self,
        df: DataFrame,
        column_name: str,
        method: str = "deterministic",
        output_length: int = 16,
        preserve_prefix: int = 0,
        preserve_suffix: int = 0,
    ) -> DataFrame:
        """Tokenize a single column.

        Args:
            df: Input DataFrame
            column_name: Name of column to tokenize
            method: Tokenization method (deterministic, format_preserving, hash, redact)
            output_length: Length of output token
            preserve_prefix: Characters to preserve at start (format_preserving only)
            preserve_suffix: Characters to preserve at end (format_preserving only)

        Returns:
            DataFrame with tokenized column
        """
        if column_name not in df.columns:
            if self.logger:
                self.logger.warn(f"Column {column_name} not found in DataFrame")
            return df

        if method == "deterministic":
            return self._deterministic_tokenize(df, column_name, output_length)
        elif method == "format_preserving":
            return self._format_preserving_tokenize(
                df, column_name, preserve_prefix, preserve_suffix
            )
        elif method == "hash":
            return self._hash_tokenize(df, column_name)
        elif method == "redact":
            return self._redact_column(df, column_name)
        else:
            raise ValueError(f"Unknown tokenization method: {method}")

    def tokenize_dataframe(
        self,
        df: DataFrame,
        column_configs: list[dict[str, Any]],
    ) -> DataFrame:
        """Tokenize multiple columns in a DataFrame.

        Args:
            df: Input DataFrame
            column_configs: List of column configuration dicts with keys:
                - column_name: Name of column
                - method: Tokenization method
                - output_length: Token length (optional)
                - preserve_prefix: Prefix chars to keep (optional)
                - preserve_suffix: Suffix chars to keep (optional)

        Returns:
            DataFrame with all specified columns tokenized
        """
        result_df = df

        for config in column_configs:
            column_name = config["column_name"]
            method = config.get("method", "deterministic")
            output_length = config.get("output_length", 16)
            preserve_prefix = config.get("preserve_prefix", 0)
            preserve_suffix = config.get("preserve_suffix", 0)

            if self.logger:
                self.logger.info(f"Tokenizing column: {column_name} with method: {method}")

            result_df = self.tokenize_column(
                result_df,
                column_name,
                method,
                output_length,
                preserve_prefix,
                preserve_suffix,
            )

        return result_df

    def _deterministic_tokenize(
        self,
        df: DataFrame,
        column_name: str,
        output_length: int,
    ) -> DataFrame:
        """Apply deterministic HMAC-based tokenization.

        Same input always produces same output, enabling joins.
        """
        salt = self.salt

        @F.udf(returnType=StringType())
        def tokenize_udf(value: str) -> str:
            if value is None:
                return None
            # Use HMAC-SHA256 for secure deterministic hashing
            token = hmac.new(
                salt.encode("utf-8"),
                value.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()[:output_length]
            return token

        return df.withColumn(column_name, tokenize_udf(F.col(column_name)))

    def _format_preserving_tokenize(
        self,
        df: DataFrame,
        column_name: str,
        preserve_prefix: int,
        preserve_suffix: int,
    ) -> DataFrame:
        """Apply format-preserving tokenization.

        Preserves prefix and suffix while masking middle portion.
        """
        salt = self.salt

        @F.udf(returnType=StringType())
        def fp_tokenize_udf(value: str) -> str:
            if value is None:
                return None

            # Remove any non-alphanumeric characters for hashing
            clean_value = "".join(c for c in value if c.isalnum())

            # Generate hash for middle portion
            middle_hash = hmac.new(
                salt.encode("utf-8"),
                clean_value.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Reconstruct with preserved prefix/suffix
            if len(value) <= preserve_prefix + preserve_suffix:
                return value

            prefix = value[:preserve_prefix] if preserve_prefix > 0 else ""
            suffix = value[-preserve_suffix:] if preserve_suffix > 0 else ""
            middle_length = len(value) - preserve_prefix - preserve_suffix

            # Use hash characters for middle, preserving special chars positions
            middle_chars = []
            hash_idx = 0
            for i in range(preserve_prefix, len(value) - preserve_suffix):
                original_char = value[i]
                if original_char.isalnum():
                    middle_chars.append(middle_hash[hash_idx % len(middle_hash)].upper())
                    hash_idx += 1
                else:
                    middle_chars.append(original_char)

            return prefix + "".join(middle_chars) + suffix

        return df.withColumn(column_name, fp_tokenize_udf(F.col(column_name)))

    def _hash_tokenize(
        self,
        df: DataFrame,
        column_name: str,
    ) -> DataFrame:
        """Apply one-way SHA-256 hash tokenization."""

        @F.udf(returnType=StringType())
        def hash_udf(value: str) -> str:
            if value is None:
                return None
            return hashlib.sha256(value.encode("utf-8")).hexdigest()

        return df.withColumn(column_name, hash_udf(F.col(column_name)))

    def _redact_column(
        self,
        df: DataFrame,
        column_name: str,
    ) -> DataFrame:
        """Completely redact a column."""
        return df.withColumn(column_name, F.lit("***REDACTED***"))


def create_tokenizer(salt: str, logger: Any = None) -> PIITokenizer:
    """Factory function to create a tokenizer instance.

    Args:
        salt: Salt for deterministic tokenization
        logger: Optional Glue logger

    Returns:
        Configured PIITokenizer instance
    """
    return PIITokenizer(salt=salt, logger=logger)
