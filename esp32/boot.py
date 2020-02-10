# -*- coding: utf-8 -*-
#
# Author: ATRedline
#
# This scrypt is application for "ESP32 Fan Control"
# must be used on ESP32 with MicroPython compiled with machine.pwm module by LoBoris
#
# Version 1.0b


from utime import sleep
from neopixel import NeoPixel
from machine import Pin, PWM, UART
from _thread import start_new_thread


"""Пользовательские переменные:"""


network_name = ''            # Имя точки доступа WiFi, ввести если необходимо подключение
password = ''                # Пароль WiFi (Не желательно использовать Wi-Fi вкупе с динамической подсветкой!)
accel_speed = 0.05           # Время единицы разгона вентиляторов (Не желательно повышать более чем наа 0.01)
boost_zone = 50              # Граница зоны оборотов (в процентах) в которой 3-пин вентиляторы бустятся при старте с 0
PWM_Pins = [19, 5, 16, 2]    # Пины PWM-линий, с первой по четвёртую
EXT_Pins = [18, 17, 4, 15]   # Пины линий расширения,с первой по четвёртую
uart_pins = [1, 3]           # Пины UART, изменять при использовании внешнего UART
led_pin = 13                 # Пин подключения подсветки (WS2811/2812b)


"""Исполняемый код:"""


def do_connect(apn, psswd):
    """Функция подключения к WiFi сети, вызвается только при введённом имени точке доступа и пароле. Сеть может быть
    использована для контроля за работой посредством telnet или для интеграции устройства в систему умного дома
    (автоматическое включение/выключение ПК, подсветки). Не рекомендуется использовать вкупе с динамической подсветкой,
    т.к. даёт наводки на RMT-драйвер"""
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(apn, psswd)
        while not wlan.isconnected():
            pass


class FanControl:
    """Класс объекта обработки сигналов FanControl"""

    def __init__(self, acs, boost_zn, pwm_pins, ext_pins, ledpin, uart_pin):
        """Переменные модулей управления LED-подсветкой:"""
        self.np = ''
        self.new_rgb = []
        self.last_rgb = []
        self.led_msg = ''
        self.led_busy = 0
        self.led_effect = 0
        self.led_pixels = 0
        self.led_Pin = ledpin
        self.led_last_mode = 0
        self.led_brightness = 0
        self.led_last_pixels = 0
        self.led_last_effect = 0
        self.led_effect_status = 0
        self.led_last_brightness = 0
        self.led_last_effect_speed = 0

        """Переменные модулей управления вентиляторами и инициализация отдельных тредов:"""

        self.accel_speed = acs
        self.uart_pins = uart_pin
        self.boost_zone = boost_zn
        self.lines_last_duty = [0, 0, 0, 0]
        self.ext_lines = [Pin(ext_pins[0], Pin.OUT, value=1),
                          Pin(ext_pins[1], Pin.OUT, value=1),
                          Pin(ext_pins[2], Pin.OUT, value=1),
                          Pin(ext_pins[3], Pin.OUT, value=1)]
        self.lines_pwm = [PWM(Pin(pwm_pins[0]), freq=1000, duty=0, timer=0),
                          PWM(Pin(pwm_pins[1]), freq=1000, duty=0, timer=1),
                          PWM(Pin(pwm_pins[2]), freq=1000, duty=0, timer=2),
                          PWM(Pin(pwm_pins[3]), freq=1000, duty=0, timer=3)]
        start_new_thread(self.processing, ())  # Запуск отдельного треда для функции processing
        start_new_thread(self.neopixel_processing, ())  # Запуск отдельного треда для функции neopixel_processing

    def np_clear(self):
        """Вспомогательная функция, выключение светодиодов ленты"""
        for i in range(self.led_pixels):
            self.np[i] = (0, 0, 0)
        self.np.write()

    def led_closure(self):
        """Вспомогательная функция, завершение цикла активного Эффекта"""
        self.led_effect = 0
        while self.led_effect_status:
            sleep(0.1)

    def neopixel_control(self, command):
        """Модуль первичной обработки команды управления подсветкой.
        Получает команду управления подсветкой от функции работы с COM-портом (processing), разбивает команду на
        переменные, после чего в зависимости от переменных в полученной строке выключает посдсветку/включает подсветку/
        /передаёт дальнейшие команды функции neopixel_processing"""
        self.led_last_pixels = self.led_pixels
        pixels = int(command[2:5])
        if not pixels:
            if self.led_effect_status:
                self.led_closure()
            if self.np:
                self.np_clear()
            self.led_busy = 0
            self.last_rgb = []
            self.led_last_mode = 0
            self.led_last_effect = 0
            self.led_last_brightness = 0
            self.led_last_effect_speed = 0
        else:
            self.led_pixels = pixels
            self.led_last_brightness = self.led_brightness
            self.led_brightness = int(command[5:7])
            if self.led_brightness == 99:
                self.led_brightness = 100
            not_smooth = int(command[17])
            effect = int(command[7:9])
            if effect:
                """Код ниже занимается эффектами LED-ленты (если команда эффекта присутствует в команде LED)"""
                speed = int(command[9:11])
                if not self.np or self.led_pixels != self.led_last_pixels:
                    if self.led_effect_status:
                        self.led_closure()
                    self.np = NeoPixel(Pin(self.led_Pin, Pin.OUT), self.led_pixels)
                    self.led_last_brightness = 0
                if self.led_brightness != self.led_last_brightness:
                    if self.led_effect_status:
                        self.led_closure()
                if self.led_last_effect != effect or self.led_last_effect_speed != speed or not self.led_effect_status:
                    if self.led_effect_status:
                        self.led_closure()
                    self.led_msg = 'eff;{0};{1}'.format(effect, command[9:11])
                    self.led_last_effect = effect
                    self.led_last_effect_speed = speed
                    self.led_last_mode = 1
                else:
                    self.led_busy = 0
            else:
                """Код ниже занимается установкой статического цвета(если команда эффекта отсутствует в комманде LED)"""
                self.led_last_effect = 0
                self.led_effect = 0
                if self.led_effect_status:
                    self.led_closure()
                if not self.np or self.led_pixels != self.led_last_pixels:
                    self.np = NeoPixel(Pin(self.led_Pin, Pin.OUT), self.led_pixels)
                    self.last_rgb = []
                exec('r = {0}{1}'.format('0x', command[11:13]))
                exec('g = {0}{1}'.format('0x', command[13:15]))
                exec('b = {0}{1}'.format('0x', command[15:17]))
                rgb = [r, g, b]
                for i in range(3):
                    rgb[i] = round(rgb[i] / 100 * self.led_brightness)
                if rgb != self.last_rgb or self.led_last_mode:  # Если цвет изменён, предыдущий режим = динам, если это
                    if not self.last_rgb or self.led_last_mode or not_smooth:  # первая команда,имеется комманда быстрой
                        self.np.fill(rgb)                                      # установки: цвет выставляется сразу
                        self.np.write()
                        self.last_rgb = rgb
                        self.led_last_mode = 0
                        self.led_busy = 0
                    else:  # Иначе обработка цвета передаётся в функцию led_processing для плавного изменения цвета
                        self.led_msg = 'rgb;{0};{1};{2}'.format(rgb[0], rgb[1], rgb[2])
                else:
                    self.led_busy = 0

    def neopixel_processing(self):
        """Функция выполняется в фоновом треде, обеспечивает плавную смену цвета подсветки,
         а так же занимается включением led-эффектов"""
        while True:
            if self.led_msg:  # Функци принимает команды через переменную класса self.led_msg
                """Секция запуска плавного изменения цвета.
                Цвет меняется плавно путём поочерёного изменения каждого
                цветового диапазона на единицу шага (в вычисленном направлении) в цикле, после шага цикла выставляется
                время ожидания. Общее время цикла для изменения цвета от 0 до 255 не должно превышать 5 секунд"""
                if self.led_msg.startswith('rgb'):
                    rgb = self.led_msg.replace('rgb;', '').split(';')
                    self.led_msg = ''
                    for i in range(len(rgb)):
                        rgb[i] = int(rgb[i])
                    direction = {0: '', 1: '', 2: ''}
                    for i in range(3):  # В данном модуле вычисляем направление изменения цвета для всех трёх цветов
                        difference = rgb[i] - self.last_rgb[i]
                        if difference > 0:
                            direction[i] = '+'
                        elif difference < 0:
                            direction[i] = '-'
                    step = max(round((2.55*self.led_brightness)/100*2), 1)  # - шаг изменения цвета
                    while True:  # В данном цикле происходит вычисление изменения цвета для всех каналов цвет по-очереди
                        for num in direction:
                            if direction[num] == '+':
                                if self.last_rgb[num] == rgb[num]:
                                    direction[num] = ''
                                else:
                                    self.last_rgb[num] = min(self.last_rgb[num] + step, rgb[num])
                            elif direction[num] == '-':
                                if self.last_rgb[num] == rgb[num]:
                                    direction[num] = ''
                                else:
                                    self.last_rgb[num] = max(self.last_rgb[num] - step, rgb[num])
                        if not ''.join(direction.values()):
                            self.new_rgb = []
                            self.led_busy = 0
                            break
                        self.np.fill(self.last_rgb)
                        self.np.write()
                        sleep(0.06)  # время ожидания после шага цикла

                """Секция запуска визуальных эффектов LED-ленты.
                Функции эффектов запускаются от имени треда фоновым процессом и коммуницируют с остальнынми функциями
                (получают сигналы на завершение, сообщают своё состояние) через переменные класса"""
                if self.led_msg.startswith('eff'):
                    eff = self.led_msg.replace('eff;', '').split(';')
                    self.led_msg = ''
                    for i in range(len(eff)):
                        eff[i] = int(eff[i])
                    self.led_busy = 0
                    self.led_effect = 1
                    if eff[0] == 1:
                        self.effect1(eff[1])
                    if eff[0] == 2:
                        self.effect2(eff[1])
                    if eff[0] == 3:
                        self.effect3(eff[1])
                    if eff[0] == 4:
                        self.effect4(eff[1])
            sleep(0.5)

    def processing_backstage(self, commands, command):
        """Функция предварительной обработки команд контроля линий PWM. Необходима для разгрузки основного модуля
        processing. Устанавливает частоту, определяет направление изменения частоты для плавного увеличения оборотов"""
        pos = int(command[2]) - 1
        new_frequency = int(command[3:5]) * 1000
        new_duty = int(command[6:])
        if self.lines_pwm[pos].freq() != new_frequency:  # Выставляем новую частоту если она отличается от устанновленно
            self.lines_pwm[pos].freq(new_frequency)
        if new_duty != self.lines_last_duty[pos]:  # Занимаемся частотой если новая частота отличается от установленной
            if new_duty and new_duty < self.boost_zone and command[5] == 'b' and not self.lines_last_duty[pos]:
                direction = int(new_duty / 2)  # данный кусок кода для НЕ плавного запуска 3-пин вентиляторов с нуля об.
                line = {pos: [new_duty, direction]}
                commands.update(line)
            else:  # В данном куске кода определяем направление изменения частоты для конкретной линии
                direction = new_duty - self.lines_last_duty[pos]
                if direction > 0:
                    direction = '+'
                else:
                    direction = '-'
                line = {pos: [new_duty, direction]}
                commands.update(line)
        return commands  # Возвращаем новую частоту с направлением изменения частоты (в + или в -)

    def processing(self):
        """Основная функция, работает в фоновом процессе, создаёт объект UART, проверяет наличие команд в буфере,
        обеспечивает первичную обработку полученной через UART команды и плавную установку оборотов вентиляторов,
         отправляет отчёт о получении команды и проделанной работе"""
        uart = UART(2, tx=self.uart_pins[0], rx=self.uart_pins[1])
        count = 0
        while True:
            try:   # для исключения невыявленных проблем
                cmnd = uart.read()
                if cmnd:
                    cmnd = cmnd.decode('utf-8')
                if cmnd and cmnd.startswith('cmnd'):  # Начало обработки команды, если команда начинается с 'cmnd'
                    count += 1
                    cmnd = cmnd.split(';')  # Разбиваем команду на подкоманды
                    if len(cmnd) > 1:
                        commands = {}
                        for i in cmnd:
                            if i.startswith('np'):
                                self.led_busy = 1
                                self.neopixel_control(i)
                            elif i.startswith('fn'):
                                commands = self.processing_backstage(commands, i)
                        while True:  # Данный кусок кода занимается плавным паралельным изменением оборотов вентиляторов
                            if commands:
                                for line in commands:
                                    if commands[line][1] == '+':
                                        if self.lines_last_duty[line] == commands[line][0]:
                                            self.ext_lines[line].value(0)
                                            commands.pop(line)
                                        else:
                                            self.lines_last_duty[line] = self.lines_last_duty[line] + 1  # - шаг
                                            self.lines_pwm[line].duty(self.lines_last_duty[line])
                                    elif commands[line][1] == '-':
                                        if self.lines_last_duty[line] == commands[line][0]:
                                            if not commands[line][0]:
                                                self.ext_lines[line].value(1)
                                            commands.pop(line)
                                        else:
                                            self.lines_last_duty[line] = self.lines_last_duty[line] - 1  # - шаг
                                            self.lines_pwm[line].duty(self.lines_last_duty[line])
                                    elif type(commands[line][1]) == int:  # Данное условие выполняется для НЕ плавного
                                        if commands[line][1] == 1:      # старта 3-pin вентиляторов при 50% выполнения
                                            self.lines_pwm[line].duty(100)         # плавной установки остальных линий
                                            commands[line][1] -= 1
                                        elif commands[line][1] == 0:
                                            self.lines_pwm[line].duty(commands[line][0])
                                            self.lines_last_duty[line] = commands[line][0]
                                            self.ext_lines[line].value(0)
                                            commands.pop(line)
                                        else:
                                            commands[line][1] -= 1
                            else:
                                break
                            sleep(self.accel_speed)  # время задержки после установки шага всех линий (общее время <6c)
                    while self.led_busy:  # Ожидание процесса led_processing, запускаемого перед модулем плавной
                        sleep(1)  # смены оборотов, и выполняемого параллельно в фоне
                    uart.read()  # стираем повторные сообщения, которые были полученны в процессе обработки команд
                    uart.write(b'answ:done')  # отправляем отчёт о проделанной работе или о получении комманды
                sleep(0.5)
            except:
                pass

    """Секция LED-эффектов"""

    def effect1(self, speed):
        """Эффект 'Переливы' """
        self.led_effect_status = 1
        delay = round(0.1 - (0.0007 * speed), 3)
        max_color = round(2.55 * self.led_brightness)
        step = round(max(1, max_color / 100 * 2))
        rgb = [0, max_color, 0]
        while self.led_effect:
            for i in range(3):
                if not rgb[i]:
                    while rgb[i] < max_color:
                        rgb[i] = min(max_color, rgb[i]+step)
                        sleep(0.005)
                        self.np.fill(rgb)
                        self.np.write()
                        sleep(delay)
                        if not self.led_effect:
                            break
                elif rgb[i]:
                    while rgb[i] > 0:
                        rgb[i] = max(0, rgb[i]-step)
                        sleep(0.005)
                        self.np.fill(rgb)
                        self.np.write()
                        sleep(delay)
                        if not self.led_effect:
                            break
        else:
            self.np_clear()
            self.led_effect_status = 0

    def effect2(self, speed):
        """Эффект 'Бегущая строка' """
        from urandom import choice
        self.led_effect_status = 1
        colors = [0, round(128/100*self.led_brightness), round(255/100*self.led_brightness)]
        delay = round(0.1 - (0.0009 * speed), 3)
        while self.led_effect:
            col = [choice(colors), choice(colors), choice(colors)]
            for led in range(self.led_pixels):
                black = led - 4
                if black < 0:
                    black = self.led_pixels + black
                self.np[led] = col
                self.np[black] = ([0, 0, 0])
                self.np.write()
                sleep(delay)
                if not self.led_effect:
                    break
        else:
            self.np_clear()
            self.led_effect_status = 0

    def effect3(self, speed):
        """Эффект 'Появление' """
        self.led_effect_status = 1
        from urandom import randint, choice
        delay = round((0.2 - (speed * 0.0015)), 3)
        colors = [0, round(128/100*self.led_brightness), round(255/100*self.led_brightness)]
        step = max(1, round(colors[2]/100*2))
        while self.led_effect:
            col = [choice(colors), choice(colors), choice(colors)]
            leds = list(range(self.led_pixels))
            while leds:
                led = randint(0, len(leds) - 1)
                self.np[leds[led]] = col
                self.np.write()
                del leds[led]
                sleep(delay)
                if not self.led_effect:
                    break
            while True:
                if sum(col):
                    if not self.led_effect:
                        break
                    for i in range(3):
                        if col[i] > 0:
                            col[i] = max(0, col[i]-step)
                    sleep(0.01)
                    self.np.fill(col)
                    self.np.write()
                else:
                    break
            sleep(0.5)
        else:
            self.np_clear()
            self.led_effect_status = 0

    def effect4(self, speed):
        """Эффект 'Замыкание' """
        from urandom import randint
        self.led_effect_status = 1
        delay = round(5 - (speed * 0.05))
        spark_leds = list(range(3, self.led_pixels))
        while self.led_effect:
            for i in range(5):
                for i in range(4):
                    self.np[i] = [255, 255, 255]
                    self.np.write()
                sleep(0.03)
                sleep(randint(0, 4) / 100)
                self.np_clear()
                sleep(randint(4, 8) / 100)
            sleep(0.2)
            bri = 100
            for i in spark_leds:
                self.np[i] = [round(2.55*bri), round(2.35*bri), round(1.28*bri)]
                self.np.write()
                sleep(0.03)
                self.np_clear()
                if bri > 4:
                    bri = round(bri / 2)
            ts = randint(1 + delay, 6 + delay)
            while ts:
                if not self.led_effect:
                    break
                sleep(1)
                ts -= 1
        else:
            self.np_clear()
            self.led_effect_status = 0


"""Секция инициализации платы:"""

autostart_pin = Pin(14, Pin.IN, Pin.PULL_DOWN)  # Пин определяющий тип запуска (с выполнением скрипта или без)
enable_pin = Pin(12, Pin.OUT, value=1)

if autostart_pin.value():
    processing = FanControl(accel_speed, boost_zone, PWM_Pins, EXT_Pins, led_pin, uart_pins)
if network_name:
    do_connect(network_name, password)