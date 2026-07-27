import threading
import queue
from playsound import playsound


class SoundSystem(threading.Thread):

    def __init__(self):

        super().__init__()

        self.queue = queue.Queue()

    def play(self,sound):

        self.queue.put(sound)

    def run(self):

        while True:

            sound=self.queue.get()

            try:
                playsound(sound)
            except Exception:
                pass