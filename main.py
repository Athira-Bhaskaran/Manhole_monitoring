import RPi.GPIO as GPIO
import time
import threading
import pymysql
import smbus
from flask import *
import json
import telepot

TRIG=26
ECHO=19
IR=13
STAT_LED=21
BUZZ=20
motorF=6
motorR=5
fan=16
exhaust=16

IR_STAT='closed'
GAS_STAT='low'
distance = 0
chat_id=783923173
app=Flask(_name_)
bot=telepot.Bot('6018280638:AAHKG9S-4b5GzJIfC80KB5SLa1c_0YzW0js')

try:
    con=pymysql.connect(host='192.168.43.51',port=3306,user='root',passwd='root',db='manhole')
    cmd=con.cursor()
    print("db config successfull")
except Exception as e:
    print(e)
    print("db config failed")


address=0x48
a0=0x40
bus=smbus.SMBus(1)

GAS_VAL=0

@app.route('/control',methods=['get','post'])
def control():
    try:
        val=request.form['data']
        print(val)
        if val=="A":
            GPIO.output(exhaust,True)
            val=""
        elif val=="B":
            GPIO.output(exhaust,False)
            val=""
        elif val=="C":
            GPIO.output(motorF,True)
            GPIO.output(motorR,False)
            val=""
        elif val=="D":
            GPIO.output(motorF,False)
            GPIO.output(motorR,False)
            val=""
        else:
            val=""
        return jsonify({'status':"success"})
    except Exception as e:
        return jsonify({'status':"failed"})

@app.route('/sensor_reading',methods=['get','post'])
def sensor_reading():
    
    try:
        global IR_STAT
        global GAS_STAT
        global distance 
        return jsonify({'result':'success','ir':str(IR_STAT),'gval':str(GAS_STAT),'dist':str(distance)})
    except Exception as e:
        return jsonify({'status':"failed"})

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(STAT_LED,GPIO.OUT)
    GPIO.setup(BUZZ,GPIO.OUT)
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO,GPIO.IN)
    GPIO.setup(motorF,GPIO.OUT)
    GPIO.setup(motorR,GPIO.OUT)
    GPIO.setup(fan,GPIO.OUT)
    GPIO.setup(exhaust,GPIO.OUT)
    GPIO.setup(IR,GPIO.IN)
    GPIO.output(BUZZ,False)
    GPIO.output(exhaust,False)
    threading.Thread(target=buffering).start()
    threading.Thread(target=cont).start()


def buffering():
    while(1):
        GPIO.output(STAT_LED,True)
        time.sleep(0.5)
        GPIO.output(STAT_LED,False)
        time.sleep(0.5)


def cont():
    count=0
    global IR_STAT
    global GAS_STAT
    global distance 
    while(1):
        GPIO.output(TRIG,False)
        time.sleep(0.00001)
        GPIO.output(TRIG,True)
        time.sleep(0.00001)
        GPIO.output(TRIG,False)
        StartTime=time.time()
        StopTime=time.time()
        while GPIO.input(ECHO) == 0:
            StartTime=time.time()
        while GPIO.input(ECHO) == 1:
            StopTime=time.time()
        TimeElapse=StopTime-StartTime
        distance=round(((TimeElapse*34300)/2),2)
        
        count=count+1
        #print(count)
        #print(distance)
        if GPIO.input(IR)==0:
            IR_STAT='closed'
            GPIO.output(BUZZ,False)
        if GPIO.input(IR)==1:
            IR_STAT='open'
            bot.sendMessage(783923173, "valve is open")
            GPIO.output(BUZZ,True)
        
        bus.write_byte(address,a0)
        GAS_VAL=bus.read_byte(address)
        GAS_VAL=GAS_VAL-120
        #print(GAS_VAL)
        if GAS_VAL>60:
            #print("fan")
            bot.sendMessage(783923173, "poisonous gas detected")
            GPIO.output(fan,True)
        if GAS_VAL<60:
            GPIO.output(fan,False)
            
        
        if distance<10:
            bot.sendMessage(783923173, "BLOCK DETECTED...!!!!!!")
            GPIO.output(motorF,True)
            GPIO.output(motorR,False)
            time.sleep(5)
            GPIO.output(motorF,False)
            GPIO.output(motorR,False)
        if distance>10:
            GPIO.output(motorF,False)
            GPIO.output(motorR,False)
            
        if count>60:
            count=0
            try:
                cmd.execute("insert into data values(null,'"+str(distance)+"','"+str(IR_STAT)+"','"+str(GAS_VAL)+"',curdate(),curtime())")
                con.commit()
            except Exception as e:
                print("updation failed")

        
if _name=="main_":
    main()
    app.run(host='0.0.0.0',port=5000)