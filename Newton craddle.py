import pygame
import math
import sys

# Pygame Initialize
pygame.init()


# Constants

WIDTH, HEIGHT = 800, 600
FPS = 60
Radius_Of_Ball = 25
number_Of_Balls = 5
cable_length = 200           # pixels
pix_to_meter = 0.003        # 1 pixel ~ 0.003 meters (~0.6m pendulum)
gravity = 9.81                # real gravity
DAMPING = .9999
AIR_RESISTANCE = .9995
MAX_LIFT_ANGLE = math.radians(80)  # limit max lift angle

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
BLUE = (70, 130, 180)


try:
    cat_pic = pygame.image.load("cat_playing.jpeg")
    image_width, image_height = cat_pic.get_size()
    width_scale = WIDTH / image_width
    height_scale = HEIGHT / image_height
    scale = min(width_scale, height_scale)  # fit without cropping

    New_width = int(image_width * scale)
    New_height = int(image_height * scale)

    cat_pic = pygame.transform.smoothscale(cat_pic, (New_width, New_height))
    bg_x = (WIDTH - New_width) // 2
    bg_y = (HEIGHT - New_height) // 2
except:
    cat_pic = None
    bg_x = bg_y = 0


# Ball Class
class PENDULUM_BOB:
    def __init__(self, x, y, index):
        self.rest_x = x
        self.rest_y = y
        self.x = x
        self.y = y
        self.angle = 0
        self.angular_velocity = 0
        self.index = index
        self.drag = False
        self.pivot_x = x
        self.pivot_y = y - cable_length

    def update(self):
        if not self.drag:
            L = cable_length * pix_to_meter                        #Converts the pixel size to the physical length in meters.
            angular_accel = -(gravity / L) * math.sin(self.angle)     #Calculates the force (torque) applied by gravity.
            self.angular_velocity += angular_accel / FPS
            self.angular_velocity *= AIR_RESISTANCE
            self.angular_velocity *= DAMPING
            self.angle += self.angular_velocity / FPS

            # Update position
            self.x = self.pivot_x + cable_length * math.sin(self.angle)
            self.y = self.pivot_y + cable_length * math.cos(self.angle)

    def draw(self, screen):
        pygame.draw.line(screen, GRAY, (self.pivot_x, self.pivot_y),
                         (int(self.x), int(self.y)), 2)
        color = RED if self.drag else BLUE
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), Radius_Of_Ball)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), Radius_Of_Ball, 2)

    def get_lin_velocity(self):
        L = cable_length * pix_to_meter
        return self.angular_velocity * L

    def set_lin_velocity(self, v):              #transfers linear V from one ball to another, converting back to angular V
        L = cable_length * pix_to_meter
        self.angular_velocity = v / L

# Newton's Cradle Class
class CRADLE_SIMULATOR:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Ms Y Cradle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)

        self.balls = []
        self.running = True

        self.display_angle = 0
        self.lift_angle_locked = False
        self.start_time = None
        self.elapsed_time = 0
        self.last_collision_velocity = 0

        # Create balls
        START_X = WIDTH // 2 - (number_Of_Balls - 1) * Radius_Of_Ball
        for i in range(number_Of_Balls):
            x = START_X + i * (Radius_Of_Ball * 2)
            y = HEIGHT // 2 + 100
            self.balls.append(PENDULUM_BOB(x, y, i))

    # Collision & energy transfer
    def process_collisions(self):
        # LEFT → RIGHT
        for k in range(number_Of_Balls - 1):
            b1 = self.balls[k]
            b2 = self.balls[k + 1]
            if abs(b2.x - b1.x) <= Radius_Of_Ball * 2.1:
                V1 = b1.get_lin_velocity()
                V2 = b2.get_lin_velocity()
                if V1 > 0.001 and V1 > V2 + 0.001:
                    Station = 0
                    for j in range(k + 1, number_Of_Balls):
                        if abs(self.balls[j].get_lin_velocity()) < 0.001 and abs(self.balls[j].angle) < 0.001:
                            Station += 1
                        else:
                            break
                    index_last_one = k + Station
                    if index_last_one < number_Of_Balls:
                        for j in range(k, index_last_one):
                            self.balls[j].set_lin_velocity(0)
                            self.balls[j].angle = 0
                        self.balls[index_last_one].set_lin_velocity(V1)
                        self.last_collision_velocity = V1

        # RIGHT → LEFT
        for k in range(number_Of_Balls - 1, 0, -1):
            b1 = self.balls[k]
            b2 = self.balls[k - 1]
            if abs(b2.x - b1.x) <= Radius_Of_Ball * 2.1:
                V1 = b1.get_lin_velocity()
                V2 = b2.get_lin_velocity()
                if V1 < -0.001 and V1 < V2 - 0.001:
                    Station = 0
                    for j in range(k - 1, -1, -1):
                        if abs(self.balls[j].get_lin_velocity()) < 0.001 and abs(self.balls[j].angle) < 0.001:
                            Station += 1
                        else:
                            break
                    index_last_one = k - Station
                    if index_last_one >= 0:
                        for j in range(index_last_one + 1, k + 1):
                            self.balls[j].set_lin_velocity(0)
                            self.balls[j].angle = 0
                        self.balls[index_last_one].set_lin_velocity(V1)
                        self.last_collision_velocity = abs(V1)

    # Input events
    def events_handle(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                pressed = None
                for i, b in enumerate(self.balls):
                    if math.dist((b.x, b.y), (mx, my)) <= Radius_Of_Ball:
                        pressed = i
                        break
                if pressed is not None:
                    self.lift_angle_locked = False
                    if pressed <= number_Of_Balls // 2:
                        for j in range(pressed + 1):
                            self.balls[j].drag = True
                    else:
                        for j in range(pressed, number_Of_Balls):
                            self.balls[j].drag = True

            elif event.type == pygame.MOUSEBUTTONUP:
                for b in self.balls:
                    b.drag = False
                self.lift_angle_locked = True

            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                mx, my = event.pos
                dragging = [b for b in self.balls if b.drag]
                if dragging:
                    first = dragging[0]
                    dx = mx - first.pivot_x
                    dy = my - first.pivot_y
                    angle = math.atan2(dx, dy)
                    angle = max(-MAX_LIFT_ANGLE, min(MAX_LIFT_ANGLE, angle))
                    self.display_angle = math.degrees(angle)
                    for b in dragging:
                        b.angle = angle
                        b.angular_velocity = 0
                        b.x = b.pivot_x + cable_length * math.sin(angle)
                        b.y = b.pivot_y + cable_length * math.cos(angle)

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_r, pygame.K_SPACE):
                    self.reset_game()

     # Reset cradle
    def reset_game(self):
        for b in self.balls:
            b.angle = 0
            b.angular_velocity = 0
            b.x = b.rest_x
            b.y = b.rest_y
            b.drag = False
        self.start_time = None
        self.elapsed_time = 0
        self.display_angle = 0
        self.lift_angle_locked = False
        self.last_collision_velocity = 0

    # Main loop
    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.events_handle()

            for b in self.balls:
                b.update()

            self.process_collisions()

            # Start timer
            if self.start_time is None:
                for b in self.balls:
                    if abs(b.angular_velocity) > 0.001:
                        self.start_time = pygame.time.get_ticks()
                        break
            if self.start_time:
                self.elapsed_time = (pygame.time.get_ticks() - self.start_time) / 1000

            # Draw background
            if cat_pic:
                self.screen.fill(WHITE)
                self.screen.blit(cat_pic, (bg_x, bg_y))
            else:
                self.screen.fill(WHITE)

            # Draw pivot line
            yPivot = self.balls[0].pivot_y
            pygame.draw.line(self.screen, BLACK,
                             (WIDTH // 2 - 200, yPivot),
                             (WIDTH // 2 + 200, yPivot), 4)

            # Draw balls
            for b in self.balls:
                b.draw(self.screen)

            # UI
            Time = self.font.render(f"Time: {self.elapsed_time:.2f} s", True, RED)
            self.screen.blit(Time, (WIDTH // 2 - Time.get_width() // 2, 20))

            I_Text = self.font.render("Drag balls to pull | R/SPACE to Reset", True, RED)
            self.screen.blit(I_Text, (30, 60))

            A_Text = self.font.render(
                ("Initial Angle: " if self.lift_angle_locked else "Lift Angle: ") +
                f"{self.display_angle:.1f}°", True, RED
            )
            self.screen.blit(A_Text, (30, 90))

            Velocity_Text = self.font.render(
                f"Last Collision Velocity: {self.last_collision_velocity:.3f} m/s", True, RED
            )
            self.screen.blit(Velocity_Text, (30, 120))

            # Bottom credits
            credit_one = self.font.render("Newton's Cradle – made by:", True, RED)
            credit_two = self.font.render(
                "Ignacio Penaloza", True, RED
            )
            self.screen.blit(credit_one, (WIDTH // 2 - credit_one.get_width() // 2, HEIGHT - 60))
            self.screen.blit(credit_two, (WIDTH // 2 - credit_two.get_width() // 2, HEIGHT - 30))

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# Run Simulation
if __name__ == "__main__":
    CRADLE_SIMULATOR().run()
