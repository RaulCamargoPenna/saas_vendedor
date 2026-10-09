"""Docker health probe: publish readiness only after HTTP and DB pass."""

import os
import http.client

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from core.structured_events import publish_event


class Command(BaseCommand):
    help = "Check local HTTP and database; optionally publish a closed readiness event"

    def handle(self, *args, **options):
        failed = False
        try:
            conn = http.client.HTTPConnection("127.0.0.1", 8000, timeout=3)
            try:
                conn.request("GET", "/saas/", headers={"Host": "saas.raulcamargo.com.br"})
                response = conn.getresponse()
                if response.status != 200:
                    failed = True
            finally:
                conn.close()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                if cursor.fetchone() != (1,):
                    failed = True
            if not failed and os.environ.get("SAAS_EVENT_SOURCE_DIR"):
                publish_event(os.environ["SAAS_EVENT_SOURCE_DIR"], "app.ready")
        except Exception:
            # The underlying exception may contain a URL, DB credentials, or path.
            failed = True
        if failed:
            raise CommandError("readiness unavailable")
