#By: Guy Fisher, @guyisit
#More at https://github.com/guyisit/photobooth ; https://hackaday.io/project/6625-raspberry-pi-photobooth
#
#Inspired/ helped by:
#http://www.instructables.com/id/Raspberry-Pi-photo-booth-controller/?ALLSTEPS
#http://code.activestate.com/recipes/362879-watermark-with-pil/
#https://github.com/jcroucher/pi-photo-booth/blob/master/photobooth.py	
#http://stackoverflow.com/questions/25592240/raspberry-pi-camera-auto-capture-python-script
#
#Todo:
#finish watermark/ blank files
#Notes:
#Camera output is currently 1920x1080
#watermark is turned off temporarily
#
from threading import Thread
import RPi.GPIO as GPIO
import ImageEnhance
import time
import io
import picamera
import random
import os
import sys
import cups
import PIL
from PIL import Image

imgPath = '/home/pi/PiCam/temp' #location for images to be saved
GPIO.setwarnings(False) #disabled errors when ready LED is already ON
GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.IN) #4x1 button
GPIO.setup(21, GPIO.IN) #2x2 button
GPIO.setup(26, GPIO.OUT) #ready LED
GPIO.setup(16, GPIO.IN) #1x1 button
GPIO.setup(18, GPIO.OUT) #flash relay

#capture image from camera
def take_pictures():
    with picamera.PiCamera() as cam:
        counter = 0
        for each in range(4):
            counter = counter + 1
            cam.start_preview()
            if counter == 1: #length of preview time for first picture
                time.sleep(6)
            if counter > 1: #length of preview time for pictures 2-4
                time.sleep(3)
            cam.capture(imgPath + '/image' + str(counter) + '.jpg')
            cam.stop_preview()

def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def watermark(im, mark, position, opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0,0,0,0))
    if position == 'tile':
        for y in range(0, im.size[1], mark.size[1]):
            for x in range(0, im.size[0], mark.size[0]):
                layer.paste(mark, (x, y))
    elif position == 'scale':
        # scale, but preserve the aspect ratio
        ratio = min(
            float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
        w = int(mark.size[0] * ratio)
        h = int(mark.size[1] * ratio)
        mark = mark.resize((w, h))
        layer.paste(mark, ((im.size[0] - w) / 2, (im.size[1] - h) / 2))
    else:
        layer.paste(mark, position)
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)

def combineImages2x2():		
# Do the merging
	blankImage = Image.open(imgPath + '/2x2blank.jpg')

	image1 = Image.open(imgPath + '/image1.jpg')
	blankImage.paste(image1, (0,200)) #each image is offset 200px to account for boarder

	image2 = Image.open(imgPath + '/image2.jpg')
	blankImage.paste(image2, (1920,200))

	image3 = Image.open(imgPath + '/image3.jpg')
	blankImage.paste(image3, (0,1280))

	image4 = Image.open(imgPath + '/image4.jpg')
	blankImage.paste(image4, (1920,1280))

	blankImage.save(imgPath + '/combined' + now + '.jpg', 'JPEG', quality=100)

def combineImages4x1():
			
	# Do the merging
	blankImage = Image.open(imgPath + '/blank4x1.jpg')

	image1 = Image.open(imgPath + '/image1.jpg')		
	image1 = image1.rotate(90)
	blankImage.paste(image1, (0,0))

	image2 = Image.open(imgPath + '/image2.jpg')		
	image2 = image2.rotate(90)
	blankImage.paste(image2, (1080,0))

	image3 = Image.open(imgPath + '/image3.jpg')		
	image3 = image3.rotate(90)
	blankImage.paste(image3, (2160,0))

	image4 = Image.open(imgPath + '/image4.jpg')		
	image4 = image4.rotate(90)
	blankImage.paste(image4, (3240,0))

	blankImage.save(imgPath + '/combined' + now + '.jpg', 'JPEG', quality=100)	

def combineImages1x1():
    blankImage = Image.open(imgPath + '/1x1blank.jpg')

    image1 = Image.open(imgPath + '/image5.jpg')		
    image1 = image1.rotate(90)
    blankImage.paste(image1, (0,0))

    blankImage.save(imgPath + '/combined' + now + '.jpg', 'JPEG', quality=100)	
	
#Print it!!
def printPhoto():
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = printers.keys()[0]
    conn.printFile(printer_name, imgPath + '/' + now + '.jpg', "TITLE",{})

    time.sleep(180) #An attempt to make people wait before ready light comes on again; not tested yet

def two_by_two():
    GPIO.output(18, True) #turn on flash
    take_pictures()
    GPIO.output(18, False) #turn flash off
    combineImages2x2()
    #im = Image.open(imgPath + '/combined' + now + '.jpg')
    #mark = Image.open(imgPath + '/mark.jpg')
    #watermark(im, mark, 'tile', 0.5).show()
    #watermark(im, mark, 'scale', 1.0).show()
    #watermark(im, mark, (0, 0), 0.25).save(imgPath + '/' + now + '.jpg')
    #printPhoto()

def four_by_one():
    GPIO.output(18, True)
    take_pictures()
    GPIO.output(18, False)
    combineImages4x1()
    #im = Image.open(imgPath + '/combined' + now + '.jpg')
    #mark = Image.open(imgPath + '/mark.jpg')
    #watermark(im, mark, 'tile', 0.5).show()
    #watermark(im, mark, 'scale', 1.0).show()
    #watermark(im, mark, (0, 0), 0.25).save(imgPath + '/' + now + '.jpg')
    #printPhoto()	

def one_by_one():
    with picamera.PiCamera() as cam:
        cam.start_preview()
        GPIO.output(18, True)
        time.sleep(6)
        cam.capture(imgPath + '/image' + str(5) + '.jpg')
        cam.stop_preview()
        GPIO.output(18, False)
    combineImages1x1()
    #printPhoto()	
	
if __name__ == '__main__':
    while True:
        GPIO.output(26, True) #turn on camera ready LED
        if (GPIO.input(21) == False): #2x2
            GPIO.output(26, False) #turn off camera ready LED
            now = time.strftime("%Y-%m-%d-%H:%M:%S") #set timestamp
            two_by_two() #execute subroutine
	if (GPIO.input(20) == False): #4x1
            GPIO.output(26, False)
            now = time.strftime("%Y-%m-%d-%H:%M:%S")
            four_by_one()
	if (GPIO.input(16) == False): #1x1
            GPIO.output(26, False)
            now = time.strftime("%Y-%m-%d-%H:%M:%S")
            one_by_one()
			
#FIN
