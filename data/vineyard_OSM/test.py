import osmium
import os
import sys

class FileValidatorHandler(osmium.SimpleHandler):
    def __init__(self):
        super(FileValidatorHandler, self).__init__()
        self.nodes = 0
        self.ways = 0
        self.relations = 0

    def node(self, n):
        self.nodes += 1
        if self.nodes % 1000000 == 0:
            print(f"Обработано узлов: {self.nodes}")

    def way(self, w):
        self.ways += 1

    def relation(self, r):
        self.relations += 1

def validate_pbf(filename):
    handler = FileValidatorHandler()
    try:
        print(f"Начинаю проверку файла: {filename}")
        # Проходим по файлу
        handler.apply_file(filename, locations=False)
        print("Проверка завершена успешно.")
        print(f"Узлов: {handler.nodes}")
        print(f"Путей: {handler.ways}")
        print(f"Отношений: {handler.relations}")
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

input_csv = os.path.join(BASE_DIR, "data/vineyards_enriched.csv")    # input.csv
output_csv = os.path.join(BASE_DIR, "data/output.csv")
osm_file = os.path.join(BASE_DIR, "data/osm/europe-latest.osm.pbf")
cache_file = os.path.join(BASE_DIR, "cache/cache.db")

if __name__ == '__main__':
    # Укажите путь к вашему файлу
    validate_pbf(osm_file)