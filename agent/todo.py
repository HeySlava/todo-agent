import json
from pathlib import Path
from typing import Any
from typing import NamedTuple


class Task(NamedTuple):
    name: str
    date: str
    summary: str

    def as_dict(self) -> dict[str, Any]:
        return {
                'date': self.date,
                'summary': self.summary,
            }


class Todo:
    def __init__(self, init_dir: Path) -> None:
        self.init_dir = init_dir
        self.pending_directory = init_dir / 'pending'
        self.archive_directory = init_dir / 'archive'
        self.pending_directory.mkdir(parents=True, exist_ok=True)
        self.archive_directory.mkdir(parents=True, exist_ok=True)

    def add(self, task: Task) -> None:
        filename = self.pending_directory / f'{task.name}.json'
        with open(filename, 'w') as f:
            json.dump(task.as_dict(), f, indent=4, ensure_ascii=False)

    def archive(self, task: Task) -> None:
        task_name = self.pending_directory / f'{task.name}.json'
        task_name.rename(self.archive_directory / f'{task.name}.json')

    def all(self) -> list[Task]:
        files = [f for f in self.pending_directory.glob('*.json')]
        tasks = []
        for f in files:
            with open(f) as fp:
                data = json.load(fp)
            tasks.append(
                    Task(
                        name=f.stem,
                        date=data['date'],
                        summary=data['summary'],
                    ),
                )
        return tasks
