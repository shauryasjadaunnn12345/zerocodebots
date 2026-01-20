from django.core.management.base import BaseCommand
from home.models import Project
from home.analytics_utils import export_project_csv


class Command(BaseCommand):
    help = 'Export analytics for a given project id as CSV to stdout or file'

    def add_arguments(self, parser):
        parser.add_argument('project_id', type=int)
        parser.add_argument('--output', '-o', help='Output file path (optional)')

    def handle(self, *args, **options):
        pid = options['project_id']
        out = options.get('output')
        try:
            project = Project.objects.get(pk=pid)
        except Project.DoesNotExist:
            self.stderr.write('Project not found: %s' % pid)
            return

        csv_text = export_project_csv(project)
        if out:
            with open(out, 'w', encoding='utf-8') as f:
                f.write(csv_text)
            self.stdout.write('Wrote analytics to %s' % out)
        else:
            self.stdout.write(csv_text)
