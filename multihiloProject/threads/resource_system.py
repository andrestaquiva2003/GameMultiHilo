import threading
import random
import time

class ResourceSystem(threading.Thread):

    def __init__(self,state):

        super().__init__()

        self.state=state

    def run(self):

        while True:

            with self.state.lock:

                x=random.randint(50,700)
                y=random.randint(50,500)

                resource=random.choice(
                    ["tree","stone"]
                )

                self.state.resources.append(
                    (x,y,resource)
                )

            time.sleep(5)