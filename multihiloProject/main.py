import tkinter as tk

from game_state import GameState

from player.player import Player

from ui.game_window import GameWindow

from threads.hunger_system import HungerSystem
from threads.weather_system import WeatherSystem
from threads.resource_system import ResourceSystem
from threads.sound_system import SoundSystem
from threads.enemy_system import EnemySystem


state=GameState()

state.player=Player()
sound=SoundSystem()

state.sound=sound

hunger=HungerSystem(state)
weather=WeatherSystem(state)
resources=ResourceSystem(state)
enemy=EnemySystem(state)

hunger.start()
weather.start()
resources.start()
enemy.start()
sound.start()

root=tk.Tk()

root.title("Survival Threads - Simulación Multihilo")
root.configure(bg="#0d0d0d")
root.resizable(False, False)

window=GameWindow(
    root,
    state
)

root.mainloop()