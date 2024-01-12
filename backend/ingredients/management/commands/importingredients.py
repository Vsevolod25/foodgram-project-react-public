import csv
import os
import sqlite3

from django.core.management.base import BaseCommand

from backend.settings import STATIC_URL


class Command(BaseCommand):
    help = 'Импортирует данные об ингредиентах из .csv файла.'

    def handle(self, *args, **options):
        path = os.path.join(STATIC_URL[1:], 'data/')

        con = sqlite3.connect('db.sqlite3')
        cur = con.cursor()

        with open(f'{path}ingredients.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            db = []
            id = 1
            for row in reader:
                lst = [row.get(key) for key in row]
                db.append([id] + lst)
                id += 1

        cur.executemany(
           'INSERT INTO ingredients_ingredient (id, name, measurement_unit) '
           'VALUES (?, ?, ?);', db
        )

        con.commit()
        con.close()

        print('Ингредиенты успешно импортированы.')
