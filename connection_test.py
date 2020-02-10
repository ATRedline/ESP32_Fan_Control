# -*- coding: utf-8 -*-
#
# Author: ATRedline
#
# Version: 2.0
#
# This script is for testing connection with FanControl script of ESP32
# Данный скрипт тестирует соединение с ESP32 путём генерации случайных команд и отправки их со случайными интервалами
# времени, подсчитывая колличество реконнектов и ошибок связи.

import random
import serial
import time


"""Пользовательские переменные:"""
prt = 'COM8'        # Ком-порт
boost_for = [0]     # Линии с 3-pin вентиляторами (отсчёт начиная с 0)
num_leds = '21'     # колличество светодиодов


class SerialPort:
    """Класс объекта, производящего манипуляции с COM-портом (Взят из Fan_Control)"""
    def __init__(self):
        self.opened_port = False
        self.port = ''
        self.busy = False
        self.connecting = False
        self.answer_result = 0
        self.writing = False
        self.accepted_msgs = 0
        self.sended_msgs=0
        self.reconnections=0
        self.errors=0

    def connect(self, port):
        """Функция, создающая подключение к COM-порту"""
        self.connecting = True
        try:
            print('Принятый компорт:', port)
            self.opened_port = serial.Serial(port=port, baudrate=115200, timeout=0, write_timeout=3)
            print('Подключено: ', self.opened_port)
            self.port = port
            self.connecting = False
        except (OSError, serial.SerialException):
            print('Произошла ошибка прям в компорту ёпта')
            self.error()

    def send(self, command):
        """Функция отправки команды в ком-порт.
        Функция предполагает подтверждение получения команды устройством, а в случае отсутствия ответа (например т.к.
        устройство не успело загрузиться или перезагрузилось) выполняет повторную отправку команды и/или реконнект"""
        if self.opened_port:
            self.busy = True
            self.answer_result = 0
            sending_count = 0
            reconnections = 0
            command = command.encode('utf-8')
            self.sended_msgs += 1
            while sending_count < 2:  # Количество попыток передать команду
                try:
                    self.opened_port.write(command)
                    answer_count = 0  # модуль ожидания ответа устройства начинается тут_______________________________
                    while answer_count < 6:
                        time.sleep(1)
                        try:
                            answer = self.opened_port.read_all()
                        except AttributeError:
                            pass
                        if b'answ:done' in answer:
                            self.answer_result = 1
                            self.accepted_msgs += 1
                            return True
                        elif self.answer_result:
                            break
                        answer_count += 1
                    if self.answer_result:
                        self.busy = False
                        break
                    sending_count += 1
                    if sending_count == 2:  # Модуль переподключения
                        if not reconnections:
                            self.opened_port.close()
                            time.sleep(1)
                            self.opened_port = serial.Serial(port=self.port, baudrate=115200, timeout=0,
                                                             write_timeout=3)
                            self.reconnections+=1
                            sending_count = -1
                            reconnections = 1  # модуль ожидания ответа устройства завершается тут______________________
                except (OSError, serial.SerialException):  # происходит при неудачной попытке записать или читать из com
                    print('первый except')
                    sending_count = 3
                    self.error()
                    return False
            else:  # происходит при превышении порога ожидания ответа
                print('вторрой except')
                self.error()
                return False
        else:  # происходит, если компорт закрыт
            print('третий except')
            self.error()
            return False

    def close(self):
        """Функция закрытия открытого подключения"""
        while self.busy:
            time.sleep(0.3)
        if self.opened_port:
            self.opened_port.close()
            self.opened_port = False
            print('Закрываю компорт:', self.opened_port)

    def error(self):
        """Функция вызываемая при ошибках работы с COM-портом"""
        print('происходит ошибка отправки по компорту', self.opened_port)
        self.busy = False
        self.connecting = False
        self.writing = False
        if self.opened_port:
            self.close()
            while self.opened_port:
                time.sleep(0.1)
        self.errors += 1


def command_generator():
    """Генератор произвольных комманд"""
    global boost_for, num_leds
    led_bri = str(random.randint(5, 31))
    led_eff = str(random.randint(0, 4))
    eff_speed = str(random.randint(1, 99))
    smoothness = str(random.randint(0, 1))
    if len(num_leds) == 2:
        num_leds = '0{0}'.format(num_leds)
    if len(led_bri) == 1:
        led_bri = '0{0}'.format(led_bri)
    if len(eff_speed) == 1:
        eff_speed = '0{0}'.format(eff_speed)
    led_command = 'np{0}{1}0{2}{3}ffff5a{4};'.format(num_leds, led_bri, led_eff, eff_speed, smoothness)
    append = random.randint(0, 3)
    command = 'cmnd;'
    for i in range(4):
        if i in boost_for:
            boost = 'b'
            fan_freq = str(random.randint(18, 32))
        else:
            boost = 'h'
            fan_freq = str(random.randint(1, 32))
        fan_speed = ['00', str(random.randint(15, 51)), str(random.randint(15, 51))]
        fan_speed = random.choice(fan_speed)
        if len(fan_freq) == 1:
            fan_freq = '0{0}'.format(fan_freq)
        cur = 'fn{0}{1}{2}{3};'.format(i+1, fan_freq, boost, fan_speed)
        command += cur
        if i == append:
            command += led_command
    return command


sp = SerialPort()
sp.connect(prt)
state = True
sa = time.monotonic()


while True:
    d = random.randint(0, 3)  # Переменные с рандомными интервалами времени
    s = random.randint(0, 120)
    j = random.randint(0, 20)
    f = random.randint(0, 2)
    z = time.localtime()
    if len(str(z.tm_hour)) == 1:
        hr = '0{0}'.format(z.tm_hour)
    else:
        hr = z.tm_hour
    if len(str(z.tm_min)) == 1:
        mn = '0{0}'.format(z.tm_min)
    else:
        mn = z.tm_min
    ltime = '{0}:{1}'.format(hr, mn)
    cmnd = '{0}{1};'.format(command_generator(), ltime)
    print('{0}, Команда: {1}'.format(ltime, cmnd))
    if sp.send(cmnd):
        pass
    else:
        time.sleep(5)
        sp.connect(prt)
    b = time.monotonic()
    a = int(b - sa)
    h = str(a // 3600)
    m = (a // 60) % 60
    sс = a % 60
    if m < 10:
        m = '0' + str(m)
    else:
        m = str(m)
    if sс < 10:
        sс = '0' + str(sс)
    else:
        sс = str(sс)
    timeleft = h + ':' + m + ':' + sс
    print('Отправленно команд: {0}, Принятых команд: {1}, Переконнектов: {2}, Ошибок: {3}, Общее время теста: {4}'.format(sp.sended_msgs, sp.accepted_msgs, sp.reconnections, sp.errors, timeleft))
    if f == 0:
        print('Ожидание, секунд:', d)
        time.sleep(d)
    elif f == 1:
        print('Ожидание, секунд:', s)
        time.sleep(s)
    elif f == 2:
        print('Ожидание, секунд:', j)
        time.sleep(j)
