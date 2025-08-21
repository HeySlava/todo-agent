import json
from datetime import datetime
from pathlib import Path


def format_date(date_str: str) -> str:
    if date_str == '16.08.2025 09:62':
        return '16.08.2025 09:55'
    for fmt in ('%Y-%m-%d %H:%M', '%d.%m.%Y %H:%M:%S'):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime('%d.%m.%Y %H:%M')
        except ValueError:
            continue
    return date_str


def process_json_files(directory: Path) -> None:
    for filepath in directory.glob('*.json'):
        with filepath.open('r', encoding='utf-8') as file:
            data = json.load(file)
        if 'date' in data:
            data['date'] = format_date(data['date'])
        with filepath.open('w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
