__author__ = 'kalipsoaqua'

import blynklib
import sys
import random

TOKEN = '3ab3605dafeb4e30bae01a214e2039d8'


blynk = blynklib.Hardware(server='127.0.0.1')


@blynk.route(name='vr', pin=1)
def vr1(**kwargs):
    print("Читаю vr 1", kwargs)
    blynk.send('vw', kwargs['pin'], random.randint(50, 70))

@blynk.route(name='vw', pin=9)
def vw9(**kwargs):
    print("Пишу ", kwargs)

@blynk.timer(timer=10000)
def timer1(**kwargs):
    print('Тимер 1', kwargs)



if not blynk.connect():
    print('ERROR: Unable to connect')
    sys.exit(-1)

if not blynk.auth(TOKEN):
    print('ERROR: Unable to auth')
    sys.exit(-1)

try:
    while True:
        blynk.run()
except:
    print(sys.exc_info())