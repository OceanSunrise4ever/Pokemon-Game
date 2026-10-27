"""Pocket Quest: a small, arcade-style Pokemon adventure.

Run with: python "Pokemon game.py"
Requires: pygame (python -m pip install pygame)
"""

import random
import sys

import pygame


WIDTH, HEIGHT = 960, 640
FPS = 100
ROSTER_SIZE = 1000

COLORS = [(245, 96, 91), (71, 170, 255), (255, 193, 76), (122, 218, 144),
		  (190, 125, 245), (255, 132, 185)]
STARTERS = ["Bulbasaur", "Charmander", "Squirtle", "Pikachu", "Eevee", "Ralts"]
EVOLUTIONS = {
	"Bulbasaur": (5, "Ivysaur"), "Ivysaur": (10, "Venusaur"),
	"Charmander": (5, "Charmeleon"), "Charmeleon": (10, "Charizard"),
	"Squirtle": (5, "Wartortle"), "Wartortle": (10, "Blastoise"),
	"Pikachu": (8, "Raichu"), "Eevee": (7, "Vaporeon"),
	"Ralts": (8, "Gardevoir"),
}
MOVE_LIBRARY = [
	("Quick Jab", "NORMAL", 18, "Fast and reliable."),
	("Ember", "FIRE", 24, "A warm burst of flame."),
	("Bubble Beam", "WATER", 22, "A stream of bouncing bubbles."),
	("Vine Whip", "GRASS", 23, "A crackling green lash."),
	("Thunder Pop", "ELECTRIC", 27, "A shocking surprise."),
	("Moon Spark", "MYSTIC", 20, "A strange silver flash."),
	("Meteor Crash", "EARTH", 65, "An overpowered starfall strike."),
	("Hypernova", "MYSTIC", 95, "A devastating cosmic blast."),
	("Recover", "HEAL", -28, "Restore some HP."),
	("Lucky Star", "MYSTIC", 35, "Big power, but sometimes misses."),
]
BOSS_NAMES = ["Titan Charizard", "Titan Gengar", "Titan Dragonite", "Titan Mewtwo"]


def make_roster():
	"""Keep the game playable without a data download: 1,000 unique species."""
	famous = [
		"Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard",
		"Squirtle", "Wartortle", "Blastoise", "Pikachu", "Raichu", "Eevee", "Vaporeon",
		"Jolteon", "Flareon", "Espeon", "Umbreon", "Leafeon", "Glaceon", "Sylveon",
		"Mew", "Mewtwo", "Lucario", "Gengar", "Snorlax", "Dragonite", "Gardevoir",
		"Greninja", "Rowlet", "Fuecoco", "Sprigatito", "Quaxly",
	]
	prefixes = ["Aqua", "Blaze", "Bloom", "Volt", "Stone", "Frost", "Shadow", "Star", "Cloud", "Moss"]
	suffixes = ["ling", "on", "drake", "bit", "fin", "paw", "wing", "mite", "roo", "let"]
	roster = famous[:]
	for number in range(len(roster) + 1, ROSTER_SIZE + 1):
		roster.append(f"{prefixes[number % len(prefixes)]}{suffixes[number % len(suffixes)]} {number}")
	return roster


ROSTER = make_roster()


def text(surface, message, position, font, color=(240, 244, 250)):
	surface.blit(font.render(message, True, color), position)


def creature(surface, center, color, scale=1.0, flip=False):
	x, y = center
	body = pygame.Rect(0, 0, int(100 * scale), int(86 * scale))
	body.center = (x, y + int(12 * scale))
	pygame.draw.ellipse(surface, color, body)
	pygame.draw.circle(surface, color, (x, y - int(28 * scale)), int(38 * scale))
	eye_x = x + (-13 if flip else 13) * scale
	pygame.draw.circle(surface, (25, 31, 43), (int(eye_x), int(y - 35 * scale)), max(3, int(6 * scale)))
	pygame.draw.circle(surface, (255, 255, 255), (int(eye_x + 2), int(y - 37 * scale)), max(1, int(2 * scale)))
	pygame.draw.polygon(surface, color, [(x - 27, y - 53), (x - 42, y - 88), (x - 8, y - 64)])
	pygame.draw.polygon(surface, color, [(x + 27, y - 53), (x + 42, y - 88), (x + 8, y - 64)])
	pygame.draw.line(surface, (25, 31, 43), (x - 12, y - 13), (x + 12, y - 13), 3)


class Game:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Pocket Quest: 1000 Wonders")
		self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
		self.clock = pygame.time.Clock()
		self.title_font = pygame.font.Font(None, 54)
		self.big_font = pygame.font.Font(None, 40)
		self.font = pygame.font.Font(None, 26)
		self.small_font = pygame.font.Font(None, 20)
		self.state = "title"
		self.hero = pygame.Vector2(480, 390)
		self.starter = None
		self.level = 1
		self.xp = 0
		self.next_xp = 100
		self.form_name = ""
		self.party = []
		self.message = "Choose a partner and begin your adventure!"
		self.enemy = None
		self.enemy_name = ""
		self.enemy_is_boss = False
		self.enemy_hp = 0
		self.player_hp = 0
		self.turn = "player"
		self.potions = 3
		self.caught = 0
		self.shake = 0

	def start(self, starter_index):
		self.starter = starter_index
		self.form_name = STARTERS[starter_index]
		self.level = 1
		self.xp = 0
		self.next_xp = 100
		self.party = [starter_index]
		self.state = "explore"
		self.message = "Explore the tall grass. Move with WASD or arrow keys."

	def new_battle(self):
		self.enemy = random.randrange(ROSTER_SIZE)
		self.enemy_is_boss = self.caught > 0 and self.caught % 5 == 0
		self.enemy_name = random.choice(BOSS_NAMES) if self.enemy_is_boss else ROSTER[self.enemy]
		enemy_level = 1 + self.enemy % 8
		self.enemy_hp = (260 + self.level * 18) if self.enemy_is_boss else 50 + enemy_level * 12
		self.player_hp = self.max_hp()
		self.turn = "player"
		self.state = "battle"
		self.message = f"BOSS BATTLE! {self.enemy_name} appeared! Pick a move." if self.enemy_is_boss else f"A wild {self.enemy_name} appeared! Pick a move."

	def max_hp(self):
		return 100 + self.level * 20

	def award_xp(self):
		self.xp += 55 + (self.enemy % 35)
		while self.xp >= self.next_xp:
			self.xp -= self.next_xp
			self.level += 1
			self.next_xp = 75 + self.level * 35
			self.player_hp = self.max_hp()
			if self.form_name in EVOLUTIONS and self.level >= EVOLUTIONS[self.form_name][0]:
				old_name = self.form_name
				self.form_name = EVOLUTIONS[old_name][1]
				self.message = f"LEVEL UP! {old_name} evolved into {self.form_name}!"
			else:
				self.message = f"LEVEL UP! {self.form_name} reached level {self.level}!"

	def player_move(self, move_index):
		if self.turn != "player":
			return
		name, move_type, power, description = MOVE_LIBRARY[move_index]
		if move_type == "HEAL":
			self.player_hp = min(self.max_hp(), self.player_hp - power)
			self.message = f"{self.form_name} used {name}! HP restored."
		elif move_type == "MYSTIC" and name == "Lucky Star" and random.random() < 0.2:
			self.message = f"{name} missed! {self.enemy_name} dances away."
		else:
			damage = max(8, power + random.randrange(-5, 7))
			self.enemy_hp -= damage
			self.shake = 8
			self.message = f"{self.form_name} used {name} for {damage} damage!"
		if self.enemy_hp <= 0:
			self.caught += 1
			self.award_xp()
			if "LEVEL UP" not in self.message:
				result = "BOSS DEFEATED! " if self.enemy_is_boss else "Victory! "
				self.message = f"{result}{self.enemy_name} joined your collection. Space to explore."
			self.state = "explore"
			return
		self.turn = "enemy"

	def enemy_turn(self):
		if self.turn != "enemy":
			return
		damage = random.randrange(24, 40) if self.enemy_is_boss else random.randrange(8, 22)
		self.player_hp -= damage
		self.message = f"{self.enemy_name} struck back for {damage}! Press Space."
		self.turn = "player"
		if self.player_hp <= 0:
			self.player_hp = self.max_hp()
			self.state = "explore"
			self.message = "Your partner recovered at camp. Keep exploring!"

	def draw_background(self):
		self.screen.fill((18, 28, 43))
		pygame.draw.rect(self.screen, (31, 70, 67), (0, 110, WIDTH, HEIGHT - 110))
		for x in range(0, WIDTH, 32):
			for y in range(140, HEIGHT, 28):
				if (x * 3 + y) % 5:
					pygame.draw.line(self.screen, (55, 125, 85), (x + 7, y + 12), (x + 2, y - 2), 2)
		pygame.draw.rect(self.screen, (101, 73, 51), (0, 300, WIDTH, 48))
		pygame.draw.rect(self.screen, (122, 91, 58), (0, 310, WIDTH, 28))

	def draw_ui(self):
		pygame.draw.rect(self.screen, (13, 20, 33), (0, 0, WIDTH, 110))
		text(self.screen, "POCKET QUEST", (28, 18), self.big_font, (255, 211, 92))
		text(self.screen, "1000 wonders to discover", (30, 58), self.small_font, (155, 173, 193))
		text(self.screen, f"Collection {len(self.party) + self.caught}/{ROSTER_SIZE}", (690, 25), self.font)
		text(self.screen, f"Potions: {self.potions}", (690, 58), self.font, (255, 154, 122))

	def draw_explore(self):
		self.draw_background()
		self.draw_ui()
		pygame.draw.circle(self.screen, (255, 205, 82), (self.hero.x, self.hero.y), 18)
		pygame.draw.circle(self.screen, (242, 103, 76), (self.hero.x, self.hero.y - 24), 14)
		pygame.draw.line(self.screen, (242, 103, 76), (self.hero.x - 10, self.hero.y - 30), (self.hero.x + 14, self.hero.y - 34), 5)
		text(self.screen, "CAMP", (25, 275), self.small_font, (255, 230, 180))
		text(self.screen, "TALL GRASS", (410, 155), self.small_font, (180, 235, 160))
		if self.starter is not None:
			creature(self.screen, (820, 260), COLORS[self.starter % len(COLORS)], 0.72)
			text(self.screen, f"{self.form_name}  Lv.{self.level}", (760, 325), self.small_font)
			text(self.screen, f"XP {self.xp}/{self.next_xp}", (760, 350), self.small_font, (255, 211, 92))
		pygame.draw.rect(self.screen, (13, 20, 33), (20, 525, WIDTH - 40, 88), border_radius=12)
		text(self.screen, self.message, (40, 545), self.font)
		text(self.screen, "WASD / arrows: move     SPACE: continue     R: rest at camp", (40, 580), self.small_font, (167, 186, 205))

	def draw_bar(self, label, value, maximum, x, y, color):
		text(self.screen, label, (x, y - 28), self.small_font)
		pygame.draw.rect(self.screen, (32, 39, 54), (x, y, 240, 18), border_radius=6)
		pygame.draw.rect(self.screen, color, (x, y, max(0, int(240 * value / maximum)), 18), border_radius=6)
		text(self.screen, f"{max(0, value)}/{maximum}", (x + 92, y - 2), self.small_font)

	def draw_battle(self):
		self.screen.fill((23, 31, 48))
		pygame.draw.ellipse(self.screen, (43, 76, 71), (80, 220, 360, 150))
		pygame.draw.ellipse(self.screen, (43, 76, 71), (520, 170, 360, 150))
		creature(self.screen, (250, 285), COLORS[self.starter % len(COLORS)], 1.18)
		creature(self.screen, (700, 235), COLORS[self.enemy % len(COLORS)], 1.05, True)
		text(self.screen, f"{self.form_name}  Lv.{self.level}", (125, 145), self.big_font)
		text(self.screen, self.enemy_name, (550, 95), self.big_font, (255, 116, 102) if self.enemy_is_boss else (240, 244, 250))
		self.draw_bar("ALLY HP", self.player_hp, self.max_hp(), 120, 190, (93, 215, 129))
		enemy_max_hp = (260 + self.level * 18) if self.enemy_is_boss else 50 + (1 + self.enemy % 8) * 12
		self.draw_bar("BOSS HP" if self.enemy_is_boss else "WILD HP", self.enemy_hp, enemy_max_hp, 590, 140, (255, 92, 82) if self.enemy_is_boss else (242, 104, 101))
		pygame.draw.rect(self.screen, (13, 20, 33), (35, 410, WIDTH - 70, 190), border_radius=12)
		text(self.screen, self.message, (60, 430), self.font, (255, 224, 159))
		for index, (name, move_type, power, _) in enumerate(MOVE_LIBRARY[:8]):
			x = 60 + (index % 4) * 215
			y = 475 + (index // 4) * 52
			pygame.draw.rect(self.screen, COLORS[index % len(COLORS)], (x, y, 190, 38), border_radius=8)
			text(self.screen, f"{index + 1}  {name}", (x + 10, y + 9), self.small_font, (18, 26, 38))
		text(self.screen, "Press 1-8 to attack     SPACE to pass enemy turn", (60, 580), self.small_font, (167, 186, 205))

	def draw_title(self):
		self.screen.fill((18, 28, 43))
		pygame.draw.circle(self.screen, (35, 77, 89), (790, 190), 180)
		pygame.draw.circle(self.screen, (255, 211, 92), (790, 190), 90, 5)
		pygame.draw.line(self.screen, (255, 211, 92), (700, 190), (880, 190), 5)
		text(self.screen, "POCKET QUEST", (60, 90), self.title_font, (255, 211, 92))
		text(self.screen, "A 1000-species adventure", (65, 145), self.big_font, (229, 237, 245))
		text(self.screen, "Choose your first partner", (65, 205), self.font, (161, 181, 202))
		for index, name in enumerate(STARTERS):
			x = 70 + (index % 3) * 285
			y = 275 + (index // 3) * 145
			pygame.draw.rect(self.screen, (30, 43, 61), (x, y, 245, 110), border_radius=12)
			creature(self.screen, (x + 52, y + 57), COLORS[index], 0.42)
			text(self.screen, f"{index + 1}  {name}", (x + 95, y + 48), self.font)
		text(self.screen, "1-6: choose     Every adventure starts small.", (65, 590), self.small_font, (167, 186, 205))

	def run(self):
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()
				if event.type == pygame.KEYDOWN:
					if self.state == "title" and pygame.K_1 <= event.key <= pygame.K_6:
						self.start(event.key - pygame.K_1)
					elif self.state == "battle" and pygame.K_1 <= event.key <= pygame.K_8:
						self.player_move(event.key - pygame.K_1)
					elif event.key == pygame.K_SPACE and self.state == "battle":
						self.enemy_turn()
					elif event.key == pygame.K_SPACE and self.state == "explore" and self.message.startswith("Victory"):
						self.message = "The path ahead is sparkling. Find another wild Pokemon!"
					elif event.key == pygame.K_r and self.state == "explore":
						self.message = "Camp restored your energy. The wild is waiting."
			if self.state == "explore":
				keys = pygame.key.get_pressed()
				direction = pygame.Vector2(keys[pygame.K_RIGHT] - keys[pygame.K_LEFT], keys[pygame.K_DOWN] - keys[pygame.K_UP])
				if direction.length_squared():
					self.hero += direction.normalize() * 4
					self.hero.x = max(25, min(WIDTH - 25, self.hero.x))
					self.hero.y = max(135, min(500, self.hero.y))
					if 330 < self.hero.x < 650 and 190 < self.hero.y < 500 and random.random() < 0.012:
						self.new_battle()
			if self.state == "title":
				self.draw_title()
			elif self.state == "explore":
				self.draw_explore()
			else:
				self.draw_battle()
			pygame.display.flip()
			self.clock.tick(FPS)


if __name__ == "__main__":
	Game().run()