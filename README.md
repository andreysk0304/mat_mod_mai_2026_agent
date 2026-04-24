# Minimal Python AI Agent

Минимальный CLI-агент с in-memory историей диалога, OpenAI-compatible API и расширением через tools и skills.

## Запуск

```bash
cp .env.example .env
# затем заполнить .env
python3 main.py
```

Если `.env` не используется автоматически, проверь, что установлен `python-dotenv`.

## Команды CLI

- `/help`
- `/exit`
- `/reset`
- `/reload`
- `/log status`
- `/log on`
- `/log off`
- `/log enable STAGES`
- `/log disable STAGES`
- `/history`
- `/tools`
- `/skills`
- `/skill enable NAME`
- `/skill disable NAME`

## Архитектура

- `main.py` — entrypoint.
- `agent/cli.py` — CLI loop и runtime commands.
- `agent/agent.py` — orchestration: system prompt, tool loop, memory integration.
- `agent/client.py` — HTTP client для OpenAI-compatible `/chat/completions`.
- `agent/memory.py` — in-memory история текущей CLI-сессии.
- `agent/tools.py` — registry tools и загрузка Python tool modules из `tools/`.
- `agent/tool_api.py` — стабильный API для пользовательских tool-файлов.
- `agent/skills.py` — registry skills и загрузка markdown skills из `skills/`.
- `tools/*.py` — Python tools, которые подхватываются автоматически при старте.
- `skills/*.md` — prompt fragments, которые можно включать в рантайме.

По умолчанию в проекте уже есть tools для:

- арифметики (`calculate`)
- текущего времени (`get_current_time`)
- просмотра директорий проекта (`ls`)
- чтения текстовых файлов проекта (`read_project_file`)
- записи и дописывания текстовых файлов проекта (`write_project_file`)

## Как расширять

### Добавить новый tool

1. Создать `tools/<name>.py`.
2. Экспортировать tool одним из способов:
   `@tool(...) def handler(...): ...`
   или `TOOL = ToolDefinition(...)`
   или `def register(registry): registry.register(...)`
3. Выполнить `/reload` или перезапустить CLI.

Пример:

```python
from agent.tool_api import JsonDict, tool


@tool(
    name="echo",
    description="Return text as-is.",
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
        "additionalProperties": False,
    },
)
def echo(arguments: JsonDict) -> JsonDict:
    return {"text": arguments["text"]}
```

### Self-edit tools

- `read_project_file` читает UTF-8 текстовый файл внутри текущего проекта.
- `write_project_file` умеет полностью перезаписывать файл или дописывать текст в конец.
- Оба инструмента запрещают выход за пределы рабочей директории проекта.
- После добавления новых tool-файлов выполните `/reload`.

### Добавить новый skill

1. Создать `skills/<name>.md`.
2. Запустить CLI.
3. Включить skill командой `/skill enable <name>`.

## TLS/SSL

- По умолчанию клиент проверяет TLS-сертификаты.
- Если локальный Python не видит CA, можно указать `AI_AGENT_CA_BUNDLE=/path/to/ca.pem`.
- Для временной локальной отладки можно выставить `AI_AGENT_SSL_VERIFY=false`.
- `AI_AGENT_SSL_VERIFY=false` отключает проверку сертификатов и не подходит для production.

## Логирование

- `AI_AGENT_LOG_ENABLED=true` включает логирование.
- `AI_AGENT_LOG_STAGES=input,prompt,output,usage,tools,errors` задаёт стадии.
- `prompt` показывает полный payload, который уходит в модель.
- `AI_AGENT_LOG_FILE=./logs/agent.log` пишет логи в файл. Без этого логи идут в `stdout`.
- `usage` логирует токены на каждой upstream-итерации и суммарно на одну пользовательскую задачу.
