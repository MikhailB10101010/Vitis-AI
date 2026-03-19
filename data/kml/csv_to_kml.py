import csv
import simplekml
from pathlib import Path


def create_kml_from_csv(
    csv_path: Path,
    kml_path: Path,
    name_col: str,
    lat_col: str,
    lon_col: str,
    desc_cols: list
):
    """Конвертирует CSV в KML с динамическим описанием и путями Pathlib."""
    if not csv_path.exists():
        print(f"[-] Файл не найден: {csv_path}")
        return

    kml = simplekml.Kml()

    with csv_path.open(mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Собираем описание только из существующих в строке колонок
                description = "\n".join([f"{col}: {row[col]}" for col in desc_cols if col in row])

                kml.newpoint(
                    name=row[name_col],
                    coords=[(row[lon_col], row[lat_col])],
                    description=description
                )
            except KeyError as e:
                print(f"[-] Ошибка: Столбец {e} не найден в {csv_path.name}")
                return

    # Создаем родительские папки для KML, если их нет
    kml_path.parent.mkdir(parents=True, exist_ok=True)

    kml.save(str(kml_path))
    print(f"[+] KML сохранен: {kml_path.relative_to(kml_path.parents[1])}")


def main():
    from pathlib import Path

    # Определяем корень репозитория
    repo_root = Path(__file__).resolve()

    for parent in repo_root.parents:
        if (parent / '.git').exists():
            repo_root = parent
            break
    else:
        # Если .git не найден, оставляем папку файла или ставим заглушку
        repo_root = repo_root.parent

    data_dir = repo_root / "data" / "vineyards Oliver Dressler"
    output_dir = repo_root / "data" / "kml"

    # Настройки путей относительно КОРНЯ
    config = {
        "csv_path": data_dir / "vineyards_enriched.csv",
        "kml_path": output_dir / "vineyards_enriched.kml",
        "name_col": "name",  # столбец
        "lat_col": "latitude",
        "lon_col": "longitude",
        "desc_cols": ['continent', 'country', 'city', 'website']  # Выбирайте любые колонки
    }

    create_kml_from_csv(**config)


if __name__ == "__main__":
    main()
