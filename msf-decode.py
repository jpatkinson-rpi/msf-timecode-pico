#-------------------------------------------------------------------
# This script decodes MSF timecode 60KHz signal for RPI PICO
#-------------------------------------------------------------------

from machine import Pin
from machine import Timer, Pin
from time import sleep
import array

timer_count = 0 # global variable
last_timer_count = 0 # global variable
   
irq_count = 0 # global variable
irq_time = array.array('i', (0 for _ in range(100)))
irq_state = array.array('i', (0 for _ in range(100)))
seq_start = False
irq_end = False

#pin_button = Pin(15, mode=Pin.IN, pull=Pin.PULL_NONE)
pin_led    = Pin(14, mode=Pin.OUT)
gpio_irq = Pin(15, mode=Pin.IN, pull=Pin.PULL_UP)
    
def irq_triggered(pin):
    global irq_count
    global last_timer_count
    global irq_time
    global irq_state
    global irq_end
    flags = pin.irq().flags()
    timer_count=time.ticks_ms()
    #print( flags & Pin.IRQ_RISING, (timer_count-last_timer_count) )
    irq_time[irq_count]=(timer_count-last_timer_count)
    if pin.irq().flags() & Pin.IRQ_RISING :
        irq_state[irq_count]=1
    else:
        irq_state[irq_count]=0
    last_timer_count=timer_count
    if irq_time[irq_count] > 490 and irq_time[irq_count] < 510:
        irq_end=True
    else:
        irq_count += 1



if __name__ == "__main__":
    pin_led.value(0)
    last_timer_count=time.ticks_ms()
    #soft_timer = Timer(mode=Timer.PERIODIC, period=10, callback=interruption_handler)
    gpio_irq.irq(handler=irq_triggered, trigger=Pin.IRQ_FALLING|Pin.IRQ_RISING)
    #pin_button.irq(trigger=Pin.IRQ_RISING,handler=button_isr)
    while True:
        while not(irq_end):
            sleep(0.1)
            pin_led.value(1)
            sleep(0.1)
            pin_led.value(0)
            sleep(0.2)
            pin_led.value(1)
            sleep(0.2)
            pin_led.value(0)
            sleep(0.3)
            pin_led.value(1)
            sleep(0.3)
            pin_led.value(0)
            sleep(0.4)
            pin_led.value(1)
            sleep(0.4)
            pin_led.value(0)
            sleep(0.5)
            pin_led.value(1)
            sleep(0.5)
            pin_led.value(0)
        for i in range(irq_count):
            print(irq_state[i], irq_time[i])
        irq_count=0
        irq_end=False
