import MFRC522
import time
import RPi.GPIO as GPIO


READER = MFRC522.MFRC522()
HEADER = "CESI"
CARD_KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'
DELAY = 0.5
BLOCK_NUMBER = 6

print('Waiting for RFID/NFC card to read from!')
try:
    while True:
        (status, TagType) = READER.MFRC522_Request(READER.PICC_REQIDL)
        if status == READER.MI_OK:
            print("Card detected")
        else:
            continue

        (status, uid) = READER.MFRC522_Anticoll()
        if uid is None:
            continue

        if status == READER.MI_OK:
            READER.MFRC522_SelectTag(uid)
            status = READER.MFRC522_Auth(READER.PICC_AUTHENT1A, BLOCK_NUMBER, CARD_KEY, uid)

            if status == READER.MI_OK:
                data = READER.MFRC522_Read(BLOCK_NUMBER)
                READER.MFRC522_StopCrypto1()

            dataHEADER = ''.join(chr(i) for i in data[0:4])
            if dataHEADER != HEADER:
                print("Carte invalide !")
                continue

            student_id = ''.join([str(x) for x in data[4:11]])
            print('Student Id: %s' % student_id)
            time.sleep(DELAY)

        else:
            print("Authentication error")


except KeyboardInterrupt:
    print("Bye")
    GPIO.cleanup()

except Exception as e:
    print(e)
finally:
    GPIO.cleanup()