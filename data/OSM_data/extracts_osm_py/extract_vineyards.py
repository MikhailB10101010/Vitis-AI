"""
Извлечение виноградников (landuse=vineyard) из OSM PBF файлов.

Использование как библиотеки:
    from extract_vineyards import extract_vineyards_main

    # Базовое использование
    vineyards = extract_vineyards_main(
        input_file="data/france-latest.osm.pbf",
        output_prefix="results/vineyards"
    )

    # Расширенное использование
    vineyards = extract_vineyards_main(
        input_file=Path("data/region.osm.pbf"),
        output_prefix=Path("results/vineyards"),
        formats=["geojson", "csv"],
        show_stats=True,
        skip_count=False
    )

Зависимости:
    pip install osmium tqdm
"""

import osmium
import json
import csv
import sys
import os
import argparse
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from tqdm import tqdm


# ──────────────────────────── Конфигурация тегов ────────────────────────────

# Теги, которые извлекаем в отдельные поля
VINEYARD_TAGS = [
    "name",
    "grape_variety",
    "operator",
    "organic",
    "species",
    "crop",
    "description",
    "wikidata",
    "source",
    "surface",
    "alt_name",
    "old_name",
    "start_date",
    "ownership",
    "irrigation",
]


# ──────────────────────────── Структуры данных ──────────────────────────────

@dataclass
class Vineyard:
    """Структура для хранения данных одного виноградника."""
    osm_id: int
    osm_type: str  # "node", "way", "relation"
    tags: dict = field(default_factory=dict)
    coordinates: list = field(default_factory=list)  # [(lon, lat), ...]

    @property
    def name(self) -> str:
        return self.tags.get("name", "")

    @property
    def grape_variety(self) -> str:
        return self.tags.get("grape_variety", "")

    @property
    def centroid(self) -> Optional[tuple]:
        """Вычисляет центроид по координатам."""
        if not self.coordinates:
            return None
        lon_avg = sum(c[0] for c in self.coordinates) / len(self.coordinates)
        lat_avg = sum(c[1] for c in self.coordinates) / len(self.coordinates)
        return (lon_avg, lat_avg)


# ──────────────────────── Получение размера файла ───────────────────────────

def get_file_size(filepath: Union[str, Path]) -> int:
    """Возвращает размер файла в байтах."""
    return os.path.getsize(str(filepath))


def format_size(size_bytes: int) -> str:
    """Форматирует размер в человекочитаемый вид."""
    for unit in ["Б", "КБ", "МБ", "ГБ", "ТБ"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} ПБ"


def format_duration(seconds: float) -> str:
    """Форматирует длительность."""
    if seconds < 60:
        return f"{seconds:.1f} сек"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes} мин {secs} сек"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} ч {minutes} мин"


# ──────────────────── Подсчёт объектов (для прогресс-бара) ──────────────────

class CountHandler(osmium.SimpleHandler):
    """Первый проход: считает общее количество объектов для прогресс-бара."""

    def __init__(self):
        super().__init__()
        self.nodes = 0
        self.ways = 0
        self.relations = 0

    @property
    def total(self) -> int:
        return self.nodes + self.ways + self.relations

    def node(self, n):
        self.nodes += 1

    def way(self, w):
        self.ways += 1

    def relation(self, r):
        self.relations += 1


def count_objects(filepath: Union[str, Path], verbose: bool = True) -> dict:
    """
    Считает количество объектов в PBF файле.
    Для больших файлов используем оценку по размеру.
    """
    filepath = Path(filepath)
    file_size = get_file_size(filepath)

    # Для файлов > 2 ГБ считать объекты долго — используем оценку
    if file_size > 2 * 1024 * 1024 * 1024:
        # Эмпирическая оценка: ~15 млн объектов на 1 ГБ PBF
        estimated = int((file_size / (1024 * 1024 * 1024)) * 15_000_000)
        if verbose:
            print(f"  Файл большой ({format_size(file_size)}), "
                  f"оценка: ~{estimated:,} объектов")
        return {"total": estimated, "estimated": True}

    if verbose:
        print(f"  Подсчёт объектов в файле ({format_size(file_size)})...")

    counter = CountHandler()
    counter.apply_file(str(filepath))

    if verbose:
        print(f"  Найдено: {counter.nodes:,} нод, "
              f"{counter.ways:,} линий, "
              f"{counter.relations:,} отношений")

    return {
        "nodes": counter.nodes,
        "ways": counter.ways,
        "relations": counter.relations,
        "total": counter.total,
        "estimated": False,
    }


# ──────────────────── Основной обработчик виноградников ─────────────────────

class VineyardHandler(osmium.SimpleHandler):
    """Извлекает все объекты с landuse=vineyard."""

    def __init__(self, progress_bar: Optional[tqdm] = None):
        super().__init__()
        self.vineyards: list[Vineyard] = []
        self.progress = progress_bar
        self.processed = 0
        self._update_interval = 100_000  # обновляем прогресс каждые 100K объектов

    def _update_progress(self):
        """Обновляет прогресс-бар."""
        self.processed += 1
        if self.progress and self.processed % self._update_interval == 0:
            self.progress.update(self._update_interval)
            self.progress.set_postfix(
                vineyards=len(self.vineyards),
                refresh=False,
            )

    def _is_vineyard(self, tags) -> bool:
        """Проверяет, является ли объект виноградником."""
        landuse = tags.get("landuse")
        return landuse == "vineyard"

    def _extract_tags(self, osm_tags) -> dict:
        """Извлекает все теги в словарь."""
        return dict(osm_tags)

    def node(self, n):
        self._update_progress()
        if self._is_vineyard(n.tags):
            vineyard = Vineyard(
                osm_id=n.id,
                osm_type="node",
                tags=self._extract_tags(n.tags),
            )
            if n.location.valid():
                vineyard.coordinates.append((n.location.lon, n.location.lat))
            self.vineyards.append(vineyard)

    def way(self, w):
        self._update_progress()
        if self._is_vineyard(w.tags):
            vineyard = Vineyard(
                osm_id=w.id,
                osm_type="way",
                tags=self._extract_tags(w.tags),
            )
            for node in w.nodes:
                try:
                    if node.location.valid():
                        vineyard.coordinates.append(
                            (node.location.lon, node.location.lat)
                        )
                except osmium.InvalidLocationError:
                    pass
            self.vineyards.append(vineyard)

    def relation(self, r):
        self._update_progress()
        if self._is_vineyard(r.tags):
            vineyard = Vineyard(
                osm_id=r.id,
                osm_type="relation",
                tags=self._extract_tags(r.tags),
            )
            # Координаты relation не извлекаем (требует сборки мультиполигонов)
            self.vineyards.append(vineyard)


# ──────────────────────── Извлечение виноградников ──────────────────────────

def extract_vineyards(filepath: Union[str, Path],
                      skip_count: bool = False,
                      verbose: bool = True) -> list[Vineyard]:
    """
    Главная функция извлечения.
    Два прохода: 1) подсчёт для прогресс-бара, 2) извлечение данных.

    Args:
        filepath: Путь к PBF файлу
        skip_count: Пропустить подсчёт объектов (для очень больших файлов)
        verbose: Выводить информацию в консоль

    Returns:
        Список объектов Vineyard
    """
    filepath = Path(filepath)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Извлечение виноградников из OSM PBF")
        print(f"  Файл: {filepath}")
        print(f"  Размер: {format_size(get_file_size(filepath))}")
        print(f"{'='*60}\n")

    # Шаг 1: подсчёт объектов
    if not skip_count:
        if verbose:
            print("[1/2] Оценка количества объектов...")
        counts = count_objects(filepath, verbose=verbose)
        total = counts["total"]
    else:
        if verbose:
            print("[1/2] Пропуск подсчёта объектов (--skip-count)")
        # Если пропускаем подсчёт, используем оценку по размеру файла
        file_size = get_file_size(filepath)
        total = int((file_size / (1024 * 1024 * 1024)) * 15_000_000)
        if verbose:
            print(f"  Оценка по размеру: ~{total:,} объектов")

    # Шаг 2: извлечение с прогресс-баром
    if verbose:
        print(f"\n[2/2] Извлечение виноградников...")

    progress = None
    if verbose:
        progress = tqdm(
            total=total,
            unit=" obj",
            desc="  Обработка",
            bar_format=(
                "  {desc}: {percentage:3.0f}%|{bar:40}| "
                "{n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] "
                "{postfix}"
            ),
            miniters=100_000,
        )

    handler = VineyardHandler(progress_bar=progress)

    try:
        handler.apply_file(str(filepath), locations=True)
    except Exception as e:
        if progress:
            progress.close()
        raise e

    # Финальное обновление прогресс-бара
    if progress:
        remaining = handler.processed - progress.n
        if remaining > 0:
            progress.update(remaining)
        progress.set_postfix(vineyards=len(handler.vineyards))
        progress.close()

    if verbose:
        print(f"\n  Готово! Найдено виноградников: {len(handler.vineyards):,}")

    return handler.vineyards


# ──────────────────────── Статистика ────────────────────────────────────────

def print_statistics(vineyards: list[Vineyard]):
    """Выводит статистику по извлечённым виноградникам."""
    if not vineyards:
        print("\n  Виноградники не найдены.")
        return

    print(f"\n{'='*60}")
    print(f"  Статистика")
    print(f"{'='*60}")

    # По типам
    types = {}
    for v in vineyards:
        types[v.osm_type] = types.get(v.osm_type, 0) + 1

    print(f"\n  По типу OSM-объекта:")
    for t, count in sorted(types.items()):
        print(f"    {t:>12}: {count:,}")

    # По наличию тегов
    print(f"\n  Наличие тегов:")
    for tag_name in VINEYARD_TAGS:
        count = sum(1 for v in vineyards if tag_name in v.tags)
        if count > 0:
            pct = count / len(vineyards) * 100
            print(f"    {tag_name:>20}: {count:>7,} ({pct:5.1f}%)")

    # С координатами
    with_coords = sum(1 for v in vineyards if v.coordinates)
    print(f"\n  С координатами: {with_coords:,} / {len(vineyards):,}")

    # Топ сортов винограда
    grape_counts = {}
    for v in vineyards:
        grape = v.tags.get("grape_variety", "")
        if grape:
            grape_counts[grape] = grape_counts.get(grape, 0) + 1

    if grape_counts:
        print(f"\n  Топ-10 сортов винограда:")
        for grape, count in sorted(
            grape_counts.items(), key=lambda x: -x[1]
        )[:10]:
            print(f"    {grape:>30}: {count:,}")

    # Все уникальные ключи тегов
    all_keys = set()
    for v in vineyards:
        all_keys.update(v.tags.keys())

    print(f"\n  Всего уникальных ключей тегов: {len(all_keys)}")
    print(f"  Ключи: {', '.join(sorted(all_keys))}")


# ──────────────────────── Сохранение в GeoJSON ──────────────────────────────

def _build_geometry(vineyard: Vineyard) -> Optional[dict]:
    """Строит GeoJSON geometry из координат."""
    coords = vineyard.coordinates
    if not coords:
        return None

    if len(coords) == 1:
        return {
            "type": "Point",
            "coordinates": [coords[0][0], coords[0][1]],
        }

    # Проверяем замкнутость
    is_closed = (
        len(coords) >= 4
        and coords[0][0] == coords[-1][0]
        and coords[0][1] == coords[-1][1]
    )

    if is_closed:
        return {
            "type": "Polygon",
            "coordinates": [[[c[0], c[1]] for c in coords]],
        }
    else:
        return {
            "type": "LineString",
            "coordinates": [[c[0], c[1]] for c in coords],
        }


def save_geojson(vineyards: list[Vineyard], filepath: Union[str, Path], verbose: bool = True):
    """Сохраняет виноградники в формат GeoJSON."""
    filepath = Path(filepath)

    if verbose:
        print(f"\n  Сохранение GeoJSON: {filepath}")

    features = []
    iterator = tqdm(vineyards, desc="  GeoJSON", unit=" obj",
                    bar_format="  {desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt}") if verbose else vineyards

    for v in iterator:
        feature = {
            "type": "Feature",
            "id": v.osm_id,
            "geometry": _build_geometry(v),
            "properties": {
                "osm_id": v.osm_id,
                "osm_type": v.osm_type,
                **v.tags,
            },
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"  Сохранено: {format_size(os.path.getsize(filepath))}")


# ──────────────────────── Сохранение в CSV ──────────────────────────────────

def save_csv(vineyards: list[Vineyard], filepath: Union[str, Path], verbose: bool = True):
    """Сохраняет виноградники в CSV."""
    filepath = Path(filepath)

    if verbose:
        print(f"\n  Сохранение CSV: {filepath}")

    # Собираем все уникальные ключи тегов
    all_tag_keys = set()
    for v in vineyards:
        all_tag_keys.update(v.tags.keys())
    all_tag_keys = sorted(all_tag_keys)

    # Заголовки
    headers = [
        "osm_id",
        "osm_type",
        "lon_centroid",
        "lat_centroid",
        "num_coordinates",
    ] + all_tag_keys

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()

        iterator = tqdm(vineyards, desc="  CSV", unit=" obj",
                        bar_format="  {desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt}") if verbose else vineyards

        for v in iterator:
            centroid = v.centroid
            row = {
                "osm_id": v.osm_id,
                "osm_type": v.osm_type,
                "lon_centroid": f"{centroid[0]:.7f}" if centroid else "",
                "lat_centroid": f"{centroid[1]:.7f}" if centroid else "",
                "num_coordinates": len(v.coordinates),
            }
            # Добавляем все теги
            for key in all_tag_keys:
                row[key] = v.tags.get(key, "")

            writer.writerow(row)

    if verbose:
        print(f"  Сохранено: {format_size(os.path.getsize(filepath))}")


# ──────────── Сохранение в JSON (полный дамп с координатами) ────────────────

def save_json(vineyards: list[Vineyard], filepath: Union[str, Path], verbose: bool = True):
    """Сохраняет полный дамп в JSON (включая все координаты)."""
    filepath = Path(filepath)

    if verbose:
        print(f"\n  Сохранение JSON: {filepath}")

    data = []
    iterator = tqdm(vineyards, desc="  JSON", unit=" obj",
                    bar_format="  {desc}: {percentage:3.0f}%|{bar:30}| {n_fmt}/{total_fmt}") if verbose else vineyards

    for v in iterator:
        entry = {
            "osm_id": v.osm_id,
            "osm_type": v.osm_type,
            "tags": v.tags,
            "centroid": {
                "lon": v.centroid[0],
                "lat": v.centroid[1],
            } if v.centroid else None,
            "coordinates": [
                {"lon": c[0], "lat": c[1]} for c in v.coordinates
            ],
        }
        data.append(entry)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    if verbose:
        print(f"  Сохранено: {format_size(os.path.getsize(filepath))}")


# ──────────────────────── Главная функция сохранения ────────────────────────

def save_results(vineyards: list[Vineyard],
                 output_prefix: Union[str, Path],
                 formats: List[str],
                 verbose: bool = True):
    """Сохраняет результаты в указанных форматах."""
    output_prefix = Path(output_prefix)

    # Создаём директорию если не существует
    output_dir = output_prefix.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"\n{'='*60}")
        print(f"  Сохранение результатов")
        print(f"  Директория: {output_dir.resolve()}")
        print(f"  Форматы: {', '.join(formats)}")
        print(f"{'='*60}")

    if "geojson" in formats:
        save_geojson(vineyards, f"{output_prefix}.geojson", verbose=verbose)

    if "csv" in formats:
        save_csv(vineyards, f"{output_prefix}.csv", verbose=verbose)

    if "json" in formats:
        save_json(vineyards, f"{output_prefix}.json", verbose=verbose)


# ──────────────────── Основная функция для вызова из кода ───────────────────

def extract_vineyards_main(
    input_file: Union[str, Path],
    output_prefix: Union[str, Path] = "./vineyards",
    formats: List[str] = ["all"],
    show_stats: bool = True,
    skip_count: bool = False,
    verbose: bool = True
) -> List[Vineyard]:
    """
    Главная функция для извлечения виноградников из OSM PBF файла.

    Args:
        input_file: Путь к входному PBF файлу
        output_prefix: Префикс выходных файлов (по умолчанию: "./vineyards")
        formats: Список форматов вывода ["geojson", "csv", "json", "all"]
                (по умолчанию: ["all"])
        show_stats: Показывать статистику (по умолчанию: True)
        skip_count: Пропустить предварительный подсчёт объектов (по умолчанию: False)
        verbose: Выводить информацию в консоль (по умолчанию: True)

    Returns:
        Список объектов Vineyard

    Примеры:
        # Базовое использование
        vineyards = extract_vineyards_main("data/france.osm.pbf")

        # Расширенное использование
        vineyards = extract_vineyards_main(
            input_file=Path("data/italy.osm.pbf"),
            output_prefix=Path("output/italy_vineyards"),
            formats=["geojson", "csv"],
            show_stats=True,
            skip_count=False
        )

        # Только извлечение без сохранения
        vineyards = extract_vineyards_main(
            input_file="data/region.osm.pbf",
            output_prefix=None,
            show_stats=True
        )
    """
    # Преобразуем пути в объекты Path
    input_file = Path(input_file)

    # Проверяем существование входного файла
    if not input_file.exists():
        raise FileNotFoundError(f"Файл не найден: {input_file.resolve()}")

    # Определяем форматы
    if formats == ["all"]:
        formats = ["geojson", "csv", "json"]

    # Засекаем время
    start_time = time.time()

    # Извлечение
    vineyards = extract_vineyards(input_file, skip_count=skip_count, verbose=verbose)

    extraction_time = time.time() - start_time

    if not vineyards:
        if verbose:
            print("\nВиноградники не найдены в файле.")
        return []

    # Статистика
    if show_stats and verbose:
        print_statistics(vineyards)

    # Сохранение (если указан префикс)
    if output_prefix:
        save_results(vineyards, output_prefix, formats, verbose=verbose)

    # Итог
    total_time = time.time() - start_time
    if verbose:
        print(f"\n{'='*60}")
        print(f"  Итог")
        print(f"{'='*60}")
        print(f"  Извлечено виноградников: {len(vineyards):,}")
        print(f"  Время извлечения:        {format_duration(extraction_time)}")
        print(f"  Общее время:             {format_duration(total_time)}")
        print(f"  Входной файл:            {input_file.resolve()}")
        if output_prefix:
            print(f"  Выходные файлы:          {Path(output_prefix).resolve()}.*")
        print(f"{'='*60}\n")

    return vineyards


# ──────────────────────── CLI интерфейс (для обратной совместимости) ────────

def parse_arguments():
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Извлечение виноградников (landuse=vineyard) из OSM PBF файлов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python extract_vineyards.py -i data/france.osm.pbf -o results/france_vineyards
  python extract_vineyards.py -i data/italy.osm.pbf -o output/italy --format csv geojson
  python extract_vineyards.py -i data/region.osm.pbf -o ./vineyards --format all --no-stats
        """,
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Путь к входному PBF файлу (относительный или абсолютный)",
    )

    parser.add_argument(
        "-o", "--output",
        default="./vineyards",
        help="Префикс выходных файлов (по умолчанию: ./vineyards)",
    )

    parser.add_argument(
        "-f", "--format",
        nargs="+",
        default=["all"],
        choices=["geojson", "csv", "json", "all"],
        help="Форматы вывода (по умолчанию: all)",
    )

    parser.add_argument(
        "--no-stats",
        action="store_true",
        help="Не выводить статистику",
    )

    parser.add_argument(
        "--skip-count",
        action="store_true",
        help="Пропустить предварительный подсчёт объектов (быстрее для огромных файлов)",
    )

    return parser.parse_args()


def main_cli():
    """Точка входа для командной строки."""
    args = parse_arguments()

    try:
        extract_vineyards_main(
            input_file=args.input,
            output_prefix=args.output,
            formats=args.format,
            show_stats=not args.no_stats,
            skip_count=args.skip_count,
            verbose=True
        )
    except Exception as e:
        print(f"Ошибка: {e}")
        sys.exit(1)


# ──────────────────────── Точка входа ───────────────────────────────────────

if __name__ == "__main__":
    main_cli()