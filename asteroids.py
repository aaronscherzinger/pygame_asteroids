import pygame
import random

# classes for geometric objects (polygons, etc.)
class Polygon2D:
    'A simple class for 2D polygons'
    vertices = []
    rotation_angle = 0
    translation = pygame.math.Vector2(0)

    aabb_valid = False
    transformed_vertices_valid = False
    aabb = []
    transformed_vertices = []

    def __init__(self, vertices):
        self.vertices = vertices

        # in order to define a polygon, we need at least 3 vertices
        assert(len(vertices) >= 3), "Not enough vertices in polygon"

    def get_num_vertices(self):
        return len(self.vertices)

    def get_rotation_angle(self):
        return self.rotation_angle

    def get_translation(self):
        return self.translation

    def invalidate_transformation(self):
        self.aabb_valid = False
        self.transformed_vertices_valid = False

    def set_rotation_angle(self, angle):
        self.rotation_angle = angle
        self.invalidate_transformation()

    def set_translation(self, translation):
        self.translation = translation
        self.invalidate_transformation()

    def rotate(self, angle):
        self.rotation_angle = (self.rotation_angle + angle) % 360.0
        self.invalidate_transformation()

    def translate(self, offset):
        self.translation += offset
        self.invalidate_transformation()

    def get_transformed_vertices(self):
        if not self.transformed_vertices_valid:
            self.transformed_vertices = [ v.rotate(self.rotation_angle) + self.translation for v in self.vertices ]
            self.transformed_vertices_valid = True
            self.update_aabb()

        return self.transformed_vertices

    def update_aabb(self):
        if not self.aabb_valid:
            transformed_vertices = self.get_transformed_vertices()
            min_coord = transformed_vertices[0]
            max_coord = transformed_vertices[0]

            for v in transformed_vertices:
                min_coord = pygame.math.Vector2(min([min_coord[0], v[0]]), min([min_coord[1], v[1]]))
                max_coord = pygame.math.Vector2(max([max_coord[0], v[0]]), max([max_coord[1], v[1]]))
        
            self.aabb = [min_coord, max_coord]
            self.aabb_valid = True

    def render(self, surface, color):
        pygame.draw.polygon(surface, color, self.get_transformed_vertices(), 1)

    def get_aabb(self):
        if not self.aabb_valid:
            self.update_aabb()

        return self.aabb


    # TODO: convexity test?
    # TODO: self-intersection test?
    # TODO: triangulation

# --------------------
# geometric predicates
# --------------------

# orientation test for three points, >0: left turn, ==0: collinear, <0: right turn
def orientation_test(p_a, p_b, p_c):
    acx = p_a.x - p_c.x
    bcx = p_b.x - p_c.x
    acy = p_a.y - p_c.y
    bcy = p_b.y - p_c.y

    return acx * bcy - acy * bcx

# line intersection test, line segments are defined by p0-p1 and p2-p3
def lines_intersect(p0, p1, p2, p3): 
    # compute bounding boxes
    r0 = pygame.math.Vector2(min(p0.x, p1.x), min(p0.y, p1.y))
    r1 = pygame.math.Vector2(max(p0.x, p1.x), max(p0.y, p1.y))
    r2 = pygame.math.Vector2(min(p2.x, p3.x), min(p2.y, p3.y))
    r3 = pygame.math.Vector2(max(p2.x, p3.x), max(p2.y, p3.y))

    return ((r1.x >= r2.x) and (r3.x >= r0.x) and (r1.y >= r2.y) and (r3.y >= r0.y)
            and (orientation_test(p0, p2, p3) * orientation_test(p1, p2, p3) <= 0)
            and (orientation_test(p2, p0, p1) * orientation_test(p3, p0, p1) <= 0))


# checks if a point v is inside a polygon p given by its vertices in correct (CCW) order.
# the algorithm uses the ray crossing method described in "Computational Geometry in C"
def point_in_poly(v, p):
    c = False

    p_vertices = p.get_transformed_vertices()
    p_first = p_vertices[-1]
    for p_second in p_vertices:
        if ((p_second.y > v.y) != (p_first.y > v.y)) and (v.x < (p_first.x - p_second.x) * (v.y - p_second.y) / (p_first.y - p_second.y) + p_second.x):
            c = not c
        p_first = p_second
    
    return c

# checks if there is a collision (i.e., intersection) between two polygons a and b
# TODO: this method might be quite slow (quadratic in runtime), make it more efficient
def collision_test(a, b):
    a_vertices = a.get_transformed_vertices()
    b_vertices = b.get_transformed_vertices()

    # speed up the computation by checking if bounding boxes overlap
    a_aabb = a.get_aabb()
    b_aabb = b.get_aabb()
    if not ((a_aabb[1].x >= b_aabb[0].x) and (b_aabb[1].x >= a_aabb[0].x) and (a_aabb[1].y >= b_aabb[0].y) and (b_aabb[1].y >= a_aabb[0].y)):
        return False

    # check if vertices of one polygon are inside of the other one
    for v in a_vertices:
        if point_in_poly(v, b):
            return True
    for v in b_vertices:
        if point_in_poly(v, a):
            return True

    # check if any edges intersect
    for a_index in range(0, len(a_vertices)):
        for b_index in range(0, len(b_vertices)):
            if lines_intersect(a_vertices[a_index - 1], a_vertices[a_index], b_vertices[b_index - 1], b_vertices[b_index]):
                return True

    return False

class GameObject(Polygon2D):
    
    speed = 0
    direction = pygame.math.Vector2(0,0)
    is_destroyed = False
    color = [255, 255, 255]
    screen_wrap_modifiers = []

    def __init__(self, vertices, color):
        Polygon2D.__init__(self, vertices)
        self.color = color

    def get_speed(self):
        return self.speed

    def set_speed(self, speed):
        self.speed = speed

    def change_speed(self, delta):
        self.speed = self.speed + delta

    def get_direction(self):
        return self.direction

    def set_direction(self, direction):
        self.direction = direction

    def set_destroyed(self):
        self.is_destroyed = True

    def destroyed(self):
        return self.is_destroyed

    def get_color(self):
        return self.color

    def set_color(self, color):
        self.color = color

    def move(self, speed_factor):
        self.translate(speed_factor * self.speed * self.get_direction())

    def screen_wrap(self, screen_width, screen_height):
        # move the translation vector within the screen bounds
        if self.translation[0] < 0:
            self.translate(pygame.math.Vector2(screen_width, 0))

        if self.translation[1] < 0:
            self.translate(pygame.math.Vector2(0, screen_height))

        if self.translation[0] >= screen_width:
            self.translate(pygame.math.Vector2(-screen_width, 0))

        if self.translation[1] >= screen_height:
            self.translate(pygame.math.Vector2(0, -screen_height))

        self.screen_wrap_modifiers = get_screen_wrap_modifiers(self, screen_width, screen_height)

    def render_with_screen_wraps(self, surface):
        # first of all: render at the standard position
        self.render(surface, self.color)

        # get transformed vertices
        vertices = self.get_transformed_vertices()

        # now get the screen wrap modifiers
        wrap_modifiers = self.screen_wrap_modifiers

        for m in wrap_modifiers:
            current_vertices = [v + m for v in vertices]
            pygame.draw.polygon(surface, self.color, current_vertices, 1)

class Spaceship(GameObject):

    def __init__(self, color):
        super(Spaceship,self).__init__( [pygame.math.Vector2(10, 5), pygame.math.Vector2(0, -20), pygame.math.Vector2(-10, 5)], color)

    def add_thrust(self, amount):
        thrust = amount * pygame.math.Vector2(0, -1).rotate(self.rotation_angle)
        momentum = self.speed * self.direction + thrust

        # speed is capped at 15
        self.speed = min(momentum.length(), 15)
        self.direction = momentum.normalize()

    def get_tip_position(self):
        return self.vertices[1].rotate(self.rotation_angle) + self.translation

class LaserShot(GameObject):

    traveled_distance = 0
    shot_color_begin = pygame.math.Vector3(255, 50, 50)
    shot_color_end = pygame.math.Vector3(255, 255, 50)
    max_travel_dist = -1

    def __init__(self, position, direction, rotation_angle, max_travel_dist):
        super(LaserShot,self).__init__( [pygame.math.Vector2(-1.5,0), pygame.math.Vector2(1.5,0), pygame.math.Vector2(0, -7)], [self.shot_color_begin.x, self.shot_color_begin.y, self.shot_color_begin.z] )
        self.rotation_angle = rotation_angle
        self.translation = position
        self.direction = direction
        self.traveled_distance = 0
        self.max_travel_dist = max_travel_dist

    def get_traveled_distance(self):
        return self.traveled_distance

    def move(self, speed_factor):
        super(LaserShot, self).move(speed_factor)
        self.traveled_distance = self.traveled_distance + (speed_factor * self.speed * self.get_direction()).length()
        if self.max_travel_dist > 0:
            factor = min(1, self.traveled_distance / self.max_travel_dist)
            current_color = self.shot_color_begin.lerp(self.shot_color_end, factor)
            self.color = [ int(current_color.x), int(current_color.y), int(current_color.z) ]
            if self.traveled_distance > self.max_travel_dist:
                self.is_destroyed = True

class Asteroid(GameObject):

    spin = 0
    destruction_vector = pygame.math.Vector2(0,0)
    destruction_speed = 0
    radius = 0

    def __init__(self, radius, num_vertices, color):
        assert(num_vertices > 2), "asteroid must have >2 vertices"
        
        self.radius = radius
        # we randomy generate asteroids by choosing points on a perturbed circle
        vertices = []
        mean_angle = 360 / num_vertices
        mean_radius = radius

        angle_variation = 0.2 * mean_angle
        radius_variation = 0.3 * mean_radius

        current_angle = 0
        for i in range(0, num_vertices):
            current_radius = mean_radius + random.uniform(-radius_variation, radius_variation) 
            current_vector = pygame.math.Vector2(0, current_radius)

            current_angle = current_angle + random.uniform(-angle_variation, angle_variation)
            current_vector.rotate_ip(current_angle)
            vertices.append(current_vector)

            current_angle = current_angle + mean_angle

        self.vertices = vertices

        # now randomly generate the direction
        self.direction = pygame.math.Vector2(0, 1)
        self.direction.rotate_ip(random.uniform(0, 360))
        self.direction.normalize_ip()

        # now randomly generate the speed
        min_speed = 0.01 
        max_speed = 1
        self.speed = random.uniform(min_speed, max_speed)

        # now randomly generate the spin
        max_spin = 1
        self.spin = random.uniform(-max_spin, max_spin)

        self.color = color

    def get_radius(self):
        return self.radius

    def set_spin(self, spin):
        self.spin = spin

    def get_spin(self):
        return spin

    def change_spin(self, delta):
        self.spin = self.spin.delta

    def move(self, speed_factor):
        super(Asteroid,self).move(speed_factor)
        self.rotation_angle += self.spin * speed_factor

    def set_destruction_vector(self, v):
        self.destruction_vector = v

    def get_destruction_vector(self):
        return self.destruction_vector

    def set_destruction_speed(self, speed):
        self.destruction_speed = speed

    def get_destruction_speed(self):
        return self.destruction_speed

class Debris(GameObject):

    spin = 0
    life_time = 0
    max_life = 0
    original_color = [0, 0, 0]
    fade_to_color = [0, 0, 0]

    def __init__(self, position, color):
        self.vertices=[ pygame.math.Vector2(1,1), pygame.math.Vector2(0,-1), pygame.math.Vector2(-1,1) ]
        # now randomly generate the direction
        self.direction = pygame.math.Vector2(0, 1)
        self.direction.rotate_ip(random.uniform(0, 360))
        self.direction.normalize_ip()

        # now randomly generate the speed
        min_speed = 0.1 
        max_speed = 1.5
        self.speed = random.uniform(min_speed, max_speed)

        # now randomly generate the spin
        max_spin = 2
        self.spin = random.uniform(-max_spin, max_spin)

        # now randomly generate the life time, 60 corresponds to one second
        self.max_life = random.uniform(100, 200)

        self.translation = position

        self.original_color = color
        self.color = color

    def set_spin(self, spin):
        self.spin = spin

    def get_spin(self):
        return spin

    def change_spin(self, delta):
        self.spin = self.spin.delta

    def move(self, speed_factor):
        super(Debris,self).move(speed_factor)
        self.rotation_angle += self.spin * speed_factor
        self.add_to_life_time(speed_factor)

    def add_to_life_time(self, time):
        self.life_time = self.life_time + time
        if self.life_time > self.max_life:
            self.is_destroyed = True
        factor = min(1, self.life_time / self.max_life)
        current_color = []
        for i in range(0, 3):
            current_color.append(int(max(0,min(255,(1-factor) * self.original_color[i] + factor * self.fade_to_color[i]))))
        self.color = current_color

def check_screen_wraps(object, screen_width, screen_height):
    aabb = object.get_aabb()
    wraps = [False, False, False, False]

    if aabb[0].x < 0:
        wraps[0] = True

    if aabb[1].x >= screen_width:
        wraps[1] = True

    if aabb[0].y < 0:
        wraps[2] = True

    if aabb[1].y >= screen_height:
        wraps[3] = True

    return wraps

def get_screen_wrap_modifiers(p, screen_width, screen_height):
    wraps = check_screen_wraps(p, screen_width, screen_height)

    modifier_list = [
            pygame.math.Vector2(0),
            pygame.math.Vector2(0),
            pygame.math.Vector2(0)
            ]

    if wraps[0]:
        modifier_list[0] = pygame.math.Vector2(screen_width, 0)
    elif wraps[1]:
        modifier_list[0] = pygame.math.Vector2(-screen_width,0)
    
    if wraps[2]:
        modifier_list[1] = pygame.math.Vector2(0, screen_height)
    elif wraps[3]:
        modifier_list[1] = pygame.math.Vector2(0, -screen_height)

    if wraps[0] and wraps[2]:
        modifier_list[2] = pygame.math.Vector2(screen_width, screen_height)
    elif wraps[0] and wraps[3]:
        modifier_list[2] = pygame.math.Vector2(screen_width, -screen_height)
    elif wraps[1] and wraps[2]:
        modifier_list[2] = pygame.math.Vector2(-screen_width, screen_height)
    elif wraps[1] and wraps[3]:
        modifier_list[2] = pygame.math.Vector2(-screen_width, -screen_height)

    return [ v for v in modifier_list if v != pygame.math.Vector2(0) ]

def collision_test_with_screen_wraps(a, b):
    # get all displacement vectors
    a_modifier_list = a.screen_wrap_modifiers
    b_modifier_list = b.screen_wrap_modifiers

    # add the empty modifier
    a_modifier_list.append(pygame.math.Vector2(0))
    b_modifier_list.append(pygame.math.Vector2(0))

    a_translation = a.get_translation()
    b_translation = b.get_translation()

    # we only need to test the collision for the smallest distance
    a_min_modifier, b_min_modifier = pygame.math.Vector2(0), pygame.math.Vector2(0)
    min_dist = (a_translation - b_translation).length_squared()
    for a_m in a_modifier_list:
        for b_m in b_modifier_list:
            dist = ((a_translation + a_m) - (b_translation + b_m)).length_squared()
            if dist < min_dist:
                min_dist = dist
                a_min_modifier = a_m
                b_min_modifier = b_m

    if a_min_modifier != pygame.math.Vector2(0):
        a.set_translation(a_translation + a_min_modifier)
    if b_min_modifier != pygame.math.Vector2(0):
        b.set_translation(b_translation + b_min_modifier)
    
    collide = collision_test(a,b)

    if a_min_modifier != pygame.math.Vector2(0):
        a.set_translation(a_translation)
    if b_min_modifier != pygame.math.Vector2(0):
        b.set_translation(b_translation)

    if collide:
        return True

    return False


# function for clean-up
def exit_game():
    print("Quit game...")



# basic initialization
screen_width, screen_height = 1024, 768
bg_color = 0, 0, 0


print("Initializing PyGame...")
pygame.init()
screen = pygame.display.set_mode( (screen_width, screen_height), 0, 32)
clock = pygame.time.Clock()

# font initialization
text_color = 255, 255, 255
print("Initializing font. This may take some time...")
font = pygame.font.SysFont(pygame.font.get_default_font(), 30) 
pause_font = pygame.font.SysFont(pygame.font.get_default_font(), 45) 
print("Font initialized to " + pygame.font.get_default_font())

# color settings
spaceship_color = [50,255,50]
asteroid_color = [200, 200, 200]
debris_color = [180, 180, 180]

# game object initialization
shot_limit = 10
fired_shots = []
asteroids = []
debris_objects = []
points = 0
level = 0
lifes = 3

# configuration
max_shot_range = 620
asteroid_points = 10


# default state: no shot fired in frame
shot_fired = False

spaceship_destroyed = False
game_over = False

# TODO: allow for some randomness in asteroid spawn position
spawn_border = 55
asteroid_spawn_positions = [
        pygame.math.Vector2(spawn_border, spawn_border),
        pygame.math.Vector2(screen_width // 3, spawn_border),
        pygame.math.Vector2(screen_width // 3 * 2, spawn_border),
        pygame.math.Vector2(screen_width - spawn_border, spawn_border),

        pygame.math.Vector2(spawn_border, screen_height - spawn_border),
        pygame.math.Vector2(screen_width // 3, screen_height - spawn_border),
        pygame.math.Vector2(screen_width // 3 * 2, screen_height - spawn_border),
        pygame.math.Vector2(screen_width - spawn_border, screen_height - spawn_border),

        pygame.math.Vector2(spawn_border, screen_height // 3),
        pygame.math.Vector2(spawn_border, screen_height // 3 * 2),
        pygame.math.Vector2(screen_width - spawn_border, screen_height // 3),
        pygame.math.Vector2(screen_width - spawn_border, screen_height // 3 * 2)
        ]

render_fps = False

spaceship = Spaceship(spaceship_color) 
spaceship.translate(pygame.math.Vector2(screen_width//2,screen_height//2))

# music initialization
pygame.mixer.music.load("space_music.ogg")

# play music loop endlessly
pygame.mixer.music.play(-1)

# main game loop
running = True
pause = False
while running:

    # limit to 60 FPS
    time_passed = clock.tick(60)

    current_fps = clock.get_fps()
    if (current_fps <= 0):
        current_fps = 60

    fps_factor = 60 / current_fps

    if game_over:
        pause = False

    for event in pygame.event.get():
        # if the program is quit break the game loop
        if event.type == pygame.QUIT:
            running = False
        # check pause input
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not game_over:
            pause = not pause
            if pause:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
        # check fps rendering
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            render_fps = not render_fps
        # fire shots if necessary
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and not spaceship_destroyed and not pause:
            if len(fired_shots) < shot_limit:
                shot_fired = True
        # create new ship if allowed
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and spaceship_destroyed and not game_over and not pause:
            spaceship_destroyed = False

    # game logic is only applied if not paused    
    if not pause:
        # check inputs
        if not spaceship_destroyed:
            if pygame.key.get_pressed()[pygame.K_RIGHT] == True:
                spaceship.rotate(1.5 * fps_factor)
            if pygame.key.get_pressed()[pygame.K_LEFT] == True:
                spaceship.rotate(-1.5 * fps_factor)
            if pygame.key.get_pressed()[pygame.K_UP] == True:
                spaceship.add_thrust(0.1 * fps_factor)

        # check if we need to progress to the next level
        if not asteroids:
            level = min(9, level + 1)
            random.shuffle(asteroid_spawn_positions)
            for i in range(0, level):
                # create n asteroids in level n
                asteroid = Asteroid(50, 11, [ c + min(255, int(random.uniform(-15,15))) for c in asteroid_color] )
                # find the spawn position that maximizes distance to all of the game objects (TODO: revise)
                max_dist = 0
                spawn_pos = pygame.math.Vector2(0,0)
                for pos in asteroid_spawn_positions:
                    min_dist_vec = (spaceship.get_translation() - pos).length_squared()
                    for a in asteroids:
                        min_dist_vec = min(min_dist_vec, (a.get_translation() - pos).length_squared())
                    if min_dist_vec > max_dist:
                        max_dist = min_dist_vec
                        spawn_pos = pos
                asteroid.set_translation(pygame.math.Vector2(spawn_pos))
                # set a direction that more or less moves towards the screen center
                a_dir = pygame.math.Vector2(screen_width // 2, screen_height // 2) - asteroid.get_translation() 
                a_dir.rotate_ip(random.uniform(-35, 35))
                asteroid.set_direction(a_dir.normalize())
                asteroid.set_speed(asteroid.get_speed() + level / 10)
                asteroids.append(asteroid)

        # object movement
        if not spaceship_destroyed:
            spaceship.move(1 * fps_factor)
            spaceship.screen_wrap(screen_width, screen_height)

        for s in fired_shots:
            s.move(1 * fps_factor)
            s.screen_wrap(screen_width, screen_height)

        if shot_fired:
            # create a new shot
            position = spaceship.get_tip_position()
            displacement_vector = pygame.math.Vector2(0,-1)
            displacement_vector.rotate_ip(spaceship.get_rotation_angle())
            s = LaserShot(position + displacement_vector, displacement_vector, spaceship.get_rotation_angle(), max_shot_range)
            s.set_speed(6)
            fired_shots.append(s)
            shot_fired = False

        for a in asteroids:
            a.move(1 * fps_factor)
            a.screen_wrap(screen_width, screen_height)

        for d in debris_objects:
            d.move(1 * fps_factor)
            d.screen_wrap(screen_width, screen_height)

        # check collisions
        # 1. shots against asteroids
        for s in fired_shots:
            for a in asteroids:
                collide = collision_test_with_screen_wraps(s, a)
                if collide:
                    # player hit an asteroid -> points
                    if not game_over:
                        points = min(99999999, points + asteroid_points)
                    # destroy objects
                    s.set_destroyed()
                    a.set_destroyed()
                    a.set_destruction_vector(s.get_direction())
                    a.set_destruction_speed(s.get_speed() / 2)

        # 2. shots against player will just be destroyed
        if not spaceship_destroyed:
            for s in fired_shots:
                collide = collision_test_with_screen_wraps(s, spaceship)
                if collide:
                    s.set_destroyed()

        # 3. player against asteroids
        if not spaceship_destroyed:
            for a in asteroids:
                collide = collision_test_with_screen_wraps(spaceship, a)
                if collide:
                    a.set_destroyed()
                    d_vec = (a.get_translation() - spaceship.get_translation() + spaceship.get_direction()).normalize()
                    a.set_destruction_vector(d_vec)
                    spaceship.set_destroyed()

        # 4. asteroids against asteroids
        for i in range(0, len(asteroids)-1):
            for j in range(i+1, len(asteroids)):
                collide = collision_test_with_screen_wraps(asteroids[i], asteroids[j])
                if collide:
                    asteroids[i].set_destroyed()
                    #asteroids[i].set_destruction_vector(asteroids[j].get_direction())
                    d_vec1 = (asteroids[i].get_translation() - asteroids[j].get_translation() + asteroids[j].get_direction()).normalize()
                    asteroids[i].set_destruction_vector(d_vec1)
                    asteroids[i].set_destruction_speed(asteroids[j].get_speed())

                    asteroids[j].set_destroyed()
                    #asteroids[j].set_destruction_vector(asteroids[i].get_direction())
                    d_vec2 = (asteroids[j].get_translation() - asteroids[i].get_translation() + asteroids[i].get_direction()).normalize()
                    asteroids[j].set_destruction_vector(d_vec2)
                    asteroids[j].set_destruction_speed(asteroids[i].get_speed())

        # do not check debris for collisions to save time every frame
        # TODO: do a coarser collision test, e.g., spheres or bounding boxes?
        # shots, player, and asteroids against debris: just remove debris
        #for s in fired_shots:
        #    for d in debris_objects:
        #        if collision_test_with_screen_wraps(s, d, screen_width, screen_height):
        #            d.set_destroyed()
        #for a in asteroids:
        #    for d in debris_objects:
        #        if collision_test_with_screen_wraps(a, d, screen_width, screen_height):
        #            d.set_destroyed()
        #if not spaceship_destroyed:
        #    for d in debris_objects:
        #        if collision_test_with_screen_wraps(d, spaceship, screen_width, screen_height):
        #            d.set_destroyed()

        # handle events when an asteroid is destroyed   
        for a in asteroids:
            if a.destroyed():
                # generate random debris particles within the radius of the old asteroid
                m_pos = a.get_translation()
                radius = a.get_radius()
                for i in range(0, radius):
                    current_radius = random.uniform(radius / 4, radius)
                    current_direction = pygame.math.Vector2(0, 1)
                    current_direction.rotate_ip(random.uniform(0, 360))
                    current_pos = m_pos + current_radius * current_direction
                    new_debris = Debris(current_pos, [ min(255, c + int(random.uniform(-15,15))) for c in a.get_color()] )
                    move_dir = current_direction.rotate(random.uniform(-15,15)).normalize()
                    new_debris.set_direction(move_dir)
                    new_debris.set_speed((a.get_destruction_speed() + a.get_speed()) / random.uniform(2.5,3.5))
                    debris_objects.append(new_debris)

                # for large asteroids: create smaller asteroids
                if radius // 2 > 10:
                    new_num_verts = max(3, a.get_num_vertices() - 2)
                    new_radius1 = radius // 2 + int(random.uniform(-4, 5))
                    new_radius2 = radius // 2 + int(random.uniform(-4, 5)) 
                    dist_axis = a.get_destruction_vector().normalize().rotate(90)
                    pos1 = m_pos + dist_axis * (new_radius1 * 1.5)
                    pos2 = m_pos - dist_axis * (new_radius2 * 1.5)
                    dir1 = dist_axis.rotate(random.uniform(-30, 30))
                    dir2 = dist_axis.rotate(180 + random.uniform(-30,30))

                    a1 = Asteroid(new_radius1, new_num_verts,  [ c + min(255, int(random.uniform(-15,15))) for c in asteroid_color] )
                    a2 = Asteroid(new_radius2, new_num_verts,  [ c + min(255, int(random.uniform(-15,15))) for c in asteroid_color] )

                    a1.set_translation(pos1)
                    a1.set_direction(dir1)
                    a1.set_speed((a.get_destruction_speed() + a.get_speed()) / random.uniform(2,3))
                    asteroids.append(a1)

                    a2.set_translation(pos2)
                    a2.set_direction(dir2)
                    a2.set_speed((a.get_destruction_speed() + a.get_speed()) / random.uniform(2,3))
                    asteroids.append(a2)

        for s in fired_shots:
            if s.destroyed():
                # generate random debris particles
                m_pos = s.get_translation()
                radius = 5
                for i in range(0, radius):
                    current_radius = random.uniform(radius / 2, radius)
                    current_direction = pygame.math.Vector2(0, 1)
                    current_direction.rotate_ip(random.uniform(0, 360))
                    current_pos = m_pos + current_radius * current_direction
                    new_debris = Debris(current_pos, [ min(255, c + int(random.uniform(-15,15))) for c in s.get_color()] )
                    move_dir = current_direction.rotate(random.uniform(-15,15)).normalize()
                    new_debris.set_direction(move_dir)
                    debris_objects.append(new_debris)

        # handle events when player spaceship is destroyed
        if spaceship.destroyed():
            m_pos = spaceship.get_translation()
            radius = 20
            for i in range(0, radius):
                current_radius = random.uniform(radius / 4, radius)
                current_direction = pygame.math.Vector2(0, 1)
                current_direction.rotate_ip(random.uniform(0, 360))
                current_pos = m_pos + current_radius * current_direction
                new_debris = Debris(current_pos, [ min(255, c + int(random.uniform(-15,15))) for c in spaceship.get_color()] )
                move_dir = current_direction.rotate(random.uniform(-15,15)).normalize()
                new_debris.set_direction(move_dir)
                new_debris.set_speed((a.get_destruction_speed() + a.get_speed()) / random.uniform(2.5,3.5))
                debris_objects.append(new_debris)

            lifes = lifes - 1
            spaceship_destroyed = True
            if lifes < 1:
                game_over = True

            spaceship = Spaceship(spaceship_color) 
            spaceship.set_translation(pygame.math.Vector2(screen_width//2,screen_height//2))


        # remove destroyed objects
        asteroids = [a for a in asteroids if not a.destroyed()]
        fired_shots = [s for s in fired_shots if not s.destroyed() ]
        debris_objects = [d for d in debris_objects if not d.destroyed() ]

    # RENDERING (is also done in pause)

    # Redraw the background
    screen.fill(bg_color)

    # Draw objects
    if not spaceship_destroyed:
        spaceship.render_with_screen_wraps(screen)
    for a in asteroids:
        a.render_with_screen_wraps(screen)
    for s in fired_shots:
        s.render_with_screen_wraps(screen)
    for d in debris_objects:
        d.render_with_screen_wraps(screen)

    # Render FPS
    if render_fps:
        text = "FPS: " + "{0:.1f}".format(current_fps)
        text = font.render(text, True, text_color)
        screen.blit(text, (5, 5))

    # render score and level
    score_text = "Score: " + str(points).zfill(8)    
    score_text = font.render(score_text, True, text_color)
    screen.blit(score_text, (screen_width - score_text.get_width() - 5, 5))
    level_text = "Level: " + str(level)
    level_text = font.render(level_text, True, text_color)
    screen.blit(level_text, (screen_width - score_text.get_width() - 5, 5 + score_text.get_height() + 5))
    lifes_text = "Ships: " + str(lifes)
    lifes_text = font.render(lifes_text, True, text_color)
    screen.blit(lifes_text, (screen_width - score_text.get_width() - 5, 5 + score_text.get_height() + 5 + level_text.get_height() + 5))

    # Render destroyed message and game over
    if spaceship_destroyed and not pause:
        destroyed_text = "Press Space for new ship"
        if game_over:
            destroyed_text = "G A M E   O V E R"
        destroyed_text = pause_font.render(destroyed_text, True, text_color)
        screen.blit(destroyed_text, (screen_width // 2 - destroyed_text.get_width() // 2, screen_height // 2 - destroyed_text.get_height() // 2))    

    # if paused, render pause text
    if pause:
        pause_text = "P A U S E"
        pause_text = pause_font.render(pause_text, True, text_color)
        screen.blit(pause_text, (screen_width // 2 - pause_text.get_width() // 2, screen_height // 2 - pause_text.get_height() // 2))

    # Buffer swap
    pygame.display.flip()

# After the game loop: exit
pygame.mixer.music.stop()
exit_game()
pygame.quit()
