import asyncio
import datetime as dt
import functools
import json
import logging
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from typing import Optional

import ffmpeg
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from agent import ai
from agent import todo

TOKEN = os.environ['TELEGRAM_TOKEN']
user_id = int(os.environ['ADMIN_ID'])

dp = Dispatcher()

HERE = Path.cwd() / 'files'
INPUT_AUDIO_FOLDER = HERE / 'input_voice'
INPUT_AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
CONVERTED_AUDIO_FOLDER = HERE / 'converted_voice'
CONVERTED_AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__file__)
storage = todo.Todo(HERE)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
            'Это бот Славы, который планирует за него задачи',
        )


def do_it(payload: dict[str, Any]) -> None:
    task = todo.Task(
            name=str(uuid.uuid4()),
            summary=payload['payload']['summary'],
            date=payload['payload']['date'],
        )
    storage.add(task)


def remember(payload: dict[str, Any]) -> None:
    summary = payload['payload']
    now = ai.now_moscow()
    intervals = [
            dt.timedelta(minutes=15),
            dt.timedelta(hours=10),
            dt.timedelta(hours=27),
            dt.timedelta(days=4),
            dt.timedelta(days=15),
            dt.timedelta(days=30),
        ]
    for interval in intervals:
        date_ = (now + interval).strftime(ai.TIME_FORMAT)
        task = todo.Task(
                summary=summary,
                name=str(uuid.uuid4()),
                date=date_,
            )
        storage.add(task)
        logger.info(f'Запланировал задачу на {date_}')


mapping = {
        'todo': do_it,
        'remember': remember,
    }


async def send_and_delete(
        bot: Bot,
        chat_id: int,
        text: str,
        parse_mode: Optional[ParseMode] = None,
        sleep: int = 1,
) -> None:
    response = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
        )
    await asyncio.sleep(sleep)
    await bot.delete_message(
            chat_id=user_id,
            message_id=response.message_id,
        )


@dp.message(F.voice)
async def voice_command_handler(message: Message) -> None:
    assert message.voice
    assert message.bot
    responses = []
    _msg = functools.partial(
            message.bot.send_message,
            chat_id=user_id,
        )
    dest_file = INPUT_AUDIO_FOLDER / f'{message.message_id}.ogg'
    output_file = CONVERTED_AUDIO_FOLDER / f'{message.message_id}.mp3'

    responses.append(await _msg(text='Качаю файл для дальнейшей конвертации'))
    await message.bot.download(message.voice.file_id, destination=dest_file)
    responses.append(await _msg(text='Запускаю ffmpeg'))
    ffmpeg.input(dest_file.as_posix()).output(output_file.as_posix()).run()
    responses.append(await _msg(text='Отправляю файл на транскрибацию'))
    transcription = ai.convert_audio_to_text(output_file.as_posix())
    responses.append(
            await _msg(
                text=(
                    'Текст который я получил от транскрибатора:\n\n'
                    f'{transcription!r}'
                )
            )
        )

    responses.append(await _msg(text='Отправляю файл на категоризацию'))
    json_ = ai.categorize(transcription)
    json_str = json.dumps(json_, indent=2, ensure_ascii=False)
    text = f'```json\n{json_str}```'

    responses.append(
            await _msg(text=text, parse_mode=ParseMode.MARKDOWN_V2)
        )
    if json_['task'] in mapping:
        mapping[json_['task']](json_)
    else:
        await message.answer(f'Ничего не создал: {json_}')
    responses.append(message)

    await asyncio.sleep(30)

    for res in responses:
        await message.bot.delete_message(
                chat_id=user_id,
                message_id=res.message_id,
            )


async def run_pending_tasks(bot: Bot) -> None:
    while True:
        tasks = storage.all()
        logger.debug(f'Всего запланировано задач {len(tasks)}')
        now = ai.now_moscow()
        for task in tasks:
            execution_datetime = dt.datetime.strptime(
                    task.date,
                    ai.TIME_FORMAT,
                )
            execution_datetime = execution_datetime.replace(
                    tzinfo=ai.MOSCOW_TZ,
                )
            if now > execution_datetime:
                kb = InlineKeyboardBuilder()
                kb.button(
                        text='Done!',
                        callback_data='1',
                    )
                markup = kb.as_markup()
                await bot.send_message(
                        chat_id=user_id,
                        text=task.summary,
                        reply_markup=markup,
                        disable_notification=False,
                    )
                storage.archive(task)
        await asyncio.sleep(10)


@dp.callback_query()
async def handle_template_manager_cb(
        cb: CallbackQuery,
) -> None:
    await cb.answer()
    await cb.message.delete()


async def _main() -> None:
    bot = Bot(
            token=TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    schedule_job = asyncio.create_task(run_pending_tasks(bot))

    try:
        await dp.start_polling(bot)
    finally:
        logging.info('Telegram bot polling stopped.')
        schedule_job.cancel()
        try:
            await schedule_job
        except asyncio.CancelledError:
            logging.info('Scheduler job cancelled successfully.')


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(_main())


if __name__ == '__main__':
    main()
