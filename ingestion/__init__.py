"""Ingestion module for the Alert Fatigue Quantifier.

This package exposes log file parsers and validation tools to ingest raw CSV or
JSON activity records.
"""

from ingestion.parser import parse_log_file
from ingestion.validator import validate_log_schema

__all__ = ["parse_log_file", "validate_log_schema"]
