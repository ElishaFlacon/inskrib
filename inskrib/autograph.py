import cv2
import numpy as np


class Autograph():
    """

    Класс для получения подписи из документа (pdf, png, jpg, bmp)
        - color_low - нижняя граница hsv цвета, по которому находится цветная печать и подпись, по стандарту [0, 50, 0]
        - color_hight верхняя граница hsv цвета, по которому находится цветная печать и подпись, по стандарту [255, 255, 255]
        - blur - насколько сильно будет размываться изображение, чем сильнее размытие, тем сильнее печать становиться более круглой, что упростит ее нахождение и удаление, по стандарту (3, 3)
        - min_radius - минимальный радиус для удаления окружности (печати), по стандарту 80
        - max_radius - максимальный радиус для удаления окружности (печати), по стандарту 200
        - precent_expansion - увеличение области удаления окружности (печати), чем больше значение, тем более большой круг вырежеться, если 0 - то будет окружность будет вырезана четко по контуру, оставляя небольшие следы из пикселей, по стандарту 0.15
        - pixel_thickness - ширина пикселей, чем больше - тем меньше шанс, что подпись разорвертся, но при этом у выходного изображения будут широкие пиксели
        - size - размер выходного изображения, по стандарту (256, 256)

    """

    def __init__(
            self,
            color_low=[0, 50, 0],
            color_hight=[255, 255, 255],
            blur=(3, 3),
            min_radius=80,
            max_radius=200,
            precent_expansion=0.15,
            pixel_thickness=(3, 3),
            size=(256, 256)
    ) -> None:
        self.__color_low = color_low
        self.__color_hight = color_hight
        self.__blur = blur
        self.__min_radius = min_radius
        self.__max_radius = max_radius
        self.__precent_expansion = precent_expansion
        self.__pixel_thickness = pixel_thickness
        self.__size = size

    def __remove_text(self, picture):
        """
        Метод для очистки документа от текста, оставляя только печать и подпись в заданом диапозоне цветов, по стандарту оставляет синий цвет
            - picture - объект MatLike из opencv

        Возвращает объект MatLike из opencv
        """
        hsv = cv2.cvtColor(picture, cv2.COLOR_BGR2HSV)

        low = np.array(self.__color_low)
        hight = np.array(self.__color_hight)

        mask = cv2.inRange(hsv, low, hight)
        picture = (255 - mask)

        rgb = cv2.cvtColor(picture, cv2.COLOR_RGB2BGR)
        return rgb

    def __remove_print(self, picture):
        """
        Метод для удаления круглой печати
            - picture - объект MatLike из opencv

        Возвращает объект MatLike из opencv
        """
        gray_blurred = cv2.blur(picture, self.__blur)
        detected_circles = cv2.HoughCircles(
            image=gray_blurred,
            method=cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=500,
            param1=50,
            param2=30,
            minRadius=self.__min_radius,
            maxRadius=self.__max_radius
        )

        if detected_circles is None:
            return picture

        detected_circles = np.uint16(np.around(detected_circles))

        first_point = detected_circles[0, :][0]
        a, b, r = first_point[0], first_point[1], first_point[2]

        cv2.circle(
            picture,
            (a, b),
            int(r + (r * self.__precent_expansion)),
            (255, 255, 255),
            -1
        )

        return picture

    def __finishing_lines(self, picture):
        """
        Метод для удаление разрывов на подписи, так как при удалении текста и печать, в некоторых местах она разрывается из-за чего в последствии она обрежеться не корректно
            - picture - объект MatLike из opencv

        Возвращает объект MatLike из opencv
        """
        kernel = np.ones(self.__pixel_thickness, np.uint8)
        # picture = cv2.dilate(picture, kernel, iterations=1)
        picture = cv2.erode(picture, kernel, iterations=1)
        return picture

    def __crop_picture(self, picture):
        """
        Метод для обрезки изображения по контурам подписи
            - picture - объект MatLike из opencv

        Возвращает объект MatLike из opencv
        """
        _, thresh_gray = cv2.threshold(
            picture,
            thresh=100,
            maxval=255,
            type=cv2.THRESH_BINARY_INV
        )

        contours, _ = cv2.findContours(
            thresh_gray,
            cv2.RETR_LIST,
            cv2.CHAIN_APPROX_SIMPLE
        )

        max_box = (0, 0, 0, 0)
        max_area = 0
        for cont in contours:
            x, y, w, h = cv2.boundingRect(cont)
            area = w * h
            if area > max_area:
                max_box = x, y, w, h
                max_area = area
        x, y, w, h = max_box

        crop_picture = picture[y:y+h, x:x+w]
        return crop_picture

    def __resize_picture(self, picture):
        """
        Метод для изменеия размеров изображения
            - picture - объект MatLike из opencv

        Возвращает объект MatLike из opencv
        """
        picture = cv2.resize(picture, self.__size)
        return picture

    def rotate_picture(self, picture, direction: int):
        """
        Метод для переворачивания изображения
            - picture - объект MatLike из opencv
            - direction - rotateCode

        Возвращает объект MatLike из opencv
        """
        picture = cv2.rotate(picture, direction)
        return picture

    def get_clear_autograph(self, path: str):
        """
        Метод для получения готовой, очищенной подписи
            - path - путь к изображению

        Возвращает объект MatLike из opencv
        """
        picture = cv2.imread(path, cv2.IMREAD_COLOR)

        picture = self.__remove_text(picture)

        picture = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY)

        picture = self.__remove_print(picture)
        picture = self.__finishing_lines(picture)
        picture = self.__crop_picture(picture)
        picture = self.__resize_picture(picture)

        return picture
