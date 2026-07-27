# game_state.py

import threading

class GameState:

    def __init__(self):

        self.lock=threading.Lock()

        self.health=100
        self.hunger=100
        self.temperature=20

        self.wood=0
        self.stone=0

        self.resources=[]
        self.enemies=[]
        self.campfires=[]

        self.player=None
        self.walls = [

            (200,200),
            (250,200),
            (300,200),

            (500,300),
            (500,350),
            (500,400)

        ]

    def reduce_hunger(self, amount):

        with self.lock:
            self.hunger -= amount

    def add_wood(self, amount):

        with self.lock:
            self.wood += amount

    def get_data(self):

        with self.lock:

            return {
                "health": self.health,
                "hunger": self.hunger,
                "temperature": self.temperature,
                "wood": self.wood,
                "stone": self.stone
            }