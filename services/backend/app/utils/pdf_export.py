"""
PDF Export Utilities for Reports.

OPETSE-16: Generate PDF reports for instructors with anonymization support.
Exports respect the same anonymization rules as CSV exports.
"""
from io import BytesIO
from datetime import datetime, timezone
from typing import Dict, List
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib.enums import TA_CENTER


def generate_pdf_header(story: List, title: str, subtitle: str = None, styles: Dict = None):
    """
    Generate common PDF header with title and optional subtitle.

    Args:
        story: ReportLab story list to append elements to
        title: Main title text
        subtitle: Optional subtitle text
        styles: ReportLab styles dictionary
    """
    if styles is None:
        styles = getSampleStyleSheet()

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    story.append(Paragraph(title, title_style))

    # Subtitle
    if subtitle:
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.gray,
            spaceAfter=20,
            alignment=TA_CENTER
        )
        story.append(Paragraph(subtitle, subtitle_style))

    story.append(Spacer(1, 0.2 * inch))


def generate_pdf_footer(canvas, doc):
    """
    Generate PDF footer with page number and timestamp.

    Args:
        canvas: ReportLab canvas object
        doc: ReportLab document object
    """
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    canvas.setFillColor(colors.gray)

    # Page number
    page_num = f"Page {doc.page}"
    canvas.drawRightString(7.5 * inch, 0.5 * inch, page_num)

    # Timestamp
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    canvas.drawString(inch, 0.5 * inch, f"Generated: {timestamp}")

    canvas.restoreState()


def export_project_report_to_pdf(report_data: Dict, anonymize: bool = True) -> bytes:
    """
    Export project evaluation report to PDF.

    OPETSE-16: Generate comprehensive project report with team breakdowns.
    OPETSE-8: Respects anonymization for student users.

    Args:
        report_data: Project report dictionary from get_project_report
        anonymize: Whether to anonymize evaluator identities

    Returns:
        PDF file content as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch)
    story = []
    styles = getSampleStyleSheet()

    # Header
    project = report_data.get('project', {})
    project_title = project.get('title', 'Project Report')
    subtitle = f"Project ID: {project.get('id', 'N/A')}"
    if anonymize:
        subtitle += " (Anonymized)"

    generate_pdf_header(story, project_title, subtitle, styles)

    # Project Overview
    overview_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=10
    )
    story.append(Paragraph("Project Overview", overview_style))

    # Project details
    details = [
        ['Description:', project.get('description', 'N/A')],
        ['Status:', project.get('status', 'N/A')],
        ['Start Date:', project.get('start_date', 'N/A')],
        ['End Date:', project.get('end_date', 'N/A')]
    ]

    details_table = Table(details, colWidths=[1.5 * inch, 5 * inch])
    details_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#4f46e5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 0.3 * inch))

    # Overall Statistics
    story.append(Paragraph("Overall Statistics", overview_style))

    stats = report_data.get('overall_statistics', {})
    stats_data = [
        ['Total Teams', 'Total Evaluations', 'Average Score'],
        [
            str(stats.get('total_teams', 0)),
            str(stats.get('total_evaluations', 0)),
            f"{stats.get('average_score', 0):.2f}"
        ]
    ]

    stats_table = Table(stats_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.3 * inch))

    # Team Details
    teams = report_data.get('teams', [])
    if teams:
        story.append(Paragraph("Team Performance", overview_style))

        team_headers = ['Team Name', 'Members', 'Evaluations', 'Avg Score']
        team_data = [team_headers]

        for team_info in teams:
            team = team_info.get('team', {})
            statistics = team_info.get('statistics', {})

            team_data.append([
                team.get('name', 'N/A'),
                str(statistics.get('total_members', 0)),
                str(statistics.get('total_evaluations', 0)),
                f"{statistics.get('average_score', 0):.2f}"
            ])

        team_table = Table(team_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        team_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(team_table)

    # Build PDF
    doc.build(story, onFirstPage=generate_pdf_footer, onLaterPages=generate_pdf_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def export_team_report_to_pdf(report_data: Dict, anonymize: bool = True) -> bytes:
    """
    Export team evaluation report to PDF.

    OPETSE-16: Generate detailed team report with member evaluations.
    OPETSE-8: Anonymizes evaluator identities for students.

    Args:
        report_data: Team report dictionary from get_team_report
        anonymize: Whether to anonymize evaluator identities

    Returns:
        PDF file content as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch)
    story = []
    styles = getSampleStyleSheet()

    # Header
    team = report_data.get('team', {})
    team_name = team.get('name', 'Team Report')
    subtitle = f"Team ID: {team.get('id', 'N/A')}"
    if report_data.get('project_name'):
        subtitle += f" | Project: {report_data['project_name']}"
    if anonymize:
        subtitle += " (Anonymized)"

    generate_pdf_header(story, team_name, subtitle, styles)

    # Team Statistics
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#4f46e5'),
        spaceAfter=10
    )
    story.append(Paragraph("Team Statistics", section_style))

    statistics = report_data.get('statistics', {})
    stats_data = [
        ['Total Members', 'Total Evaluations', 'Average Score'],
        [
            str(statistics.get('total_members', 0)),
            str(statistics.get('total_evaluations', 0)),
            f"{statistics.get('average_score', 0):.2f}"
        ]
    ]

    stats_table = Table(stats_data, colWidths=[2 * inch, 2 * inch, 2 * inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.3 * inch))

    # Member Performance
    members = report_data.get('members', [])
    if members:
        story.append(Paragraph("Member Performance", section_style))

        member_headers = ['Member Name', 'Email', 'Evaluations Received', 'Average Score']
        if anonymize:
            member_headers = ['Member Name', 'Evaluations Received', 'Average Score']

        member_data = [member_headers]

        for member_info in members:
            member = member_info.get('member', {})

            if anonymize:
                row = [
                    member.get('name', 'N/A'),
                    str(member_info.get('evaluations_received', 0)),
                    f"{member_info.get('average_score', 0):.2f}"
                ]
            else:
                row = [
                    member.get('name', 'N/A'),
                    member.get('email', 'N/A'),
                    str(member_info.get('evaluations_received', 0)),
                    f"{member_info.get('average_score', 0):.2f}"
                ]

            member_data.append(row)

        col_widths = [2 * inch, 1.5 * inch, 1.5 * inch] if anonymize else [2 * inch, 2 * inch, 1.5 * inch, 1.5 * inch]
        member_table = Table(member_data, colWidths=col_widths)
        member_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(member_table)

    # Anonymization Notice
    if anonymize:
        story.append(Spacer(1, 0.3 * inch))
        notice_style = ParagraphStyle(
            'Notice',
            parent=styles['Italic'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Note: Evaluator identities are anonymized in this report.", notice_style))

    # Build PDF
    doc.build(story, onFirstPage=generate_pdf_footer, onLaterPages=generate_pdf_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def export_evaluations_to_pdf(evaluations: List[Dict], anonymize: bool = True) -> bytes:
    """
    Export evaluations list to PDF.

    OPETSE-16: Generate PDF of individual evaluations.
    OPETSE-8: Anonymizes evaluator details for students.

    Args:
        evaluations: List of evaluation dictionaries
        anonymize: Whether to anonymize evaluator identities

    Returns:
        PDF file content as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=inch, bottomMargin=inch)
    story = []
    styles = getSampleStyleSheet()

    # Header
    title = "Evaluations Report"
    subtitle = f"Total Evaluations: {len(evaluations)}"
    if anonymize:
        subtitle += " (Anonymized)"

    generate_pdf_header(story, title, subtitle, styles)

    # Evaluations Table
    if evaluations:
        headers = ['Evaluatee', 'Evaluator', 'Form', 'Score', 'Submitted']
        if anonymize:
            headers = ['Evaluatee', 'Form', 'Score', 'Submitted']

        eval_data = [headers]

        for evaluation in evaluations:
            evaluatee = evaluation.get('evaluatee', {})
            evaluator = evaluation.get('evaluator', {})

            submitted_at = evaluation.get('submitted_at', 'N/A')
            if isinstance(submitted_at, str) and len(submitted_at) > 10:
                submitted_at = submitted_at[:10]  # Just date

            if anonymize:
                row = [
                    evaluatee.get('name', 'N/A'),
                    evaluation.get('form_title', 'N/A'),
                    str(evaluation.get('total_score', 0)),
                    submitted_at
                ]
            else:
                row = [
                    evaluatee.get('name', 'N/A'),
                    evaluator.get('name', 'N/A'),
                    evaluation.get('form_title', 'N/A'),
                    str(evaluation.get('total_score', 0)),
                    submitted_at
                ]

            eval_data.append(row)

        col_widths = [1.5 * inch, 2 * inch, 1 * inch, 1.5 * inch] if anonymize else [1.5 * inch, 1.5 * inch, 1.5 * inch, 1 * inch, 1.5 * inch]
        eval_table = Table(eval_data, colWidths=col_widths)
        eval_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        story.append(eval_table)
    else:
        story.append(Paragraph("No evaluations found.", styles['Normal']))

    # Anonymization Notice
    if anonymize:
        story.append(Spacer(1, 0.3 * inch))
        notice_style = ParagraphStyle(
            'Notice',
            parent=styles['Italic'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        story.append(Paragraph("Note: Evaluator identities are anonymized in this report.", notice_style))

    # Build PDF
    doc.build(story, onFirstPage=generate_pdf_footer, onLaterPages=generate_pdf_footer)

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
