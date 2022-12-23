import binascii
import sys
import RPi.GPIO as GPIO
import MFRC522

CARD_KEY = b'\xFF\xFF\xFF\xFF\xFF\xFF'
DELAY = 0.5
HEADER = b'CESI'
BLOCK_NUMBER = 6

reader = MFRC522.MFRC522()

print('== STEP 1 =========================')
student_id = None
while student_id is None:
    print('')
    student_id = input('Enter student ID: ')
    if not (len(student_id) == 7):
        student_id = None
        print('Error! Student ID must be egal to 7 digits - exemple: 1234567')
        continue
    print('')

print('== STEP 2 =========================')
print('Confirm you are ready to write to the card:')
print('')
print('Student ID: {0}'.format(student_id))
print('')
choice = input('Confirm card write (Y or N)? ')
if choice.lower() != 'y' and choice.lower() != 'yes':
    print('Aborted!')
    GPIO.cleanup()
    sys.exit(0)

print('== STEP 3 =========================')
print('Place the card to be written on the RFID reader...')
while True:
    (status, tag_type) = reader.MFRC522_Request(reader.PICC_REQIDL)
    if status == reader.MI_OK:
        print("Card detected")
        break

(status, uid) = reader.MFRC522_Anticoll()
if status != reader.MI_OK:
    print("Error reading card UID")
    sys.exit(1)
print("Card UID: " + str(uid))
print('Writing card (DO NOT REMOVE CARD FROM RFID READER)...')

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
    sys.exit(1)

reader.MFRC522_Write(BLOCK_NUMBER, data)

student_id = ''.join([str(x) for x in data[4:11]])

dataCompare = ''.join([str(x) for x in data])
readerBlockCompare = ''.join([str(x) for x in reader.MFRC522_Read(BLOCK_NUMBER)])

if readerBlockCompare == dataCompare:
    print('Wrote card successfully! You may now remove the card from the RFID reader.')
    print("Student Id Writed: %s" % student_id)
else:
    print('Error writing card')
    print("got" + dataCompare + "want" + readerBlockCompare)

GPIO.cleanup()