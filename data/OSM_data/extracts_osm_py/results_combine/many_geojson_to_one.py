import geopandas as gpd
import pandas as pd
from pathlib import Path
from tqdm import tqdm


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
    select_cols : list
        Список столбцов которые требуется оставить
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
    count_error = 0

    # Читаем каждый файл
    for file_path in geojson_files:
        try:
            print(f"{file_path.name}\t\t", end='')
            gdf = gpd.read_file(file_path)

            if select_cols is not None:
                # 1. Определяем список колонок, которые НУЖНО удалить
                # Оставляем только те, что в select_cols И обязательно 'geometry'
                # keep = set(select_cols) | {'geometry'}
                if 'geometry' not in select_cols:
                    select_cols = select_cols + ['geometry']
                cols_to_drop = [c for c in gdf.columns if c not in select_cols]

                # 2. Удаляем их "на месте" (inplace=True), чтобы не пересоздавать объект
                gdf.drop(columns=cols_to_drop, inplace=True, errors='ignore')

            # Добавляем колонку с именем исходного файла для отслеживания
            gdf['source_file'] = file_path.name

            gdf_list.append(gdf)
            all_obj += len(gdf)
            print(f" - OK\t(объектов: {len(gdf)}, колонок: {len(gdf.columns)})")

        except Exception as e:
            print(f"Ошибка при загрузке {file_path}: {e}")
            count_error +=1

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

    #
    if select_cols is not None:
        # 1. Берем только те колонки из списка, которые существуют в gdf
        # (сохраняя порядок из select_cols)

        cols_sort = [c for c in select_cols if c in merged_gdf.columns]

        # 3. Перестраиваем таблицу в новом порядке
        merged_gdf = merged_gdf[cols_sort]

        # 4. Явно подтверждаем, что это GeoDataFrame (на случай потери метаданных)
        if 'geometry' in merged_gdf.columns:
            merged_gdf = merged_gdf.set_geometry('geometry')

    # Удаление дубликатов
    merged_gdf.drop_duplicates(subset=["osm_id"], inplace=True)

    # Удаление пустых geometry
    merged_gdf.dropna(subset=['geometry'], inplace=True)

    # Удаление "osm_type": "node"
    merged_gdf.drop(merged_gdf[merged_gdf['osm_type'] == 'node'].index, inplace=True)

    # Фильтр поиск огрызков
    merged_gdf.reset_index(drop=True, inplace=True)
    merged_gdf = remove_spatial_duplicates_advanced(
        merged_gdf,
        distance_threshold=2000,
        overlap_threshold=0.7
    )
    merged_gdf.reset_index(drop=True, inplace=True)

    # Выводим информацию о результате
    print(f"\nРезультат объединения:")
    print(f"  - Всего объектов: {len(merged_gdf)} (До удаления дубликатов и прочего: {all_obj})")
    if select_cols is None:
        print(f"  - Количество колонок: {len(merged_gdf.columns)}")
    else:
        print(f"  - Количество колонок: {len(merged_gdf.columns)} (Подано в функцию: {len(select_cols)})")
    print(f"  - Колонки: {list(merged_gdf.columns)}")

    if count_error != 0:
        print(f"!!! Ошибок при чтении файлов: {count_error} !!!")

    # Сохраняем результат
    try:
        merged_gdf.to_file(output_file, driver='GeoJSON')
        print(f"\nФайл успешно сохранён: {output_file}")
        print(f"Размер файла: {Path(output_file).stat().st_size / 1024 / 1024:.2f} MB")
    except Exception as e:
        print(f"\nОшибка при сохранении: {e}")


def remove_spatial_duplicates_advanced(
        gdf,
        distance_threshold=2000,   # метры
        overlap_threshold=0.7
):
    """
    Удаление spatial-дубликатов:
    1. Фильтр по расстоянию центроидов
    2. Проверка вложенности
    3. Проверка пересечения (overlap)
    """

    print("\nУдаление spatial-дубликатов (advanced)...")

    gdf = gdf.copy()

    # --- CRS обязательно в метрах ---
    if gdf.crs.is_geographic:
        gdf = gdf.to_crs(epsg=3857)

    # Предрасчеты
    gdf["area"] = gdf.geometry.area
    gdf["centroid"] = gdf.geometry.centroid

    sindex = gdf.sindex
    to_drop = set()

    for idx, row in tqdm(gdf.iterrows(), total=len(gdf), desc="Обработка объектов"):
        if idx in to_drop:
            continue

        geom = row.geometry
        centroid = row.centroid

        # bbox кандидаты
        possible_idx = list(sindex.intersection(geom.bounds))

        for other_idx in possible_idx:
            if other_idx == idx or other_idx in to_drop:
                continue

            other = gdf.loc[other_idx]

            # --- 1. ФИЛЬТР ПО РАССТОЯНИЮ ---
            dist = centroid.distance(other.centroid)
            if dist > distance_threshold:
                continue

            other_geom = other.geometry

            # --- 2. ПРОВЕРКА ВЛОЖЕННОСТИ ---
            if geom.contains(other.centroid):
                # другой внутри текущего
                to_drop.add(other_idx)
                continue

            if other_geom.contains(centroid):
                to_drop.add(idx)
                break

            # --- 3. ПРОВЕРКА ПЕРЕСЕЧЕНИЯ ---
            if not geom.intersects(other_geom):
                continue

            intersection = geom.intersection(other_geom)

            if intersection.is_empty:
                continue

            inter_area = intersection.area
            min_area = min(row.area, other.area)

            if min_area == 0:
                continue

            overlap_ratio = inter_area / min_area

            if overlap_ratio > overlap_threshold:
                if row.area >= other.area:
                    to_drop.add(other_idx)
                else:
                    to_drop.add(idx)
                    break

    print(f"Удалено объектов: {len(to_drop)}")

    gdf = gdf.drop(index=list(to_drop))
    gdf = gdf.drop(columns=["area", "centroid"])

    return gdf


if __name__ == "__main__":
    #
    current_path = Path(__file__).resolve().parent
    merged_geo_name = 'merged.geojson'
    space_geo_file = current_path.parent / 'results'

    essential_columns = [
        'osm_id',  # уникальный идентификатор
        'osm_type',  # тип объекта (way/relation)
        'name',  # название
        'landuse',  # тип землепользования (должен быть vineyard)
        'geometry'  # геометрия объекта
    ]

    vineyard_specific = [
        'grape_variety',  # сорт винограда
        #'vine_row_orientation',  # ориентация рядов
        #'vine_row_direction',  # направление рядов
        'crop',  # культура
        'produce',  # производимая продукция
        #'plantation',  # плантация/насаждение
        #'vineyard:class',  # класс виноградника
        #'vineyard:locality',  # местность/апелласьон
        #'vineyard:soil',  # тип почвы
        #'vineyard:village',  # деревня/село
        #'vineyard:type',  # тип виноградника
        #'vineyard:description:it',  # описание (итальянские регионы)
        'wine:label',  # винная этикетка/бренд
        'wine:region',  # винный регион
        #'harvest_year_start',  # год начала сбора
        #'harvest_first_year',  # первый год сбора
        #'organic',  # органическое земледелие
        #'irrigation',  # орошение
        #'irrigation:water_supply',  # источник воды для орошения
        #'terraced'  # террасирование
    ]

    merge_geojson_files(
        root_folder=space_geo_file,
        output_file=merged_geo_name,
        select_cols=essential_columns + vineyard_specific
    )