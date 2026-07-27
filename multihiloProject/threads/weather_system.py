import threading
import time

# La temperatura ya no es aleatoria: baja sola con el tiempo, como en
# Starve.io, y solo sube si el jugador está cerca de una fogata prendida.
WARMTH_RADIUS = 90
MIN_TEMP = -10
MAX_TEMP = 35
COLD_DAMAGE_THRESHOLD = -5


class WeatherSystem(threading.Thread):

    def __init__(self,state):

        super().__init__()

        self.state=state

    def run(self):

        while True:

            with self.state.lock:

                player = self.state.player

                near_fire = False

                if player is not None:

                    for fire in self.state.campfires:

                        distance = ((player.x - fire["x"]) ** 2 +
                                    (player.y - fire["y"]) ** 2) ** 0.5

                        if distance < WARMTH_RADIUS:
                            near_fire = True
                            break

                if near_fire:
                    self.state.temperature = min(MAX_TEMP, self.state.temperature + 4)
                else:
                    self.state.temperature = max(MIN_TEMP, self.state.temperature - 2)

                # el frío extremo sin fogata también daña la vida
                if self.state.temperature <= COLD_DAMAGE_THRESHOLD and self.state.health > 0:
                    self.state.health = max(0, self.state.health - 3)

            time.sleep(3)