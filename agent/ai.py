import datetime as dt
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

prompt = '''\
Ты мой ассистент-классификатор, который принимает запросы и возвращает JSON-ответ. Твоя задача — вернуть JSON с ключами "task", "payload" и "confidence".  # noqa: E501

Сегодня {datetime}.

Возможные варианты ответов для task: "remember", "todo", "unknown". Ты не должен придумываться другие варианты.  # noqa: E501

Если в запросе я говорю, что выучил что-то новое, то для такого запроса ты должен вернуть "remember" для ключа "task", а в качестве "payload" — словарь с ключом "summary". "summary" это коротко сформулировая исходная мысль без упущения деталей.  # noqa: E501

Для того, чтобы классифицировать задачу как "todo", а запросе обязательно должна быть указана задача и когда ее выполнить. Если даты нет, но указан интервал времени, тебе необходимо определить date самостоятельно путем сложения текущей даты и интервала. Если чего-то из этого не хватает, ты не можешь ответить полностью на поставленный вопрос. Для "payload" должен быть словарь, где "summary" — это задача, которую я прошу выполнить, а "date" — значение в формате день.месяц.год часы:минуты. Например: 08.06.2025 12:39 # noqa: E501


Если ты не можешь определить тип задачи, верни JSON с task = 'unknown', а в payload, для ключа summary напиши какой информации тебе не хватило для корректной классификации.  # noqa: E501

Строго следуй моим инструкциям

Перед тем как ты ответишь, ты должен проанализировать, насколько ты уверен в своем ответе по шкале от 1 до 100, где 100 — это полная уверенность. В каждом ответе возвращай свою уверенность для ключа "confidence".'''  # noqa: E501


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
