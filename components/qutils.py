from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

class WorkerSignals(QObject):
    """工作线程的信号"""
    started = pyqtSignal()
    finished = pyqtSignal(object)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)


class AsyncWorker(QObject):
    """异步工作器"""
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self._is_cancelled = False
        
    @pyqtSlot()
    def run(self):
        """在工作线程中运行任务"""
        try:
            self.signals.started.emit()
            result = self.func(self.signals, *self.args, **self.kwargs)
            if not self._is_cancelled:
                self.signals.finished.emit(result)
        except Exception as e:
            if not self._is_cancelled:
                self.signals.error.emit(str(e))
    
    def cancel(self):
        """取消任务"""
        self._is_cancelled = True


class ThreadManager(QObject):
    """线程管理器"""
    
    def __init__(self):
        super().__init__()
        self.threads = []
        self.workers = []
    
    def start_task(self, func, *args, **kwargs):
        """启动异步任务"""
        # 创建工作线程和工作器
        thread = QThread()
        worker = AsyncWorker(func, *args, **kwargs)
        worker.moveToThread(thread)
        
        # 连接信号槽
        thread.started.connect(worker.run)
        worker.signals.finished.connect(thread.quit)
        worker.signals.error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(worker.deleteLater)
        
        # 保存引用
        self.threads.append(thread)
        self.workers.append(worker)
        
        # 清理引用
        thread.finished.connect(lambda: self._cleanup(thread, worker))
        
        # 启动线程
        thread.start()
        # print(f"Started thread {thread} for task {func.__name__}")
        
        return worker.signals
    
    def _cleanup(self, thread, worker):
        """清理线程和工作者"""
        if thread in self.threads:
            self.threads.remove(thread)
        if worker in self.workers:
            self.workers.remove(worker)
        # print(f"Cleaned up thread {thread} and worker {worker}")
    
    def cancel_all(self):
        """取消所有任务"""
        for worker in self.workers:
            worker.cancel()
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)