from RPLCD import CharLCD
GPIO.setwarning()
lcd = CharLCD(cols=16, rows=2, pin_rs=22, pin_e=18, pins_data=[ 40, 38, 36, 32, 16, 11, 12, 22])
lcd.write_string(u'Hello world!')