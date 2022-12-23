#!/usr/bin/env python
import sys
import RPi.GPIO as GPIO
import MFRC522
import paho.mqtt.client as paho
from paho import mqtt
import json
import board
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from adafruit_display_text import wrap_text_to_lines
import time

GPIO.setwarnings(False)

WIDTH = 128
HEIGHT = 64
CARD_KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'
DELAY = 1.5
HEADER = b'CESI'
BLOCK_NUMBER = 6

reader = MFRC522.MFRC522()

def oled_text(text):
    oled_reset = digitalio.DigitalInOut(board.D4)
    i2c = board.I2C()
    oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3C, reset=oled_reset)

    oled.fill(0)
    oled.show()

    image = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
    text = text
    (font_width, font_height) = font.getsize(text)
    draw.text(
        (oled.width // 16 - font_width // 40, oled.height // 16 - font_height // 40),
        text,
        font=font,
        fill=255,
    )
    oled.image(image)
    oled.show()

oled_text("En attente de donnees...")
print('== WAITING...=========================')

def on_message(client, userdata, message):
    data = message.payload.decode('utf-8')
    objects = json.loads(data)
    createIdCard(objects['badge_students'])

client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
client.username_pw_set("ID", "PASSWORD")
client.connect(host='HOST', port=8883)
client.subscribe('TOPIC', qos=1)
client.on_message = on_message

def createIdCard(objects):
    for obj in objects:
        obj_id = obj['badge_id']
        obj_name = obj['student_name']
        reader.MFRC522_Init()

        print('== STEP 1 =========================')

        student_id = None
        while student_id is None:
            student_id = obj_id
            print(obj_id)
            if not (len(student_id) == 7):
                student_id = None
                oled_text("Erreur ! \nL'ID doit posseder 7 chiffres")
                print('Error! Student ID must be egal to 7 digits - exemple: 1234567')
                continue

            print('== STEP 2 =========================')
            print('Place the card to be written on the RFID reader...')
            oled_text('student_id: \n{0} \n{1} \n Veuillez placer la carte'.format(student_id, obj_name))
            time.sleep(DELAY)

            while True:
                (status, tag_type) = reader.MFRC522_Request(reader.PICC_REQIDL)
                if status == reader.MI_OK:
                    print("Card detected")
                    break

            (status, uid) = reader.MFRC522_Anticoll()
            if status != reader.MI_OK:
                print("Error reading card UID")
                oled_text('Erreur de lecture de la carte')
                time.sleep(2.5)
                continue

            print("Card UID: " + str(uid))

            buff = bytearray(16)
            buff[0:4] = HEADER
            buff[4:] = [int(x) for x in list(student_id)]

            while (16 > len(buff)):
                buff.append(0)

            data = bytes(buff)
            reader.MFRC522_SelectTag(uid)
            status = reader.MFRC522_Auth(reader.PICC_AUTHENT1A, BLOCK_NUMBER, CARD_KEY, uid)

            if status != reader.MI_OK:
                print("Error authenticating card")
                oled_text('Erreur d\'authentification de la carte')
                time.sleep(2.5)
                continue

            reader.MFRC522_Write(BLOCK_NUMBER, data)
            student_id = ''.join([str(x) for x in data[4:11]])
            dataCompare = ''.join([str(x) for x in data])
            readerBlockCompare = ''.join([str(x) for x in reader.MFRC522_Read(BLOCK_NUMBER)])

            if readerBlockCompare == dataCompare:
                print('Wrote card successfully! You may now remove the card from the RFID reader.')
                print("{0} Id Writed: {1}".format(obj_name, student_id ))
                oled_text('\nLa carte a ete ecrite \navec succes !')
                time.sleep(DELAY)
            else:
                print('Error writing card')
                oled_text('Erreur d\'ecriture')

        print('== DONE ===========================')

    oled_text('Fin de l\'ecriture \n En attente de donnees...')

client.loop_forever()
