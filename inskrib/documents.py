import os
import cv2
import fitz
import shutil
import unidecode
from inskrib.utils import ProgressBar


class Document():
    """

    ПОЗЖЕ НАПИСАТЬ ДОКУ

    """

    def __init__(
        self,
        result_path='result',
        result_autographs="result/autographs",
        result_persons="result/persons.csv",
        result_filenames="result/filenames.csv",
        result_temp="result/temp",
        output_picture_type="png"
    ) -> None:
        self.__result_path = result_path
        self.__result_autographs = result_autographs
        self.__result_persons = result_persons
        self.__result_filenames = result_filenames
        self.__result_temp = result_temp
        self.__output_picture_type = output_picture_type

    def __create_storage(self) -> None:
        if not os.path.exists(self.__result_path):
            os.mkdir(self.__result_path)
        if not os.path.exists(self.__result_autographs):
            os.mkdir(self.__result_autographs)
        if not os.path.exists(self.__result_temp):
            os.mkdir(self.__result_temp)

        open(self.__result_filenames, "w")
        open(self.__result_persons, "w")

    # write id into persons.txt, one id for one person
    def __write_new_person(self, person: str) -> None:
        with open(self.__result_persons, 'a') as file:
            file.write(f'{person}\n')

    # write filename into indexed.csv
    def __write_new_filename(self, string: str) -> None:
        with open(self.__result_filenames, 'a') as file:
            file.write(f'{string}\n')

    def __get_person_name(self, dirpath) -> str:
        person = dirpath.split('\\').pop()
        person = unidecode.unidecode(person)
        return person

    def __pdf_to_image(self, path_to_file, path_to_save):
        with fitz.open(path_to_file) as pdf:
            page = pdf.load_page(0)
            pix = page.get_pixmap()
            pix.save(path_to_save)

    def __save_temp_file(self, dirpath, filename, person, id, index) -> None:
        splited_filename = filename.split('.')

        path_to_file = f'{dirpath}/{filename}'
        new_file_name = f'{id}-{person}-{index}.{self.__output_picture_type}'
        path_to_save = f'{self.__result_temp}/{new_file_name}'

        if (splited_filename.pop() == 'pdf'):
            self.__pdf_to_image(path_to_file, path_to_save)
            return

        shutil.copyfile(path_to_file, path_to_save)

    def __save_authograph(self, path, picture) -> None:
        cv2.imwrite(path, picture)

    def __process_temp(self, path: str) -> str:
        prefix = 'Process Temp Files:'
        length = len(os.listdir(path)) - 2
        ProgressBar.print(0, length, prefix)

        id = 0
        for dirpath, _, filenames in os.walk(path):
            person = self.__get_person_name(dirpath)
            if (person == path):
                continue

            self.__write_new_person(f'{person},{id}')

            index = 0
            for filename in filenames:
                self.__save_temp_file(dirpath, filename, person, id, index)
                index += 1

            id += 1
            ProgressBar.print(id, length, prefix)

    def __process_authograph(self, autograph) -> None:
        prefix = 'Process Authograph:'
        length = len(os.listdir(self.__result_temp))
        ProgressBar.print(0, length, prefix)

        index = 0
        for picture in os.listdir(self.__result_temp):
            path_to_save = f'{self.__result_autographs}/{picture}'
            path_to_picture = f'{self.__result_temp}/{picture}'

            id = picture.split('-')[0]

            try:
                ath = autograph.get_clear_autograph(path_to_picture)
                self.__save_authograph(path_to_save, ath)
                self.__write_new_filename(f'{picture},{id}')
            except Exception:
                pass

            index += 1
            ProgressBar.print(index, length, prefix)

    def __remove_temp(self) -> None:
        shutil.rmtree(self.__result_temp)

    def get_authoraphs(self, path: str, autograph, remove_temp: bool = True) -> None:
        self.__create_storage()
        self.__process_temp(path)
        self.__process_authograph(autograph)

        if remove_temp:
            self.__remove_temp()
            print('Temp Directory Removed')
