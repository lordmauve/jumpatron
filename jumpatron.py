import wasabi2d as w2d
from wasabi2d.rect import ZRect
from wasabi2d.keyboard import keys
import random
import math

scene = w2d.Scene(1280, 720, title="Jumpatron", background="#2288cc", fullscreen=True)
main_layer = scene.layers[0]

floor = scene.height - 70
GRAVITY = 3000
SPEED = 301


class Char:
    def __init__(self, base, pos):
        self.base = base
        self.sprite = main_layer.add_sprite(
            f'{self.base}_walk1',
            pos=pos,
            anchor_x='center',
            anchor_y='bottom',
        )
        self.n = 0
        self.vy = 0
        self.can_jump = True
        self.jump_sound = w2d.sounds.load(f'{self.base}_jump')
        w2d.clock.coro.run(self.animate())

    def __repr__(self):
        return f'Char({self.base!r})'

    async def animate(self):
        t = random.random()
        async for dt in w2d.clock.coro.frames_dt():

            if not self.can_jump:
                uv = self.vy
                self.vy += GRAVITY * dt
                self.sprite.y += (uv + self.vy) / 2 * dt
            else:
                t += dt
                if t > 0.1:
                    t = 0
                    self.n += 1
                    f = self.n % 2 + 1
                    self.sprite.image = f'{self.base}_walk{f}'
            if self.sprite.y >= floor:
                self.sprite.y = floor
                self.can_jump = True
                self.can_spin = False
                self.was_hit = False
                self.vy = 0

    def set_sprite(self, name):
        self.sprite.image = f'{self.base}_{name}'

    async def spin(self):
        self.can_spin = False
        self.set_sprite('duck')
        self.sprite.anchor_y = 'center'
        await w2d.animate(self.sprite, 'accel_decel', duration=0.33, angle=-math.tau)
        self.sprite.anchor_y = 'bottom'
        self.sprite.angle = 0
        await w2d.clock.coro.sleep(0.1)
        self.sprite.image = f'{self.base}_jump'
        self.can_spin = True

    def jump(self):
        if self.can_jump:
            self.can_jump = False
            self.can_spin = True
            self.vy = -1200
            self.sprite.image = f'{self.base}_jump'
            self.jump_sound.play()
        elif self.can_spin:
            self.vy -= 400
            self.sprite.y -= 20
            w2d.clock.coro.run(self.spin())
            self.jump_sound.play()

    def hit(self):
        self.can_jump = self.can_spin = False
        self.was_hit = True
        self.set_sprite('hurt')
        self.vy = -800


class Grass:
    tile_size = 70

    def __init__(self):
        self.sprites = [
            main_layer.add_sprite('grass_mid', pos=(i * self.tile_size, floor), anchor_y='top')
            for i in range(scene.width // self.tile_size + 2)
        ]
        w2d.clock.coro.run(self.animate())

    async def animate(self):
        async for t in w2d.clock.coro.frames():
            off = round(SPEED * t)
            for i, sprite in enumerate(self.sprites):
                sprite.x = (i * self.tile_size - off) % (self.tile_size * len(self.sprites)) - self.tile_size


async def play_obstacle():
    sprite_name = random.choice(
        ['wall', 'crate', 'sign', 'fence'],
    )
    sprite = main_layer.add_sprite(
        sprite_name,
        pos=(scene.width + 100, floor),
        anchor_y='bottom'
    )
    start = scene.width + 100
    async for t in w2d.clock.coro.frames():
        x = start - round(SPEED * t)
        sprite.x = x
        if sprite.bounds.right < 0:
            break

        in_order = sorted(chars, key=lambda c: c.slot)
        out_order = []
        for i, c in enumerate(in_order):
            out_order.append(c)
            try:
                bounds = c.sprite.bounds
            except TypeError:
                continue
            if not c.was_hit and bounds.colliderect(sprite.bounds):
                c.hit()
                c = out_order.pop()
                try:
                    prev = out_order.pop()
                except IndexError:
                    out_order.append(c)
                else:
                    out_order.extend([c, prev])

        if out_order != in_order:
            for c, slot in zip(out_order, slots):
                c.slot = slot
                w2d.animate(c.sprite, duration=0.3, x=slot)
    sprite.delete()


slots = [scene.width // 12 * i for i in range(1, 5)]

red = Char('alienpink', (slots[0], floor))
yellow = Char('alienyellow', (slots[1], floor))
blue = Char('alienblue', (slots[2], floor))
green = Char('aliengreen', (slots[3], floor))

chars = [
    blue, green, red, yellow
]
for c, slot in zip(chars, slots):
    c.slot = slot

Grass()


async def spawn_obstacles():
    while True:
        w2d.clock.coro.run(play_obstacle())
        interval = random.uniform(2.5, 5)
        await w2d.clock.coro.sleep(interval)

w2d.clock.coro.run(spawn_obstacles())

pad = None


@w2d.event
def on_joystick_attached(device_index):
    global pad
    from pygame.joystick import Joystick
    if pad is None:
        pad = Joystick(device_index)


@w2d.event
def on_joystick_detached(instance_id):
    global pad
    if pad and instance_id == pad.get_instance_id():
        pad.quit()
        pad = None


@w2d.event
def on_joybutton_down(button):
    if 0 <= button < len(chars):
        char = chars[button]
        char.jump()


keys = [keys.K_1, keys.K_2, keys.K_3, keys.K_4]
@w2d.event
def on_key_down(key):
    try:
        idx = keys.index(key)
    except ValueError:
        pass
    else:
        on_joybutton_down(idx)



w2d.run()
