# 🍅 Django Mozza Timer

This is a simple Pomodoro application using Django, sqlite, Tailwind and vanilla JS.

_(I'm basically learning to start and improve a modern Django project from scratch)_

```mermaid
flowchart LR
  S([sqlite]) <--> D([Django])
  D <--> T([Tailwind])
```

## Getting started

The project uses [uv](https://docs.astral.sh/uv) for dependencies.

```sh
uv sync
cd timers
uv run manage.py migrate
uv run manage.py runserver # server available at localhost:8000
```

Additionally, we depend on [tailwind 4](https://tailwindcss.com/), and therefore a node dependency tool.
We use [PNPM](https://pnpm.io/) and [node 22 LTS](https://nodejs.org/en/blog/release/v22.18.0).

[Tailwind standalone](https://github.com/tailwindlabs/tailwindcss/releases/tag/v4.1.11) might become an option in the future.

```sh
pnpm install
pnpm run css # for building
pnpm run css:watch # for development
```

In development, [Ruff](https://docs.astral.sh/ruff/) is also the primary formatter.

```sh
uv run ruff format
```

## Data modelling

Modelling a timer is fun, because we need to design it in a stateless way.

```mermaid
erDiagram

  TimerSequence ||--o{ TimerSequenceDuration: has
  TimerSequence ||--o{ TimerSequenceRun: has
  TimerSequenceRun ||--o{ TimerSequencePause: has

  TimerSequence {
    INT id
    TEXT name
    TEXT created_by
    DATETIME created_at
    DATETIME updated_at
  }

  TimerSequenceDuration {
    INT id PK
    BIGINT duration
    SMALLINT index
    INT timer_sequence_id FK
  }

  TimerSequenceRun {
    INT id
    TEXT timer_sequence_name
    DATETIME started_at
    INT timer_sequence_id FK
  }

  TimerSequencePause {
    INT id
    DATETIME started_at
    DATETIME ended_at
    INT timer_sequence_run_id FK
  }
```

## Testing

Testing, relies on [pytest](https://docs.pytest.org/en/stable/)
and [pytest-django](https://pytest-django.readthedocs.io/en/latest/).

```sh
uv run pytest
```

## :sparkles: Django template components

To stay DRY, while keeping a good readability, some components' classes are stored in
utilities ([timers/lib/classes](./timers/timers/lib/classes.py)).

Those classes are available inside a template tag: `cx` in reference to [clsx](https://www.npmjs.com/package/clsx).

```html
{% load components %}

<button class="{% cx 'button' variant='secondary' %}">Hello</button>
<input class="{% cx 'input' %}" />
```

Currently there are 2 components:

- Button (`'button'`)
- Input (`'input'`)
