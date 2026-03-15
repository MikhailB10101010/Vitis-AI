# winerymap
Dataset: https://github.com/oOo0oOo/winerymap/tree/main

User: Oliver Dressler

Лицензия на проект MIT License

# json to csv

Перенес json файл в csv разделив region на contry, city

Встречаются пустые ячейки данных, они оставлены как пустые или ''

## json

```
Region (ключ)
 ├─ color
 └─ vineyards (массив)
       ├─ latitude
       ├─ longitude
       ├─ name
       ├─ website
       └─ [дополнительный массив чисел]
```

## csv

| Column    | Type   | Description                                                         |
| --------- | ------ | ------------------------------------------------------------------- |
| country   | string | Страна, извлечённая из поля `region`                                |
| city      | string | Город или регион внутри страны                                      |
| name      | string | Название винодельни                                                 |
| latitude  | float  | Географическая широта                                               |
| longitude | float  | Географическая долгота                                              |
| website   | string | Сайт винодельни (если отсутствует — пустая строка)                  |
| extra     | string | Дополнительные данные, массив чисел преобразован в строку через `;` |

