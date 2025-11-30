"""
OPETSE-32: Report Export Utilities
Handles exporting evaluation reports to CSV with proper anonymization.
"""
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


def export_evaluations_to_csv(
    evaluations: List[Dict[str, Any]],
    anonymize: bool = True,
    include_metadata: bool = True
) -> str:
    """
    Export evaluations to CSV format with optional anonymization.

    Args:
        evaluations: List of evaluation dictionaries
        anonymize: Whether to anonymize rater identities
        include_metadata: Whether to include timestamp and metadata columns

    Returns:
        CSV string content
    """
    if not evaluations:
        return ""

    output = io.StringIO()

    # Define CSV headers based on anonymization setting
    if anonymize:
        headers = [
            "Evaluatee Name",
            "Evaluatee Email",
            "Rater",
            "Overall Score",
            "Comments",
        ]
    else:
        headers = [
            "Evaluatee Name",
            "Evaluatee Email",
            "Rater Name",
            "Rater Email",
            "Overall Score",
            "Comments",
        ]

    if include_metadata:
        headers.extend(["Submitted At", "Form Title"])

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    for evaluation in evaluations:
        row = {}

        # Evaluatee information (always visible)
        evaluatee = evaluation.get("evaluatee", {})
        row["Evaluatee Name"] = evaluatee.get("name", "Unknown")
        row["Evaluatee Email"] = evaluatee.get("email", "unknown@example.com")

        # Rater information (anonymized for students)
        if anonymize:
            row["Rater"] = "Anonymous Peer"
        else:
            evaluator = evaluation.get("evaluator", {})
            row["Rater Name"] = evaluator.get("name", "Unknown")
            row["Rater Email"] = evaluator.get("email", "unknown@example.com")

        # Evaluation data
        row["Overall Score"] = evaluation.get("total_score", 0)
        row["Comments"] = evaluation.get("comments", "")

        if include_metadata:
            row["Submitted At"] = evaluation.get("created_at", "")
            row["Form Title"] = evaluation.get("form_title", "")

        writer.writerow(row)

    return output.getvalue()


def export_team_report_to_csv(
    team_data: Dict[str, Any],
    anonymize: bool = True
) -> str:
    """
    Export team report to CSV format.

    Args:
        team_data: Team report dictionary
        anonymize: Whether to anonymize rater identities

    Returns:
        CSV string content
    """
    output = io.StringIO()

    # Team summary section
    output.write(f"Team Report: {team_data.get('name', 'Unknown Team')}\n")
    output.write(f"Project: {team_data.get('project_name', 'Unknown Project')}\n")
    output.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    output.write(f"Anonymized: {'Yes' if anonymize else 'No'}\n")
    output.write("\n")

    # Team statistics
    stats = team_data.get("statistics", {})
    output.write("Team Statistics\n")
    output.write(f"Total Members,{stats.get('total_members', 0)}\n")
    output.write(f"Total Evaluations,{stats.get('total_evaluations', 0)}\n")
    output.write(f"Average Score,{stats.get('average_score', 0)}\n")
    output.write("\n")

    # Member evaluations
    output.write("Member Evaluations\n")

    if anonymize:
        headers = ["Member Name", "Member Email", "Average Score", "Evaluation Count"]
    else:
        headers = ["Member Name", "Member Email", "Rater Name", "Rater Email", "Score", "Comments"]

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    members = team_data.get("members", [])
    for member in members:
        if anonymize:
            # Aggregated view for students
            row = {
                "Member Name": member.get("name", "Unknown"),
                "Member Email": member.get("email", "unknown@example.com"),
                "Average Score": member.get("average_score", 0),
                "Evaluation Count": len(member.get("evaluations", []))
            }
            writer.writerow(row)
        else:
            # Detailed view for instructors
            for evaluation in member.get("evaluations", []):
                evaluator = evaluation.get("evaluator", {})
                row = {
                    "Member Name": member.get("name", "Unknown"),
                    "Member Email": member.get("email", "unknown@example.com"),
                    "Rater Name": evaluator.get("name", "Unknown"),
                    "Rater Email": evaluator.get("email", "unknown@example.com"),
                    "Score": evaluation.get("total_score", 0),
                    "Comments": evaluation.get("comments", "")
                }
                writer.writerow(row)

    return output.getvalue()


def export_project_report_to_csv(
    project_data: Dict[str, Any],
    anonymize: bool = True
) -> str:
    """
    Export project report to CSV format.

    Args:
        project_data: Project report dictionary
        anonymize: Whether to anonymize rater identities

    Returns:
        CSV string content
    """
    output = io.StringIO()

    # Project summary
    project = project_data.get("project", {})
    output.write(f"Project Report: {project.get('title', 'Unknown Project')}\n")
    output.write(f"Description: {project.get('description', '')}\n")
    output.write(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
    output.write(f"Anonymized: {'Yes' if anonymize else 'No'}\n")
    output.write("\n")

    # Overall statistics
    stats = project_data.get("overall_statistics", {})
    output.write("Project Statistics\n")
    output.write(f"Total Teams,{stats.get('total_teams', 0)}\n")
    output.write(f"Total Evaluations,{stats.get('total_evaluations', 0)}\n")
    output.write(f"Average Score,{stats.get('average_score', 0)}\n")
    output.write(f"Participation Rate,{stats.get('participation_rate', 0)}%\n")
    output.write("\n")

    # Team-by-team breakdown
    output.write("Team Breakdown\n")

    if anonymize:
        headers = ["Team Name", "Members", "Average Score", "Evaluations"]
    else:
        headers = ["Team Name", "Member Name", "Rater Name", "Score", "Comments"]

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()

    teams = project_data.get("teams", [])
    for team in teams:
        if anonymize:
            # Summary view
            row = {
                "Team Name": team.get("name", "Unknown"),
                "Members": len(team.get("members", [])),
                "Average Score": team.get("statistics", {}).get("average_score", 0),
                "Evaluations": team.get("statistics", {}).get("total_evaluations", 0)
            }
            writer.writerow(row)
        else:
            # Detailed view
            for member in team.get("members", []):
                for evaluation in member.get("evaluations", []):
                    evaluator = evaluation.get("evaluator", {})
                    row = {
                        "Team Name": team.get("name", "Unknown"),
                        "Member Name": member.get("name", "Unknown"),
                        "Rater Name": evaluator.get("name", "Unknown"),
                        "Score": evaluation.get("total_score", 0),
                        "Comments": evaluation.get("comments", "")
                    }
                    writer.writerow(row)

    return output.getvalue()


def determine_anonymization(requester_role: Optional[str]) -> bool:
    """
    Determine if exports should be anonymized based on user role.

    Args:
        requester_role: Role of the requesting user

    Returns:
        True if exports should be anonymized
    """
    privileged_roles = ["instructor", "admin"]
    return not (requester_role and requester_role.lower() in privileged_roles)
