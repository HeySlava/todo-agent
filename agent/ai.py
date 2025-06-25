import datetime as dt
import importlib.resources
import json
import os
from typing import Any
from zoneinfo import ZoneInfo

from openai import OpenAI


MOSCOW_TZ = ZoneInfo('Europe/Moscow')
TIME_FORMAT = '%d.%m.%Y %H:%M'


def now_moscow() -> dt.datetime:
    now_utc = dt.datetime.now(dt.timezone.utc)
    return now_utc.astimezone(MOSCOW_TZ)


api_key = os.environ['OPENAI_TOKEN']

client = OpenAI(api_key=api_key)


file_manager = importlib.resources.files('agent')
prompt_path = file_manager / 'prompt.txt'
with prompt_path.open('r') as f:
    prompt = f.read()


def convert_audio_to_text(audio_path: str) -> str:
    audio_file = open(audio_path, 'rb')

    transcription = client.audio.transcriptions.create(
        model='gpt-4o-mini-transcribe',
        file=audio_file
    )

    return transcription.text


def categorize(input_: str) -> dict[str, Any]:
    instructions = prompt.format(
            datetime=now_moscow().strftime(TIME_FORMAT),
        )
    response = client.responses.create(
        model='gpt-4o-mini',
        temperature=0,
        instructions=instructions,
        input=input_,
    )
    try:
        res = json.loads(response.output_text)
    except json.JSONDecodeError:
        res = {
                'task': 'unknown',
                'payload': {
                    'summary': (
                        f'I have got json.JSONDecodeError '
                        f'for {response.output_text}'
                    )
                }
            }
    return res
