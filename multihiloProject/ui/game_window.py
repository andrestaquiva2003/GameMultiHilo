import tkinter as tk
import math
import random

from threads.weather_system import WARMTH_RADIUS


# Paleta "survival"
COLOR_GRASS_A = "#4f7a30"
COLOR_GRASS_B = "#456b28"
COLOR_DIRT = "#6b4d30"
COLOR_WORLD_BORDER = "#2b3a1a"

COLOR_ROCK_BASE = "#7d7d7d"
COLOR_ROCK_LIGHT = "#9a9a9a"
COLOR_ROCK_OUTLINE = "#3f3f3f"

COLOR_HUD_BG = "#141414"
COLOR_HUD_BORDER = "#5a5a5a"

COLOR_HEALTH = "#e74c3c"
COLOR_HUNGER = "#e6912b"
COLOR_WOOD = "#a9784b"
COLOR_STONE = "#b0b0b0"
COLOR_ENEMY = "#ff4747"
COLOR_BAR_BG = "#2c2c2c"
COLOR_BAR_BORDER = "#0a0a0a"
COLOR_SWORD_ON = "#7be08a"
COLOR_SWORD_OFF = "#7a7a7a"

FONT_HUD = ("Consolas", 12, "bold")
FONT_HUD_SMALL = ("Consolas", 10)

# recetas de crafteo (madera, piedra)
CAMPFIRE_COST = (5, 5)
SWORD_COST = (3, 2)

ATTACK_RANGE = 55
FIST_DAMAGE = 8
SWORD_DAMAGE = 25


class GameWindow:

    def __init__(self, root, state):

        self.root = root
        self.state = state

        self.width = 800
        self.height = 600

        self.canvas = tk.Canvas(
            root,
            width=self.width,
            height=self.height,
            bg=COLOR_GRASS_A,
            highlightthickness=0
        )

        self.canvas.pack()

        # Cargar GIF del personaje
        self.frames = []

        i = 0

        while True:

            try:

                frame = tk.PhotoImage(
                    file="images/player.gif",
                    format=f"gif -index {i}"
                )

                frame = frame.subsample(3, 3)

                self.frames.append(frame)

                i += 1

            except Exception:
                break

        self.current_frame = 0

        # Estado visual auxiliar (no interfiere con los hilos)
        self.prev_health = state.health
        self.damage_flash = 0
        self.message = ""
        self.message_timer = 0

        self._draw_static_background()

        self.animate_player()

        root.bind("<Key>", self.controls)

        self.update_ui()

    # ------------------------------------------------------------------
    # Fondo estático (tiles de pasto + tierra + paredes), se dibuja una
    # sola vez para no repintar cientos de rectángulos cada frame.
    # ------------------------------------------------------------------
    def _draw_static_background(self):

        rng = random.Random(42)

        tile = 40

        for gy in range(0, self.height, tile):

            for gx in range(0, self.width, tile):

                checker = ((gx // tile) + (gy // tile)) % 2
                color = COLOR_GRASS_A if checker == 0 else COLOR_GRASS_B

                if rng.random() < 0.06:
                    color = COLOR_DIRT

                self.canvas.create_rectangle(
                    gx, gy, gx + tile, gy + tile,
                    fill=color, outline="", tags="bg"
                )

                # brizna de pasto decorativa
                if color != COLOR_DIRT and rng.random() < 0.35:

                    bx = gx + rng.randint(6, tile - 6)
                    by = gy + rng.randint(6, tile - 6)

                    self.canvas.create_line(
                        bx, by, bx, by - 5,
                        fill="#3a5c22", width=2, tags="bg"
                    )

        # borde del mundo
        self.canvas.create_rectangle(
            2, 2, self.width - 2, self.height - 2,
            outline=COLOR_WORLD_BORDER, width=4, tags="bg"
        )

        self._draw_walls()

    def _draw_walls(self):

        for x, y in self.state.walls:

            # sombra
            self.canvas.create_rectangle(
                x + 4, y + 4, x + 44, y + 44,
                fill="#000000", stipple="gray50", outline="", tags="bg"
            )

            self.canvas.create_rectangle(
                x, y, x + 40, y + 40,
                fill=COLOR_ROCK_BASE, outline=COLOR_ROCK_OUTLINE,
                width=2, tags="bg"
            )

            self.canvas.create_rectangle(
                x + 4, y + 4, x + 20, y + 18,
                fill=COLOR_ROCK_LIGHT, outline="", tags="bg"
            )

    # ------------------------------------------------------------------
    # Helpers de dibujo reutilizables
    # ------------------------------------------------------------------
    def _rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):

        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]

        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _outlined_text(self, x, y, text, font, fill, outline="#000000"):

        for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)):

            self.canvas.create_text(
                x + dx, y + dy, text=text, font=font,
                fill=outline, tags="dynamic"
            )

        self.canvas.create_text(x, y, text=text, font=font, fill=fill, tags="dynamic")

    def _bar(self, x, y, w, h, pct, color):

        pct = max(0.0, min(1.0, pct))

        self.canvas.create_rectangle(
            x, y, x + w, y + h,
            fill=COLOR_BAR_BG, outline=COLOR_BAR_BORDER, tags="dynamic"
        )

        fill_w = int(w * pct)

        if fill_w > 0:

            self.canvas.create_rectangle(
                x, y, x + fill_w, y + h,
                fill=color, outline="", tags="dynamic"
            )

        self.canvas.create_rectangle(
            x, y, x + w, y + h,
            outline=COLOR_BAR_BORDER, tags="dynamic"
        )

    # ------------------------------------------------------------------
    # Iconos vectoriales (Tk en Windows no renderiza emojis a color en
    # el Canvas, así que todos los iconos se dibujan con formas nativas)
    # ------------------------------------------------------------------
    def _icon_heart(self, cx, cy, r, color, tag="dynamic"):

        self.canvas.create_oval(
            cx - r, cy - r * 0.7, cx, cy + r * 0.2,
            fill=color, outline="#5a0f0f", tags=tag
        )

        self.canvas.create_oval(
            cx, cy - r * 0.7, cx + r, cy + r * 0.2,
            fill=color, outline="#5a0f0f", tags=tag
        )

        self.canvas.create_polygon(
            cx - r, cy - r * 0.15,
            cx + r, cy - r * 0.15,
            cx, cy + r,
            fill=color, outline="#5a0f0f", smooth=False, tags=tag
        )

    def _icon_apple(self, cx, cy, r, color, tag="dynamic"):

        self.canvas.create_line(
            cx, cy - r, cx + r * 0.5, cy - r * 1.6,
            fill="#5a3a1a", width=2, tags=tag
        )

        self.canvas.create_polygon(
            cx + r * 0.5, cy - r * 1.6,
            cx + r * 1.3, cy - r * 1.5,
            cx + r * 0.6, cy - r * 1.0,
            fill="#3a8c3a", outline="", tags=tag
        )

        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=color, outline="#7a3d0f", width=1, tags=tag
        )

    def _icon_thermometer(self, cx, cy, r, pct, color, tag="dynamic"):

        tube_w = r * 0.55
        top = cy - r * 1.4
        bottom = cy + r * 0.6

        self._rounded_rect(
            cx - tube_w, top, cx + tube_w, bottom,
            radius=tube_w, fill="#2c2c2c", outline="#888888", width=1, tags=tag
        )

        fill_top = bottom - (bottom - top) * max(0.08, min(1.0, pct))

        self._rounded_rect(
            cx - tube_w + 2, fill_top, cx + tube_w - 2, bottom - 2,
            radius=tube_w - 2, fill=color, outline="", tags=tag
        )

        self.canvas.create_oval(
            cx - r * 0.75, cy + r * 0.1, cx + r * 0.75, cy + r * 1.5,
            fill=color, outline="#888888", width=1, tags=tag
        )

    def _icon_wood(self, cx, cy, s, tag="dynamic"):

        self.canvas.create_rectangle(
            cx - s, cy - s * 0.45, cx + s, cy + s * 0.45,
            fill="#8a5a30", outline="#4a2f18", tags=tag
        )

        for ex in (cx - s, cx + s):

            self.canvas.create_oval(
                ex - s * 0.28, cy - s * 0.45, ex + s * 0.28, cy + s * 0.45,
                fill="#c99a63", outline="#4a2f18", tags=tag
            )

    def _icon_stone(self, cx, cy, s, tag="dynamic"):

        self.canvas.create_polygon(
            cx - s, cy + s * 0.3,
            cx - s * 0.5, cy - s * 0.7,
            cx + s * 0.4, cy - s * 0.8,
            cx + s, cy - s * 0.1,
            cx + s * 0.6, cy + s * 0.7,
            cx - s * 0.4, cy + s * 0.8,
            fill=COLOR_STONE, outline="#5a5a5a", tags=tag
        )

    def _icon_skull(self, cx, cy, s, tag="dynamic"):

        self.canvas.create_oval(
            cx - s, cy - s, cx + s, cy + s * 0.6,
            fill="#e0e0e0", outline="#6b0f0f", width=1, tags=tag
        )

        self.canvas.create_oval(cx - s * 0.5, cy - s * 0.1, cx - s * 0.1, cy + s * 0.3, fill="#6b0f0f", outline="", tags=tag)
        self.canvas.create_oval(cx + s * 0.1, cy - s * 0.1, cx + s * 0.5, cy + s * 0.3, fill="#6b0f0f", outline="", tags=tag)

    def _icon_tree(self, x, y, tag="dynamic"):

        self.canvas.create_rectangle(
            x - 5, y + 2, x + 5, y + 20,
            fill="#6b4423", outline="#3a2412", tags=tag
        )

        self.canvas.create_oval(x - 20, y - 26, x + 4, y + 2, fill="#2f5c22", outline="#1f3d16", tags=tag)
        self.canvas.create_oval(x - 4, y - 30, x + 22, y - 2, fill="#356b27", outline="#1f3d16", tags=tag)
        self.canvas.create_oval(x - 14, y - 34, x + 12, y - 8, fill="#3f7c2e", outline="#1f3d16", tags=tag)
        self.canvas.create_oval(x - 6, y - 30, x + 2, y - 22, fill="#5aa63f", outline="", tags=tag)

    def _icon_rock_node(self, x, y, tag="dynamic"):

        self.canvas.create_polygon(
            x - 18, y + 8,
            x - 10, y - 12,
            x + 4, y - 18,
            x + 18, y - 8,
            x + 16, y + 10,
            x + 2, y + 18,
            x - 12, y + 16,
            fill=COLOR_ROCK_BASE, outline=COLOR_ROCK_OUTLINE, width=2, tags=tag
        )

        self.canvas.create_polygon(
            x - 10, y - 6, x - 2, y - 12, x + 4, y - 6,
            fill=COLOR_ROCK_LIGHT, outline="", tags=tag
        )

    def _icon_slime(self, x, y, tag="dynamic"):

        self.canvas.create_polygon(
            x - 18, y + 16,
            x - 20, y,
            x - 12, y - 16,
            x, y - 20,
            x + 12, y - 16,
            x + 20, y,
            x + 18, y + 16,
            x + 10, y + 20,
            x - 10, y + 20,
            fill="#8b1a1a", outline="#3a0808", width=2, smooth=True, tags=tag
        )

        self.canvas.create_oval(x - 10, y - 4, x - 2, y + 4, fill="#ffffff", outline="", tags=tag)
        self.canvas.create_oval(x + 2, y - 4, x + 10, y + 4, fill="#ffffff", outline="", tags=tag)
        self.canvas.create_oval(x - 8, y - 2, x - 4, y + 2, fill="#000000", outline="", tags=tag)
        self.canvas.create_oval(x + 4, y - 2, x + 8, y + 2, fill="#000000", outline="", tags=tag)

    def _icon_campfire(self, x, y, tag="dynamic"):

        self.canvas.create_line(x - 16, y + 10, x + 16, y + 2, fill="#5a3a1a", width=6, tags=tag)
        self.canvas.create_line(x - 16, y + 2, x + 16, y + 10, fill="#6b4423", width=6, tags=tag)

        jitter = random.randint(-4, 4)

        self.canvas.create_polygon(
            x - 10, y, x, y - 26 + jitter, x + 10, y, x + 4, y - 8, x - 4, y - 8,
            fill="#ff8c1a", outline="", smooth=True, tags=tag
        )

        self.canvas.create_polygon(
            x - 5, y - 2, x, y - 15 + jitter, x + 5, y - 2,
            fill="#ffd23f", outline="", smooth=True, tags=tag
        )

    def _icon_sword(self, cx, cy, s, color, tag="dynamic"):

        self.canvas.create_polygon(
            cx, cy - s * 1.6, cx + s * 0.35, cy, cx, cy + s * 0.3, cx - s * 0.35, cy,
            fill=color, outline="#2a2a2a", tags=tag
        )

        self.canvas.create_rectangle(
            cx - s * 0.6, cy, cx + s * 0.6, cy + s * 0.25,
            fill="#5a3a1a", outline="#2a1a0a", tags=tag
        )

        self.canvas.create_rectangle(
            cx - s * 0.15, cy + s * 0.25, cx + s * 0.15, cy + s * 0.9,
            fill="#3a2410", outline="#1a0f05", tags=tag
        )

    # ------------------------------------------------------------------
    def animate_player(self):

        if len(self.frames) > 0:

            self.current_frame = (
                self.current_frame + 1
            ) % len(self.frames)

        self.root.after(
            100,
            self.animate_player
        )

    def controls(self, event):

        player = self.state.player

        newX = player.x
        newY = player.y

        if event.keysym == "w":
            newY -= 20

        elif event.keysym == "s":
            newY += 20

        elif event.keysym == "a":
            newX -= 20

        elif event.keysym == "d":
            newX += 20

        elif event.keysym == "space":

            self.interact()
            return

        elif event.keysym in ("f", "F"):

            self.build_campfire()
            return

        elif event.keysym in ("e", "E"):

            self.craft_sword()
            return

        newX = max(10, min(self.width - 40, newX))
        newY = max(10, min(self.height - 40, newY))

        blocked = False

        for wallX, wallY in self.state.walls:

            if abs(newX - wallX) < 40 and abs(newY - wallY) < 40:

                blocked = True
                break

        if not blocked:

            player.x = newX
            player.y = newY

    def interact(self):
        """Espacio: ataca al enemigo más cercano si hay uno a rango,
        si no, intenta recolectar el recurso más cercano."""

        player = self.state.player

        with self.state.lock:

            for enemy in self.state.enemies[:]:

                distance = math.sqrt(
                    (player.x - enemy["x"]) ** 2 +
                    (player.y - enemy["y"]) ** 2
                )

                if distance < ATTACK_RANGE:

                    damage = SWORD_DAMAGE if player.has_sword else FIST_DAMAGE
                    enemy["hp"] -= damage

                    self.state.sound.play("sound/stone.wav")

                    if enemy["hp"] <= 0:
                        self.state.enemies.remove(enemy)

                    return

            for resource in self.state.resources[:]:

                x, y, rtype = resource

                distance = math.sqrt(
                    (player.x - x) ** 2 +
                    (player.y - y) ** 2
                )

                if distance < 60:

                    if rtype == "tree":

                        self.state.wood += 1
                        self.state.sound.play("sound/wood.wav")

                    else:

                        self.state.stone += 1
                        self.state.sound.play("sound/stone.wav")

                    self.state.resources.remove(
                        resource
                    )

                    break

    def build_campfire(self):

        player = self.state.player
        cost_wood, cost_stone = CAMPFIRE_COST

        with self.state.lock:

            if self.state.wood >= cost_wood and self.state.stone >= cost_stone:

                self.state.wood -= cost_wood
                self.state.stone -= cost_stone

                self.state.campfires.append({
                    "x": player.x + 15,
                    "y": player.y + 15
                })

                self.state.sound.play("sound/wood.wav")
                self._set_message("Fogata construida")

            else:

                self._set_message(f"Necesitas {cost_wood} madera y {cost_stone} piedra")

    def craft_sword(self):

        player = self.state.player
        cost_wood, cost_stone = SWORD_COST

        with self.state.lock:

            if player.has_sword:

                self._set_message("Ya tienes una espada")
                return

            if self.state.wood >= cost_wood and self.state.stone >= cost_stone:

                self.state.wood -= cost_wood
                self.state.stone -= cost_stone
                player.has_sword = True

                self.state.sound.play("sound/stone.wav")
                self._set_message("Espada forjada")

            else:

                self._set_message(f"Necesitas {cost_wood} madera y {cost_stone} piedra")

    def _set_message(self, text):

        self.message = text
        self.message_timer = 50

    # ------------------------------------------------------------------
    def update_ui(self):

        self.canvas.delete("dynamic")

        player = self.state.player

        with self.state.lock:

            health = self.state.health
            hunger = self.state.hunger
            temperature = self.state.temperature
            wood = self.state.wood
            stone = self.state.stone
            resources = list(self.state.resources)
            enemies = list(self.state.enemies)
            campfires = list(self.state.campfires)
            has_sword = player.has_sword

        # -------------------- tinte ambiental por temperatura --------------------
        if temperature <= 5:

            self.canvas.create_rectangle(
                0, 0, self.width, self.height,
                fill="#1a3d7c", stipple="gray25", outline="", tags="dynamic"
            )

        elif temperature >= 32:

            self.canvas.create_rectangle(
                0, 0, self.width, self.height,
                fill="#7c2a1a", stipple="gray25", outline="", tags="dynamic"
            )

        # -------------------- fogatas --------------------
        for fire in campfires:

            fx, fy = fire["x"], fire["y"]

            self.canvas.create_oval(
                fx - WARMTH_RADIUS, fy - WARMTH_RADIUS,
                fx + WARMTH_RADIUS, fy + WARMTH_RADIUS,
                outline="#ff8c1a", dash=(4, 4), tags="dynamic"
            )

            self._icon_campfire(fx, fy)

        # -------------------- recursos --------------------
        for x, y, rtype in resources:

            self.canvas.create_oval(
                x - 14, y + 16, x + 14, y + 22,
                fill="#000000", stipple="gray50", outline="", tags="dynamic"
            )

            if rtype == "tree":
                self._icon_tree(x, y)
            else:
                self._icon_rock_node(x, y)

        # -------------------- enemigos --------------------
        for enemy in enemies:

            ex, ey = enemy["x"], enemy["y"]

            self.canvas.create_oval(
                ex - 16, ey + 18, ex + 16, ey + 24,
                fill="#000000", stipple="gray50", outline="", tags="dynamic"
            )

            self._icon_slime(ex, ey)

        # -------------------- jugador --------------------
        self.canvas.create_oval(
            player.x + 6, player.y + 34, player.x + 34, player.y + 42,
            fill="#000000", stipple="gray50", outline="", tags="dynamic"
        )

        if len(self.frames) > 0:

            self.canvas.create_image(
                player.x,
                player.y,
                image=self.frames[self.current_frame],
                anchor="nw",
                tags="dynamic"
            )

        else:

            self.canvas.create_oval(
                player.x, player.y, player.x + 30, player.y + 30,
                fill="#f1c27d", outline="#7a4a20", width=2, tags="dynamic"
            )

        # -------------------- flash de daño --------------------
        if health < self.prev_health:
            self.damage_flash = 6

        self.prev_health = health

        if self.damage_flash > 0:

            self.canvas.create_rectangle(
                0, 0, self.width, self.height,
                fill="#ff0000", stipple="gray25", outline="", tags="dynamic"
            )

            self.damage_flash -= 1

        # viñeta roja si la vida es crítica
        if health <= 30:

            self.canvas.create_rectangle(
                4, 4, self.width - 4, self.height - 4,
                outline=COLOR_HEALTH, width=6, tags="dynamic"
            )

        # -------------------- mensaje de crafteo --------------------
        if self.message_timer > 0:

            msg_y = self.height - 78

            self._rounded_rect(
                self.width / 2 - 150, msg_y - 14, self.width / 2 + 150, msg_y + 14,
                radius=10, fill=COLOR_HUD_BG, outline=COLOR_HUD_BORDER,
                width=1, stipple="gray75", tags="dynamic"
            )

            self.canvas.create_text(
                self.width / 2, msg_y, text=self.message,
                font=("Consolas", 10, "bold"), fill="#ffd23f", tags="dynamic"
            )

            self.message_timer -= 1

        self._draw_hud(health, hunger, temperature, wood, stone, len(enemies), has_sword)

        self.root.after(
            50,
            self.update_ui
        )

    def _draw_hud(self, health, hunger, temperature, wood, stone, enemy_count, has_sword):

        panel_x, panel_y = 14, 14
        panel_w, panel_h = 270, 312

        self._rounded_rect(
            panel_x, panel_y, panel_x + panel_w, panel_y + panel_h,
            radius=14, fill=COLOR_HUD_BG, outline=COLOR_HUD_BORDER,
            width=2, stipple="gray75", tags="dynamic"
        )

        self.canvas.create_text(
            panel_x + panel_w / 2, panel_y + 18,
            text="ESTADO DEL JUGADOR", font=("Consolas", 12, "bold"),
            fill="#e8e8e8", tags="dynamic"
        )

        self.canvas.create_line(
            panel_x + 14, panel_y + 32, panel_x + panel_w - 14, panel_y + 32,
            fill=COLOR_HUD_BORDER, tags="dynamic"
        )

        icon_x = panel_x + 30
        bar_x = panel_x + 54
        bar_w = panel_w - 54 - 60
        value_x = panel_x + panel_w - 16

        row_y = panel_y + 52
        row_h = 30

        # vida
        self._icon_heart(icon_x, row_y, 10, COLOR_HEALTH)
        self._bar(bar_x, row_y - 7, bar_w, 14, health / 100, COLOR_HEALTH)
        self.canvas.create_text(value_x, row_y, anchor="e", text=f"{health}/100", font=FONT_HUD_SMALL, fill="#fff", tags="dynamic")

        row_y += row_h

        # hambre
        self._icon_apple(icon_x, row_y, 9, COLOR_HUNGER)
        self._bar(bar_x, row_y - 7, bar_w, 14, hunger / 100, COLOR_HUNGER)
        self.canvas.create_text(value_x, row_y, anchor="e", text=f"{hunger}/100", font=FONT_HUD_SMALL, fill="#fff", tags="dynamic")

        row_y += row_h

        # temperatura (-10 a 40)
        temp_pct = (temperature + 10) / 50
        temp_color = "#3498db" if temperature <= 10 else ("#e74c3c" if temperature >= 30 else "#f1c40f")

        self._icon_thermometer(icon_x, row_y, 9, temp_pct, temp_color)
        self._bar(bar_x, row_y - 7, bar_w, 14, temp_pct, temp_color)
        self.canvas.create_text(value_x, row_y, anchor="e", text=f"{temperature}°C", font=FONT_HUD_SMALL, fill="#fff", tags="dynamic")

        row_y += row_h + 4

        self.canvas.create_line(
            panel_x + 14, row_y - 14, panel_x + panel_w - 14, row_y - 14,
            fill=COLOR_HUD_BORDER, tags="dynamic"
        )

        # inventario
        self._icon_wood(icon_x, row_y, 8)
        self.canvas.create_text(
            bar_x, row_y, anchor="w",
            text=f"Madera: {wood}", font=FONT_HUD_SMALL, fill=COLOR_WOOD, tags="dynamic"
        )

        row_y += 26

        self._icon_stone(icon_x, row_y, 9)
        self.canvas.create_text(
            bar_x, row_y, anchor="w",
            text=f"Piedra: {stone}", font=FONT_HUD_SMALL, fill=COLOR_STONE, tags="dynamic"
        )

        row_y += 26

        self._icon_skull(icon_x, row_y, 9)
        self.canvas.create_text(
            bar_x, row_y, anchor="w",
            text=f"Enemigos: {enemy_count}", font=FONT_HUD_SMALL, fill=COLOR_ENEMY, tags="dynamic"
        )

        row_y += 26

        self.canvas.create_line(
            panel_x + 14, row_y - 13, panel_x + panel_w - 14, row_y - 13,
            fill=COLOR_HUD_BORDER, tags="dynamic"
        )

        # arma equipada
        sword_color = COLOR_SWORD_ON if has_sword else COLOR_SWORD_OFF
        self._icon_sword(icon_x, row_y, 9, sword_color)
        self.canvas.create_text(
            bar_x, row_y, anchor="w",
            text="Espada equipada" if has_sword else "Sin espada (usa E)",
            font=FONT_HUD_SMALL, fill=sword_color, tags="dynamic"
        )

        row_y += 30

        # crafteo disponible
        self.canvas.create_text(
            panel_x + 16, row_y, anchor="w",
            text="CRAFTEO", font=("Consolas", 10, "bold"), fill="#e8e8e8", tags="dynamic"
        )

        row_y += 20

        cf_wood, cf_stone = CAMPFIRE_COST
        sw_wood, sw_stone = SWORD_COST

        self.canvas.create_text(
            panel_x + 16, row_y, anchor="w",
            text=f"[F] Fogata  ({cf_wood} madera + {cf_stone} piedra)",
            font=("Consolas", 9), fill="#ff8c1a", tags="dynamic"
        )

        row_y += 18

        self.canvas.create_text(
            panel_x + 16, row_y, anchor="w",
            text=f"[E] Espada  ({sw_wood} madera + {sw_stone} piedra)",
            font=("Consolas", 9), fill=COLOR_SWORD_OFF, tags="dynamic"
        )

        # ayuda de controles, esquina inferior
        self._rounded_rect(
            10, self.height - 34, 320, self.height - 10,
            radius=10, fill=COLOR_HUD_BG, outline=COLOR_HUD_BORDER,
            width=1, stipple="gray75", tags="dynamic"
        )

        self.canvas.create_text(
            165, self.height - 22,
            text="WASD mover  -  ESPACIO golpear  -  F fogata  -  E espada",
            font=("Consolas", 9), fill="#cfcfcf", tags="dynamic"
        )
