from PIL import Image, ImageDraw, ImageFont
from time import sleep
import RPi.GPIO as GPIO
import os, socket, subprocess, SH1106

class MenuItem:
    def __init__(self, id="", label="", callback=None):
        self.id = id
        self.label = label
        self.callback = callback

class RpiDisplay:
    current_item = MenuItem()

    def __init__(self):
        self.setupDevice()
        self.initImage()
        self.initFonts()

    def setupDevice(self):
        #GPIO define
        RST_PIN        = 25
        CS_PIN         = 8
        DC_PIN         = 24

        self.KEY_UP_PIN     = 6 
        self.KEY_DOWN_PIN   = 19
        self.KEY_LEFT_PIN   = 5
        self.KEY_RIGHT_PIN  = 26
        self.KEY_PRESS_PIN  = 13

        self.KEY1_PIN       = 21
        self.KEY2_PIN       = 20
        self.KEY3_PIN       = 16

        self.disp = SH1106.SH1106()
        self.disp.Init()

        self.disp.clear()

        GPIO.setmode(GPIO.BCM) 
        GPIO.setup(self.KEY_UP_PIN,      GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY_DOWN_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY_LEFT_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY_RIGHT_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY_PRESS_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY1_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY2_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
        GPIO.setup(self.KEY3_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up

    def initImage(self):
        self.image = Image.new('1', (self.disp.height, self.disp.width), "WHITE")
        self.draw = ImageDraw.Draw(self.image)

    def initFonts(self):
        self.font10 = ImageFont.truetype("/home/frost/RaspberryPi/python3/Font.ttf", 11)

    def drawImageToDevice(self):
        self.image = self.image.rotate(90, expand=1)
        self.disp.ShowImage(self.disp.getbuffer(self.image))
        self.image = self.image.rotate(-90, expand=1)
        self.draw = ImageDraw.Draw(self.image)

    def drawBlank(self):
        self.draw.rectangle([(0,0), (self.disp.height, self.disp.width)], fill = 1)

    def printMsg(self, msg, font = "default", sleep = 3):
        if font == "default":
            font = self.font10

        self.drawBlank()
        self.draw.rectangle([(0,0), (self.disp.height, self.disp.width)], fill = 1)
        _, _, w, h = self.draw.textbbox((0, 0), msg, font=font)
        self.draw.text(((self.disp.height-w)/2, (self.disp.width-h)/2), msg, font=font, fill=0)
        self.drawImageToDevice()

    def printScr(self):
        self.draw.text((0, 90), "SEL", font = self.font10, fill = 0)
        self.draw.text((0, 100), "BACK", font = self.font10, fill = 0)
        self.draw.text((0, 110), "LOCK", font = self.font10, fill = 0)

        self.drawImageToDevice()

    def wifi_menu(self):
        self.draw.text((0,0), 'IP: {}'.format(self.get_ip()), font = self.font10, fill = 0)
        self.draw.text((0,10), 'SSID: {}'.format(self.get_ip()), font = self.font10, fill = 0)

    def drawMenu(self, items, hl_pos, menu_pos):
        self.drawBlank()

        for i in range(0, min(7, len(items))):
            if hl_pos == i:
                self.draw.rectangle([(0, (i*16)+2), (self.disp.height, (i*16)+18)], fill = 0)
                self.draw.text((5, 3+i*16), items[i+menu_pos].label, font = self.font10, fill = 1)
                self.current_item = items[i+menu_pos]
            else:
                self.draw.text((5, 3+i*16), items[i+menu_pos].label, font = self.font10, fill = 0)

        self.drawImageToDevice()

    def start(self):
        while True:
            sleep(100)

def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def getSSID():
    result = subprocess.check_output("iwgetid -r", shell=True, text=True)
    return result.strip()

def powerMenu():
    power_menu_items = [
            MenuItem("halt", "Halt", ),
            MenuItem("Reboot", "Reboot")
        ]

class MyMenu:
    menu_pos = 0
    hl_pos = 0

    def __init__(self):
        self.main_menu_items = [
            MenuItem("wifi", "WiFi"),
            MenuItem("power", "Power"),
            MenuItem("exit", "EXIT"),
        ]
        self.rd = RpiDisplay()
        self.rd.drawMenu(self.main_menu_items, self.hl_pos, self.menu_pos)
        self.setupCallbacks()
        self.rd.start()

    def key_callback(self, pin):
        self.rd.printMsg("Button on Pin {} Pressed".format(pin))

    display = "menu"
    device_busy = False

    def sel_callback(self, pin):
        if self.device_busy:
            return

        self.device_busy = True
        if self.display == "menu":
            self.rd.printMsg(self.rd.current_item.label)
            self.display = "item"
            if self.rd.current_item.id == "halt":
                os.system("sudo halt")
            if self.rd.current_item.id == "exit":
                self.rd.disp.clear()
                exit()
            self.device_busy = False
            return

        if self.display == "item":
            self.rd.drawMenu(self.main_menu_items, self.hl_pos, self.menu_pos)
            self.display = "menu"
            self.device_busy = False
            return

    def handle_key_up(self, pin):
        if self.device_busy:
            return

        self.device_busy = True
        if self.hl_pos > 0:
            self.hl_pos -= 1

        if self.hl_pos <= 0 and self.menu_pos > 0:
            self.menu_pos -= 1

        self.rd.drawMenu(self.main_menu_items, self.hl_pos, self.menu_pos)
        self.device_busy = False
        return

    def handle_key_down(self, pin):
        if self.device_busy:
            return

        self.device_busy = True
        if self.hl_pos == 6 and self.menu_pos < 2:
            self.menu_pos += 1

        if self.hl_pos < 6:
            self.hl_pos += 1

        self.rd.drawMenu(self.main_menu_items, self.hl_pos, self.menu_pos)
        self.device_busy = False
        return

    def setupCallbacks(self):
        GPIO.add_event_detect(self.rd.KEY2_PIN, GPIO.RISING, callback=self.key_callback)
        GPIO.add_event_detect(self.rd.KEY3_PIN, GPIO.RISING, callback=self.sel_callback)
        GPIO.add_event_detect(self.rd.KEY_LEFT_PIN, GPIO.RISING, callback=self.handle_key_up)
        GPIO.add_event_detect(self.rd.KEY_RIGHT_PIN, GPIO.RISING, callback=self.handle_key_down)

MyMenu()
