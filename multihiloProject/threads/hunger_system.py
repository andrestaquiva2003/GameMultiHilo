import threading
import time

class HungerSystem(threading.Thread):

    def __init__(self,state):

        super().__init__()

        self.state=state

    def run(self):

        while True:

            with self.state.lock:

                if self.state.hunger > 0:
                    self.state.hunger -= 1

            time.sleep(3)