#-------------------------------------------------------------------
# UK MSF Radio Time Signal Decoder for RPi PICO
#
# https://en.wikipedia.org/wiki/Time_from_NPL_(MSF)
#
# Data Format: http://www.npl.co.uk/upload/pdf/MSF_Time_Date_Code.pdf
#
# The MSF radio signal operates on a frequency of 60 kHz and carries the current
# UK time and date that can be received and decoded in UK.
#
# Each second contains an  'A' & 'B' bit that can be decoded every minute.
# Parity bits are included in the data
#-------------------------------------------------------------------

from machine import Pin
from machine import Timer, Pin
from time import sleep
import time
import array


MINUTE_SECONDS = 60

previous_time = 0
previous_signal = 0

year = 0
month = 0
dayofmonth = 0
dayofweek = 0
hour = 0
minute = 0
seconds_count = 0

dst = 0

seq_start = False

a = array.array('i', (0 for _ in range(MINUTE_SECONDS))) # a codes
b = array.array('i', (0 for _ in range(MINUTE_SECONDS))) # b codes

bcdlist = [80, 40, 20, 10, 8, 4, 2, 1]

daysofweek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
months = [ '-', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec' ]
timezone = [ 'GMT', 'BST' ]
gpio_msf = Pin(15, mode=Pin.IN, pull=Pin.PULL_UP)


######################################################
# check 'a' Bits 52-29 signature 01111110
######################################################
def check_signature():
    global a
    result = 0
    if a[52] == 0 and a[53] == 1 and a[54] == 1 and a[55] == 1 and a[56] == 1 and a[57] == 1 and a[58] == 1 and a[59] == 0:
        result = 1
        
    return result

######################################################
# check data parity
# Parity provides odd number of bits set to '1'
######################################################
def check_parity( start, length, parity ):
    global a
    global b
    
    sum = 0

    for x in range(start, start+length):
        sum += a[x]

    sum += b[parity]

    result = (sum % 2)
    return result


######################################################
# convert MSF data to BCD values
######################################################
def convert_bcd_value( start, len ):
    val = 0;

    digit = 8 - len;

    for x in range(start, start+len):
        val += (a[x] * bcdlist[digit])
        digit += 1

    return val


######################################################
# decode date & time using 'a' codes
######################################################
def decode_time():
    global year
    global month
    global dayofmonth
    global dayofweek
    global hour
    global minute
 
    result = 1
    if check_signature() == 0:
        print("check signature failed")
        result = 0
    else:
        year = 0
        if check_parity(17, 8, 54)  == 1:
            year = convert_bcd_value( 17, 8 )
            print("year=", year)
        else:
            print("year parity failed")
            result = 0
                
        month = 0
        dayofmonth = 0
        if check_parity(25, 11, 55) == 1:
            month = convert_bcd_value( 25, 5 )
            print("month=", month)            

            dayofmonth = convert_bcd_value( 30, 6 )
            print("dayofmonth=", dayofmonth)
        else:
            print("month parity failed")
            result = 0

        dayofweek = 0
        if check_parity(36, 3, 56) == 1:
            dayofweek = convert_bcd_value( 36, 3 )
            print("dayofweek=", dayofweek)
        else:
            print("day parity failed")
            result = 0

        hour = 0
        minute = 0
        if check_parity(39, 13, 57) == 1:
            hour = convert_bcd_value( 39, 6 )
            print("hour=", hour)
            
            minute = convert_bcd_value( 45, 7 )
            print("minute=", minute)
        else:
            print("time parity failed")
            result = 0
    
        dst = b[58]
        print("dst bit:", dst)
        
        return result


######################################################
# process input signal sequence and covert to
# 'a' and 'b' codes 
######################################################
def process_input_change( signal, interval ):
    global seq_start
    global seconds_count
    global a
    global b
    
    if seq_start == True:
        #print(signal, interval)
        if signal == 0:
            # signal low
            if interval > 450 and interval < 550:
                # minute marker
                a[0] = 0
                b[0] = 0
                seconds_count = 1
                
            elif interval > 250 and interval < 350:
                # 300ms => a=1 b=1
                #print("11")
                a[seconds_count] = 1
                b[seconds_count] = 1
                
            elif interval > 150 and interval < 250:
                # 200ms => a=1 b=0
                #print("10")
                a[seconds_count] = 1
                b[seconds_count] = 0
                
            elif interval > 50 and interval < 150:
                # 100ms => a=0 b=0 or a=0 b=1
                #print("00")
                a[seconds_count] = 0
                b[seconds_count] = 0
 
        else:
            # signal high
            if interval > 450 and interval < 550:
                # minute marker
                seconds_count = 1
                print("T=", seconds_count)
                #if seq_end == False:
                #    print("seq end")
                #    seq_end = True
            elif interval > 50 and interval < 150:
                # 100ms => a=0 b=1
                #print("01")
                a[seconds_count] = 0
                a[seconds_count] = 1
            elif interval > 650:
                seconds_count += 1
                print("T=", seconds_count)
            
    else:
        if signal == 0 and interval > 450:
            print("seq start")
            seq_start = True
            a[0] = 0
            b[0] = 0
            seconds_count = 1


######################################################
# check MSF signal and process state change
######################################################
def check_msf_signal():
    global previous_signal
    global previous_time
    
    current_time = time.ticks_ms()
    current_signal = gpio_msf.value()

    # signal state has changed
    if current_signal == previous_signal:
        time.sleep_ms(10)
    else:
        process_input_change( current_signal, current_time - previous_time )
        previous_time = current_time
        previous_signal = current_signal


######################################################
# program loop tasks
######################################################
def main_loop():
    global seconds_count
    
    check_msf_signal()
    
    if seconds_count == (MINUTE_SECONDS-1):
        if decode_time() == 1:
            print( year, months[month], dayofmonth, daysofweek[dayofweek], hour, minute, timezone[dst])
        seconds_count = 0


######################################################
# main program body
######################################################
if __name__ == "__main__":
#    while seq_start == False or seq_end == False:
    while True:
        main_loop()

