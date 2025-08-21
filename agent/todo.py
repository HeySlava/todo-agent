import datetime as dt
import json
import logging
from pathlib import Path
from typing import Any

from agent import utils


HERE = Path.cwd() / 'files'
logger = logging.getLogger(__file__)


class Task:
    def __init__(
            self,
            id_: str,
            date: str,
            summary: str,
            details: list[str],
    ) -> None:
        self.id_ = id_
        try:
            dt.datetime.strptime(date, utils.TIME_FORMAT)
        except ValueError:
            raise ValueError(
                    f'Invalid date format: {date}. '
                    f'Expected format: {utils.TIME_FORMAT}'
                )
        self.date = date
        self.summary = summary
        self.details = details

    def as_dict(self) -> dict[str, Any]:
        return {
                'date': self.date,
                'summary': self.summary,
                'details': self.details,
            }


class Todo:
    def __init__(self, init_dir: Path) -> None:
        self.init_dir = init_dir
        self.pending_directory = init_dir / 'pending'
        self.archive_directory = init_dir / 'archive'
        self.pending_directory.mkdir(parents=True, exist_ok=True)
        self.archive_directory.mkdir(parents=True, exist_ok=True)

    def add(self, task: Task) -> None:
        filename = self.pending_directory / f'{task.id_}.json'
        with open(filename, 'w') as f:
            json.dump(task.as_dict(), f, indent=4, ensure_ascii=False)

    def archive(self, task: Task) -> None:
        task_name = self.pending_directory / f'{task.id_}.json'
        task_name.rename(self.archive_directory / f'{task.id_}.json')

    def all(self) -> list[Task]:
        files = [f for f in self.pending_directory.glob('*.json')]
        tasks = []
        for f in files:
            with open(f) as fp:
                data = json.load(fp)
            tasks.append(
                    Task(
                        id_=f.stem,
                        date=data['date'],
                        summary=data['summary'],
                        details=data.get('details', [])
                    ),
                )
        return tasks


storage = Todo(HERE)
