# -*- coding: utf-8 -*-
import sys, os
import subprocess, time
from datetime import timedelta, datetime
from pathlib import Path
import logging
import main
from PIL import Image, PdfImagePlugin # модуль PIL - для обработки изображений
import traceback

zip = '7z\\7za.exe'
dir_work = []
MiB = 1024 * 1024
limit = (int(sys.argv[1]) if len(sys.argv) > 1 else 20) * MiB
list_suffix = ['.7z', '.zip', '.rar', '.gz', '.gzip', '.log']
list_suffix_img = ['.jpg', '.png', '.bmp', '.tiff', '.gif', '.JPG', '.PNG', '.BMP', '.TIFF', '.GIF']
date_time = datetime.now()
#file_count = 0

#logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG)


def utime(file, times):
    os.utime(file, times)
    return file

def total_seconds(filename, m):
    try:
        epoch = datetime.utcfromtimestamp(0)
        delta = datetime.now() - epoch
        time_delta = datetime.now() - m
        total_second = (delta.total_seconds() - time_delta.total_seconds()) - 10800
        utime(filename, (total_second, total_second))
    except Exception as e:  # при ошибке ввода/вывода
        print('Ошибка:\n', traceback.format_exc())
        return False
    return True

def stat(filename):
    stat = os.stat(filename)
    try:
        s = datetime.fromtimestamp(stat.st_size)  # размер файла в байтах
    except OSError:
        print("Ошибка: Invalid argument")
    try:
        a = datetime.fromtimestamp(stat.st_atime)  # время самого последнего доступа.
    except OSError:
        print("Ошибка: Invalid argument")
    try:
        m = datetime.fromtimestamp(stat.st_mtime)  # время самого последнего контента модификации.
    except OSError:
        print("Ошибка: Invalid argument")
    try:
        c = datetime.fromtimestamp(stat.st_ctime)  # время последнего изменения метаданных.
    except OSError:
        print("Ошибка: Invalid argument")
    return s, a, m, c

# Сканировать папки
def ScanDir(dir):
    if dir != '':
        logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG,
                            filename=dir + '\\arhive_' + date_time.strftime("%d-%m-%Y") + '.log',
                            filemode='w')
    global dir_work
    for root, dirs, files in os.walk(dir):
        # print(root)
        dir_work.append(root)
    return dir_work

# Смотрим есть ли исключения расширений
def suffix_file(filename):
    for i in list_suffix:
        if Path(filename).suffix == i:
            return True
    return False

# Смотрим есть ли изображения
def suffix_img(filename):
    for i in list_suffix_img:
        if Path(filename).suffix == i:
            return True
    return False

# Архивируем файл в потоке
def zip_popen(filename):
    args = [zip, "a", "-tzip", "-ssw", "-mx7", filename+".7z", filename]
    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    data = process.communicate()
    code = process.wait()
    if code == 0:
        # Сообщение информационное
        logging.info(u'- Файл: ' + filename + ' архивирован ')
    else:
        # Сообщение ошибки
        logging.error(u'This is an error message:' + filename)
        return False
    return True

# Обрезаем изображения
def zip_img(filename):
    path, _filename = os.path.split(filename)
    basename, extension = os.path.splitext(_filename)
    basewidth = 1920
    suf = Path(filename).suffix
    outfile = os.path.splitext(path + "\\" + basename)[0] + "_zip" + extension # новое имя файла = старое имя без расширения + '_zip.jpg'
    if filename != outfile: # если эти имена не совпадают
        try:  # попытаться
            img = Image.open(filename)  # открыть файл для чтения
            '''
            if suf == ".pdf" or ".PDF":
                PdfImagePlugin
                img.info['dpi']
                img.save(outfile, dpi=(200, 200))
            else:
            '''
            ratio = (basewidth / float(img.size[0]))
            height = int((float(img.size[1]) * float(ratio)))
            img = img.resize((basewidth, height), Image.ANTIALIAS)
            img.save(outfile)  # сохранить в новом файле

            # Сообщение информационное
            logging.info(u'- Файл: ' + filename + ' обрезан ')
        except Exception as e:  # при ошибке ввода/вывода
            print('Ошибка:\n', traceback.format_exc())
            return False
    return True

