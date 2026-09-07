"""Shared helpers for loading config used across the pipeline."""

import yaml


def load_config(config_path="config.yaml"):
    """Load the YAML config file into a dict."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config


def to_snake_case(name):
    """Convert a column name like 'Order ID' into 'order_id'."""
    return (
        str(name)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )
