# blynk-hardware


Install blynk client:
    blynk = blynklib.Hardware()

Decorator @blynk.route(name, pin):
    name - pin name, example: vr, vw, dw,dr,ar,aw
    pin  - pin number, example: 1,2,3,... 

Decorator @blynk.timer(timer):
    timer - how many milliseconds to execute a function

Connect to Server BLYNK (True, False):
    blynk.connect():

Log in to the server (True, False):
    blynk.auth(TOKEN):

Run loop client:
    while True:
        blynk.run()
        
