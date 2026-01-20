def get_breadcrumbs(request, **kwargs):
    path = request.path.rstrip('/')

    crumbs = [
        {"name": "Home", "url": "/"}
    ]

    # Static pages
    static_map = {
        "/services": [("Services", None)],
        "/features": [("Features", None)],
        "/signup": [("Signup", None)],
        "/login": [("Login", None)],
        "/forgot": [("Forgot Password", None)],
        "/my-projects": [("My Projects", None)],
        "/dashboard": [("Dashboard", None)],
    }

    if path in static_map:
        for name, url in static_map[path]:
            crumbs.append({"name": name, "url": url})
        return crumbs

    # Project-based routes
    if path.startswith("/project/"):
        crumbs.append({"name": "My Projects", "url": "/my-projects/"})

        if "analytics" in path:
            crumbs.append({"name": "Analytics", "url": None})
        elif "summary" in path:
            crumbs.append({"name": "Summary", "url": None})
        elif "edit" in path:
            crumbs.append({"name": "Edit Project", "url": None})
        elif "import-website" in path:
            crumbs.append({"name": "Import Website", "url": None})

        return crumbs

    # Chatbot routes
    if path.startswith("/chatbot/"):
        crumbs.append({"name": "My Projects", "url": "/my-projects/"})
        crumbs.append({"name": "Chatbot", "url": None})
        return crumbs

    return crumbs
