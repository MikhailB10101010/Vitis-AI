import geopandas as gpd
import pandas as pd
from pathlib import Path


def merge_geojson_files(
        root_folder,
        output_file='merged.geojson',
        select_cols=None
):
    """
    Объединяет все .geojson файлы из указанной папки и всех её подпапок.

    Parameters:
    -----------
    root_folder : str или Path
        Путь к корневой папке, в которой нужно искать .geojson файлы
    output_file : str
        Имя выходного файла
    """

    # Преобразуем в Path объект
    root_path = Path(root_folder)

    # Рекурсивно находим все .geojson файлы
    geojson_files = list(root_path.rglob('*.geojson'))

    if not geojson_files:
        print("Файлы .geojson не найдены в указанной папке и её подпапках.")
        return

    print(f"Найдено {len(geojson_files)} файлов .geojson")

    # Список для хранения всех GeoDataFrame
    gdf_list = []
    all_obj = 0

    # Читаем каждый файл
    for file_path in geojson_files:
        try:
            print(f"{file_path.name}\t\t", end='')
            gdf = gpd.read_file(file_path)

            if select_cols is not None:
                gdf = gdf[select_cols]

            # Добавляем колонку с именем исходного файла для отслеживания
            gdf['source_file'] = file_path.name

            gdf_list.append(gdf)
            all_obj += len(gdf)
            print(f" - OK\t(объектов: {len(gdf)})")

        except Exception as e:
            print(f"Ошибка при загрузке {file_path}: {e}")

    if not gdf_list:
        print("Не удалось загрузить ни одного файла.")
        return

    print("\nОбъединение файлов...")

    # Объединяем все GeoDataFrame
    # Используем pd.concat с параметрами для обработки разных колонок
    merged_gdf = gpd.GeoDataFrame(pd.concat(
        gdf_list,
        ignore_index=True,
        sort=False  # Не сортируем колонки, чтобы сохранить порядок
    ))

    # Проверяем и исправляем геометрию (опционально)
    if not merged_gdf.geom_type.isnull().all():
        # Убеждаемся, что все геометрии валидны
        # merged_gdf['geometry'] = merged_gdf['geometry'].buffer(0)
        merged_gdf['geometry'] = merged_gdf.make_valid()

    # Выводим информацию о результате
    print(f"\nРезультат объединения:")
    print(f"  - Всего объектов: {len(merged_gdf)} ({all_obj})")
    print(f"  - Количество колонок: {len(merged_gdf.columns)}")
    print(f"  - Колонки: {list(merged_gdf.columns)}")

    # Сохраняем результат
    try:
        merged_gdf.to_file(output_file, driver='GeoJSON')
        print(f"\nФайл успешно сохранён: {output_file}")
        print(f"Размер файла: {Path(output_file).stat().st_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"\nОшибка при сохранении: {e}")


if __name__ == "__main__":
    #
    current_path = Path(__file__).resolve().parent
    merged_geo_name = 'merged.geojson'
    space_geo_file = current_path.parent / 'results'

    essential_columns = [
        'osm_id',  # уникальный идентификатор
        'osm_type',  # тип объекта (way/relation)
        'name',  # название
        'landuse'  # тип землепользования (должен быть vineyard)
        'geometry',  # геометрия объекта
    ]

    vineyard_specific = [
        'grape_variety',  # сорт винограда
        'vine_row_orientation',  # ориентация рядов
        'vine_row_direction',  # направление рядов
        'crop',  # культура
        'produce',  # производимая продукция
        'plantation',  # плантация/насаждение
        'vineyard:class',  # класс виноградника
        'vineyard:locality',  # местность/апелласьон
        'vineyard:soil',  # тип почвы
        'vineyard:village',  # деревня/село
        'vineyard:type',  # тип виноградника
        'vineyard:description:it',  # описание (итальянские регионы)
        'wine:label',  # винная этикетка/бренд
        'wine:region',  # винный регион
        'harvest_year_start',  # год начала сбора
        'harvest_first_year',  # первый год сбора
        'organic',  # органическое земледелие
        'irrigation',  # орошение
        'irrigation:water_supply',  # источник воды для орошения
        'terraced'  # террасирование
    ]

    merge_geojson_files(
        root_folder=space_geo_file,
        output_file=merged_geo_name,
        select_cols=essential_columns + vineyard_specific
    )

