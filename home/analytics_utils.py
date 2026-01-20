import csv
import io
from typing import Dict, Any, Optional
from django.db.models import Avg, Count, Q
from .models import AnalyticsEvent, BotResponse, Feedback
from django.utils import timezone
from datetime import timedelta, date


def aggregate_project(project) -> Dict[str, Any]:
    events = AnalyticsEvent.objects.filter(project=project).values('event_type').annotate(count=Count('id'))
    event_counts = {e['event_type']: e['count'] for e in events}

    resp_qs = BotResponse.objects.filter(project=project)
    avg_conf = resp_qs.aggregate(avg=Avg('confidence'))['avg']

    fb_qs = Feedback.objects.filter(project=project)
    fb_count = fb_qs.count()
    avg_rating = fb_qs.aggregate(avg=Avg('rating'))['avg'] if fb_count else None

    return {
        'event_counts': event_counts,
        'responses_count': resp_qs.count(),
        'avg_confidence': float(avg_conf) if avg_conf is not None else None,
        'feedback_count': fb_count,
        'avg_rating': float(avg_rating) if avg_rating is not None else None,
    }


def export_project_csv(project) -> str:
    """Return CSV bytes as string for analytics export."""
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(['metric', 'value'])
    agg = aggregate_project(project)
    for k, v in agg.items():
        writer.writerow([k, v])

    # Add top events lines
    writer.writerow([])
    writer.writerow(['event_type', 'count'])
    for et, cnt in agg['event_counts'].items():
        writer.writerow([et, cnt])

    return buf.getvalue()


def time_series_events(project, days: int = 30, start_date: Optional[date] = None, end_date: Optional[date] = None, intent: Optional[str] = None):
    """Return list of {'date': iso, 'count': n} between start_date and end_date.

    If start_date/end_date not provided, use last `days` days ending today.
    Optional `intent` filters AnalyticsEvent.metadata__intent.
    """
    today = timezone.now().date()
    if end_date is None:
        end_date = today
    if start_date is None:
        start_date = end_date - timedelta(days=days - 1)

    qs = AnalyticsEvent.objects.filter(project=project, timestamp__date__gte=start_date, timestamp__date__lte=end_date)
    if intent:
        qs = qs.filter(metadata__intent=intent)

    # Group by date
    rows = qs.extra({'day': "date(timestamp)"}).values('day').annotate(count=Count('id')).order_by('day')
    date_map = {r['day']: r['count'] for r in rows}

    # normalize full range
    delta = (end_date - start_date).days + 1
    out = []
    for i in range(delta):
        d = start_date + timedelta(days=i)
        out.append({'date': d.isoformat(), 'count': date_map.get(d, 0)})
    return out


def top_questions(project, limit=10, start_date: Optional[date] = None, end_date: Optional[date] = None, intent: Optional[str] = None):
    """Return most frequent questions from BotResponse optionally filtered by date range.
    Note: BotResponse currently stores created_at; intent filtering is best-effort via AnalyticsEvent linkage.
    """
    qs = BotResponse.objects.filter(project=project)
    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)
    qs = qs.values('question').annotate(count=Count('id')).order_by('-count')[:limit]
    return [{'question': r['question'] or '(empty)', 'count': r['count']} for r in qs]


def intent_breakdown(project, start_date: Optional[date] = None, end_date: Optional[date] = None):
    """Return counts per detected intent using AnalyticsEvent metadata, optionally within date range."""
    qs = AnalyticsEvent.objects.filter(project=project, event_type='intent_detected')
    if start_date:
        qs = qs.filter(timestamp__date__gte=start_date)
    if end_date:
        qs = qs.filter(timestamp__date__lte=end_date)
    rows = qs.values('metadata__intent').annotate(count=Count('id')).order_by('-count')
    out = []
    for r in rows:
        intent = r.get('metadata__intent')
        out.append({'intent': intent or 'unknown', 'count': r['count']})
    return out


def recent_events(project, limit: int = 50, start_date: Optional[date] = None, end_date: Optional[date] = None, intent: Optional[str] = None):
    """Return recent AnalyticsEvent rows for display in the dashboard.

    Returns list of dicts with keys: timestamp (datetime), event_type, metadata
    """
    qs = AnalyticsEvent.objects.filter(project=project)
    if start_date:
        qs = qs.filter(timestamp__date__gte=start_date)
    if end_date:
        qs = qs.filter(timestamp__date__lte=end_date)
    if intent:
        qs = qs.filter(metadata__intent=intent)
    qs = qs.order_by('-timestamp')[:limit]

    out = []
    for e in qs:
        out.append({
            'timestamp': e.timestamp,
            'event_type': e.event_type,
            'metadata': e.metadata or {},
        })
    return out
