# Інструкція користувача програмної системи Research Opportunity Matcher

## 1. Компоненти програмного забезпечення

### 1.1. Загальний опис системи

Програмна система **Research Opportunity Matcher** призначена для пошуку, персоналізованого ранжування та супроводу подання заявок на академічні можливості: гранти, стипендії, програми академічної мобільності, дослідницькі позиції, стажування та навчальні програми.

Користувач створює або імпортує академічний профіль, після чого система порівнює його з можливостями з різних джерел, формує рекомендації, пояснює причини відповідності, дозволяє зберігати можливості, планувати подання заявки, відстежувати статуси на Kanban-дошці та отримувати нагадування про дедлайни. Для підготовки заявки передбачено модуль **Apply Assistant**, який формує список наступних дій, попередження щодо ризиків, пояснення readiness score та advisor memo.

### 1.2. Використані технології

Система є вебзастосунком і складається з клієнтської частини, серверної частини, бази даних, фонових процесів та інтеграцій із зовнішніми джерелами.

Основні технології:

| Компонент | Технології | Призначення |
|---|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Alembic, Pydantic | REST API, бізнес-логіка, робота з БД, рекомендації, імпорт можливостей |
| Frontend | React 19, TypeScript, Vite | Інтерфейс користувача, профіль, matches, Kanban-дошка, Apply Assistant, адмін-панель |
| База даних | SQLite для локального запуску; PostgreSQL + pgvector для повного режиму | Збереження користувачів, профілів, можливостей, статусів, нагадувань, embedding-векторів |
| Черги та фонові задачі | Redis, RQ, scheduler | Імпорт можливостей, reminders, digest/high-match notifications, фонові задачі |
| Пошук | Elasticsearch, fallback database search | Повнотекстовий пошук по можливостях |
| Семантичне порівняння | Hash embeddings або sentence-transformers | Semantic similarity між профілем і можливістю |
| AI / LLM | Deterministic provider, Groq, local OpenAI-compatible endpoint | Apply Assistant, metadata extraction, profile enrichment |
| Web research | DuckDuckGo Search | Додаткові web snippets для advisor memo |
| Email | Console SMTP або Mailtrap/SMTP | Email verification, notifications, reminders |
| Контейнеризація | Docker, Docker Compose | Запуск повного стеку з PostgreSQL, Redis, Elasticsearch, API, worker, scheduler, frontend |

### 1.3. Основні модулі системи

| Модуль | Призначення |
|---|---|
| Authentication | Реєстрація, вхід, JWT, refresh token, email verification, ORCID OAuth |
| Profile | Створення профілю дослідника, редагування академічних даних, ORCID/OpenAlex імпорт |
| Opportunities | Каталог академічних можливостей, деталі можливості, фільтрація, пошук |
| Matching | Персоналізовані рекомендації з match score, readiness score та поясненнями |
| Workflow / Kanban | Статуси `saved`, `planned`, `applied`, `accepted`, `rejected`, `ignored` |
| Reminders | Нагадування про дедлайни, manual reminders, completed reminders |
| Notifications | Email/системні сповіщення, preferences, history |
| Admin | Імпорт джерел, batch history, analytics, duplicate merge, manual edit |
| Apply Assistant | Checklist, readiness explanation, advisor memo, warnings/gaps |
| Integrations | Grants.gov, EU Funding, Erasmus, NAWA, ORCID, OpenAlex, українські та європейські джерела |

### 1.4. Набір основних файлів проєкту

| № | Файл або директорія | Призначення | Належить проєкту |
|---:|---|---|---|
| 1 | `app/main.py` | Точка входу FastAPI-застосунку | Так |
| 2 | `app/api/` | API routes: auth, profiles, opportunities, recommendations, assistant, admin | Так |
| 3 | `app/services/` | Сервісний шар: рекомендації, імпорт, embeddings, assistant, notifications | Так |
| 4 | `app/modules/` | SQLAlchemy ORM-моделі за функціональними модулями | Так |
| 5 | `app/domain/` | Domain enums/entities, незалежні від FastAPI | Так |
| 6 | `app/integrations/` | Клієнти й адаптери зовнішніх джерел | Так |
| 7 | `app/workers/` | Worker і scheduler для фонових задач | Так |
| 8 | `migrations/` | Alembic migrations для схеми БД | Так |
| 9 | `frontend/src/` | React/TypeScript frontend-код | Так |
| 10 | `frontend/package.json` | Скрипти й залежності frontend | Так |
| 11 | `pyproject.toml` | Python-залежності backend | Так |
| 12 | `docker-compose.yml` | Повний Docker Compose стек | Так |
| 13 | `Makefile` | Команди швидкого запуску | Так |
| 14 | `.env.example`, `.env.full.example`, `.env.full.local.example` | Приклади конфігурації середовища | Так |
| 15 | `scripts/run-full-app.ps1` | Windows PowerShell запуск backend + frontend + worker + scheduler | Так |
| 16 | `tests/` | Backend тести | Так |
| 17 | `frontend/src/**/*.test.tsx` | Frontend unit/UI тести | Так |

### 1.5. Сторонні компоненти та бібліотеки

Система використовує такі основні сторонні компоненти:

| Компонент | Призначення |
|---|---|
| FastAPI | Побудова REST API |
| SQLAlchemy | ORM і робота з базою даних |
| Alembic | Міграції БД |
| Pydantic / pydantic-settings | Валідація даних і налаштування |
| PyJWT | JWT access/refresh tokens |
| Redis + RQ | Черги фонових задач |
| httpx | HTTP-клієнт для інтеграцій |
| duckduckgo-search | Web research для Apply Assistant |
| sentence-transformers | Локальні semantic embeddings |
| React | Побудова frontend UI |
| TypeScript | Типізація frontend-коду |
| Vite | Dev server і збірка frontend |
| Vitest | Frontend тести |
| Docker Compose | Контейнеризація повного середовища |
| Elasticsearch | Повнотекстовий пошук |
| PostgreSQL + pgvector | Продукційна БД і vector similarity |

## 2. Встановлення програмного забезпечення

### 2.1. Вимоги до апаратного та програмного забезпечення

Мінімальні вимоги для локального запуску:

| Компонент | Мінімальна вимога | Рекомендовано |
|---|---|---|
| ОС | Windows 10/11, Linux або macOS | Windows 11 або Linux |
| Python | 3.11+ | Python 3.11 |
| Node.js | 20+ | Node.js LTS |
| RAM | 4 GB | 8-16 GB |
| CPU | 2 ядра | 4+ ядра |
| Диск | 2 GB | 5+ GB |
| Docker | Не обов’язково для SQLite | Docker Desktop для повного стеку |

Для повного режиму з PostgreSQL, Redis, Elasticsearch та embeddings бажано мати щонайменше 8 GB RAM.

### 2.2. Встановлення залежностей backend

1. Відкрити PowerShell у корені проєкту.
2. Створити virtual environment:

```powershell
python -m venv .venv
```

3. Активувати середовище:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Встановити backend-залежності:

```powershell
pip install -e ".[dev]"
```

5. Якщо планується використовувати локальні embeddings:

```powershell
pip install -e ".[embeddings]"
```

### 2.3. Встановлення залежностей frontend

Перейти до директорії frontend:

```powershell
cd frontend
npm install
cd ..
```

### 2.4. Налаштування `.env`

Для базового локального запуску можна використовувати налаштування за замовчуванням. Для повнішого режиму потрібно створити `.env` на основі прикладу:

```powershell
Copy-Item .env.full.local.example .env
```

Основні параметри:

| Змінна | Призначення |
|---|---|
| `DATABASE_URL` | Підключення до SQLite або PostgreSQL |
| `REDIS_URL` | Підключення до Redis |
| `JWT_SECRET_KEY` | Секрет для JWT |
| `ELASTICSEARCH_ENABLED` | Увімкнення Elasticsearch |
| `EMBEDDING_PROVIDER` | `hash` або `sentence_transformers` |
| `OPPORTUNITY_EXTRACTION_PROVIDER` | `deterministic`, `groq`, `local` |
| `ADVISOR_PROVIDER` | `deterministic`, `groq`, `local` |
| `GROQ_API_KEY` | API key для Groq |
| `ASSISTANT_WEB_RESEARCH_ENABLED` | Увімкнення DuckDuckGo web research |
| `EMAIL_PROVIDER` | `console` або `smtp` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` | SMTP/Mailtrap налаштування |
| `ORCID_OAUTH_ENABLED` | Увімкнення ORCID OAuth |

Для web research у Apply Assistant:

```env
ASSISTANT_WEB_RESEARCH_ENABLED=true
ASSISTANT_WEB_RESEARCH_PROVIDER=duckduckgo
ASSISTANT_WEB_RESEARCH_MAX_RESULTS=3
ASSISTANT_WEB_RESEARCH_TIMEOUT_SECONDS=8
```

### 2.5. Запуск міграцій

Якщо використовується PostgreSQL або потрібно оновити схему БД:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

### 2.6. Локальний запуск без Docker

Запустити backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Запустити frontend:

```powershell
cd frontend
npm run dev
```

Адреси:

| Компонент | URL |
|---|---|
| Frontend | `http://127.0.0.1:3000` |
| Backend API | `http://127.0.0.1:8000` |
| Swagger/OpenAPI | `http://127.0.0.1:8000/docs` |

### 2.7. Запуск усієї системи однією командою

На Windows можна використати:

```powershell
.\scripts\run-full-app.ps1
```

Цей скрипт запускає:

- backend;
- frontend;
- worker, якщо доступний Redis;
- scheduler, якщо доступний Redis.

Якщо Redis недоступний, backend і frontend запускаються, а background-процеси пропускаються з попередженням.

### 2.8. Make-команди

У проєкті є `Makefile`:

```powershell
make setup
make backend
make frontend
make worker
make scheduler
make run-full-app
make test
make migrate
make docker-up
make docker-down
```

На Windows команда `make` може бути недоступна за замовчуванням. У такому разі потрібно встановити GNU Make через Chocolatey, Scoop, Git Bash/MSYS2 або WSL. Альтернативно можна запускати PowerShell-скрипти напряму.

### 2.9. Повний запуск через Docker Compose

Для запуску повного стеку:

```powershell
Copy-Item .env.full.example .env
docker compose up --build
```

Docker Compose запускає:

- API;
- frontend;
- PostgreSQL;
- Redis;
- Elasticsearch;
- worker;
- scheduler.

Зупинити стек:

```powershell
docker compose down
```

## 3. Налаштування програмного забезпечення

### 3.1. Перший запуск

Після запуску frontend потрібно перейти за адресою:

```text
http://127.0.0.1:3000
```

Перший типовий сценарій:

1. Зареєструвати обліковий запис.
2. Підтвердити email, якщо увімкнена email verification.
3. Увійти в систему.
4. Створити профіль дослідника.
5. Заповнити career stage, country, disciplines, keywords.
6. Додати research summary, publications, degrees, languages.
7. Перейти на сторінку Matches.
8. Зберегти або запланувати цікаві можливості.
9. Використати Kanban Board та Apply Assistant.

### 3.2. Реєстрація користувача

На сторінці входу потрібно вибрати реєстрацію і ввести:

- full name;
- email;
- password.

Пароль вводиться двічі. Якщо увімкнена email verification, система надсилає лист із посиланням підтвердження. Для локальної розробки лист може виводитися в console або приходити в Mailtrap.

### 3.3. Вхід у систему

Для входу потрібно ввести email і password. Після успішного входу користувач отримує доступ до:

- dashboard;
- profile;
- matches;
- opportunity details;
- board;
- reminders;
- notifications;
- Apply Assistant.

Admin-користувач додатково бачить вкладку Admin.

### 3.4. ORCID OAuth

Якщо увімкнено ORCID OAuth, користувач може входити через ORCID. Для цього потрібно налаштувати:

```env
ORCID_OAUTH_ENABLED=true
ORCID_CLIENT_ID=...
ORCID_CLIENT_SECRET=...
ORCID_REDIRECT_URI=http://127.0.0.1:8000/auth/orcid/callback
```

ORCID використовується для безпечної автентифікації та/або імпорту публічних академічних даних.

### 3.5. Налаштування email / Mailtrap

Для Mailtrap приклад:

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=587
SMTP_USERNAME=your_username
SMTP_PASSWORD=your_password
SMTP_USE_TLS=true
EMAIL_FROM=Research Matcher <noreply@example.local>
```

Email використовується для:

- підтвердження пошти;
- deadline reminders;
- weekly digest;
- high match alerts.

### 3.6. Налаштування AI

Система може працювати без AI у deterministic режимі. Для Groq:

```env
ADVISOR_PROVIDER=groq
GROQ_API_KEY=...
GROQ_MODEL=llama-3.1-8b-instant
OPPORTUNITY_EXTRACTION_PROVIDER=groq
```

Для локальної OpenAI-compatible моделі:

```env
ADVISOR_PROVIDER=local
ADVISOR_LOCAL_BASE_URL=http://localhost:11434/v1
ADVISOR_LOCAL_MODEL=llama3.1:8b
```

### 3.7. Налаштування Elasticsearch

Для повнотекстового пошуку:

```env
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_OPPORTUNITY_INDEX=research_opportunities
```

Якщо Elasticsearch недоступний, система використовує fallback database search.

### 3.8. Налаштування embeddings

Базовий режим:

```env
EMBEDDING_PROVIDER=hash
```

Режим із локальною моделлю:

```env
EMBEDDING_PROVIDER=sentence_transformers
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

Якщо встановлено:

```env
EMBEDDING_AUTO_INSTALL=true
```

backend спробує автоматично встановити `sentence-transformers`, якщо пакет відсутній.

## 4. Базові функції програмного забезпечення

### 4.1. Сторінка How It Works

Ця сторінка пояснює:

- для чого призначена система;
- як працюють matches;
- які джерела використовуються;
- як система формує рекомендації;
- навіщо потрібен Apply Assistant.

Сторінка доступна і для гостя, і для авторизованого користувача.

### 4.2. Guest Mode

Гість може переглядати доступні можливості без створення профілю. У цьому режимі:

- доступний загальний каталог можливостей;
- немає персоналізованого match score;
- не можна зберігати, планувати або ігнорувати можливості;
- система пропонує створити акаунт для персоналізації.

### 4.3. Profile

Профіль складається з кількох підсторінок:

1. **Profile Wizard / Editor** - основні обов’язкові поля.
2. **Research Evidence** - research summary, publications, degrees, languages.
3. **Imports** - ORCID/OpenAlex імпорт.

Основні поля:

| Поле | Призначення |
|---|---|
| Full name | Ім’я користувача з акаунта |
| Career stage | Рівень кар’єри: bachelor, master, phd, postdoc тощо |
| Country | Країна користувача / поточна країна профілю |
| Disciplines | Наукові дисципліни |
| Keywords | Теми досліджень |
| Publications | Публікації для readiness та assistant |
| Degrees | Освіта / ступені |
| Languages | Мови |
| Funding interests | Теми фінансування |
| Unavailable countries | Країни, які користувач не розглядає |

### 4.4. ORCID та OpenAlex

ORCID може використовуватися для:

- входу через OAuth;
- імпорту публічного ORCID-профілю;
- підв’язки ORCID ID до профілю.

OpenAlex використовується для:

- пошуку автора;
- імпорту публікацій;
- генерації suggested disciplines;
- генерації suggested keywords;
- збагачення funding interests;
- покращення readiness та Apply Assistant.

### 4.5. Matches

Сторінка Matches показує персоналізовані можливості для активного профілю.

Користувач може:

- шукати за keywords;
- сортувати за match score, deadline, created date, readiness score;
- фільтрувати за source, type, country, career stage;
- вмикати або вимикати active only;
- відкривати деталі можливості;
- зберігати або ігнорувати можливість.

Match score формується з кількох компонентів:

- topic / semantic similarity;
- eligibility;
- deadline/timing;
- readiness;
- user history.

### 4.6. Opportunity Details

На сторінці деталей можливості відображається:

- опис;
- eligibility;
- parsed requirements;
- key details;
- source evidence;
- match explanation;
- radar/compass diagram;
- status slider;
- reminders;
- Apply Assistant shortcut.

Status slider дозволяє змінити стан можливості:

```text
saved -> planned -> applied -> accepted/rejected
```

Також можливість можна позначити як `ignored`.

### 4.7. Kanban Board

Kanban-дошка використовується для відстеження заявок. Підтримуються колонки:

- saved;
- planned;
- applied;
- accepted;
- rejected;
- ignored.

Картки можна переміщувати між колонками мишкою. Переміщення змінює статус можливості для активного профілю.

### 4.8. Reminders

Reminders використовуються для нагадування про дедлайни. Система може:

- автоматично створювати reminder для saved/planned можливостей;
- дозволяти створювати reminder вручну;
- показувати pending/completed reminders;
- позначати reminder як completed.

### 4.9. Notifications

Notifications - це історія й налаштування сповіщень. Вони можуть включати:

- deadline reminders;
- weekly digest;
- high-match alerts;
- email delivery status;
- read/unread status.

Різниця:

- **Reminder** - запланована подія/нагадування.
- **Notification** - фактично створене або надіслане повідомлення.

### 4.10. Apply Assistant

Apply Assistant допомагає підготувати заявку до конкретної можливості.

Він формує:

- readiness score;
- пояснення readiness;
- next actions;
- advisor memo;
- preparation gaps;
- missing profile fields;
- eligibility warnings;
- optional web research snippets через DuckDuckGo.

Readiness score залежить від:

- заповненості профілю;
- наявності публікацій;
- degrees;
- languages;
- відповідності career stage;
- відповідності country/citizenship/mobility rules;
- parsed opportunity requirements;
- gaps і warnings.

Advisor memo не замінює офіційні правила програми. Воно допомагає користувачу зрозуміти, що перевірити на офіційному сайті, як сформулювати application angle і які дії виконати першими.

### 4.11. Admin

Admin-сторінка доступна тільки користувачу з роллю admin.

Admin може:

- імпортувати Grants.gov можливості;
- імпортувати EU Funding / Erasmus / NAWA / Horizon / інші джерела;
- імпортувати зовнішні RSS/JSON/HTML джерела;
- переглядати batch history;
- бачити source freshness;
- редагувати можливості;
- переглядати analytics;
- виконувати duplicate merge.

### 4.12. Імпорт можливостей з українських та європейських джерел

Для українських можливостей можна використовувати:

- NRFU;
- nauka.gov.ua;
- House of Europe;
- Science for Ukraine;
- MSCA4Ukraine;
- DAAD Ukraine;
- Fulbright Ukraine.

Для європейських можливостей:

- Erasmus+;
- NAWA;
- Horizon Europe;
- EU Funding and Tenders;
- MSCA.

У разі імпорту система:

1. Завантажує список можливостей.
2. Пропускає вже існуючі URL.
3. Нормалізує title, summary, eligibility.
4. За можливості викликає AI extraction.
5. Створює embeddings.
6. Індексує можливість в Elasticsearch.
7. Додає результат у catalog.

## 5. Аналіз помилок і способи вирішення

### 5.1. `make` не розпізнається

Помилка:

```text
The term 'make' is not recognized as the name of a cmdlet
```

Причина: GNU Make не встановлений у Windows.

Рішення:

- встановити Make через Chocolatey/Scoop/Git Bash/MSYS2/WSL;
- або використовувати:

```powershell
.\scripts\run-full-app.ps1
```

### 5.2. Redis connection error

Помилка:

```text
redis.exceptions.ConnectionError: Error connecting to redis:6379
```

Причина: Redis не запущений або неправильно вказаний `REDIS_URL`.

Рішення:

```powershell
docker compose up -d redis
```

або запустити повний Docker Compose:

```powershell
docker compose up --build
```

Для локального `.venv` потрібно використовувати:

```env
REDIS_URL=redis://localhost:6379/0
```

Не `redis://redis:6379/0`, бо ім’я `redis` працює тільки всередині Docker Compose network.

### 5.3. PostgreSQL / transaction aborted

Помилка:

```text
current transaction is aborted, commands ignored until end of transaction block
```

Причина: попередній SQL-запит у цій транзакції завершився помилкою.

Рішення:

1. Подивитися першу помилку перед цим повідомленням.
2. Виправити причину, наприклад відсутню колонку або міграцію.
3. Запустити:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

4. Перезапустити backend.

### 5.4. Відсутня колонка в БД

Приклад:

```text
column opportunities.opportunity_embedding does not exist
```

Причина: код очікує нову колонку, але міграції не застосовані.

Рішення:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Якщо це локальна SQLite база з дуже старої версії, можна видалити `research_matcher.db` і запустити backend заново.

### 5.5. `sentence-transformers is not installed`

Причина: увімкнено `EMBEDDING_PROVIDER=sentence_transformers`, але пакет не встановлено.

Рішення:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[embeddings]"
```

Або увімкнути:

```env
EMBEDDING_AUTO_INSTALL=true
```

Або перейти на deterministic режим:

```env
EMBEDDING_PROVIDER=hash
```

### 5.6. Matches довго завантажуються

Можливі причини:

- перше завантаження embedding-моделі;
- відсутні збережені embeddings;
- backend виконує backfill;
- багато можливостей у БД;
- Elasticsearch або PostgreSQL недоступні;
- профіль щойно змінено і кеш embeddings інвалідовано.

Рішення:

1. Дочекатися першого завантаження моделі.
2. Перевірити backend logs.
3. Запустити embedding refresh.
4. Для швидкого режиму встановити:

```env
EMBEDDING_PROVIDER=hash
```

### 5.7. Apply Assistant не використовує web research

Причини:

- `ASSISTANT_WEB_RESEARCH_ENABLED=false`;
- пакет `duckduckgo-search` не встановлений;
- немає інтернету;
- DuckDuckGo тимчасово блокує або не повертає результати.

Рішення:

```env
ASSISTANT_WEB_RESEARCH_ENABLED=true
```

Потім:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Якщо web research недоступний, система продовжує працювати через retrieved context.

### 5.8. Email verification не приходить

Перевірити:

- `EMAIL_PROVIDER`;
- SMTP host/port;
- username/password;
- TLS;
- Mailtrap inbox;
- backend logs.

Для локальної перевірки можна використати console provider:

```env
EMAIL_PROVIDER=console
```

### 5.9. Admin tab не видно

Admin tab показується тільки користувачу з роллю `admin`.

Якщо користувач researcher:

- admin endpoints недоступні;
- admin вкладка прихована.

Для тестового середовища роль можна змінити напряму в БД або через seed/admin script, якщо він використовується.

### 5.10. External source імпортує загальну сторінку, а не конкретні можливості

Причина: джерело не має стабільного API/RSS або HTML-сторінка містить загальні navigation links.

Рішення:

- використовувати source-specific connector;
- імпортувати API/RSS, якщо доступний;
- перевірити URL, щоб він вів на список конкретних opportunities/calls;
- після імпорту перевірити Admin batch history;
- якщо потрібно, додати окремий connector mapper для цього джерела.

### 5.11. Elasticsearch недоступний

Ознаки:

- пошук працює повільніше;
- logs показують fallback to database search.

Рішення:

```powershell
docker compose up -d elasticsearch
```

Перевірити:

```text
http://localhost:9200
```

### 5.12. Де дивитися logs

Основні джерела logs:

- terminal backend;
- terminal worker;
- terminal scheduler;
- Docker logs;
- browser console;
- Network tab у DevTools.

Для Docker:

```powershell
docker compose logs api
docker compose logs worker
docker compose logs scheduler
docker compose logs frontend
```

## 6. Перевірка працездатності

### 6.1. Backend tests

```powershell
.\.venv\Scripts\python.exe -m pytest
```

### 6.2. Frontend build

```powershell
cd frontend
npm run build
```

### 6.3. Frontend tests

```powershell
cd frontend
npm run test
```

### 6.4. Docker config check

```powershell
docker compose config
```

## 7. Рекомендований сценарій демонстрації системи

Для демонстрації роботи системи рекомендується виконати такий сценарій:

1. Запустити систему.
2. Зареєструвати користувача.
3. Підтвердити email.
4. Створити профіль дослідника.
5. Заповнити research summary, publications, languages.
6. Імпортувати або додати кілька можливостей.
7. Відкрити Matches.
8. Пояснити match score і radar/compass diagram.
9. Зберегти одну можливість.
10. Перемістити її на Kanban Board у `planned`.
11. Створити reminder.
12. Відкрити Apply Assistant.
13. Показати readiness score, clickable chips, next actions і advisor memo.
14. Увійти як admin і показати імпорт джерел / batch history.

## 8. Примітки щодо безпеки

Для production-режиму потрібно:

- змінити `JWT_SECRET_KEY`;
- використовувати PostgreSQL замість SQLite;
- увімкнути HTTPS;
- зберігати секрети не в репозиторії, а в secret manager або environment variables;
- використовувати SMTP credentials тільки через `.env`;
- обмежити admin-доступ;
- увімкнути rate limiting;
- перевіряти зовнішні URL для SSRF-захисту;
- регулярно запускати міграції й тести.

## 9. Коротка довідка URL

| Призначення | URL |
|---|---|
| Frontend | `http://127.0.0.1:3000` |
| Backend API | `http://127.0.0.1:8000` |
| API Docs | `http://127.0.0.1:8000/docs` |
| Elasticsearch | `http://localhost:9200` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

## 10. Коротка довідка команд

```powershell
# Встановлення
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd frontend
npm install
cd ..

# Запуск backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload

# Запуск frontend
cd frontend
npm run dev

# Повний запуск Windows
.\scripts\run-full-app.ps1

# Міграції
.\.venv\Scripts\python.exe -m alembic upgrade head

# Тести
.\.venv\Scripts\python.exe -m pytest
cd frontend
npm run test
npm run build

# Docker
docker compose up --build
docker compose down
```

## 11. Резервне копіювання та перевірка швидкодії

Для створення резервної копії PostgreSQL використовується скрипт:

```powershell
.\scripts\backup-postgres.ps1
```

Скрипт створює файл у папці `backups`. Якщо доступні `pg_dump` і `DATABASE_URL`, використовується локальний PostgreSQL client. Якщо ні, скрипт пробує виконати backup через Docker Compose сервіс `postgres`.

Для відновлення бази даних:

```powershell
.\scripts\restore-postgres.ps1 -BackupPath .\backups\research-matcher-YYYYMMDD-HHMMSS.dump
```

Відновлення очищає існуючі таблиці перед імпортом backup-файлу, тому його потрібно запускати лише для бази, яку можна перезаписати.

Для перевірки вимоги щодо відкриття основних API до 3 секунд:

```powershell
.\scripts\performance-check.ps1
```

Для авторизованих перевірок:

```powershell
$env:ROM_ACCESS_TOKEN = "<access-token>"
$env:ROM_PROFILE_ID = "1"
.\scripts\performance-check.ps1 -RunFrontendBuild
```

Скрипт вимірює `/opportunities`, `/profiles/me`, `/recommendations/{profile_id}` і, за потреби, frontend build.
