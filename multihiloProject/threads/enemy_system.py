import threading
import time
import random


class EnemySystem(threading.Thread):

    def __init__(self,state):

        super().__init__()

        self.state=state

    def run(self):

        while True:

            with self.state.lock:

                player=self.state.player

                # Crear enemigos si hay pocos
                if len(self.state.enemies)<3:

                    self.state.enemies.append({

                        "x":random.randint(50,700),
                        "y":random.randint(50,500),
                        "hp":40
                    })

                # Movimiento enemigo
                for enemy in self.state.enemies:

                    if enemy["x"]<player.x:
                        enemy["x"]+=5

                    elif enemy["x"]>player.x:
                        enemy["x"]-=5

                    if enemy["y"]<player.y:
                        enemy["y"]+=5

                    elif enemy["y"]>player.y:
                        enemy["y"]-=5


                    # daño al tocar jugador
                    distance=((enemy["x"]-player.x)**2+
                              (enemy["y"]-player.y)**2)**0.5

                    if distance<30:

                        self.state.health-=5

            time.sleep(.3)