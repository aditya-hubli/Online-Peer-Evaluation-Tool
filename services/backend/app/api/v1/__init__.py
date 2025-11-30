"""API v1 router - aggregates all v1 endpoints."""
from fastapi import APIRouter
from app.api.v1 import auth, forms, users, evaluations, audit_logs, reminders, reports, chats, projects, teams

# OPETSE-4: Authentication feature
# OPETSE-5: Role-Based Access Control (RBAC) feature
# OPETSE-6: Forms/evaluation criteria feature
# OPETSE-11: Automated deadline reminders feature
# OPETSE-15: Audit logging feature
# OPETSE-32: Export reports feature
# OPETSE-12: Submission analytics & instructor dashboard feature
# OPETSE-18: Team chat feature
# Projects and Teams management

api_router = APIRouter(prefix="/v1")

# Include authentication routes (OPETSE-4)
api_router.include_router(auth.router)

# Include users routes with RBAC (OPETSE-5)
api_router.include_router(users.router)

# Include forms routes (OPETSE-6)
api_router.include_router(forms.router)

# Include evaluations routes (OPETSE-7)
api_router.include_router(evaluations.router)

# Include reports and analytics routes (OPETSE-32, OPETSE-12)
api_router.include_router(reports.router)

# Include reminders routes (OPETSE-11)
api_router.include_router(reminders.router)

# Include audit logs routes (OPETSE-15)
api_router.include_router(audit_logs.router)

# Include team chat routes (OPETSE-18)
api_router.include_router(chats.router)

# Include projects routes
api_router.include_router(projects.router)

# Include teams routes
api_router.include_router(teams.router)
