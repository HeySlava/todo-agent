import datetime as dt
import logging
import uuid
from pathlib import Path

from langchain_core.tools import tool

from agent import todo
from agent import utils


HERE = Path.cwd() / 'files'
INPUT_AUDIO_FOLDER = HERE / 'input_voice'
INPUT_AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
CONVERTED_AUDIO_FOLDER = HERE / 'converted_voice'
CONVERTED_AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__file__)
storage = todo.Todo(HERE)


@tool
def do_it(summary: str, date: str, details: list[str]) -> str:
    '''
    Эта функция используется для планирования задач, создания TODO, напоминаний и так далее.

    summary: коротко обозначенная суть задачи
    details: list[str]. массив строк, с перечислением задач или последовательностей действий которые надо выполнить.
        Если подробностей нет, необходимо передать пустой список.
    date: строка, отформатированная как %d.%m.%Y %H:%M. Время наступления задачи.
        Определите дату и время выполнения на основе текущей даты и любых указанных интервалов (например, "через 3 дня").
        Если сказана что надо напомнить через 2 дня, значит к текущий дате необходимо прибавить 2 дня, это и будет значением
        Если указана конкретная дата, значит его и нужно использовать
    return: статус выполнения задачи
    '''  # noqa: #501
    task = todo.Task(
            id_=str(uuid.uuid4()),
            summary=summary,
            date=date,
            details=details,
        )
    storage.add(task)
    return f'Задача для "{summary}" создана'


@tool
def remember(summary: str, details: list[str]) -> str:
    '''
    Эта функция используется когда необходимо что-то запомнить

    summary: одним предложением сформированная суть того, что требуется запомнить
    details: list[str]. массив строк, ключевые моменты, которые нужно запомнить. Если их нет, необходимо передать пустой список

    return: статус операции
    '''  # noqa: #501
    now = utils.now_moscow()
    intervals = [
            dt.timedelta(minutes=15),
            dt.timedelta(days=1),
            dt.timedelta(days=3),
            dt.timedelta(days=7),
            dt.timedelta(days=14),
            dt.timedelta(days=30),
        ]
    for interval in intervals:
        date_ = (now + interval).strftime(utils.TIME_FORMAT)
        task = todo.Task(
                summary=summary,
                id_=str(uuid.uuid4()),
                date=date_,
                details=details,
            )
        storage.add(task)
        logger.info(f'Запланировал задачу {summary} на {date_}')
    return f'Задача {summary} создана для дальнейшего запоминания'
