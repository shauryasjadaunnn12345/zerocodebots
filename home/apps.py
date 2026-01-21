from django.apps import AppConfig
import os

class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp
        except Exception:
            # Tables not ready yet (first migrate) – silently skip
            return

        DOMAIN = "zerocodebots.onrender.com"
        SITE_NAME = "ZeroCodeBots"

        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

        # Do NOT crash app if env vars missing
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            return

        # 1️⃣ Ensure Site ID = 1
        site, _ = Site.objects.update_or_create(
            id=1,
            defaults={
                "domain": DOMAIN,
                "name": SITE_NAME,
            },
        )

        # 2️⃣ Ensure Google SocialApp
        app, _ = SocialApp.objects.update_or_create(
            provider="google",
            defaults={
                "name": "Google Login",
                "client_id": GOOGLE_CLIENT_ID,
                "secret": GOOGLE_CLIENT_SECRET,
            },
        )

        # 3️⃣ Bind Site → SocialApp
        app.sites.set([site])
        app.save()
