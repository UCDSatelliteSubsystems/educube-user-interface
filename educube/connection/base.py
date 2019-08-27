from abc import abstractmethod



class EduCubeInterfaceBase():
    def __init__(self):



    # context manager
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        self.stop()
        return False

    @abstractmethod
    def start(self):
        pass
        
    @abstractmethod
    def stop(self):
        pass

    # server interface
    @abstractmethod
    def handle_command(self, com




