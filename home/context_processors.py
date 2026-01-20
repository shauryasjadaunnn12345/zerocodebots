from typing import Dict


def user_first_project(request) -> Dict:
    """Provide the first `Project` for the logged-in user (or None).

    Returns {'user_project': Project instance or None} so templates can
    link to project-specific pages when available.
    """
    try:
        if request.user.is_authenticated:
            from .models import Project
            proj = Project.objects.filter(user=request.user).first()
            return {'user_project': proj}
    except Exception:
        pass
    return {'user_project': None}
