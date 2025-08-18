import asyncio
import datetime as dt
import functools
import logging
import os
import sys
from typing import Optional

import ffmpeg
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import F
from aiogram import html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.filters import Filter
from aiogram.types import CallbackQuery
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from langchain_core.messages import HumanMessage
from langchain_core.messages import SystemMessage

from agent import ai
from agent import utils
from agent.todo import HERE
from agent.todo import storage
from agent.todo import Task

TOKEN = os.environ['TELEGRAM_TOKEN']
user_id = int(os.environ['ADMIN_ID'])

dp = Dispatcher()

INPUT_AUDIO_FOLDER = HERE / 'input_voice'
INPUT_AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
CONVERTED_AUDIO_FOLDER = HERE / 'converted_voice'
CONVERTED_AUDIO_FOLDER.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger(__file__)


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        if (
                message.from_user and
                message.from_user.id and
                message.from_user.id == user_id
        ):
            return True
        return False


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


def _make_text(task: Task) -> str:
    lst = '\n'.join([f'• {d}' for d in task.details])
    return f'{html.bold(task.summary)}\n\n{lst}'.strip()


async def run_pending_tasks(bot: Bot) -> None:
    while True:
        tasks = storage.all()
        logger.debug(f'Всего запланировано задач {len(tasks)}')
        now = utils.now_moscow()
        for task in tasks:
            execution_datetime = dt.datetime.strptime(
                    task.date,
                    utils.TIME_FORMAT,
                )
            execution_datetime = execution_datetime.replace(
                    tzinfo=utils.MOSCOW_TZ,
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
                        text=_make_text(task),
                        reply_markup=markup,
                        disable_notification=False,
                    )
                storage.archive(task)
        await asyncio.sleep(10)


@dp.message(CommandStart(), IsAdmin())
async def command_start_handler(message: Message) -> None:
    await message.answer('Это личный бот-ассистент')


@dp.message(F.voice, IsAdmin())
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
    responses.append(await _msg(text='Запускаю агента'))
    from agent.prompts import SYSTEM_PROMPT
    for s in ai.agent.stream(
            {
                'messages':
                [
                    SystemMessage(
                        SYSTEM_PROMPT.format(datetime=utils.now_moscow()),
                    ),
                    HumanMessage(transcription),
                ],
            },
            stream_mode='values'
    ):
        last_msg = s['messages'][-1]
        msg = last_msg.pretty_repr()
        responses.append(
                await _msg(text=html.pre_language(msg, 'JSON')),
        )

    await asyncio.sleep(30)
    await message.delete()
    for res in responses:
        await message.bot.delete_message(
                chat_id=user_id,
                message_id=res.message_id,
            )


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


@dp.callback_query()
@dp.message(IsAdmin())
async def handle_template_manager_cb(
        cb: CallbackQuery,
) -> None:
    await cb.answer()
    await cb.message.delete()


def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(_main())


if __name__ == '__main__':
    main()
