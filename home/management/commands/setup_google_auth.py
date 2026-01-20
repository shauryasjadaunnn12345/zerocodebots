from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os

class Command(BaseCommand):
    help = "Configure Site + Google OAuth automatically"

    def handle(self, *args, **options):
        DOMAIN = "zerocodebots.onrender.com"
        SITE_NAME = "ZeroCodeBots"

        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        GOOGLE_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

        if not GOOGLE_CLIENT_ID or not GOOGLE_SECRET:
            self.stdout.write(self.style.ERROR(
                "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set"
            ))
            return

        # 1️⃣ Create / Update Site ID = 1
        site, created = Site.objects.update_or_create(
            id=1,
            defaults={
                "domain": DOMAIN,
                "name": SITE_NAME,
            }
        )

        self.stdout.write(self.style.SUCCESS(
            f"Site configured: {site.domain}"
        ))

        # 2️⃣ Create or update Google SocialApp
        app, created = SocialApp.objects.update_or_create(
            provider="google",
            defaults={
                "name": "Google Login",
                "client_id": GOOGLE_CLIENT_ID,
                "secret": GOOGLE_SECRET,
            }
        )

        # 3️⃣ Attach Site to SocialApp
        app.sites.set([site])
        app.save()

        self.stdout.write(self.style.SUCCESS(
            "Google OAuth configured successfully"
        ))
