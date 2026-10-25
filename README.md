# Mektep AI

Веб-қосымша Қазақстан мектептері үшін: мұғалім оқу жоспары мен силлабус жүктейді, жабық және ашық сұрақтары бар тест құрады. Оқушы аккаунтсыз атын жазып тест тапсырады. Ашық жауаптарды Google Gemini қазақша талдайды — не қате, неліктен, қайдан бастау және нақты нені оқу керек.

## Жылдам іске қосу

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
# .env ішіне GEMINI_API_KEY қойыңыз (https://aistudio.google.com/apikey)
PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Браузер: http://127.0.0.1:8000

Gemini кілті болмаса да қосымша жұмыс істейді: жабық сұрақтар тексеріледі, ашық сұрақтарға «API кілті жоқ» деген ескерту шығады.

## Не істейді (MVP)

| Рөл | Мүмкіндік |
| --- | --- |
| Мұғалім | Тіркелу / кіру |
| Мұғалім | Оқу жоспары мен силлабус жүктеу |
| Мұғалім | Тест: жабық (MCQ) және ашық сұрақтар, үлгі жауап |
| Оқушы | Код + аты-жөні, аккаунт жоқ |
| Жүйе | Жабық сұрақтарды бірден тексеру |
| Gemini | Ашық жауапқа қазақша кері байланыс |

## API

- `POST /api/v1/auth/register` `POST /api/v1/auth/login` `GET /api/v1/auth/me`
- `GET|POST /api/v1/materials` `GET /api/v1/materials/{id}/download`
- `GET|POST /api/v1/tests` `PUT /api/v1/tests/{id}`
- `GET /api/v1/public/tests/{code}`
- `POST /api/v1/public/tests/{code}/start`
- `POST /api/v1/public/attempts/{id}/submit`

## Docker

```bash
cp .env.example .env
docker compose up --build
```

Келесі қадамдар (V1): PostgreSQL, фондық кезек, сынып аналитикасы, i18n kk/ru.
