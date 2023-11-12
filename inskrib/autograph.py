import cv2
import numpy as np


class Autograph():
    """

    ПОЗЖЕ НАПИСАТЬ ДОКУ

    """

    def __init__(
            self,
            color_low=[0, 50, 0],
            color_hight=[255, 255, 255],
            blur=(3, 3),
            min_radius=80,
            max_radius=200,
            precent_expansion=0.15,
            size=(256, 256)
    ) -> None:
        self.__color_low = color_low
        self.__color_hight = color_hight
        self.__blur = blur
        self.__min_radius = min_radius
        self.__max_radius = max_radius
        self.__precent_expansion = precent_expansion
        self.__size = size

    def __remove_text(self, picture):
        hsv = cv2.cvtColor(picture, cv2.COLOR_BGR2HSV)

        low = np.array(self.__color_low)
        hight = np.array(self.__color_hight)

        mask = cv2.inRange(hsv, low, hight)
        picture = (255 - mask)

        rgb = cv2.cvtColor(picture, cv2.COLOR_RGB2BGR)
        return rgb

    def __remove_print(self, picture):
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
        kernel = np.ones((3, 3), np.uint8)
        picture = cv2.erode(picture, kernel, iterations=3)
        return picture

    def __crop_picture(self, picture):
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
        picture = cv2.resize(picture, self.__size)
        return picture

    def rotate_picture(self, picture, direction: int):
        picture = cv2.rotate(picture, direction)
        return picture

    def get_clear_autograph(self, path: str):
        picture = cv2.imread(path, cv2.IMREAD_COLOR)

        picture = self.__remove_text(picture)

        picture = cv2.cvtColor(picture, cv2.COLOR_BGR2GRAY)

        picture = self.__remove_print(picture)
        picture = self.__finishing_lines(picture)
        picture = self.__crop_picture(picture)
        picture = self.__resize_picture(picture)

        return picture
