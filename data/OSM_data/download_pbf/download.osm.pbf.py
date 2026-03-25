import requests
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm
import urllib.parse


def get_sub_region_pbf_links(url):
    """
    Ищет конкретную таблицу Sub Regions по классу заголовка
    и вытаскивает ссылки на .pbf.
    """
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    # Находим таблицу, внутри которой есть <th class="subregion">Sub Region</th>
    target_table = None
    all_tables = soup.find_all('table')

    for table in all_tables:
        header = table.find('th', class_='subregion')
        if header and "Sub Region" in header.text:
            target_table = table
            break

    if not target_table:
        print("Целевая таблица 'Sub Regions' не найдена.")
        return []

    links = []
    # Проходим по строкам. Нам нужны строки, где есть ссылки
    for row in target_table.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue

        # Обычно ссылки на .pbf в этой таблице находятся во 2-й или 3-й колонке.
        # Мы просто ищем все <a>, чьи ссылки заканчиваются на .osm.pbf внутри этой строки.
        pbf_anchors = row.find_all('a', href=lambda href: href and href.endswith('.osm.pbf'))

        for anchor in pbf_anchors:
            # На Geofabrik часто две ссылки на .pbf (одна маленькая [MD5]),
            # берем только ту, где в тексте нет '[MD5]' или берем первую
            if '[MD5]' not in anchor.text:
                full_url = urllib.parse.urljoin(url, anchor['href'])
                links.append(full_url)

    # Удаляем дубликаты, если они возникли
    return list(dict.fromkeys(links))


def download_file(url, target_dir, check_exists=True):
    path = Path(target_dir)
    path.mkdir(parents=True, exist_ok=True)

    filename = url.split('/')[-1]
    file_path = path / filename

    # Проверка: если файл уже скачан полностью, можно пропустить (опционально)
    if file_path.exists() and check_exists:
        print(f"Файл {filename} уже существует")
        return

    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))

    with open(file_path, 'wb') as f, tqdm(
            desc=filename[:30],  # Ограничим длину имени в прогресс-баре
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=5 * 1024 * 1024):  # Увеличили буфер для скорости
            size = f.write(data)
            bar.update(size)


def main():
    current_path = Path(__file__).resolve().parent
    download_folder = current_path.parent / "source_file" / "europe_asia_osm_data" # !!! Важно
    print(f"Папка сохранения файлов{download_folder}")

    # base_url = "https://download.geofabrik.de/asia.html"    # !!! Важно
    base_url = "https://download.geofabrik.de/europe.html"

    print(f"Сбор ссылок с {base_url}...")
    pbf_links = get_sub_region_pbf_links(base_url)

    if not pbf_links:
        print("Список ссылок пуст.")
        return

    print(f"Найдено файлов для скачивания: {len(pbf_links)}")

    for link in pbf_links:
        try:
            download_file(link, download_folder)
        except Exception as e:
            print(f"Ошибка при скачивании {link}: {e}")


if __name__ == "__main__":
    main()
