#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
"""
Turns an image into an extruded shape.
The dominant color is used as base.
Other colors are higher.
Requires the Python PIL library (http://www.pythonware.com/products/pil/)
"""
from PIL import Image
from stl_writer import ASCIISTLWriter as STLWriter
import math
import sys

# Threshold to determine if a color is similar to another
# To increase if some background is detected as part of the profile
# To decrease if the profile is not entirely detected
COLOR_THRESHOLD = 80

# The area in which the profile is framed is a square
# Number of pixels of 1 side of the square
# To increase to get a better definition
# To decrease to get a simpler shape
PROFILE_AREA_WIDTH = 150

# Size of 1 pixel in millimeters
# Allows to scale the whole shape
SHAPE_UNIT = 0.16

# Base altitude (no shape)
# in pixels
BASE_Z = 5

# Shape altitude in pixels
SHAPE_Z = 20

def main():
	"""
	Program bootstart function
	"""
	# Read arguments
	if len(sys.argv) != 3:
		print("""
This program transforms shape in front of a green background into
an extruded 3D STL file.

Usage: ./extruder.py image output
		image: path to the RGB image
		output: path to the STL file to write
		""")
		return
	imgPath = sys.argv[1]
	stlPath = sys.argv[2]
	# Reads the image to get a scaled black/white image
	pixels, dominantColor, dominantColorRate = parseImage(imgPath, COLOR_THRESHOLD, PROFILE_AREA_WIDTH)
	print "Dominant color (background): " + str(int(dominantColor[0])) + ", " + str(int(dominantColor[1])) + ", " + str(int(dominantColor[2])) + " (" + str(int(dominantColorRate * 100)) + "%)"
	print("Generated the shape image")
	# Show the resulting image
	pixels.show()
	# Gets the 3D faces from the image and write to STL
	extrudeToSTL(stlPath, pixels, SHAPE_UNIT, BASE_Z, SHAPE_Z)
	print("Written the 3D file to " + stlPath)

def colorDist(color1, color2):
	"""
	Computes the distance between 2 colors
	"""
	return math.sqrt((color2[0] - color1[0])**2 + (color2[1] - color1[1])**2 + (color2[2] - color1[2])**2)

def parseImage(filename, threshold, size):
	"""
	Reads an image file 
	and returns a new square image with the
	dominant color set as black and the others set as white.
	Returns a tuple (image, dominant color, dominant color rate)
	"""
	# Load the image
	img = Image.open(filename)
	pix = img.load()
	width, height = img.size
	# Search for the dominant color
	colorGroups = []
	dominantGroup = None
	for x in range(0, width):
		for y in range(0, height):
			color = pix[x,y]
			chosenGroup = None
			# Search for the group of this color
			for group in colorGroups:
				if colorDist(color, group['color']) <= threshold:
					group['count']+= 1
					for i in range(0, 3):
						group['sum'][i]+= color[i]
						group['color'][i] = float(group['sum'][i]) / group['count']
					chosenGroup = group
					break
			if chosenGroup is None:
				# Create the group if it does not exist
				chosenGroup = {}
				chosenGroup['count'] = 1
				chosenGroup['sum'] = list(color) 
				chosenGroup['color'] = list(color)
				colorGroups.append(chosenGroup)
			# Select the dominant group
			if dominantGroup is None or chosenGroup['count'] > dominantGroup['count']:
				dominantGroup = chosenGroup
	dominantColor = dominantGroup['color']
	dominantColorRate = float(dominantGroup['count']) / (height * width)
	# Finds and removes the surfaces that are too small (TODO)
	#minPixels = width*height / 1000
	#surfaces = []
	#colSurfaces = None
	#for x in range(0, width):
	#	prevColSurfaces = colSurfaces
	#	colSurfaces = []
	#	prevSurface = None
	#	for y in range(0, height):
	#		color = 0
	#		if colorDist(dominantColor, pix[x, y]) > threshold:
	#			color = 1
	# Finds the rectangle that contains the interesting part of the image
	minX = width
	maxX = 0
	minY = height
	maxY = 0
	for x in range(0, width):
		for y in range(0, height):
			if colorDist(dominantColor, pix[x, y]) > threshold:
				# Detected a pixel that is not background
				if minX > x:
					minX = x
				if maxX < x:
					maxX = x
				if minY > y:
					minY = y
				if maxY < y:
					maxY = y
	realWidth = float(maxX - minX)
	realHeight = float(maxY - minY)
	realSize = max(realWidth, realHeight)
	startX = minX + realWidth/2 - realSize / 2
	startY = minY + realHeight/2 - realSize / 2
	factor = realSize / size
	# Creates a new image with the proper size and only black/white pixels
	newImg = Image.new('RGB', (size, size), (0, 0, 0))
	newPix = newImg.load()
	for a in range(0, size):
		# Concerned pixels in X
		xFrom = int(round(startX + a * factor))
		if xFrom < 0:
			xFrom = 0
		xTo = int(round(startX + (a+1) * factor))
		if xFrom == xTo:
			xTo+= 1
		if xTo > width:
			xTo = width
		for b in range(0, size):
			# Concerned pixels in Y
			yFrom = int(round(startY + b * factor))
			if yFrom < 0:
				yFrom = 0
			yTo = int(round(startY + (b+1) * factor))
			if yFrom == yTo:
				yTo+= 1
			if yTo > height:
				yTo = height
			# Average the color to decide on the pixel
			colorAv = [0, 0, 0]
			colorSum = [0, 0, 0]
			count = 0
			decision = False
			for x in range(xFrom, xTo):
				for y in range(yFrom, yTo):
					color = pix[x,y]
					count+= 1
					for i in range(0, 3):
						colorSum[i]+= color[i]
						colorAv[i] = float(colorSum[i]) / count
			if count > 0:
				decision = (colorDist(dominantColor, colorAv) > threshold)
			if decision:
				newPix[a, b] = (255, 255, 255)
	return (newImg, dominantColor, dominantColorRate)

def addFrame(img, frameWidth):
	"""
	Returns a new image that is the same with a white frame around it
	"""
	width, height = img.size
	pix = img.load()
	newImg = Image.new('RGB', (width+frameWidth*2, height+frameWidth*2), (255, 255, 255))
	newPix = newImg.load()
	for x in range(0, width):
		for y in range(0, height):
			newPix[x+frameWidth, y+frameWidth] = pix[x, y]
	return newImg
	
def extrude(img, unit, baseZ, fullZ):
	"""
	Extrudes the given image and returns a set of faces
	that can be exported directly to STL
	"""
	width, height = img.size
	pix = img.load()
	# Function to get a point on the top surface from x and y
	def topPoint(x, y):
		z = baseZ
		if pix[x, y][0] != 0:
			z = fullZ
		return ((x-width/2)*unit, (height/2-y)*unit, z*unit)
	# Function to get a point on the bottom surface from x and y
	def bottomPoint(x, y):
		return ((x-width/2)*unit, (height/2-y)*unit, 0)
	# Constructs a simple square base
	base = [(bottomPoint(0, 0), bottomPoint(0, height-1), bottomPoint(width-1, height-1), bottomPoint(width-1, 0))]
	# Constructs the top surface
	top = []
	for x in range(0, width-1):
		for y in range(0, height-1):
			top.append((topPoint(x, y), topPoint(x+1, y), topPoint(x+1, y+1), topPoint(x, y+1)))
	# Constructs the sides
	sides = []
	for x in range(0, width-1):
			sides.append((bottomPoint(x, 0), bottomPoint((x+1), 0), topPoint(x+1, 0), topPoint(x, 0)))
			sides.append((bottomPoint(x, height-1), bottomPoint(x+1, height-1), topPoint(x+1, height-1), topPoint(x, height-1)))
	for y in range(0, height-1):
			sides.append((bottomPoint(0, y), bottomPoint(0, y+1), topPoint(0, y+1), topPoint(0, y)))
			sides.append((bottomPoint(width-1, y), bottomPoint(width-1, y+1), topPoint(width-1, y+1), topPoint(width-1, y)))

	shape = base + top + sides
	return shape

def extrudeToSTL(stlPath, img, unit, baseZ, fullZ):
	"""
	Addes a frame, extrudes and then writes to an STL file
	"""
	# Gets the 3D faces from the image
	faces = extrude(addFrame(img, int(fullZ-baseZ)), unit, baseZ, fullZ)
	# Writes the STL file
	with open(stlPath, 'w') as fp:
		writer = STLWriter(fp)
		writer.add_faces(faces)
		writer.close()

if __name__ == '__main__':
	main()