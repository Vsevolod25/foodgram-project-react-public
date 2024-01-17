import csv
import os

from psycopg2 import connect
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Импортирует данные об ингредиентах из .csv файла.'

    def handle(self, *args, **options):

        con = connect(
            f'dbname={os.getenv("POSTGRES_DB")} '
            f'user={os.getenv("POSTGRES_USER")} '
            f'password={os.getenv("POSTGRES_PASSWORD")} '
            f'host={os.getenv("DB_HOST")} '
            f'port={os.getenv("DB_PORT")}'
        )
        cur = con.cursor()

        with open('data/ingredients.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            db = []
            id = 1
            for row in reader:
                lst = [row.get(key) for key in row]
                db.append([id] + lst)
                id += 1

        cur.executemany(
            'INSERT INTO ingredients_ingredient (id, name, measurement_unit) '
            'VALUES (%s, %s, %s);', db
        )

        con.commit()
        cur.close()
        con.close()

        print('Ингредиенты успешно импортированы.')
