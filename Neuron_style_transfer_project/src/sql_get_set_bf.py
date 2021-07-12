"""Модуль представляет прозрачный интерфейс для работы и выполнении основных операций с БД """

import sqlite3


class SqlInterface:

    def __init__(self, db_name):
        """Constructor. Подключение к БД"""

        self.sql_connection = sqlite3.connect(db_name + '.db')
        self.cursor = self.sql_connection.cursor()

    def __del__(self):
        """Destructor -> del object. Отключаемся от БД при удалении объекта"""

        self.sql_connection.close()

    def get_connect_status(self):
        """Возвращает статус соединения """

        return self.sql_connection

    def insert_blob(self, style, style_name, content, transformed, name):
        """Вставляет в базу данных файл-изображение в формате blob - массива двоичных данных"""

        style_picture = self.convert2bd(style)
        content_picture = self.convert2bd(content)
        transformed_picture = self.convert2bd(transformed)

        # Определим id данного изображения-стиля
        query = "SELECT id FROM style_ptre WHERE name = ? AND style = ?;"
        self.cursor.execute(query, (style_name, style_picture))
        style_id = self.cursor.fetchone()

        # Если такая сущность в БД отсутствует, то вставить ее и извлечь id
        if not style_id:
            query = "INSERT INTO style_ptre (name, style) VALUES (?, ?)"
            self.cursor.execute(query, (style_name, style_picture))
            self.sql_connection.commit()
            query = "SELECT id FROM style_ptre WHERE name = ? AND style = ?;"
            self.cursor.execute(query, (style_name, style_picture))
            style_id = self.cursor.fetchone()

        # Добавить сгенерированное изображение в БД
        query = "INSERT INTO transfered (style_id, content, transformed, name) VALUES (?, ?, ?, ?)"
        self.cursor.execute(query, (style_id[0], content_picture, transformed_picture, name))
        self.sql_connection.commit()

    def blob_read(self, style_name, transform_name, path):
        """Получить данные blob-объекты из БД и преобразовать в изображение"""

        quary = "SELECT style FROM style_ptre WHERE name = ?"
        self.cursor.execute(quary, (style_name,))
        style = self.cursor.fetchone()[0]
        style_path = path + style_name + '.jpg'
        self.write2file(style, style_path)
        quary = "SELECT transformed FROM transfered WHERE name = ?"
        self.cursor.execute(quary, (transform_name,))
        trans = self.cursor.fetchone()[0]
        trans_path = path + transform_name + '.jpg'
        self.write2file(trans, trans_path)

    def write2file(self, data, file_name):
        """Сохранить полученные данные в виде файла"""

        with open(file_name, 'wb') as file:
            file.write(data)

    def convert2bd(self, file_name):
        """Считать файл в двоичный массив данных"""

        with open(file_name, 'rb') as file:
            blob = file.read()
        return blob

    def get_style_name(self):
        """Получить список имен изображений-стилей"""

        quary = "SELECT name FROM style_ptre"
        self.cursor.execute(quary)
        return list(map(lambda x: x[0], self.cursor.fetchall()))

    def get_trans_name(self):
        """Получить список имен сгенерированных изображений"""

        quary = "SELECT name FROM transfered"
        self.cursor.execute(quary)
        return list(map(lambda x: x[0], self.cursor.fetchall()))

    def get_data(self):
        """Получить объекты из таблиц стилей и сгенерированных изображений"""

        tr_column = "name, metadata, id, style_id"
        quary_tr = "SELECT " + tr_column + " FROM transfered"
        st_column = "name, metadata, id"
        quary_st = "SELECT " + st_column + " FROM style_ptre"
        return self.cursor.execute(quary_st).fetchall(), st_column, self.cursor.execute(quary_tr).fetchall(), tr_column
