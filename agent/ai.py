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

Возможные варианты ответов для task: "remember", "todo", "unknown". Ты не должен придумываться другие варианты.  # noqa: E501

Если в запросе я говорю, что выучил что-то новое, то для такого запроса ты должен вернуть "remember" для ключа "task", а в качестве "payload" — словарь с ключом "summary" и значением, полученным из моего запроса.  # noqa: E501

Если в запросе я прошу напомнить или выполнить что-то, значение для "task" должно быть "todo", а для "payload" должен быть словарь, где "summary" — это задача, которую я прошу выполнить, а "date" — значение в формате день:месяц.год часы:минуты. Например, "07.12.2025 16:30" соответствует 7 декабря 2025 года в 16:30.  # noqa: E501

Сегодня {datetime}. Если я не указываю конкретную дату, а прошу тебя напомнить о чем-то через определенный промежуток времени, ты должен самостоятельно это вычислить и ответить в формате, который я тебе описал.  # noqa: E501


Если задача не подходит для "remember". Верни JSON со значением для task = unkown, и пустым payload  # noqa: E501

Если задача не подходит для "todo". Верни JSON со значением для task = unkown, и пустым payload  # noqa: E501

Если задача подходит под "todo", но я не указал конкретную дату или период времени, верни JSON со значением для task = unkown, и пустым payload  # noqa: E501


Перед тем как ты ответишь, ты должен проанализировать, насколько ты уверен в своем ответе по шкале от 1 до 10, где 10 — это полная уверенность. В каждом ответе возвращай свою уверенность для ключа "confidence".'''  # noqa: E501


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
        instructions=instructions,
        input=input_,
    )
    return json.loads(response.output_text)
