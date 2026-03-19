# from shapely.geometry import Point
# import geopandas as gpd
# import pandas as pd
# import logging
# import sys
# from datetime import datetime
# import os
#
# # Настраиваем логирование
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[logging.StreamHandler(sys.stdout)]
# )
# logger = logging.getLogger('LocalOSM')
#
#
# class LocalOSM:
#     def __init__(self, pbf_path):
#         self.logger = logging.getLogger('LocalOSM')
#         self.logger.info(f"Инициализация LocalOSM с файлом: {pbf_path}")
#
#         # Проверяем существование файла
#         if not os.path.exists(pbf_path):
#             self.logger.error(f"Файл не найден: {pbf_path}")
#             self.gdf = None
#             return
#
#         start_time = datetime.now()
#
#         try:
#             self.gdf = self._load_with_osmium(pbf_path)
#             elapsed = (datetime.now() - start_time).total_seconds()
#
#             if self.gdf is not None and len(self.gdf) > 0:
#                 self.logger.info(f"Загрузка завершена за {elapsed:.2f} секунд. Всего объектов: {len(self.gdf)}")
#             else:
#                 self.logger.warning("Виноградники не найдены")
#                 self.gdf = gpd.GeoDataFrame()
#
#         except Exception as e:
#             self.logger.error(f"Ошибка при загрузке: {e}", exc_info=True)
#             self.gdf = None
#
#     def _load_with_osmium(self, pbf_path):
#         """Загружает данные используя osmium (самый надежный способ для PBF)"""
#         try:
#             import osmium
#
#             self.logger.info("Использую osmium для чтения PBF файла...")
#
#             class VineyardHandler(osmium.SimpleHandler):
#                 def __init__(self, logger):
#                     super().__init__()
#                     self.vineyards = []
#                     self.counter = 0
#                     self.logger = logger
#
#                 def area(self, a):
#                     self.counter += 1
#
#                     if self.counter % 10000 == 0:
#                         self.logger.info(f"Обработано {self.counter} полигонов...")
#
#                     tags = dict(a.tags)
#                     if (tags.get('landuse') == 'vineyard' or
#                             tags.get('crop') == 'grape' or
#                             tags.get('produce') == 'grapes'):
#
#                         try:
#                             # Собираем внешний контур
#                             outer_ring = []
#                             for node in a.outer_ring():
#                                 outer_ring.append((node.lon, node.lat))
#
#                             if len(outer_ring) >= 4:
#                                 from shapely.geometry import Polygon
#                                 polygon = Polygon(outer_ring)
#
#                                 if polygon.is_valid and polygon.area > 0:
#                                     self.vineyards.append({
#                                         'geometry': polygon,
#                                         'name': tags.get('name'),
#                                         'grape_variety': tags.get('grape_variety'),
#                                         'osm_id': a.id
#                                     })
#
#                                     if len(self.vineyards) % 100 == 0:
#                                         self.logger.info(f"Найдено {len(self.vineyards)} виноградников")
#
#                         except Exception as e:
#                             pass  # Пропускаем проблемные полигоны
#
#             handler = VineyardHandler(self.logger)
#             self.logger.info("Начинаем обработку файла...")
#             handler.apply_file(pbf_path)
#
#             self.logger.info(f"Обработано полигонов: {handler.counter}")
#             self.logger.info(f"Найдено виноградников: {len(handler.vineyards)}")
#
#             if handler.vineyards:
#                 self.logger.info("Создаем GeoDataFrame...")
#                 gdf = gpd.GeoDataFrame(handler.vineyards)
#                 gdf.crs = "EPSG:4326"
#                 return gdf
#             else:
#                 return gpd.GeoDataFrame()
#
#         except ImportError:
#             self.logger.error("osmium не установлен. Установите: pip install osmium")
#             return self._load_with_fallback(pbf_path)
#         except Exception as e:
#             self.logger.error(f"Ошибка в osmium: {e}")
#             return self._load_with_fallback(pbf_path)
#
#     def _load_with_fallback(self, pbf_path):
#         """Запасной метод через OGR (медленнее, но работает)"""
#         self.logger.info("Пробую загрузить через OGR...")
#
#         try:
#             import fiona
#             import geopandas as gpd
#
#             vineyards = []
#             total = 0
#
#             # Открываем слой напрямую через fiona
#             with fiona.open(pbf_path, layer='multipolygons') as src:
#                 self.logger.info(
#                     f"Слой открыт, всего объектов: {len(src) if hasattr(src, '__len__') else 'неизвестно'}")
#
#                 for i, feature in enumerate(src):
#                     total += 1
#
#                     if total % 10000 == 0:
#                         self.logger.info(f"Обработано {total} объектов...")
#
#                     props = feature['properties']
#
#                     # Проверяем теги
#                     if (props.get('landuse') == 'vineyard' or
#                             props.get('crop') == 'grape' or
#                             props.get('produce') == 'grapes'):
#
#                         try:
#                             from shapely.geometry import shape
#                             geom = shape(feature['geometry'])
#
#                             vineyards.append({
#                                 'geometry': geom,
#                                 'name': props.get('name'),
#                                 'grape_variety': props.get('grape_variety'),
#                                 'osm_id': props.get('osm_id')
#                             })
#
#                             if len(vineyards) % 100 == 0:
#                                 self.logger.info(f"Найдено {len(vineyards)} виноградников")
#
#                         except Exception as e:
#                             self.logger.debug(f"Ошибка создания геометрии: {e}")
#
#             self.logger.info(f"Всего обработано: {total}, найдено виноградников: {len(vineyards)}")
#
#             if vineyards:
#                 return gpd.GeoDataFrame(vineyards, crs="EPSG:4326")
#             else:
#                 return gpd.GeoDataFrame()
#
#         except Exception as e:
#             self.logger.error(f"Ошибка в fallback методе: {e}")
#             return gpd.GeoDataFrame()
#
#     def _filter_vineyards(self, gdf):
#         """Оставляет только виноградники (для совместимости)"""
#         return gdf
#
#     def query(self, lat, lon):
#         if self.gdf is None:
#             self.logger.warning("Данные не загружены, query возвращает None")
#             return None
#
#         point = Point(lon, lat)
#         self.logger.debug(f"Поиск точки ({lat}, {lon})")
#
#         if len(self.gdf) == 0:
#             self.logger.debug("Нет данных для поиска")
#             return None
#
#         try:
#             # Используем пространственный индекс
#             if hasattr(self.gdf, 'sindex') and self.gdf.sindex is not None:
#                 possible_matches_idx = list(self.gdf.sindex.intersection(point.bounds))
#                 if possible_matches_idx:
#                     possible_matches = self.gdf.iloc[possible_matches_idx]
#                     matches = possible_matches[possible_matches.geometry.contains(point)]
#                 else:
#                     matches = gpd.GeoDataFrame()
#             else:
#                 matches = self.gdf[self.gdf.geometry.contains(point)]
#
#             if matches.empty:
#                 return None
#
#             row = matches.iloc[0]
#             self.logger.info(f"Найден виноградник: {row.get('name', 'без имени')}")
#
#             return {
#                 "is_vineyard": True,
#                 "name": row.get("name"),
#                 "grape_variety": row.get("grape_variety"),
#                 "source": "local"
#             }
#
#         except Exception as e:
#             self.logger.error(f"Ошибка при поиске: {e}")
#             return None
#
#
# # Для тестирования
# if __name__ == "__main__":
#     # Тест с маленьким файлом
#     test_file = "test.osm.pbf"  # Замените на ваш файл
#
#     osm = LocalOSM(test_file)
#
#     if osm.gdf is not None:
#         print(f"Загружено {len(osm.gdf)} виноградников")
#
#         # Тест запроса
#         result = osm.query(48.8566, 2.3522)  # Париж
#         print(f"Результат запроса: {result}")
#     else:
#         print("Не удалось загрузить данные")


from shapely.geometry import Point
import geopandas as gpd


class LocalOSM:
    def __init__(self, pbf_path):
        try:
            self.gdf = gpd.read_file(pbf_path, layer='multipolygons')
            self.gdf = self._filter_vineyards(self.gdf)
        except Exception:
            self.gdf = None

    def _filter_vineyards(self, gdf):
        return gdf[
            (gdf['landuse'] == 'vineyard') |
            (gdf['crop'] == 'grape') |
            (gdf['produce'] == 'grapes')
        ]

    def query(self, lat, lon):
        if self.gdf is None:
            return None

        point = Point(lon, lat)
        matches = self.gdf[self.gdf.geometry.contains(point)]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "is_vineyard": True,
            "name": row.get("name"),
            "grape_variety": row.get("grape_variety"),
            "source": "local"
        }
