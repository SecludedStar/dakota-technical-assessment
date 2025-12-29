"""
Report generation module for energy analytics.

Generates Excel dashboards, PDF summaries, and analysis notebooks
from the analytics mart tables.
"""

import os
from datetime import datetime
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor


class BaseReportGenerator:
    """Base class for report generators with database connection."""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.host = host or os.environ.get("POSTGRES_HOST", "localhost")
        self.port = port or int(os.environ.get("POSTGRES_PORT", "5432"))
        self.database = database or os.environ.get("POSTGRES_DB", "energy_analytics")
        self.user = user or os.environ.get("POSTGRES_USER", "postgres")
        self.password = password or os.environ.get("POSTGRES_PASSWORD", "postgres")
    
    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )
    
    def fetch_data(self, query: str) -> list[dict]:
        """Fetch data from database."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]


class ExcelReportGenerator(BaseReportGenerator):
    """Generate Excel dashboards with operational metrics."""
    
    def generate_dashboard(self, output_path: str) -> str:
        """
        Generate Excel dashboard with multiple sheets.
        
        Args:
            output_path: Path for output Excel file
        
        Returns:
            Path to generated file
        """
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.chart import BarChart, PieChart, Reference
        from openpyxl.utils.dataframe import dataframe_to_rows
        
        wb = openpyxl.Workbook()
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # =========================================
        # Sheet 1: Executive Summary
        # =========================================
        ws_summary = wb.active
        ws_summary.title = "Executive Summary"
        
        # Add title
        ws_summary["A1"] = "Energy Analytics Dashboard"
        ws_summary["A1"].font = Font(bold=True, size=16)
        ws_summary["A2"] = f"Generated: {datetime.now():%Y-%m-%d %H:%M}"
        
        # Get summary metrics
        try:
            operator_data = self.fetch_data("""
                SELECT
                    operator,
                    total_wells,
                    active_wells,
                    total_oil_bbl_30d as total_oil_bbl,
                    total_gas_mcf_30d as total_gas_mcf,
                    total_boe_30d as total_boe,
                    avg_equipment_health
                FROM staging_analytics.dim_operator_summary
                ORDER BY total_boe_30d DESC
                LIMIT 10
            """)

            # Add operator summary
            ws_summary["A4"] = "Top Operators by Production (30 days)"
            ws_summary["A4"].font = Font(bold=True, size=12)

            headers = ["Operator", "Total Wells", "Active Wells", "Oil (BBL)", "Gas (MCF)", "BOE", "Avg Health"]
            for col, header in enumerate(headers, 1):
                cell = ws_summary.cell(row=5, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill

            for row_idx, row_data in enumerate(operator_data, 6):
                ws_summary.cell(row=row_idx, column=1, value=row_data.get("operator"))
                ws_summary.cell(row=row_idx, column=2, value=row_data.get("total_wells"))
                ws_summary.cell(row=row_idx, column=3, value=row_data.get("active_wells"))
                ws_summary.cell(row=row_idx, column=4, value=row_data.get("total_oil_bbl"))
                ws_summary.cell(row=row_idx, column=5, value=row_data.get("total_gas_mcf"))
                ws_summary.cell(row=row_idx, column=6, value=row_data.get("total_boe"))
                ws_summary.cell(row=row_idx, column=7, value=row_data.get("avg_equipment_health"))
        
        except Exception as e:
            ws_summary["A4"] = f"Error loading data: {e}"
        
        # =========================================
        # Sheet 2: Production Metrics
        # =========================================
        ws_production = wb.create_sheet("Production")
        ws_production["A1"] = "Daily Well Performance"
        ws_production["A1"].font = Font(bold=True, size=14)
        
        try:
            production_data = self.fetch_data("""
                SELECT
                    well_id,
                    well_name,
                    operator,
                    production_date,
                    oil_bbl,
                    gas_mcf,
                    water_bbl,
                    boe_total as boe,
                    water_cut_pct,
                    gor_mcf_bbl as gas_oil_ratio
                FROM staging_analytics.fct_well_performance_daily
                ORDER BY production_date DESC, boe_total DESC
                LIMIT 100
            """)
            
            headers = ["Well ID", "Well Name", "Operator", "Date", "Oil (BBL)", "Gas (MCF)", "Water (BBL)", "BOE", "Water Cut %", "GOR"]
            for col, header in enumerate(headers, 1):
                cell = ws_production.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
            
            for row_idx, row_data in enumerate(production_data, 4):
                ws_production.cell(row=row_idx, column=1, value=row_data.get("well_id"))
                ws_production.cell(row=row_idx, column=2, value=row_data.get("well_name"))
                ws_production.cell(row=row_idx, column=3, value=row_data.get("operator"))
                ws_production.cell(row=row_idx, column=4, value=str(row_data.get("production_date", "")))
                ws_production.cell(row=row_idx, column=5, value=row_data.get("oil_bbl"))
                ws_production.cell(row=row_idx, column=6, value=row_data.get("gas_mcf"))
                ws_production.cell(row=row_idx, column=7, value=row_data.get("water_bbl"))
                ws_production.cell(row=row_idx, column=8, value=row_data.get("boe"))
                ws_production.cell(row=row_idx, column=9, value=row_data.get("water_cut_pct"))
                ws_production.cell(row=row_idx, column=10, value=row_data.get("gas_oil_ratio"))
        
        except Exception as e:
            ws_production["A3"] = f"Error loading data: {e}"
        
        # =========================================
        # Sheet 3: Equipment Health
        # =========================================
        ws_equipment = wb.create_sheet("Equipment Health")
        ws_equipment["A1"] = "Equipment Health Status"
        ws_equipment["A1"].font = Font(bold=True, size=14)
        
        try:
            equipment_data = self.fetch_data("""
                SELECT 
                    equipment_id,
                    well_id,
                    equipment_type,
                    manufacturer,
                    health_score,
                    health_category,
                    status,
                    maintenance_priority_score,
                    days_until_maintenance,
                    maintenance_status
                FROM staging_analytics.fct_equipment_health
                ORDER BY maintenance_priority_score DESC
                LIMIT 100
            """)
            
            headers = ["Equipment ID", "Well ID", "Type", "Manufacturer", "Health Score", "Category", "Status", "Priority Score", "Days to Maint", "Maint Status"]
            for col, header in enumerate(headers, 1):
                cell = ws_equipment.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
            
            for row_idx, row_data in enumerate(equipment_data, 4):
                ws_equipment.cell(row=row_idx, column=1, value=row_data.get("equipment_id"))
                ws_equipment.cell(row=row_idx, column=2, value=row_data.get("well_id"))
                ws_equipment.cell(row=row_idx, column=3, value=row_data.get("equipment_type"))
                ws_equipment.cell(row=row_idx, column=4, value=row_data.get("manufacturer"))
                ws_equipment.cell(row=row_idx, column=5, value=row_data.get("health_score"))
                ws_equipment.cell(row=row_idx, column=6, value=row_data.get("health_category"))
                ws_equipment.cell(row=row_idx, column=7, value=row_data.get("status"))
                ws_equipment.cell(row=row_idx, column=8, value=row_data.get("maintenance_priority_score"))
                ws_equipment.cell(row=row_idx, column=9, value=row_data.get("days_until_maintenance"))
                ws_equipment.cell(row=row_idx, column=10, value=row_data.get("maintenance_status"))
        
        except Exception as e:
            ws_equipment["A3"] = f"Error loading data: {e}"
        
        # =========================================
        # Sheet 4: Emissions Summary
        # =========================================
        ws_emissions = wb.create_sheet("Emissions")
        ws_emissions["A1"] = "Daily Emissions Summary"
        ws_emissions["A1"].font = Font(bold=True, size=14)
        
        try:
            emissions_data = self.fetch_data("""
                SELECT 
                    well_id,
                    measurement_date,
                    methane_kg,
                    co2_kg,
                    voc_kg,
                    co2_equivalent_kg,
                    flare_volume_mcf,
                    leak_detected,
                    risk_level
                FROM staging_analytics.fct_emissions_daily
                ORDER BY measurement_date DESC, co2_equivalent_kg DESC
                LIMIT 100
            """)
            
            headers = ["Well ID", "Date", "Methane (kg)", "CO2 (kg)", "VOC (kg)", "CO2e (kg)", "Flare (MCF)", "Leak?", "Risk Level"]
            for col, header in enumerate(headers, 1):
                cell = ws_emissions.cell(row=3, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
            
            for row_idx, row_data in enumerate(emissions_data, 4):
                ws_emissions.cell(row=row_idx, column=1, value=row_data.get("well_id"))
                ws_emissions.cell(row=row_idx, column=2, value=str(row_data.get("measurement_date", "")))
                ws_emissions.cell(row=row_idx, column=3, value=row_data.get("methane_kg"))
                ws_emissions.cell(row=row_idx, column=4, value=row_data.get("co2_kg"))
                ws_emissions.cell(row=row_idx, column=5, value=row_data.get("voc_kg"))
                ws_emissions.cell(row=row_idx, column=6, value=row_data.get("co2_equivalent_kg"))
                ws_emissions.cell(row=row_idx, column=7, value=row_data.get("flare_volume_mcf"))
                ws_emissions.cell(row=row_idx, column=8, value=row_data.get("leak_detected"))
                ws_emissions.cell(row=row_idx, column=9, value=row_data.get("risk_level"))
        
        except Exception as e:
            ws_emissions["A3"] = f"Error loading data: {e}"
        
        # Adjust column widths
        for ws in [ws_summary, ws_production, ws_equipment, ws_emissions]:
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 30)
        
        wb.save(output_path)
        return output_path


class PDFReportGenerator(BaseReportGenerator):
    """Generate PDF executive summaries."""
    
    def generate_summary(self, output_path: str) -> str:
        """
        Generate PDF executive summary.
        
        Args:
            output_path: Path for output PDF file
        
        Returns:
            Path to generated file
        """
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import inch
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center
        )
        story.append(Paragraph("Energy Analytics Executive Summary", title_style))
        story.append(Paragraph(f"Generated: {datetime.now():%Y-%m-%d %H:%M}", styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        
        # Summary metrics
        try:
            # Get totals
            totals = self.fetch_data("""
                SELECT
                    COUNT(DISTINCT well_id) as total_wells,
                    SUM(oil_bbl) as total_oil,
                    SUM(gas_mcf) as total_gas,
                    SUM(boe_total) as total_boe
                FROM staging_analytics.fct_well_performance_daily
            """)
            
            if totals:
                t = totals[0]
                story.append(Paragraph("Production Summary", styles['Heading2']))
                summary_data = [
                    ["Metric", "Value"],
                    ["Total Wells", f"{t.get('total_wells', 0):,}"],
                    ["Total Oil (BBL)", f"{t.get('total_oil', 0):,.0f}"],
                    ["Total Gas (MCF)", f"{t.get('total_gas', 0):,.0f}"],
                    ["Total BOE", f"{t.get('total_boe', 0):,.0f}"],
                ]
                
                table = Table(summary_data, colWidths=[3*inch, 3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E75B6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.3*inch))
            
            # Equipment health summary
            equipment = self.fetch_data("""
                SELECT 
                    health_category,
                    COUNT(*) as count
                FROM staging_analytics.fct_equipment_health
                GROUP BY health_category
                ORDER BY 
                    CASE health_category
                        WHEN 'Excellent' THEN 1
                        WHEN 'Good' THEN 2
                        WHEN 'Fair' THEN 3
                        WHEN 'Poor' THEN 4
                        WHEN 'Critical' THEN 5
                    END
            """)
            
            if equipment:
                story.append(Paragraph("Equipment Health Distribution", styles['Heading2']))
                eq_data = [["Category", "Count"]]
                eq_data.extend([[row['health_category'], str(row['count'])] for row in equipment])
                
                table = Table(eq_data, colWidths=[3*inch, 3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E75B6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(table)
                story.append(Spacer(1, 0.3*inch))
            
            # Top operators
            operators = self.fetch_data("""
                SELECT
                    operator,
                    total_wells,
                    total_boe_30d
                FROM staging_analytics.dim_operator_summary
                ORDER BY total_boe_30d DESC
                LIMIT 5
            """)

            if operators:
                story.append(Paragraph("Top Operators by Production", styles['Heading2']))
                op_data = [["Operator", "Wells", "BOE (30d)"]]
                for row in operators:
                    boe = row.get('total_boe_30d', 0) or 0
                    op_data.append([
                        row['operator'],
                        str(row.get('total_wells', 0)),
                        f"{boe:,.0f}"
                    ])
                
                table = Table(op_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E75B6')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(table)
        
        except Exception as e:
            story.append(Paragraph(f"Error loading data: {e}", styles['Normal']))
        
        doc.build(story)
        return output_path


if __name__ == "__main__":
    # Test report generation
    excel_gen = ExcelReportGenerator()
    excel_gen.generate_dashboard("test_dashboard.xlsx")
    print("Generated test_dashboard.xlsx")
    
    pdf_gen = PDFReportGenerator()
    pdf_gen.generate_summary("test_summary.pdf")
    print("Generated test_summary.pdf")
