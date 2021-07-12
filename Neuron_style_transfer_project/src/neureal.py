""""Модуль для преобразования тензоров(массивы в tensorflow) и изображений"""

import tensorflow as tf
import PIL
from PIL import Image
import numpy as np


def tensor_to_image(tensor):
    """Преобразует массив в изображение"""

    tensor = tensor * 255   # преобразование, обратное стандартизации
    tensor = np.array(tensor, dtype=np.uint8)
    assert tensor.shape[0] == 1
    tensor = tensor[0]      # избавляемся от введенного ранее дополнительного измерения
    return PIL.Image.fromarray(tensor)


def load_img(path_to_img):
    """Загружает файл, выполняет преобразования и возвращает массив,
    содержащий элементы изображения и ограниченный размерами max_dim_val"""

    max_dim_val = 512
    img = tf.io.read_file(path_to_img)  # загрузка файла
    img = tf.image.decode_image(img, channels=3)    # преобразование в тип uint8
    img = tf.image.convert_image_dtype(img, tf.float32)     # нормализация(стандартизация) признаков
    shape = tf.cast(tf.shape(img)[:-1], tf.float32)     # приведем массив к новому типу
    new_shape = tf.cast(shape * (max_dim_val / max(shape)), tf.int32)
    img = tf.image.resize(img, new_shape)
    img = img[tf.newaxis, :]    # добавим еще одно измерение массиву, что необходимо для обработки
    return img
