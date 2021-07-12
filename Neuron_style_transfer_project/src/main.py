"""Главный модуль приложения"""

import csv
import sys
from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QFileDialog, QDialog, QTableWidgetItem
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon, QPixmap
import matplotlib.pylab as plt
from neureal import *
import os
import skimage.io
import numpy as np
from sql_get_set_bf import *
import tensorflow_hub as hub


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


class ViewerImage(QWidget):
    """Форма для отображения сгенерированного изображения"""

    def __init__(self):
        super(ViewerImage, self).__init__()
        uic.loadUi('ui_form/imview.ui', self)
        self.setWindowTitle(' ')

    def setImage(self, fname):
        """Разместить полученное изображение и ее гистограмму цветов"""

        self.im_view.setPixmap(QPixmap(fname).scaledToHeight(250))      # разместить изображение
        # Определить каналы изображения
        colors = ("r", "g", "b")
        channel_ids = (0, 1, 2)

        image = skimage.io.imread(fname=fname)      # считать изображение

        # Посторить гистограмму по каналам
        plt.clf()
        for channel_id, c in zip(channel_ids, colors):
            histogram, bin_edges = np.histogram(
                image[:, :, channel_id], bins=256, range=(0, 256)
            )
            plt.plot(bin_edges[0:-1], histogram, color=c)

        # Сохранить гистограмму и отобразить
        name = '../saved/hist.jpg'
        plt.savefig(name)
        self.hist_view.setPixmap(QPixmap(name).scaledToWidth(400))


class Helper(QDialog):
    """Справочная информация"""

    def __init__(self):
        super(Helper, self).__init__()
        uic.loadUi('ui_form/input.ui', self)
        self.setWindowTitle(' ')


class AddWindow(QWidget):
    """Представляет форму, с помощью которого загружаются изображения (стиль, контент)"""

    def __init__(self):
        super(AddWindow, self).__init__()
        uic.loadUi('ui_form/add.ui', self)

        self.setWindowTitle(' ')

        self.pixmap = QPixmap('..\\res\\im.png')
        self.pixmap = self.pixmap.scaled(150, 200, QtCore.Qt.KeepAspectRatio)
        self.import_label_1.setPixmap(self.pixmap)
        self.import_label_2.setPixmap(self.pixmap)

        self.ok_button.clicked.connect(self.closed)
        self.style_name = ''
        self.content_name = ''

    def mousePressEvent(self, event):
        """Определим области нажатия мышью, для загрузки изображений"""
        if 20 < event.x() < 190 and 10 < event.y() < 250:
            self.import_style()
        elif 215 < event.x() < 370 and 10 < event.y() < 250:
            self.import_content()

    def import_style(self):
        self.style_name = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '', 'Картинка (*.jpg);')[0]
        self.import_label_1.setPixmap((QPixmap(self.style_name).scaledToHeight(240)))

    def import_content(self):
        self.content_name = QFileDialog.getOpenFileName(
            self, 'Выбрать картинку', '', 'Картинка (*.jpg);')[0]
        self.import_label_2.setPixmap((QPixmap(self.content_name).scaledToHeight(240)))

    def closed(self):
        self.close()

    def get_style(self):
        """Вернуть имя изображения-стиля"""
        return self.style_name

    def get_content(self):
        """Вернуть имя изображения-контента"""
        return self.content_name


class Download(QWidget):
    """Класс предоставляет форму для скачивания примеров из БД"""

    def __init__(self):
        super(Download, self).__init__()
        uic.loadUi('ui_form/down.ui', self)
        self.setWindowTitle(' ')

        self.connect = SqlInterface('../database/picture2transfer')     # подключение к БД

        # Получить список стилей и сгенерированных изображений и отображаем пользователю
        self.style_box.addItems(self.connect.get_style_name())
        self.transform_box.addItems(self.connect.get_trans_name())

        self.down_button.clicked.connect(self.download)

    def download(self):
        """Скачать выбранные изображения в директорию  download"""
        try:
            # Если данная дирекория не найдена, то создать
            if not os.path.isdir('../download'):
                os.mkdir('../download')
                print('Make directory')

            # Сохранить файл в директории
            self.connect.blob_read(style_name=self.style_box.currentText(),
                                   transform_name=self.transform_box.currentText(), path='../download/')

        except sqlite3.Error as err:
            # В случае ошибки отобразить пользователю
            self.statusbar.showMessage(err)


class Save2CSV(QWidget):
    """Интерфейс для сохранения данных изображения-стиля и результирующего изображения в формате csv"""

    def __init__(self):
        super(Save2CSV, self).__init__()
        uic.loadUi('ui_form/csv_data.ui', self)
        self.setWindowTitle(' ')
        self.result = ''
        self.download_button.clicked.connect(self.save)

    def save(self):
        with open('../download/style.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            # Получить списка заголовков
            writer.writerow(
                [self.view_style.horizontalHeaderItem(i).text() for i in range(self.view_style.columnCount())])

            for i in range(self.view_style.rowCount()):
                row = []
                for j in range(self.view_style.columnCount()):
                    item = self.view_style.item(i, j)
                    if item is not None:
                        row.append(item.text())
                writer.writerow(row)    # запись строки

        with open('../download/transform.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                [self.view_content.horizontalHeaderItem(i).text() for i in range(self.view_content.columnCount())])
            for i in range(self.view_content.rowCount()):
                row = []
                for j in range(self.view_content.columnCount()):
                    item = self.view_content.item(i, j)
                    if item is not None:
                        row.append(item.text())
                writer.writerow(row)

    def load_tabel(self):
        """Заполнить таблицы для предпросмотра csv файлов"""

        record_style, style_column, record_content, content_column = \
            self.result[0], self.result[1], self.result[2], self.result[3]

        self.view_style.setColumnCount(len(record_style[0]))    # установить количество колонок таблицы
        self.view_style.setRowCount(0)      # установить начальное число строк
        self.view_style.setHorizontalHeaderLabels(style_column.split(', '))     # задать заголовок таблицы
        for i, row in enumerate(record_style):
            self.view_style.setRowCount(self.view_style.rowCount() + 1)     # увеличить число строк на 1
            for j, elem in enumerate(row):
                self.view_style.setItem(i, j, QTableWidgetItem(str(elem)))      # заполнить ячейки
        self.view_style.resizeColumnsToContents()   # подогнать размер ячеек по содержанию

        self.view_content.setColumnCount(len(record_content[0]))
        self.view_content.setRowCount(0)
        self.view_content.setHorizontalHeaderLabels(content_column.split(', '))
        for i, row in enumerate(record_content):
            self.view_content.setRowCount(self.view_content.rowCount() + 1)
            for j, elem in enumerate(row):
                self.view_content.setItem(i, j, QTableWidgetItem(str(elem)))
        self.view_content.resizeColumnsToContents()

    def setResult(self, res):
        """Получить и установить данные - результат запроса к БД"""
        self.result = res


class Window(QMainWindow):
    """Главное окно программы"""

    def __init__(self):
        super(Window, self).__init__()
        uic.loadUi('ui_form/maincpy.ui', self)
        self.setWindowTitle(' ')

        self.learn_button.setIcon(QIcon('..\\res\\lrn.png'))
        self.learn_button.setIconSize(QtCore.QSize(55, 50))
        self.learn_button.clicked.connect(self.learn)

        self.csv_button.setIcon(QIcon('..\\res\\csv.png'))
        self.csv_button.setIconSize(QtCore.QSize(50, 42))
        self.csv_button.clicked.connect(self.save_to_csv)

        self.bd_button.setIcon(QIcon('..\\res\\sl.png'))
        self.bd_button.setIconSize(QtCore.QSize(50, 50))
        self.bd_button.clicked.connect(self.save_bd)

        self.add_button.setIcon(QIcon('..\\res\\add.png'))
        self.add_button.setIconSize(QtCore.QSize(50, 50))
        self.add_button.clicked.connect(self.add_form)

        self.pixmap = QPixmap('..\\res\\style_transfer.png')
        self.pixmap = self.pixmap.scaled(300, 500, QtCore.Qt.KeepAspectRatio)
        self.viewer.setPixmap(self.pixmap)

        self.pixmap = QPixmap('..\\res\\trng.png')
        self.pixmap = self.pixmap.scaled(400, 200, QtCore.Qt.KeepAspectRatio)
        self.viewer2.setPixmap(self.pixmap)

        self.viewer1.setText('')

        self.add_files = AddWindow()

        self.helper = Helper()
        self.viewer_transformed_image = ViewerImage()
        self.about_program.triggered.connect(self.show_help)
        self.load_sample.triggered.connect(self.load_from_db)

        self.fname = ''
        self.down = Download()
        self.connect = SqlInterface('../database/picture2transfer')
        self.save2csv = Save2CSV()

    def add_form(self):
        """Отобразить форму загрузки изображений для обучения"""
        self.add_files.show()

    def learn(self):
        self.statusbar.showMessage('learn process')     # информировать о начале процесса обучения

        # Проверить наличие директории saved и создать при необходимости
        if not os.path.isdir('../saved'):
            os.mkdir('../saved')

        stylized_image = self.learn_model()     # обучить модель

        # Дать название сгенерированному изображению
        name = self.add_files.get_style().split('/')[-1][:-4] + '_' + self.add_files.get_content().split('/')[-1][:-4]
        self.fname = "../saved/" + name + ".jpg"
        tensor_to_image(stylized_image).save(self.fname)    # преобразовать массив в изображение и сохранить

        # Отобразить сгенерированное изображение
        self.viewer_transformed_image.setImage(self.fname)
        self.viewer_transformed_image.show()

    def learn_model(self):
        """Обучить модель и вернуть выходное изображение"""
        path_content = self.add_files.get_content()     # получить имея соответствующего изображения
        path_style = self.add_files.get_style()
        content_image = load_img(path_content)      # преобразовать изображение
        style_image = load_img(path_style)

        # Скачать веса модели из Сети и обученить модель
        hub_model = hub.load('https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2')
        return hub_model(tf.constant(content_image), tf.constant(style_image))[0]

    def show_help(self):
        """Отобразить справочную информацию"""
        self.helper.show()

    def save_bd(self):
        """Сохранить данные в БД"""
        try:
            self.statusbar.showMessage(str(bool(self.connect.get_connect_status())))    # отобразить статус соединения
            self.connect.insert_blob(style=self.add_files.get_style(),
                                     style_name=self.add_files.get_style().split('/')[-1][:-4],
                                     content=self.add_files.get_content(), transformed=self.fname,
                                     name=self.fname.split('/')[-1][:-4])
        except sqlite3.Error as err:
            self.statusbar.showMessage(err)     # отобразить пользователю ошибку

    def save_to_csv(self):
        """Сохранить данные об изображениях в формате csv"""
        res = self.connect.get_data()   # получить данные
        # отобразить данные
        self.save2csv.setResult(res)
        self.save2csv.load_tabel()
        self.save2csv.show()

    def load_from_db(self):
        """Отобразить форму для загрузки примеров"""
        self.down.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    wnd = Window()
    wnd.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
