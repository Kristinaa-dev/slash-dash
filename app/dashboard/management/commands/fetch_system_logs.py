# logs/management/commands/fetch_system_logs.py
import subprocess
import datetime
import json

from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import LogEntry
    
class Command(BaseCommand):
    help = 'Fetches system logs and stores them in the database'

    def handle(self, *args, **options):
        # 1. Find the most recent log we have, not the first in the table
        last_log = LogEntry.objects.order_by('-timestamp').first()

        # 2. Prepare --since argument
        if last_log:
            # Use ISO format or at least a precise timestamp
            since_time = last_log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # If no logs in DB yet, fetch the last hour or whatever default you prefer
            since_time = '1 hour ago'
        
        # 3. Call journalctl with --since
        result = subprocess.run(
            ['journalctl', '--since', since_time, '--no-pager', '--output=json'],
            capture_output=True, 
            text=True
        )
        
        logs_raw = result.stdout.strip().split('\n')
        new_entries = []

        for log_json in logs_raw:
            if not log_json.strip():
                continue
            entry_data = parse_journalctl_json(log_json)
            if entry_data:
                new_entries.append(LogEntry(**entry_data))
        
        # 4. (Optional) Deduplicate in Python before bulk_create if necessary
        #    If there's a chance that sub-second duplicates or identical lines come back,
        #    you might filter out existing logs.  For example:
        #
        #    existing_signatures = set(
        #       LogEntry.objects.filter(
        #           timestamp__gte=some_threshold
        #       ).values_list('timestamp', 'message', 'service')
        #    )
        #
        #    unique_new_entries = []
        #    for entry in new_entries:
        #        signature = (entry.timestamp, entry.message, entry.service)
        #        if signature not in existing_signatures:
        #            unique_new_entries.append(entry)
        #            existing_signatures.add(signature)
        #
        #    new_entries = unique_new_entries

        # 5. Insert in bulk
        if new_entries:
            LogEntry.objects.bulk_create(new_entries)

        self.stdout.write(self.style.SUCCESS(f'Successfully fetched {len(new_entries)} new logs.'))


def parse_journalctl_json(log_json):
    """Parses a single line of journalctl JSON output into a Python dict
    suitable for creating a LogEntry.
    """
    try:
        log = json.loads(log_json)
        # The __REALTIME_TIMESTAMP is in microseconds, so convert to seconds
        timestamp = datetime.datetime.fromtimestamp(int(log['__REALTIME_TIMESTAMP']) / 1_000_000)
        timestamp = timezone.make_aware(timestamp)

        return {
            'timestamp': timestamp,
            'service': log.get('_SYSTEMD_UNIT', 'Unknown'),
            'priority': log.get('PRIORITY', 6),
            'message': log.get('MESSAGE', ''),
        }
    except (KeyError, ValueError, json.JSONDecodeError):
        return None
