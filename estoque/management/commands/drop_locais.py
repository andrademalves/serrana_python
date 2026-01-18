from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drop locais_estoque and destinos_estoque tables'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute('DROP TABLE IF EXISTS locais_estoque')
            cursor.execute('DROP TABLE IF EXISTS destinos_estoque')
            self.stdout.write(self.style.SUCCESS('Tabelas removidas com sucesso'))
