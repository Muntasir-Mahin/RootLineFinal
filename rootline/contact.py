"""Presentation-only contact configuration. Never sends messages or stores data."""
import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode, urlsplit
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email
from django.utils import timezone

DHAKA = ZoneInfo('Asia/Dhaka')
DAYS = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}


def phone_number(raw):
    """Return a display value and canonical E.164 value, or empty for invalid input."""
    value = re.sub(r'[\s().-]', '', raw.strip())
    if value.startswith('00'):
        value = '+' + value[2:]
    if re.fullmatch(r'01[0-9]{9}', value):
        value = '+88' + value
    elif re.fullmatch(r'8801[0-9]{9}', value):
        value = '+' + value
    if not re.fullmatch(r'\+[1-9][0-9]{7,14}', value):
        return '', ''
    if re.fullmatch(r'\+8801[0-9]{9}', value):
        return f'+880 {value[4:8]}-{value[8:]}', value
    return value, value


def public_url(raw):
    value = raw.strip()
    try:
        URLValidator(schemes=['https'])(value)
        parts = urlsplit(value)
        # Accessing port also rejects malformed/out-of-range URI ports.
        _ = parts.port
        if parts.username or parts.password:
            return ''
    except (ValidationError, ValueError):
        return ''
    return value


def support_schedule(hours):
    """Parse explicit daily/day-range schedules; unsupported text is display-only."""
    text = re.sub(r'\s*\(Bangladesh time\)\s*$', '', hours.strip(), flags=re.I)
    text = text.replace('–', '-').replace('—', '-')
    schedule = []
    for period in text.split(';'):
        match = re.fullmatch(
            r'\s*(Daily|Every day|[A-Za-z]{3}(?:\s*-\s*[A-Za-z]{3})?)\s*,\s*'
            r'([0-9]{1,2}:[0-9]{2}\s*[AP]M)\s*-\s*([0-9]{1,2}:[0-9]{2}\s*[AP]M)\s*',
            period, flags=re.I,
        )
        if not match:
            return []
        day_range, opening, closing = match.groups()
        if day_range.lower() in ('daily', 'every day'):
            days = set(range(7))
        else:
            endpoints = [day.strip().lower() for day in day_range.split('-')]
            if any(day not in DAYS for day in endpoints):
                return []
            start, end = DAYS[endpoints[0]], DAYS[endpoints[-1]]
            days = {(start + offset) % 7 for offset in range((end - start) % 7 + 1)}
        try:
            opening = datetime.strptime(re.sub(r'\s*([AP]M)$', r' \1', opening.upper()), '%I:%M %p').time()
            closing = datetime.strptime(re.sub(r'\s*([AP]M)$', r' \1', closing.upper()), '%I:%M %p').time()
        except ValueError:
            return []
        if opening == closing:
            return []
        schedule.append((days, opening, closing))
    return schedule


def availability(hours, now=None):
    schedule = support_schedule(hours)
    if not schedule:
        return None
    now = (now or timezone.now()).astimezone(DHAKA)
    upcoming = []
    for offset in range(-1, 8):
        day = now.date() + timedelta(days=offset)
        for days, opening, closing in schedule:
            if day.weekday() not in days:
                continue
            start = datetime.combine(day, opening, tzinfo=DHAKA)
            end = datetime.combine(day + timedelta(days=closing < opening), closing, tzinfo=DHAKA)
            if start <= now < end:
                return {'is_open': True, 'label': 'Available now', 'next_open': None}
            if start > now:
                upcoming.append(start)
    if not upcoming:
        return None
    next_open = min(upcoming)
    clock = next_open.strftime('%I:%M %p').lstrip('0')
    difference = (next_open.date() - now.date()).days
    day_label = '' if difference == 0 else 'tomorrow ' if difference == 1 else next_open.strftime('%a ')
    return {'is_open': False, 'label': f'Back {day_label}at {clock}', 'next_open': next_open.isoformat()}


def contact_details():
    name = settings.ROOTLINE_CONTACT_BUSINESS_NAME.strip() or 'RootLine'
    phone, phone_clean = phone_number(settings.ROOTLINE_CONTACT_PHONE)
    whatsapp, whatsapp_clean = phone_number(settings.ROOTLINE_CONTACT_WHATSAPP)
    email = settings.ROOTLINE_CONTACT_EMAIL.strip()
    try:
        validate_email(email)
    except ValidationError:
        email = ''
    message = settings.ROOTLINE_CONTACT_WHATSAPP_MESSAGE.strip() or f'Hello {name}, I need help.'
    subject = settings.ROOTLINE_CONTACT_EMAIL_SUBJECT.strip() or f'{name} support'
    whatsapp_href = f'https://wa.me/{whatsapp_clean[1:]}?{urlencode({"text": message}, quote_via=quote)}' if whatsapp else ''
    email_href = f'mailto:{quote(email, safe="@+.")}?{urlencode({"subject": subject}, quote_via=quote)}' if email else ''
    channels = []

    def add(key, label, value, href, action, *, external=False, copy_value=''):
        if value and href:
            channels.append({'key': key, 'icon': key, 'label': label, 'value': value,
                             'href': href, 'action': action, 'external': external,
                             'copy_value': copy_value})

    add('whatsapp', 'WhatsApp', whatsapp, whatsapp_href, 'Chat on WhatsApp', external=True)
    add('phone', 'Phone', phone, 'tel:' + phone_clean if phone else '', 'Call us', copy_value=phone_clean)
    add('email', 'Email', email, email_href, 'Email us', copy_value=email)
    social_values = {}
    for key, label, action in [('facebook', 'Facebook', 'Visit Facebook'), ('messenger', 'Messenger', 'Open Messenger'),
                               ('instagram', 'Instagram', 'Visit Instagram'), ('youtube', 'YouTube', 'Visit YouTube')]:
        value = public_url(getattr(settings, 'ROOTLINE_CONTACT_' + key.upper()))
        social_values[key] = value
        add(key, label, value, value, action, external=True)
    try:
        extras = json.loads(settings.ROOTLINE_CONTACT_SOCIALS)
    except (ValueError, TypeError):
        extras = []
    if isinstance(extras, list):
        for item in extras[:10]:
            if not isinstance(item, dict):
                continue
            label = str(item.get('label', '')).strip()[:80]
            url = public_url(str(item.get('url', '')))
            if label and url:
                add('social', label, url, url, f'Visit {label}', external=True)
    hours = settings.ROOTLINE_CONTACT_HOURS.strip()
    return {
        'business_name': name, 'phone': phone, 'phone_href': 'tel:' + phone_clean if phone else '',
        'whatsapp': whatsapp, 'whatsapp_href': whatsapp_href, 'email': email, 'email_href': email_href,
        **social_values, 'socials': [c for c in channels if c['external'] and c['key'] != 'whatsapp'],
        'address': settings.ROOTLINE_CONTACT_ADDRESS.strip(), 'hours': hours,
        'languages': settings.ROOTLINE_CONTACT_LANGUAGES.strip(),
        'reply_time': settings.ROOTLINE_CONTACT_REPLY_TIME.strip(),
        'availability': availability(hours) if hours else None, 'channels': channels,
        'has_channels': bool(channels),
    }
