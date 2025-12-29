"""
Dagster definitions for the Energy Analytics Pipeline.

This module configures the complete Dagster deployment including:
- All assets (EIA, enrichment, dbt, reports)
- Jobs for different pipeline execution patterns
- Schedules for automated execution
- Resources for external system connections
"""

import os
import sys

# Add project modules to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "ingestion"))
sys.path.insert(0, os.path.join(project_root, "reports"))

from dagster import Definitions, load_assets_from_modules

# Import asset modules
from orchestration.assets import eia_assets, enrichment_assets, dbt_assets, reporting_assets

# Import jobs and schedules
from orchestration.jobs import all_jobs, all_schedules

# Import resources
from orchestration.resources import get_resources


# Load all assets from modules
all_assets = load_assets_from_modules([
    eia_assets,
    enrichment_assets,
    dbt_assets,
    reporting_assets,
])


# Create Dagster Definitions
defs = Definitions(
    assets=all_assets,
    jobs=all_jobs,
    schedules=all_schedules,
    resources=get_resources(),
)
