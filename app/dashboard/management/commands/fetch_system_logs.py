# logs/management/commands/fetch_system_logs.py
import subprocess
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import LogEntry

class Command(BaseCommand):
    help = 'Fetches system logs and stores them in the database'

    def handle(self, *args, **options):
        # Fetch the most recent logs since the last timestamp in the database
        last_log = LogEntry.objects.first()
        # since_time = last_log.timestamp.isoformat() if last_log else '1 hour ago'
        since_time = last_log.timestamp.strftime('%Y-%m-%d %H:%M:%S') if last_log else '1 hour ago'
        result = subprocess.run(
            ['journalctl', '--since', since_time, '--no-pager', '--output=json'],
            capture_output=True, text=True
        )

        logs = result.stdout.strip().split('\n')
        new_entries = []
        for log_json in logs:
            if not log_json:
                continue
            log_entry = parse_journalctl_json(log_json)
            if log_entry:
                new_entries.append(LogEntry(**log_entry))
        LogEntry.objects.bulk_create(new_entries)
        
        self.stdout.write(self.style.SUCCESS('Successfully fetched and stored logs.'))

def parse_journalctl_json(log_json):
    import json
    try:
        log = json.loads(log_json)
        timestamp = datetime.datetime.fromtimestamp(
            int(log['__REALTIME_TIMESTAMP']) / 1_000_000
        )
        timestamp = timezone.make_aware(timestamp)
        return {
            'timestamp': timestamp,
            'service': log.get('_SYSTEMD_UNIT', 'Unknown'),
            'priority': log.get('PRIORITY', 6),
            'message': log.get('MESSAGE', ''),
        }
    except (KeyError, ValueError, json.JSONDecodeError):
        return None
