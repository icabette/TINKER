#!/usr/bin/python3
# coding=utf-8
# 文档 https://cdn-shop.adafruit.com/datasheets/DHT11-chinese.pdf
# DHT11 python FOR ASUS THINKER BOARD /S
# 一次完整的数据为40bit，高位先出
# 8bit湿度整数数据 + 8bit湿度小数数据 + 8bit温度整数数据 + 8bit温度小数数据 + 8bit校验和

import RPi.GPIO as GPIO
import time

class Result:
    'DHT11 sensor result returned by DHT11.start() method'
    # 数据成功
    SUCCESS = 0
    # 缺少数据
    ERR_MISSING_DATA = 1
    # 数据校验失败
    ERR_CRC = 2

    error_code = SUCCESS
    temperature = -1
    humidity = -1

    def __init__(self, error_code, temperature, humidity):
        self.error_code = error_code
        self.temperature = temperature
        self.humidity = humidity

    def is_valid(self):
        return self.error_code == Result.SUCCESS
        
class Driver:
    'DHT11 sensor reader class for ASUS THINKER BOARD'
    
    __channel = 0

    def __init__(self, channel):
        self.__channel = channel
        self.__raw_data = []
        
    def __on__(self):
        GPIO.setwarnings(False) 
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.__channel, GPIO.OUT)
        time.sleep(.05)
        # 先向传感器发送开始信号，握手 LOW
        GPIO.output(self.__channel, GPIO.LOW)
        # 主机把总线拉低必须大于18毫秒，这里采用20毫秒
        time.sleep(.02)
        # 然后主机拉高并延时等待传感器的响应
        GPIO.output(self.__channel, GPIO.HIGH)
        time.sleep(.00004)
        # 执行1次需要十几微秒
        # 等待传感器的握手响应信号和数据信号
        GPIO.setup(self.__channel, GPIO.IN)

    def __read__(self):
        # 总线由上拉电阻拉高进入空闲状态
        # 末位持续100us高电平时 视为数据传输终止
        MAX_UNCHANGE = 100
        unchage_count = 0
        last = -1
        # 开始接受数据
        self.__raw_data = []
        while True:
            current = GPIO.input(self.__channel)
            self.__raw_data.append(current)
            if last != current:
                unchage_count = 0
                last = current
            else:
                unchage_count += 1
                if unchage_count > MAX_UNCHANGE:
                    break
        GPIO.cleanup(self.__channel)

    def __compute__(self):
        data = []
        length = 0
        # 原始数据转换
        for each in self.__raw_data:
            if each == GPIO.HIGH:
                # 记录高电平的高度
                length += 1
            else:
                if length != 0:
                    # 高电平持续26-28us表示0， 高电平持续70us表示1
                    data.append(0 if length <8 else 1)
                length = 0
        # 切除第一个高电平无效数据 握手数据
        data = data[1:]
        print (data, "length: ", len(data))

        # 数据不满足条件 不处理
        if len(data) != 40:
            return Result(Result.ERR_MISSING_DATA, 0, 0)
        
        print(data, "Length: ", len(data))
        # 8bit湿度整数数据
        humidity_bit = data[0:8]
        # 8bit湿度小数数据
        humidity_point_bit = data[8:16]
        # 8bit温度整数数据
        temperature_bit = data[16:24]
        # 8bit温度小数数据
        temperature_point_bit = data[24:32]
        # 8bit校验和
        check_bit = data[32:40]
        
        # 初始化数据
        humidity = 0
        humidity_point = 0
        temperature = 0
        temperature_point = 0
        check = 0
        #i = 0
        for i in range(8):
            # 湿度整数部分
            humidity += humidity_bit[i] * 2**(7-i)
            humidity_point += humidity_point_bit[i] * 2**(7-i)
            # 温度整数部分
            temperature += temperature_bit[i] * 2**(7-i)
            temperature_point += temperature_point_bit[i] * 2**(7-i)
            # 校验数
            check += check_bit[i] * 2**(7-i)
        # 计算校验和
        sum = humidity + humidity_point + temperature + temperature_point
        if check == sum:
            # 小数点前后拼接
            temperature = float(str(temperature)+"."+str(temperature_point))
            humidity = float(str(humidity)+"."+str(humidity_point))
            print("Humidity: ", humidity, "Temperature: ", temperature)
            return Result(Result.SUCCESS, temperature, humidity)
        else:
            return Result(Result.ERR_CRC, 0, 0)
            
    def start(self):
        self.__on__()
        self.__read__()
        return self.__compute__()


DHT11 = Driver(3)
Display = Result(0,0,0)
while(1):
    Display = DHT11.start()
    time.sleep(1)