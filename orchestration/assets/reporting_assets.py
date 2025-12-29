"""
Dagster assets for report generation.

Generates Excel dashboards, Jupyter notebooks, and PDF summaries
from the analytics mart tables.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dagster import (
    asset,
    AssetExecutionContext,
    MetadataValue,
    MaterializeResult,
    Failure,
)

# Add reports module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "reports"))

# Report output directory
REPORTS_DIR = Path(__file__).parent.parent.parent / "reports" / "output"


@asset(
    group_name="reports",
    description="Excel dashboard with operational metrics",
    compute_kind="python",
    deps=["dbt_mart_models"],
)
def excel_dashboard(context: AssetExecutionContext) -> dict:
    """
    Generate Excel dashboard with operational metrics.
    
    Creates a multi-sheet workbook with production KPIs, equipment health,
    and emissions summary.
    """
    from report_generator import ExcelReportGenerator
    
    start_time = datetime.now()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = REPORTS_DIR / f"operational_dashboard_{datetime.now():%Y%m%d}.xlsx"
    
    context.log.info(f"Generating Excel dashboard: {output_path}")
    
    try:
        generator = ExcelReportGenerator()
        generator.generate_dashboard(str(output_path))
        
        file_size = output_path.stat().st_size
        
    except Exception as e:
        raise Failure(
            description=f"Failed to generate Excel dashboard: {e}",
            metadata={"error": str(e)},
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "output_path": str(output_path),
            "file_size_bytes": file_size,
            "duration_seconds": duration,
        },
        metadata={
            "output_path": MetadataValue.path(str(output_path)),
            "file_size_bytes": MetadataValue.int(file_size),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="reports",
    description="PDF executive summary report",
    compute_kind="python",
    deps=["dbt_mart_models"],
)
def pdf_executive_summary(context: AssetExecutionContext) -> dict:
    """
    Generate PDF executive summary with key metrics.
    
    Creates a one-page summary suitable for leadership review.
    """
    from report_generator import PDFReportGenerator
    
    start_time = datetime.now()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = REPORTS_DIR / f"executive_summary_{datetime.now():%Y%m%d}.pdf"
    
    context.log.info(f"Generating PDF summary: {output_path}")
    
    try:
        generator = PDFReportGenerator()
        generator.generate_summary(str(output_path))
        
        file_size = output_path.stat().st_size
        
    except Exception as e:
        raise Failure(
            description=f"Failed to generate PDF summary: {e}",
            metadata={"error": str(e)},
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "output_path": str(output_path),
            "file_size_bytes": file_size,
            "duration_seconds": duration,
        },
        metadata={
            "output_path": MetadataValue.path(str(output_path)),
            "file_size_bytes": MetadataValue.int(file_size),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="reports",
    description="Jupyter notebook with exploratory analysis",
    compute_kind="python",
    deps=["dbt_mart_models"],
)
def analysis_notebook(context: AssetExecutionContext) -> dict:
    """
    Execute Jupyter notebook for exploratory analysis.
    
    Runs the analysis notebook and exports results.
    """
    import subprocess
    
    start_time = datetime.now()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    notebook_template = Path(__file__).parent.parent.parent / "reports" / "analysis_template.ipynb"
    output_notebook = REPORTS_DIR / f"analysis_{datetime.now():%Y%m%d}.ipynb"
    output_html = REPORTS_DIR / f"analysis_{datetime.now():%Y%m%d}.html"
    
    context.log.info(f"Executing analysis notebook: {output_notebook}")
    
    try:
        # Execute notebook using papermill
        result = subprocess.run(
            [
                "papermill",
                str(notebook_template),
                str(output_notebook),
                "-k", "python3",
            ],
            capture_output=True,
            text=True,
        )
        
        if result.returncode != 0:
            context.log.warning(f"Notebook execution had issues: {result.stderr}")
        
        # Convert to HTML
        subprocess.run(
            [
                "jupyter", "nbconvert",
                "--to", "html",
                str(output_notebook),
            ],
            capture_output=True,
        )
        
    except Exception as e:
        context.log.warning(f"Notebook execution failed: {e}")
        # Create a simple output even if notebook fails
        output_notebook.write_text("{}")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "notebook_path": str(output_notebook),
            "html_path": str(output_html) if output_html.exists() else None,
            "duration_seconds": duration,
        },
        metadata={
            "notebook_path": MetadataValue.path(str(output_notebook)),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="reports",
    description="All reports generated",
    compute_kind="python",
    deps=["excel_dashboard", "pdf_executive_summary"],
)
def reports_complete(
    context: AssetExecutionContext,
) -> dict:
    """
    Marker asset indicating all reports have been generated.
    
    This asset runs after all report generation is complete.
    """
    timestamp = datetime.now()
    
    # List generated reports
    reports = []
    if REPORTS_DIR.exists():
        reports = [f.name for f in REPORTS_DIR.iterdir() if f.is_file()]
    
    context.log.info(f"Reports complete. Generated {len(reports)} files.")
    
    return MaterializeResult(
        value={
            "timestamp": timestamp.isoformat(),
            "reports_generated": reports,
        },
        metadata={
            "timestamp": MetadataValue.text(timestamp.isoformat()),
            "reports_count": MetadataValue.int(len(reports)),
            "reports": MetadataValue.json(reports),
        },
    )
