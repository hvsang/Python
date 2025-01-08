import random
from os import system
from time import sleep

colors = ['\033[1;31m', '\033[33m', '\033[1;34m']

system('')

f = open("santa_claus.txt", "r")
santa_claus = f.read()

while True:
    i = random.randint(0, 2)
    print(colors[i] + santa_claus)
    sleep(0.1)
    system('cls')
