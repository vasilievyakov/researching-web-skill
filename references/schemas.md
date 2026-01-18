# JSON Schemas для извлечения данных

Готовые схемы для `tabstack_extract_json` и `tabstack_generate_json`.

## Продукт

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "price": {"type": "number"},
    "currency": {"type": "string"},
    "description": {"type": "string"},
    "rating": {"type": "number"},
    "reviews_count": {"type": "integer"},
    "availability": {"type": "boolean"},
    "images": {"type": "array", "items": {"type": "string"}}
  }
}
```

## Контакт

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "email": {"type": "string"},
    "phone": {"type": "string"},
    "company": {"type": "string"},
    "position": {"type": "string"},
    "address": {"type": "string"},
    "social_links": {"type": "array", "items": {"type": "string"}}
  }
}
```

## Событие

```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "date": {"type": "string", "format": "date-time"},
    "end_date": {"type": "string", "format": "date-time"},
    "location": {"type": "string"},
    "description": {"type": "string"},
    "organizer": {"type": "string"},
    "price": {"type": "number"},
    "registration_url": {"type": "string"}
  }
}
```

## Статья

```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "author": {"type": "string"},
    "published_date": {"type": "string", "format": "date"},
    "content": {"type": "string"},
    "summary": {"type": "string"},
    "tags": {"type": "array", "items": {"type": "string"}},
    "read_time_minutes": {"type": "integer"}
  }
}
```

## Компания

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "description": {"type": "string"},
    "website": {"type": "string"},
    "industry": {"type": "string"},
    "employees": {"type": "string"},
    "founded": {"type": "integer"},
    "headquarters": {"type": "string"},
    "social_links": {"type": "object"}
  }
}
```

## Вакансия

```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "company": {"type": "string"},
    "location": {"type": "string"},
    "salary_range": {"type": "string"},
    "employment_type": {"type": "string"},
    "description": {"type": "string"},
    "requirements": {"type": "array", "items": {"type": "string"}},
    "posted_date": {"type": "string", "format": "date"}
  }
}
```

## Список (универсальный)

```json
{
  "type": "object",
  "properties": {
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "description": {"type": "string"},
          "url": {"type": "string"}
        }
      }
    },
    "total_count": {"type": "integer"}
  }
}
```

## Использование

При вызове `tabstack_extract_json`:

```python
schema = {
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "price": {"type": "number"}
  }
}
```

Адаптировать схему под конкретный сайт — добавлять/убирать поля по необходимости.
