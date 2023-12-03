import os
import cv2
import fitz
import shutil
import unidecode

from inskrib.autograph import Autograph
from inskrib.utils import ProgressBar


class Document():
    """

    Класс для обработки большого количества документов 
        - result_path - путь для сохранения всех обработанных файлов, по стандарту 'result',
        - result_autographs - путь для сохранения готовых подписей, по стандарту "result/autographs",
        - result_persons - путь для сохранения индексированных людей которым принадлежит подпись, по стандарту "result/persons.csv",
        - result_filenames - путь для сохранения, по стандарту "result/filenames.csv",
        - result_temp - путь для сохранения временных файлов, по стандарту "result/temp",
        - output_picture_type - формат сохранения файлов, по стандарту "png",
        - grouping - будут ли подписи группироваться по человеку, по стандарту False

    """

    def __init__(
        self,
        result_path='result',
        result_autographs="result/autographs",
        result_persons="result/persons.csv",
        result_filenames="result/filenames.csv",
        result_temp="result/temp",
        output_picture_type="png",
        grouping: bool = False
    ) -> None:
        self.__result_path = result_path
        self.__result_autographs = result_autographs
        self.__result_persons = result_persons
        self.__result_filenames = result_filenames
        self.__result_temp = result_temp
        self.__output_picture_type = output_picture_type
        self.__grouping = grouping

    def __create_storage(self) -> None:
        """
        Метод для создания всех нужных директорий
        """
        if not os.path.exists(self.__result_path):
            os.mkdir(self.__result_path)
        if not os.path.exists(self.__result_autographs):
            os.mkdir(self.__result_autographs)
        if not os.path.exists(self.__result_temp):
            os.mkdir(self.__result_temp)

        open(self.__result_filenames, "w")
        open(self.__result_persons, "w")

    def __write_new_person(self, person: str) -> None:
        """
        Метод для записи всех людей в отдельный csv файл
            - person - имя человека
        """
        with open(self.__result_persons, 'a') as file:
            file.write(f'{person}\n')

    def __write_new_filename(self, filename: str) -> None:
        """
        Метод для записи имен файлов всех сохраненных подписей в отдельный csv файл
            - filename - имя файла
        """
        with open(self.__result_filenames, 'a') as file:
            file.write(f'{filename}\n')

    def __get_person_name(self, dirpath: str) -> str:
        """
        Метод для получения имени человека в транслите
            - dirpath - полный путь до директории этого человека

        Возвращает строку с обработанным именем
        """
        person = dirpath.split('\\').pop()
        person = unidecode.unidecode(person)
        return person

    def __pdf_to_image(self, path_to_file: str, path_to_save: str):
        """
        Метод для перевода pdf файла в изображение
            - path_to_file - путь до pdf файла
            - path_to_save - пусть для сохранения готового изображения
        """
        with fitz.open(path_to_file) as pdf:
            page = pdf.load_page(0)
            pix = page.get_pixmap()
            pix.save(path_to_save)

    def __save_temp_file(self, dirpath: str, filename: str, person: str, id: str, index: str) -> None:
        """
        Метод для перевода pdf файла в изображение
            - dirpath - олный путь до директории этого человека 
            - filename - имя файла
            - person - имя человека
            - id - индетификатор человека
            - index - порядковый номер файла
        """
        splited_filename = filename.split('.')

        path_to_file = f'{dirpath}/{filename}'
        new_file_name = f'{id}-{person}-{index}.{self.__output_picture_type}'
        path_to_save = f'{self.__result_temp}/{new_file_name}'

        if (splited_filename.pop() == 'pdf'):
            self.__pdf_to_image(path_to_file, path_to_save)
            return

        shutil.copyfile(path_to_file, path_to_save)

    def __save_authograph(self, path, picture) -> None:
        """
        Метод для сохранения подписи
            - path - путь сохранения подписи
            - picture - изображение в виде MatLike из opencv
        """
        cv2.imwrite(path, picture)

    def __process_temp(self, path: str) -> None:
        """
        Метод для первоначальной обработки документов
            - path - путь до директории с документами, которые нужно обработать
        """
        prefix = 'Process Temp Files:'
        length = len(os.listdir(path)) - 2
        ProgressBar.print(0, length, prefix)

        id = 0
        for dirpath, _, filenames in os.walk(path):
            person = self.__get_person_name(dirpath)

            if (person == path):
                continue

            grouping_path = f'{self.__result_autographs}/{person}'
            if self.__grouping and not os.path.exists(grouping_path):
                os.mkdir(grouping_path)

            index = 0
            for filename in filenames:
                self.__save_temp_file(dirpath, filename, person, id, index)
                index += 1

            id += 1
            ProgressBar.print(id, length, prefix)

    def __process_authographs(self, autograph: Autograph) -> None:
        """
        Метод для получения подписей из всех документов
            - autograph - инстанс класса inskrib.Autograph
        """
        prefix = 'Process Authograph:'
        length = len(os.listdir(self.__result_temp))
        ProgressBar.print(0, length, prefix)

        index = 0
        current_person = ""
        for picture in os.listdir(self.__result_temp):
            path_to_save = f'{self.__result_autographs}/{picture}'
            path_to_picture = f'{self.__result_temp}/{picture}'

            id = picture.split('-')[0]
            person = picture.split('-')[1]

            if (self.__grouping):
                path_to_save = f'{self.__result_autographs}/{person}/{picture}'

            if (current_person != person):
                current_person = person
                self.__write_new_person(f'{person},{id}')

            try:
                ath = autograph.get_clear_autograph(path_to_picture)
                self.__save_authograph(path_to_save, ath)
                self.__write_new_filename(f'{picture},{id}')
            except Exception:
                pass

            index += 1
            ProgressBar.print(index, length, prefix)

    def __remove_temp(self) -> None:
        """
        Метод для удаления temp (временной) директории
        """
        shutil.rmtree(self.__result_temp)

    def set_grouping(self, grouping_type: bool) -> None:
        """
        Метод для изменения состояния у переменной __grouping
        """
        self.__grouping = grouping_type

    def get_authoraphs(self, path: str, autograph: Autograph, remove_temp: bool = True) -> None:
        """
        Метод для получения готовых подписей и csv файлов из документов
            - path - путь до директории с документами
            - autograph - инстанс класса inskrib.Autograph
            - remove_temp - отвечает за удаление temp (временной) директории, по стандарту True 
        """
        self.__create_storage()
        self.__process_temp(path)
        self.__process_authographs(autograph)

        if remove_temp:
            self.__remove_temp()
            print('Temp Directory Removed')
