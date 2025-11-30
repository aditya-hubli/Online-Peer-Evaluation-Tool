"""
OPETSE-8: Anonymity Utilities
Handles anonymization of peer evaluation feedback to protect evaluator identities.
"""
from typing import Dict, List, Any, Optional


def anonymize_evaluator(evaluation: Dict[str, Any], requester_id: Optional[int] = None, requester_role: Optional[str] = None) -> Dict[str, Any]:
    """
    Remove evaluator identity from evaluation data to maintain anonymity.

    Only instructors and admins can see evaluator identities.
    Students (including the evaluatee) cannot see who evaluated them.

    Args:
        evaluation: The evaluation dictionary containing evaluator info
        requester_id: The ID of the user requesting the data
        requester_role: The role of the user requesting the data (student/instructor/admin)

    Returns:
        The evaluation with evaluator info anonymized or preserved based on permissions
    """
    # Create a copy to avoid mutating the original
    result = evaluation.copy()

    # Determine if evaluator info should be visible
    can_view_evaluator = _can_view_evaluator_identity(requester_role)

    if not can_view_evaluator:
        # Remove or mask evaluator information
        if "evaluator" in result:
            result["evaluator"] = {
                "id": "anonymous",
                "name": "Anonymous",
                "email": "anonymous@hidden.com"
            }

        if "evaluator_id" in result:
            # Keep the ID for system purposes but mark it as anonymous
            result["evaluator_id_hidden"] = True

    return result


def anonymize_evaluation_list(evaluations: List[Dict[str, Any]], requester_id: Optional[int] = None, requester_role: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Anonymize a list of evaluations based on user permissions.

    Args:
        evaluations: List of evaluation dictionaries
        requester_id: The ID of the user requesting the data
        requester_role: The role of the user requesting the data

    Returns:
        List of evaluations with appropriate anonymization
    """
    return [
        anonymize_evaluator(evaluation, requester_id, requester_role)
        for evaluation in evaluations
    ]


def anonymize_report_data(report_data: Dict[str, Any], requester_role: Optional[str] = None) -> Dict[str, Any]:
    """
    Anonymize report data to hide evaluator identities in aggregated statistics.

    Reports should show aggregated scores and feedback without revealing who gave which score.

    Args:
        report_data: The report dictionary containing evaluations and statistics
        requester_role: The role of the user requesting the report

    Returns:
        Report data with anonymized evaluator information
    """
    result = report_data.copy()
    can_view_evaluator = _can_view_evaluator_identity(requester_role)

    # Recursively anonymize nested evaluation data
    if "evaluations" in result:
        result["evaluations"] = anonymize_evaluation_list(
            result["evaluations"],
            requester_role=requester_role
        )

    if "detailed_evaluations" in result:
        result["detailed_evaluations"] = anonymize_evaluation_list(
            result["detailed_evaluations"],
            requester_role=requester_role
        )

    # Anonymize team member evaluations in team reports
    if "members" in result:
        for member_data in result["members"]:
            if "evaluations" in member_data:
                member_data["evaluations"] = anonymize_evaluation_list(
                    member_data["evaluations"],
                    requester_role=requester_role
                )

    # Anonymize team evaluations in project reports
    if "teams" in result:
        for team_data in result["teams"]:
            if "members" in team_data:
                for member_data in team_data["members"]:
                    if "evaluations" in member_data:
                        member_data["evaluations"] = anonymize_evaluation_list(
                            member_data["evaluations"],
                            requester_role=requester_role
                        )

    return result


def _can_view_evaluator_identity(requester_role: Optional[str]) -> bool:
    """
    Determine if a user role has permission to view evaluator identities.

    Args:
        requester_role: The role of the requesting user

    Returns:
        True if the role can view evaluator identities, False otherwise
    """
    # Only instructors and admins can see who evaluated whom
    privileged_roles = ["instructor", "admin"]
    return requester_role and requester_role.lower() in privileged_roles


def should_anonymize_for_user(requester_role: Optional[str]) -> bool:
    """
    Quick check if anonymization should be applied for a given user role.

    Args:
        requester_role: The role of the requesting user

    Returns:
        True if data should be anonymized for this role
    """
    return not _can_view_evaluator_identity(requester_role)
