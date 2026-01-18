# Автоматический Scoring по URL

Правила для быстрого определения Authority Score по домену/URL.

## Authority по домену (автоматически)

### Tier 1: Score 38-40 (Официальные/Академические)

```
# Официальная документация продукта
docs.*.com, *.docs.*, /docs/, /documentation/
developer.*.com, developers.*

# Академические
arxiv.org                           → 38
nature.com, science.org             → 38
ieee.org, acm.org                   → 38
*.edu                               → 35

# Официальные сайты продуктов (если запрос про этот продукт)
react.dev, vuejs.org, angular.io    → 40
python.org, golang.org, rust-lang.org → 40
nodejs.org, deno.land               → 40
```

### Tier 2: Score 28-35 (Качественные tech-ресурсы)

```
# GitHub
github.com (README, repo)           → 28-35 (по stars)
  - > 10k stars                     → 35
  - 1k-10k stars                    → 32
  - 100-1k stars                    → 28
  - < 100 stars                     → 22

# Tech-издания
dev.to                              → 30
css-tricks.com                      → 30
smashingmagazine.com                → 30
web.dev                             → 32
mdn.web.dev                         → 35
freecodecamp.org                    → 28

# Q&A (по accepted/score)
stackoverflow.com
  - accepted answer, score > 50     → 30
  - accepted answer, score < 50     → 25
  - no accepted, high score         → 20
  - no accepted, low score          → 15
```

### Tier 3: Score 20-28 (Известные издания)

```
# Tech-новости
techcrunch.com                      → 25
theverge.com                        → 25
arstechnica.com                     → 28
wired.com                           → 25
hackernews (news.ycombinator.com)   → 22

# Крупные медиа
bbc.com, reuters.com                → 28
nytimes.com, theguardian.com        → 25

# Спортивные (для спорт-тем)
formula1.com                        → 40 (офиц.)
skysports.com                       → 30
espn.com                            → 28
motorsport.com                      → 28
```

### Tier 4: Score 12-20 (Блоги, форумы)

```
# Medium
medium.com/@известный_автор         → 25
medium.com (обычный)                → 18

# Блоги
*.blogspot.com                      → 15
wordpress.com                       → 15
/blog/ в URL                        → 15-20

# Форумы
reddit.com                          → 15
  - r/*, high upvotes               → 18
  - r/*, low upvotes                → 12
quora.com                           → 12
```

### Tier 5: Score 0-10 (Низкое качество)

```
# Агрегаторы
"top 10", "best X" в title          → 5
listicles без глубины               → 5

# SEO-спам (отсеять)
keyword stuffing в title/snippet    → 0
подозрительные домены               → 0
сгенерированный контент             → 0
```

## Relevance: быстрая оценка

```python
relevance = 0

# Title match
if query_keywords in title:
    relevance += 15

# Snippet match
if query_keywords in snippet:
    relevance += 10

# Specific vs general
if "how to", "tutorial", "guide" in title and task == "how-to":
    relevance += 5
if answers_specific_question:
    relevance += 5
```

## Freshness: по дате

```python
from datetime import date

def freshness_score(pub_date, is_tech_topic):
    age_months = (date.today() - pub_date).days / 30

    if is_tech_topic:
        if age_months < 6: return 20
        if age_months < 12: return 15
        if age_months < 24: return 10
        if age_months < 60: return 5
        return 0
    else:
        if age_months < 6: return 20
        if age_months < 12: return 18
        if age_months < 24: return 15
        if age_months < 60: return 12
        return 8
```

## Accessibility: по домену

```python
# Известные paywall
PAYWALL_DOMAINS = [
    "nytimes.com",      # частичный
    "wsj.com",          # полный
    "ft.com",           # полный
    "medium.com",       # частичный (3 статьи бесплатно)
    "bloomberg.com",    # частичный
]

# Известные SPA (нужен automate)
SPA_DOMAINS = [
    "app.*",
    "dashboard.*",
    "*.vercel.app",
    "*.netlify.app",
]
```

## Быстрый расчёт

Для каждого результата поиска:

```
1. Domain → Authority (таблица выше)
2. Title/Snippet match → Relevance
3. Published date → Freshness
4. Paywall check → Accessibility

Score = Authority + Relevance + Freshness + Accessibility
```

Показывать в виде таблицы:

```markdown
| # | URL | Auth | Rel | Fresh | Acc | Score |
|---|-----|------|-----|-------|-----|-------|
| 1 | formula1.com/... | 40 | 25 | 15 | 10 | 90 |
| 2 | github.com/... | 32 | 20 | 20 | 10 | 82 |
```
