from operator import add
from functools import reduce
import pygame
import neat
import random
import time
import os
pygame.font.init()

# Window Vars
WIN_WIDTH = 500
WIN_HEIGHT = 500
STATS_WIDTH = 0
STATS_HEIGHT = 150
WINDOW_NAME = "Loopover"
TILE_FONT = pygame.font.SysFont('Inconsolata-Regular.ttf',int((WIN_WIDTH/5)/1.14))
CONTROLS_FONT = pygame.font.SysFont('Inconsolata-Regular.ttf',int(STATS_HEIGHT/2.3))
TIMER_FONT = pygame.font.SysFont('Inconsolata-Regular.ttf',int(STATS_WIDTH/6))

WIN = pygame.display.set_mode((WIN_WIDTH+STATS_WIDTH,WIN_HEIGHT+STATS_HEIGHT))
pygame.display.set_caption(WINDOW_NAME)

TIME_PLACES = 2
FPS = 60
gen = 0

WHITE = (255,255,255)
BLACK = (0,0,0)
GREEN = (64,220,64)
ORANGE= (200,80,40)
PURPLE= (220,20,250)
TEAL  = (50,220,190)
BG    = (30,30,30)
TX    = (200,200,200)

class Tile:
        def __init__(self, id, s):
            self.id = id
            n = id-1
            red = int(n%s) * (250/(s-1))
            blue = 250 - int(n%s) * (250/(s-1))
            green = int(n/s) * (250/(s-1))
            self.color = (red,green,blue)

        def draw(self, win, x, y, width, height):
            display = str(self.id)
            text = TILE_FONT.render(display, True, BLACK)
            tile = pygame.Surface((width, height))
            tile.fill(self.color)
            text_rect = text.get_rect(center = tile.get_rect().center)
            tile.blit(text, text_rect)
            win.blit(tile, (x, y))

class Board:
    SCRAMBLE_TURNS = 5

    def __init__(self, size = 5):
        self.game = False
        self.end_time_v = 0
        self.start_time_v = 0
        self.content = []
        self.size = size
        self.moves = 0
        for i in range(size):
            self.content.append([])
            for j in range(size):
                self.content[i].append(Tile(i + j*size + 1, size))

    def move(self, row, column, x, y):
        new_row = []
        new_column = []

        for i in range(self.size):
            new_row.append(self.content[(i+x)%self.size][row])
        for i in range(self.size):
            self.content[i][row] = new_row[i]

        for i in range(0,self.size):
            new_column.append(self.content[column][(i+y)%self.size])
        for i in range(0,self.size):
            self.content[column] = new_column

        self.moves += 1

    def draw(self, win):
        for i in range(0,self.size):
            for j in range(0,self.size):
                w = (WIN_WIDTH // self.size)
                h = (WIN_HEIGHT // self.size)
                x = i * w
                y = j * h
                self.content[i][j].draw(win, x, y, w, h)

    def scramble(self, gen):
        self.SCRAMBLE_TURNS = (gen) % 15 + 1
        for i in range(self.SCRAMBLE_TURNS):
            o = random.randint(0,3)
            if o == 0:
                self.move(random.randint(0,self.size-1), 0, -1, 0)
            elif o == 1:
                self.move(random.randint(0,self.size-1), 0, 1, 0)
            elif o == 2:
                self.move(0, random.randint(0,self.size-1), 0, -1)
            else:
                self.move(0, random.randint(0,self.size-1), 0, 1)
        self.moves = 0

    def is_solved(self):
        solved = self.size**2
        for i in range(0,self.size):
            for j in range(0,self.size):
                if self.content[i][j].id != i+j*self.size+1:
                    solved -= 1
        return solved / self.size**2

    def start_time(self):
        self.start_time_v = time.monotonic()
        self.game = True

    def end_time(self):
        self.end_time_v = time.monotonic()

    def get_time(self):
        if (not(self.is_solved() == 1)) and self.game:
            return (time.monotonic() - self.start_time_v , TX)
        elif self.is_solved() == 1 and self.game:
            return (self.end_time_V - self.start_time_v , GREEN)
        else:
            return (0 , TX)

def draw_window(win, board, gen):
    win.fill(BG)

    time = board.get_time()
    time_str =  "{0:0{r_round}.{TIME_PLACES}f}".format(time[0],TIME_PLACES=TIME_PLACES,r_round=1+TIME_PLACES+3)
    
    #render boring stuff
    text_timer = CONTROLS_FONT.render(time_str,True,time[1])
    text_moves = CONTROLS_FONT.render(str(board.moves).zfill(3),True,time[1])
    win.blit(text_timer,(0,WIN_HEIGHT))
    win.blit(text_moves,(0,int(WIN_HEIGHT+(STATS_HEIGHT/2))))

    # Render Board
    board.draw(win)

    # generations
    score_label = CONTROLS_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - 10 - score_label.get_rect().width, WIN_HEIGHT))

    pygame.display.update()

def eval_genomes(genomes, config):
    global WIN, gen
    win = WIN
    gen += 1

    nets = []
    boards = []
    ge = []
    last = []

    for genome_id, genome in genomes:
        genome.fitness = 0  # start with fitness level of 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        boards.append(Board())
        boards[-1].scramble(gen)
        ge.append(genome)
        boards[-1].start_time()
        last.append(0)

    clock = pygame.time.Clock()
    #last_was_Q = False
    pygame.time.set_timer(pygame.USEREVENT+1,int((1/FPS)*1000))
    #setup event que
    pygame.event.set_allowed(None)
    pygame.event.set_allowed(pygame.USEREVENT+1)
    pygame.event.set_allowed(pygame.KEYDOWN)
    pygame.event.set_allowed(pygame.QUIT)
    pygame.event.set_allowed(pygame.MOUSEBUTTONDOWN)
    pygame.event.set_allowed(pygame.MOUSEBUTTONUP)

    running = True
    while running and len(boards) > 0:
        clock.tick(30)

        draw_window(win, boards[0], gen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                break

        for x, board in enumerate(boards):
            ge[x].fitness += board.is_solved() / 10

            board_state = []
            for i in range(board.size):
                for j in range(board.size):
                    board_state.append(board.content[i][j].id)

            output = nets[x].activate(board_state)

            # AI move logic
            pos = 0
            if output[2] > 0:
                pos += 1
            if output[3] > 0:
                pos += 1
            if output[4] > 0:
                pos += 1
            if output[5] > 0:
                pos += 1

            if pos != last[x]:
                ge[x].fitness += 0.1
                last[x] = pos

            if output[0] > 0:
                if output[1] > 0: board.move(pos, 0, -1, 0)
                else: board.move(pos, 0, 1, 0)
            else:
                if output[1] > 0: board.move(0, pos, 0, -1)
                else: board.move(0, pos, 0, 1)

        # Check for win
        for board in boards:
            if board.is_solved() == 1:
                board.end_time()
                ge[boards.index(board)].fitness += (60 * (gen + 1)) / (board.start_time_v - board.end_time_v)**2 / (board.moves)
                nets.pop(boards.index(board))
                ge.pop(boards.index(board))
                boards.pop(boards.index(board))

        # Check for lose
        if boards[0].get_time()[0] > 60:
            for board in boards[::-1]:
                board.end_time()
                nets.pop()
                ge.pop()
                boards.pop()

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(eval_genomes, 100)
    print('\nBest genome:\n{!s}'.format(winner))
    input()

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)