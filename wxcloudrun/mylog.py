import logging
import threading
from logging.handlers import QueueListener, QueueHandler
from multiprocessing import Queue


class Mylog:
    __instance = None
    __lock = threading.RLock()

    def __init__(self, filename='log.txt', level=logging.INFO, name='mylog'):
        self.log_queue = Queue()
        self.listener = None
        self.logger = None
        self.name = name
        # if filename is None:
        #     current_file_path = os.path.abspath(__file__)
        #     path = os.path.dirname(current_file_path)
        #     filename = os.path.join(path, 'log.txt')
        self.set_log(filename, self.log_queue)
        self.queue_log(level, self.log_queue)

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        with cls.__lock:
            if not cls.__instance:
                cls.__instance = super().__new__(cls)
            return cls.__instance

    def set_log(self, path, queue):
        if not self.listener:
            fh = logging.FileHandler(path, encoding='utf-8')
            fh.setFormatter(logging.Formatter('%(message)s'))
            fh.setLevel(logging.INFO)

            self.listener = QueueListener(queue, fh, respect_handler_level=True)
            self.listener.start()

    def queue_log(self, level, queue):
        if self.logger:
            return

        self.logger = logging.getLogger(self.name)
        self.logger.propagate = False  # 禁用了logger的传递功能，所以logger会自己处理错误
        formatter = logging.Formatter('%(asctime)s -%(levelname)s '
                                      # '%(filename)s:%(lineno)d'
                                      #     '[%(processName)s][%(threadName)s] '
                                      '%(message)s')
        qh = QueueHandler(queue)
        qh.setFormatter(formatter)

        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        ch.setLevel(logging.DEBUG)

        self.logger.setLevel(level)
        self.logger.addHandler(qh)
        self.logger.addHandler(ch)

    def debug(self, msg):
        self.logger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)

    def close(self):
        self.__instance = None
        if self.listener:
            self.listener.stop()


