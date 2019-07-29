import sys, os, time
from PyQt5 import QtCore, QtWidgets
from application import *
from Arhives_Queue import *
import threading, time
from queue import Queue, Empty, Full

#***************************          ПЕРЕМЕННЫЕ         ********************************************
start_dir = ''                       #
item_count = 0                       #
img_time = 1                         #
file_time = 1                        #
successful_count = 0                 #
queue_count = 1                      #
worker_count = 1                     #
file_count = 0                       #
#***************************          Отдельный поток для интерфейса        *************************
class MyThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(int)
    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.running = False # Флаг выполнения


    def run(self):
        # ***************************          Создание основного цикла программы        *************************
        # Заполняем список папок для заданий
        ScanDir(start_dir)
        ScanFileALL(dir_work)
        # Создаем очередь с заданной длиной 2, это означает что одновременно в очереди могут находиться не более 2ух заданий
        self.queue = Queue(queue_count)
        # Создаем два потока обслуживающих очередь
        self.workers = [Worker(self.queue) for x in range(worker_count)]
        # Создаем "работодателя"
        self.employer = Employer(self.queue)
        self.running = True
        while self.running:         # Проверим значение флага
            self.mysignal.emit(self.getBar())
            self.sleep(1) # Останавливаем процесс что бы не завис интерфейс

    def getBar(self):
        if successful_count != 0:
            self.result = (successful_count * 100) // file_count
            return self.result
        else:
            return 0
#***************************          ИНТЕРФЕЙС          ****************************************
class MainUiClass(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.mythread = MyThread()
        self.ui.statusbar.showMessage('© Бородулин Дмитрий, 2017')
        # ***************************         Кнопки         ****************************************
        self.ui.btnStart.clicked.connect(self.on_start)
        self.ui.btnStop.clicked.connect(self.on_stop)
        self.ui.actionOpen.triggered.connect(self.showDialog)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.btnStart.setEnabled(False)
        # ***************************         Обработка сигналов         ****************************************
        self.mythread.mysignal.connect(self.updateProgressBar, QtCore.Qt.QueuedConnection)

    def on_start(self):
        if not self.mythread.isRunning():
            self.mythread.start()               # Запускаем поток
            self.ui.btnStart.setEnabled(False)

    def on_stop(self):
        self.ui.btnStart.setEnabled(True)
        self.mythread.running = False           # Изменяем флаг выполнения

    def updateProgressBar(self, val):
        self.ui.progressBar.setValue(val)

    def showDialog(self):
        global start_dir
        dirname = QtWidgets.QFileDialog.getExistingDirectory(self, '"Открыть папку"', 'home')
        start_dir = os.path.join(dirname)
        print(start_dir)
        self.ui.btnStart.setEnabled(True)

    def closeEvent(self, e):
        result = QtWidgets.QMessageBox.question(self, "Подтвердите действие", "Вы точно хотите выйти?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
        if result == QtWidgets.QMessageBox.Yes:
            self.hide()                         # Вызывается при закрытии окна
            self.mythread.running = False       # Скрываем окно
            self.mythread.wait(5000)            # Изменяем флаг выполнения
            e.accept()                          # Закрываем окно
        else:
            e.ignore()




#***************************          ЛОГИКА         ********************************************
class Worker(threading.Thread):
    """
    Класс, обслуживающий задачи из очереди.
    """

    def __init__(self, queue):
        super(Worker, self).__init__()

        self.__queue = queue
        # Переменная, указывающая о необходимости завершения работы потока
        self.need_exit = False

        self.setDaemon(True)
        self.start()


    def run(self):
        """
        Основной код здесь
        """
        global successful_count
        # переменная, отображающая состояние работы основного кода потока
        state = 'free'
        # метод run() циклически выполняется до тех пор, пока атрибуту экземпляра класса need_exists не будет присвоено значение True
        while not self.need_exit:
            try:
                # получаем задание из очереди, причем не используем блокировку и устанавливаем таймаут 1 секунда.
                # Это означает, что если в течениеи 1 секунды все запросы на получение задания из очереди провалятся,
                # то будет сгенерировано исключение Queue.Empty, указывающее, что очередь пуста.
                job = self.__queue.get(block=False, timeout=1)

                # Если было получено задание из очереди, то меняется статус работы на busy
                state = 'busy'
                # Выводим информацию о выполняемой задаче и содержимое очереди
                print(u'%s файл %s, в очереди %s' % (self.getName(),
                                                 str(job),
                                                 ','.join(map(str, self.__queue.__dict__['queue']))))
                successful_count += 1
                s, a, m, c = stat(job)
                # Тест на времея выполениния задания
                with Profiler() as p:
                    # архивируем задание из очереди
                    if suffix_img(job):  # проверим изображение или нет
                        if s >= 1048576:
                            if zip_img(job): #Если да то обрезаем
                                try:

                                    os.remove(job)
                                except Exception as e:  # при ошибке ввода/вывода
                                    print('Ошибка:\n', traceback.format_exc())
                        else:
                            path, _filename = os.path.split(job)
                            basename, extension = os.path.splitext(_filename)
                            suf = Path(job).suffix
                            outfile = os.path.splitext(path + "\\" + basename)[0] + "_zip" + extension  # новое имя файла = старое имя без расширения + '_zip.jpg'
                            if job != outfile:  # если эти имена не совпадают
                                try:  # попытаться
                                    img = Image.open(job)  # открыть файл для чтения
                                    img.save(outfile)  # сохранить в новом файле
                                    try:

                                        os.remove(job)
                                    except Exception as e:  # при ошибке ввода/вывода
                                        print('Ошибка:\n', traceback.format_exc())
                                except Exception as e:  # при ошибке ввода/вывода
                                    print('Ошибка:\n', traceback.format_exc())

                    else: # если нет архивируем
                        if zip_popen(job):
                            try:
                                #os.remove(job)
                                total_seconds(job+".7z", m)
                            except Exception as e:  # при ошибке ввода/вывода
                                print('Ошибка:\n', traceback.format_exc())
            except Empty:
                # Чтобы не засорять вывод ненужной информацией выводим состояние работы только после его смены
                if state != 'free':
                    print(u'%s пуст' % self.getName())
                # Меняем статус работы на free
                state = 'free'
                # засыпаем на долю секунды, что бы не загружать процессор
                time.sleep(0.1)

class Employer(threading.Thread):
    """
    Класс, выдающий задания очереди.
    """

    def __init__(self, queue):
        super(Employer, self).__init__()

        self.__queue = queue

        self.setDaemon(True)
        self.start()

    def execute(self, dir):
        global item_count
        # Переменная, отображающая состояние очереди
        state = 'full'

        names = os.listdir(dir)  # список файлов и поддиректорий в данной директории


        # В роли заданий для очереди будут выступать файлы в выбранной директории
        for self.name in names:
            fullname = os.path.join(dir, self.name)  # получаем полное имя
            if os.path.isfile(fullname):  # если это файл...
                s, a, m, c = stat(fullname)
                period = date_time - m
                if suffix_img(fullname):  # Отправляем на задание только изображения
                    if period.days >= img_time: # старый ли файл 1078 - 3 года
                        while True:
                            try:
                                # Помещаем задание в очередь, при этом не используем блокировку и устанавливаем таймаут операции в 1 сек.
                                # Это означает, что если в течение 1 секунды все попытки поместить задание в очередь окажутся неудачными,
                                # то будет сгенерировано исключение Queue.Full, указывающее что очередь полная.
                                self.__queue.put(fullname, block=False, timeout=1)
                                # Если предыдущая операция завершилась успешно,то меняем состояние работы на 'avaiable'
                                state = 'available'
                                print('Отправить в работу:', fullname)

                                # Делаем небольшой перерыв между отправкой следующего задания в очередь
                                time.sleep(0.1)
                                # Выходим из цикла while и переходим на следующую итерацию цикла for
                                break
                            except Full:
                                # Чтобы не засорять вывод ненужной информацией выводим состояние очереди только после его смены
                                if state != 'full':
                                    print(u'Очереди заполнена, в очереди %s' % ','.join(map(str, self.__queue.__dict__['queue'])))
                                # Меняем состояние очереди на full
                                state = 'full'
                                # Делаем задержку перед очередной попыткой отправить задание в очередь
                                time.sleep(1)
                    else:
                        pass
                elif not suffix_file(fullname):  # проверим надо ли архивировать
                    if period.days >= file_time: # старый ли файл 1078 - 3 года
                        while True:
                            try:
                                # Помещаем задание в очередь, при этом не используем блокировку и устанавливаем таймаут операции в 1 сек.
                                # Это означает, что если в течение 1 секунды все попытки поместить задание в очередь окажутся неудачными,
                                # то будет сгенерировано исключение Queue.Full, указывающее что очередь полная.
                                self.__queue.put(fullname, block=False, timeout=1)
                                # Если предыдущая операция завершилась успешно,то меняем состояние работы на 'avaiable'
                                state = 'available'
                                print('Отправить в работу:', fullname)

                                # Делаем небольшой перерыв между отправкой следующего задания в очередь
                                time.sleep(0.1)
                                # Выходим из цикла while и переходим на следующую итерацию цикла for
                                break
                            except Full:
                                # Чтобы не засорять вывод ненужной информацией выводим состояние очереди только после его смены
                                if state != 'full':
                                    print(u'Очереди заполнена, в очереди %s' % ','.join(map(str, self.__queue.__dict__['queue'])))
                                # Меняем состояние очереди на full
                                state = 'full'
                                # Делаем задержку перед очередной попыткой отправить задание в очередь
                                time.sleep(1)
                    else:
                        pass
                else:
                    pass

    def run(self):
        # Реализуем первую партию заданий
        for dir in dir_work:
            self.execute(dir)
            # Выжидаем 1 секунду что бы потоки обслужили всю очередь
            #time.sleep(1)

class Profiler(object):
    def __enter__(self):
        self._startTime = time.time()

    def __exit__(self, type, value, traceback):
        print("Прошедшее время: {:.3f} sec".format(time.time() - self._startTime))
# Считаем количество файлов
def ScanFileALL(dir_root):
    global file_count
    for dir in dir_root:
        names = os.listdir(dir)  # список файлов и поддиректорий в данной директории
        for name in names:
            fullname = os.path.join(dir, name)  # получаем полное имя
            if os.path.isfile(fullname):  # если это файл...
                s, a, m, c = stat(fullname)
                period = date_time - m
                if not suffix_file(fullname):  # проверим надо ли архивировать
                    if period.days >= file_time:  # старый ли файл
                        file_count += 1
                    else:
                        pass
                else:
                    pass

# Back up the reference to the exceptionhook
sys._excepthook = sys.excepthook

def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)

# Set the exception hook to our wrapping function
sys.excepthook = my_exception_hook
#***************************          СТАРТ          ********************************************
if __name__ == '__main__':

    try:
        app = QtWidgets.QApplication(sys.argv)
        window = MainUiClass()
        window.show()
        sys.exit(app.exec_())
    except:
        print("Exiting")