"""
Dagster assets for the energy analytics pipeline.

This module exports all assets organized by source:
- EIA assets: Natural gas and petroleum data from EIA API
- Enrichment assets: Synthetic operational data from FastAPI service
- dbt assets: Transformation models
- Reporting assets: Excel, PDF, and notebook reports
"""

from orchestration.assets.eia_assets import (
    eia_natural_gas_prices,
    eia_petroleum_prices,
    eia_natural_gas_quality_check,
)

from orchestration.assets.enrichment_assets import (
    enrichment_wells,
    enrichment_production,
    enrichment_equipment,
    enrichment_emissions,
    enrichment_daily_snapshot,
)

from orchestration.assets.dbt_assets import (
    dbt_deps,
    dbt_staging_models,
    dbt_intermediate_models,
    dbt_mart_models,
    dbt_tests,
    dbt_run_all,
    dbt_docs,
)

from orchestration.assets.reporting_assets import (
    excel_dashboard,
    pdf_executive_summary,
    analysis_notebook,
    reports_complete,
)

__all__ = [
    # EIA assets
    "eia_natural_gas_prices",
    "eia_petroleum_prices",
    "eia_natural_gas_quality_check",
    # Enrichment assets
    "enrichment_wells",
    "enrichment_production",
    "enrichment_equipment",
    "enrichment_emissions",
    "enrichment_daily_snapshot",
    # dbt assets
    "dbt_deps",
    "dbt_staging_models",
    "dbt_intermediate_models",
    "dbt_mart_models",
    "dbt_tests",
    "dbt_run_all",
    "dbt_docs",
    # Reporting assets
    "excel_dashboard",
    "pdf_executive_summary",
    "analysis_notebook",
    "reports_complete",
]
