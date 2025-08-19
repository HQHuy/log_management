import re


def clean_log_message(msg):
    if not isinstance(msg, str) or None:
        return ''

    msg = msg.replace('\r', ' ').replace('\n', ' ').replace('\\r', '').replace('\\n', '').strip()
    msg = re.sub(r'\s+', ' ', msg)
    msg = re.sub(r'"{2,}', '"', msg)
    msg = re.sub(r'"(https?)"://"([^"\s]+)"*', r'\1://\2', msg)
    msg = re.sub(r'https?://([^"\s]+)"{2,}', lambda m: f'https://{m.group(1).rstrip("\"")}', msg)

    return msg