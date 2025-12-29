"""
Dagster assets for dbt transformations.

Integrates dbt models as Dagster assets for the energy analytics pipeline.
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path

from dagster import (
    asset,
    AssetExecutionContext,
    MetadataValue,
    MaterializeResult,
    Failure,
    AssetIn,
)


# Path to dbt project
DBT_PROJECT_DIR = Path(__file__).parent.parent.parent / "dbt"


def run_dbt_command(command: list[str], context: AssetExecutionContext) -> dict:
    """
    Run a dbt command and return the result.
    
    Args:
        command: dbt command to run (e.g., ["run", "--select", "staging"])
        context: Dagster execution context for logging
    
    Returns:
        dict with success status and output
    """
    full_command = ["dbt"] + command

    context.log.info(f"Running: {' '.join(full_command)}")
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            cwd=str(DBT_PROJECT_DIR),
            env={
                **os.environ,
                "DBT_PROFILES_DIR": str(DBT_PROJECT_DIR),
            },
        )
        
        if result.stdout:
            for line in result.stdout.split("\n"):
                if line.strip():
                    context.log.info(line)

        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else "dbt command failed with no error output"
            context.log.error(f"dbt command failed with return code {result.returncode}")
            context.log.error(f"stderr: {error_msg}")
            context.log.error(f"stdout: {result.stdout[:500] if result.stdout else 'No stdout'}")
            return {
                "success": False,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": error_msg,
            }
        
        return {
            "success": True,
            "returncode": 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        
    except Exception as e:
        context.log.error(f"Failed to run dbt command: {e}")
        return {
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
        }


@asset(
    group_name="dbt_deps",
    description="Install dbt dependencies",
    compute_kind="dbt",
)
def dbt_deps(context: AssetExecutionContext) -> dict:
    """Install dbt package dependencies."""
    start_time = datetime.now()

    # Check if packages.yml exists
    packages_file = DBT_PROJECT_DIR / "packages.yml"
    if not packages_file.exists():
        context.log.info("No packages.yml file found - skipping dbt deps")
        duration = (datetime.now() - start_time).total_seconds()
        return MaterializeResult(
            value={"success": True, "skipped": True, "duration_seconds": duration},
            metadata={
                "duration_seconds": MetadataValue.float(duration),
                "status": MetadataValue.text("skipped - no packages.yml"),
            },
        )

    result = run_dbt_command(["deps"], context)

    if not result["success"]:
        raise Failure(
            description="dbt deps failed",
            metadata={"stderr": result["stderr"]},
        )

    duration = (datetime.now() - start_time).total_seconds()

    return MaterializeResult(
        value={"success": True, "duration_seconds": duration},
        metadata={
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="dbt_staging",
    description="Run dbt staging models",
    compute_kind="dbt",
    deps=[dbt_deps],
    ins={
        "eia_natural_gas": AssetIn(key="eia_natural_gas_prices", dagster_type=None),
        "eia_petroleum": AssetIn(key="eia_petroleum_prices", dagster_type=None),
        "enrichment_snapshot": AssetIn(key="enrichment_daily_snapshot", dagster_type=None),
    },
)
def dbt_staging_models(
    context: AssetExecutionContext,
    eia_natural_gas: dict,
    eia_petroleum: dict,
    enrichment_snapshot: dict,
) -> dict:
    """
    Run dbt staging models.
    
    These models clean and standardize raw data from EIA and enrichment sources.
    """
    start_time = datetime.now()
    
    context.log.info("Running dbt staging models")
    result = run_dbt_command(["run", "--select", "staging"], context)
    
    if not result["success"]:
        raise Failure(
            description="dbt staging models failed",
            metadata={"stderr": result["stderr"]},
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Parse output to count models run
    models_run = result["stdout"].count("SUCCESS")
    
    return MaterializeResult(
        value={
            "success": True,
            "models_run": models_run,
            "duration_seconds": duration,
        },
        metadata={
            "models_run": MetadataValue.int(models_run),
            "duration_seconds": MetadataValue.float(duration),
            "layer": MetadataValue.text("staging"),
        },
    )


@asset(
    group_name="dbt_intermediate",
    description="Run dbt intermediate models",
    compute_kind="dbt",
    deps=[dbt_staging_models],
)
def dbt_intermediate_models(context: AssetExecutionContext) -> dict:
    """
    Run dbt intermediate models.
    
    These models join and prepare data for final analytics tables.
    """
    start_time = datetime.now()
    
    context.log.info("Running dbt intermediate models")
    result = run_dbt_command(["run", "--select", "intermediate"], context)
    
    if not result["success"]:
        raise Failure(
            description="dbt intermediate models failed",
            metadata={"stderr": result["stderr"]},
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    models_run = result["stdout"].count("SUCCESS")
    
    return MaterializeResult(
        value={
            "success": True,
            "models_run": models_run,
            "duration_seconds": duration,
        },
        metadata={
            "models_run": MetadataValue.int(models_run),
            "duration_seconds": MetadataValue.float(duration),
            "layer": MetadataValue.text("intermediate"),
        },
    )


@asset(
    group_name="dbt_marts",
    description="Run dbt mart models",
    compute_kind="dbt",
    deps=[dbt_intermediate_models],
)
def dbt_mart_models(context: AssetExecutionContext) -> dict:
    """
    Run dbt mart models.
    
    These are the final analytics tables ready for reporting and BI.
    """
    start_time = datetime.now()
    
    context.log.info("Running dbt mart models")
    result = run_dbt_command(["run", "--select", "marts"], context)
    
    if not result["success"]:
        raise Failure(
            description="dbt mart models failed",
            metadata={"stderr": result["stderr"]},
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    models_run = result["stdout"].count("SUCCESS")
    
    return MaterializeResult(
        value={
            "success": True,
            "models_run": models_run,
            "duration_seconds": duration,
        },
        metadata={
            "models_run": MetadataValue.int(models_run),
            "duration_seconds": MetadataValue.float(duration),
            "layer": MetadataValue.text("marts"),
        },
    )


@asset(
    group_name="dbt_tests",
    description="Run dbt tests",
    compute_kind="dbt",
    deps=[dbt_deps, dbt_mart_models],
)
def dbt_tests(context: AssetExecutionContext) -> dict:
    """
    Run dbt tests to validate data quality.
    
    Executes all tests defined in schema.yml files.
    """
    start_time = datetime.now()
    
    context.log.info("Running dbt tests")
    result = run_dbt_command(["test"], context)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    # Count test results
    tests_passed = result["stdout"].count("PASS")
    tests_failed = result["stdout"].count("FAIL")
    tests_warned = result["stdout"].count("WARN")
    
    if tests_failed > 0:
        context.log.warning(f"{tests_failed} tests failed")
    
    return MaterializeResult(
        value={
            "success": tests_failed == 0,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "tests_warned": tests_warned,
            "duration_seconds": duration,
        },
        metadata={
            "tests_passed": MetadataValue.int(tests_passed),
            "tests_failed": MetadataValue.int(tests_failed),
            "tests_warned": MetadataValue.int(tests_warned),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="dbt_all",
    description="Run all dbt models (full refresh)",
    compute_kind="dbt",
    deps=[dbt_deps],
)
def dbt_run_all(context: AssetExecutionContext) -> dict:
    """
    Run all dbt models in a single pass.
    
    Used for full refreshes or initial loads.
    """
    start_time = datetime.now()
    
    context.log.info("Running all dbt models")
    result = run_dbt_command(["run"], context)
    
    if not result["success"]:
        raise Failure(
            description="dbt run failed",
            metadata={"stderr": result["stderr"]},
        )
    
    duration = (datetime.now() - start_time).total_seconds()
    models_run = result["stdout"].count("SUCCESS")
    
    return MaterializeResult(
        value={
            "success": True,
            "models_run": models_run,
            "duration_seconds": duration,
        },
        metadata={
            "models_run": MetadataValue.int(models_run),
            "duration_seconds": MetadataValue.float(duration),
        },
    )


@asset(
    group_name="dbt_docs",
    description="Generate dbt documentation",
    compute_kind="dbt",
    deps=[dbt_deps, dbt_mart_models],
)
def dbt_docs(context: AssetExecutionContext) -> dict:
    """Generate dbt documentation."""
    start_time = datetime.now()
    
    context.log.info("Generating dbt documentation")
    result = run_dbt_command(["docs", "generate"], context)
    
    if not result["success"]:
        context.log.warning("dbt docs generation failed, continuing anyway")
    
    duration = (datetime.now() - start_time).total_seconds()
    
    return MaterializeResult(
        value={
            "success": result["success"],
            "duration_seconds": duration,
        },
        metadata={
            "duration_seconds": MetadataValue.float(duration),
        },
    )
