#!/usr/bin/python -*- coding: UTF-8 -*-
import time
import urllib2                           #獲取網址
import json
import RPi.GPIO as GPIO
import MySQLdb
import serial                            #串列傳輸
from SimpleCV import JpegStreamCamera    

GPIO.setmode(GPIO.BOARD)                 #指定Board Pin對應到 GPIO編號
GPIO.setwarnings(False)

MotorPinX = 33
MotorPinY = 12

GPIO.setup(MotorPinX, GPIO.OUT)          #設定指定Pin腳為輸入/輸出狀態
GPIO.setup(MotorPinY, GPIO.OUT)

pwm_motorX = GPIO.PWM(MotorPinX, 50)     #透過PWM脈波訊號脈波必須每秒重複50次(50Hz), 1 秒內產生 50 個波以上才能夠讓伺服馬達運作
pwm_motorY = GPIO.PWM(MotorPinY, 50)     #脈衝寬度範圍：500~2400µs>0.5~2.4ms  (0.5ms/20ms)*100=2.5  (2.4ms/20ms)*100=12

pwm_motorX.start(7.25)
pwm_motorY.start(7.25)

transDuty = lambda x: 7.25 - float(x) / 40 * 17      #7.25-x(4.25/10)         

host = '172.20.10.2'  # 更改主機位置
url = 'http://%s/iotARM/phpFunction/json_iot.php' % host                #json_iot.php 
updateURL = 'http://%s/iotARM/phpFunction/update_iot.php?' % host       #update_iot.php


def motorMov(flag, argX, argY, update='', movSet=0.5):
    ''' 函數帶入5個引數
            flag: 'u','r','d','l','web'
            argX,argY: 為資料庫的x,y座標
            update: 更改資料庫的網址,預設為空值
            movSet: 馬達的步進值,預設為0.5

        函數返回
            返回updatet字串,串接get參數字串
    '''
    # 判斷藍芽案的按鈕---start---
    if flag == 'u' or flag == 'r':  # 如果按上或右
        if flag == 'u':
            argY += movSet
            update += 'move=up'     #updateURL +update
        elif flag == 'r':
            argX += movSet
            update += 'move=right'

    elif flag == 'd' or flag == 'l':  # 按下或左
        if flag == 'd':
            argY += -movSet
            update += 'move=down'
        elif flag == 'l':
            argX += -movSet
            update += 'move=left'
    # 判斷藍芽案的按鈕---end---

    elif flag == 'web':  # 若藍芽沒動則Web動
        global isYMov
        # 判斷Web的按鈕並驅動馬達---start---
        if isYMov:
            dutyResultY = round(transDuty(argY), 2)  # 四捨五入小數點第二位
            print 'Web Y軸dutyCycle: ' + str(dutyResultY)
            pwm_motorY.ChangeDutyCycle(dutyResultY)  # 驅動Y軸馬達
        else:
            dutyResultX = round(transDuty(argX), 2)
            print 'Web X軸dutyCycle: ' + str(dutyResultX)
            pwm_motorX.ChangeDutyCycle(dutyResultX)  # 驅動Y軸馬達

        update += 'move=web'
        print '執行的網址: ' + update
        time.sleep(0.1)
        return update
        # 判斷web的按鈕並驅動馬達---end---

    elif flag == 'trace':
        cam = JpegStreamCamera("http://192.168.137.57:8080/?action=stream")  #影像串流
        while True:
            img = cam.getImage() #擷取照片
            eyes = img.findHaarFeatures('right_eye.xml')  #比對右眼  [eye1,eye3,eye2]
            if eyes:
                bigEyes = eyes.sortArea()[-1]   #排序 取最右邊的
                location = bigEyes.coordinates()#眼睛座標
                print "偵測到臉部....x位置為:", location[0]
                print "偵測到臉部....y位置為:", location[1]
                x = location[0] - 160
				y = location[1] - 120
                print "距離x座標中心(160,120):", x
				print "距離y座標中心(160,120):", y

                movX = round(transDuty(argX), 2)
				movY = round(transDuty(argY), 2)
				
				if y >= 100:
                    movY -= 1
                elif y <= -100:
                    movY += 1
                elif 100 > y >= 50:
                    movY -= 0.5
                elif -100 < y <= -50:
                    movY += 0.5

                if movY > 11.5:
                    movY = 11.5
                elif movY < 3:
                    movY = 3
				
				
				
                if x >= 100:
                    movX -= 1
                elif x <= -100:
                    movX += 1
                elif 100 > x >= 50:
                    movX -= 0.5
                elif -100 < x <= -50:
                    movX += 0.5

                if movX > 11.5:
                    movX = 11.5
                elif movX < 3:
                    movX = 3
				
				
				backX = round((7.25 - movX) / 17 * 40,2)  #將movX轉換成duty cycle
				backY = round((7.25 - movY) / 17 * 40,2)
                break

        pwm_motorX.start(movX)
        update += 'move=trace&X=' + str(backX) + '&Y=' + str(argY)
        time.sleep(0.1)
        print '執行的網址: ' + update
        return update

    if (argY - resultY) != 0:
        dutyResultY = round(transDuty(argY), 2)  # 將Y座標轉換為DutyCycle
        print 'BT Y軸dutyCycle: ' + str(dutyResultY)
        pwm_motorY.ChangeDutyCycle(dutyResultY)
    else:
        dutyResultX = round(transDuty(argX), 2)  # 將X座標轉換為DutyCycle
        print 'BT X軸dutyCycle: ' + str(dutyResultX)
        pwm_motorX.ChangeDutyCycle(dutyResultX)
    time.sleep(0.1)

    print '執行的網址: ' + update
    return update


def execURL(url, feedback=False):
    ''' 函數帶入兩個引數
            url: 要執行的網址
            feedback: 是否要回傳資料庫轉json的格式,預設不回傳

			函數返回
            返回一個5個值的Tuple
    '''
    urlFp = urllib2.urlopen(url)  # 要求網址json

    if feedback:
        dData = json.load(urlFp)  # # 將response instance轉換為python dict字典物件
        dData['isMov'] = (False, True)[dData['isMov'] == '1']  # 將返回的dict '1'轉為True '0'轉為False
        dData['isXMov'] = (False, True)[dData['isXMov'] == '1']
        dData['isYMov'] = (False, True)[dData['isYMov'] == '1']
        dData['isTrace'] = (False, True)[dData['isTrace'] == '1']
        urlFp.close()

        print (
            float(dData['movX']), float(dData['movY']), dData['isMov'], dData['isXMov'], dData['isYMov'],
            dData['isTrace'])
        return (
            float(dData['movX']), float(dData['movY']), dData['isMov'], dData['isXMov'], dData['isYMov'],
            dData['isTrace'])

    urlFp.close()


while True:

    while True:
        try:
            resultX, resultY, isMov, isXMov, isYMov, isTrace = execURL(url, True)  # 設定變數初始值 初始 X,Y,0,0,0,0,0
        except:
            print 'Get DBData failed, retry Now!'
            time.sleep(2)
        else:
            break

    ser = serial.Serial("/dev/serial0", 9600, timeout=0.5) #連接serial0,設定9600鮑率,暫停0.5秒
    command = ser.read()  # 讀取藍芽阜的值
    # command = False
    print command
    # if-判斷藍牙是否送值,有值才繼續執行藍牙操作
    if command:
        print "BT"
        # 藍牙操作---start---
        execUpdateURL = motorMov(command, resultX, resultY, updateURL) #command,resultX,resultY,updateURL參數帶入motorMov
        execURL(execUpdateURL)
        # 藍牙操作---end---
    elif isMov:
        print 'web'
        # Web操作---start---
        execUpdateURL = motorMov('web', resultX, resultY, updateURL)
        execURL(execUpdateURL)
        # Web操作---end---

    elif isTrace:
        print 'Trace'
        # Trace操作---start---
        execUpdateURL = motorMov('trace', resultX, resultY, updateURL)
        execURL(execUpdateURL)
        # Trace操作---end---

    else:
        print "未連接"
    time.sleep(0.1)

GPIO.cleanup()
