# foodgram-project-react
foodgram-project-react

# Проект Foodgram

## Домен
https://foodgram-vs.ddns.net

## Описание
Проект Foodgram позволяет делиться своими рецептами с другими пользователями.
Просмотр уже загруженных на сайт рецептов доступен любому пользователю, однако зарегистрированные пользователи могут сами добавлять рецепты своих любимых блюд, сопровождая их набором тегов (например, "Завтрак" или "Ужин") и необходимых для приготовления ингредиентов ("яйца", "помидоры", "сыр" и др.).
Также регистрация дает возможность подписываться на других пользователей, добавлять рецепты в избранное и в корзину.
По запросу пользователь может сформировать и загрузить текстовый файл со списком и количеством всех ингредиентов, необходимых для приготовления рецептов в корзине.
Добавлять ингредиенты и теги могут только администраторы.

## Технологии
Django==3.2.3
djangorestframework==3.12.4
django-colorfield==0.11.0
django-filter==23.2
djoser==2.2.2
drf-extra-fields==3.7.0
gunicorn==20.1.0
Pillow==9.0.0
psycopg2-binary==2.9.3
PyYAML==6.0

## Запуск проекта в докере

1. Клонировать репозиторий и перейти в папку infra/:

```
git clone git@github.com:vsevolod25/foodgram-project-react
```

```
cd foodgram-project-react/infra/
```

2. Запустить docker-compose:

```
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d
```

3. Выполнить миграции, собрать статику (если проект запускается в первый раз или в него вносились изменения):

```
docker compose -f docker-compose.production.yml exec backend python manage.py migrate
docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
```

4. Загрузить в базу данных готовый список ингредиентов (опционально):

```
docker compose -f docker-compose.production.yml exec backend python manage.py importingredients
```

## Документация (при запуске на локальном сервере)
http://127.0.0.1:8000/redoc/

## Примеры запросов (при запуске на локальном сервере)

Стартовая страница с рецептами:

```
http://127.0.0.1:8000/recipes/
```

Зарегистрированные пользователи, личный профиль:

```
http://127.0.0.1:8000/users/
http://127.0.0.1:8000/users/me/
```

Личные подписки:

```
http://127.0.0.1:8000/subscriptions/
```

Загрузка файла со списком ингредиентов для рецептов в корзине:

```
http://127.0.0.1:8000/recipes/download_shopping_cart/
```

## Superuser (для входа в админку)

email: user@me.com
password: user

## Автор

Vsevolod25: https://github.com/Vsevolod25
