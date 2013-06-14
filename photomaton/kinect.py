import freenect
import numpy
import scipy.misc

# Number of depth images used to compute one averaged image
AVERAGE_WINDOW = 5
# Maximum real depth difference from the nearest point
MAX_REAL_DEPTH_DIFF = 110
# Object width
OBJECT_WIDTH = 200
# Object height
OBJECT_HEIGHT = 200
# Object depth
OBJECT_DEPTH = 100
# Base depth (in pixels)
BASE_DEPTH = 6
# Vertical pixel size (mm)
VERTICAL_PIXEL_SIZE = 0.16
# Horizontal pixel size (mm)
HORIZONTAL_PIXEL_SIZE = 0.2
# Export filename (None = to choose in the GUI)
EXPORT_FILENAME = None

class Kinect:
	"""
	Gets and treats data from the kinect.
	"""
	def __init__(self):
		# Keeps the depth to compute an average
		self.__depthHistory = []
		# Depth data, averaged
		self.__depthData = numpy.zeros((480, 640), numpy.uint16)
		# Selection rectangle for the capture (start point, dimensions)
		self.__rect = [[0, 0], [480, 480]]
		# Captured data, improved as much as possible
		self.__capturedData = None

	def readDepth(self):
		"""
		Reads the depth from the Kinect.
		Returns if raw depth data has been updated.
		Raises a Kinect.KinectError if there are communication problems with the Kinect
		"""
		response = freenect.sync_get_depth()
		if response is None:
			raise Kinect.KinectError("not replying")
		self.__depthHistory.append(response[0])
		if len(self.__depthHistory) >= AVERAGE_WINDOW:
			newData = self.__depthHistory[0]
			for i in range(0, AVERAGE_WINDOW):
				newData = numpy.minimum(newData, self.__depthHistory[i])
			self.__depthData = newData
			self.__depthHistory = []
			return True
		return False

	def selectRect(self, rect):
		"""
		Select only a rectange in the image
		"""
		self.__rect = rect

	def capture(self):
		"""
		Capture data currently in the rectangle
		and convert data to a nice object representation
		"""
		self.__capturedData = self.rectDepth.astype(numpy.uint32)
		# Detect and remove the background
		mini = numpy.amin(self.__capturedData)
		maxi = numpy.amax(self.__capturedData)
		if maxi - mini == 0:
			maxi+= 1
		histo = numpy.histogram(self.__capturedData, maxi - mini, (mini, maxi))[0]
		i = 2
		while i < (maxi - mini) and histo[i] > 0:
			i+= 1
		maxi = i + mini - 1
		# Limit the maximum depth, forgets far points
		if maxi - mini > MAX_REAL_DEPTH_DIFF:
			maxi = mini + MAX_REAL_DEPTH_DIFF
		self.__capturedData = (255 * (self.__capturedData - mini)) / (maxi - mini)
		self.__capturedData = self.__capturedData.clip(0, 255)
		# Interpolate data to remove unknown data holes
		self.__capturedData = self.__interpolate(self.__capturedData)
		# Scale data width and height (works only with data scaled between 0 and 255)
		self.__capturedData = scipy.misc.imresize(self.__capturedData, (OBJECT_WIDTH, OBJECT_HEIGHT))
		# Scale depth
		self.__capturedData = self.__capturedData.astype(numpy.uint32)
		self.__capturedData = (self.__capturedData * OBJECT_DEPTH) / 255

	def __interpolate(self, data):
		"""
		Takes a 2D array with values from 0 to 255.
		Interpolates to replace values equal to 255.
		If they are in holes.
		"""
		fixedData = data.copy()
		width = data.shape[0]
		height = data.shape[1]
		for x in range(0, width):
			# Vertical interpolation
			gapStart = None
			gapEnd = None
			beforeVal = None
			afterVal = None
			for y in range(0, height):
				val = self.__capturedData[x,y]
				if val != 255:
					if gapStart is not None:
						gapEnd = y - 1
						afterVal = val
						if beforeVal is not None and gapEnd - gapStart < 20:
							for modY in range(gapStart, gapEnd+1):
								fixedData[x,modY] = beforeVal + ((int(afterVal) - beforeVal) * (modY + 1 - gapStart)) / (gapEnd + 2 - gapStart)
						gapStart = None
						gapEnd = None
					else:
						beforeVal = val
				elif gapStart is None:
					gapStart = y
		for y in range(0, height):
			# Horizontal interpolation
			gapStart = None
			gapEnd = None
			beforeVal = None
			afterVal = None
			for x in range(0, width):
				val = self.__capturedData[x,y]
				if val != 255:
					if gapStart is not None:
						gapEnd = x - 1
						afterVal = val
						if beforeVal is not None and gapEnd - gapStart < 20:
							for modX in range(gapStart, gapEnd+1):
								newVal = beforeVal + ((int(afterVal) - beforeVal) * (modX + 1 - gapStart)) / (gapEnd + 2 - gapStart)
								if fixedData[modX,y] == 255:
									fixedData[modX,y] = newVal
								else:
									fixedData[modX,y] = (fixedData[modX,y] + newVal) / 2
						gapStart = None
						gapEnd = None
					else:
						beforeVal = val
				elif gapStart is None:
					gapStart = x
		return fixedData

	@property
	def depth(self):
		"""
		Data at the default freenect format (numpy 16-bit array)
		"""
		return self.__depthData

	@property 
	def rectDepth(self):
		"""
		Data in the selected rectange, or all if not set
		"""
		if self.__rect is None:
			return self.depth.copy()
		return self.depth[self.__rect[0][1]:(self.__rect[0][1]+self.__rect[1][1]),self.__rect[0][0]:(self.__rect[0][0]+self.__rect[1][0])]

	@property
	def rgb32Depth(self):
		"""
		Data as a 32 bits RGB grey-scale image (numpy 32-bit array)
		"""
		depth = self.depth.astype(numpy.uint32)
		# Transforms a 16-bit value into an 8-bit value
		depth = self.__scaleToByte(depth, self.rectDepth)
		# Transforms to RGB
		depth = self.__depthToRGB(depth)
		return depth

	@property 
	def rgb32Captured(self):
		"""
		Returns the last captured data 
		"""
		if self.__capturedData is None:
			return None
		data = self.__capturedData.astype(numpy.uint32)
		data = self.__scaleToByte(data)
		data = self.__depthToRGB(data)
		return data

	@property
	def stlCaptured(self):
		"""
		Transform the selected data into a set of faces
		that can be exported directly to STL
		"""
		data = self.__capturedData
		unitH = HORIZONTAL_PIXEL_SIZE
		unitV = VERTICAL_PIXEL_SIZE
		width = OBJECT_WIDTH
		height = OBJECT_HEIGHT
		depth = OBJECT_DEPTH
		if data is None:
			return None
		# Function to get a point on the top surface from x and y
		def topPoint(x, y):
			return ((x-width/2)*unitH, (height/2-y)*unitH, (BASE_DEPTH + depth - data[y,x])*unitV)
		# Function to get a point on the bottom surface from x and y
		def bottomPoint(x, y):
			return ((x-width/2)*unitH, (height/2-y)*unitH, 0)
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
		# Puts everything together
		shape = base + top + sides
		return shape

	@property
	def selectRatio(self):
		"""
		Returns the wanted select ratio
		"""
		return float(OBJECT_WIDTH) / OBJECT_HEIGHT

	@property
	def objectWidth(self):
		"""
		Object width
		"""
		return OBJECT_WIDTH

	@property
	def objectHeight(self):
		"""
		Object height
		"""
		return OBJECT_HEIGHT

	@property
	def exportFilename(self):
		"""
		Default export file name if any
		"""
		return EXPORT_FILENAME

	def __scaleToByte(self, depth, refDepth=None):
		"""
		Scales the depth beteen 0 and 255 according to itself or the reference
		"""
		if refDepth is None:
			refDepth = depth
		minimum = numpy.amin(refDepth)
		maximum = numpy.amax(refDepth)
		if maximum == minimum:
			maximum+= 1
		depth = (depth - minimum) * 255 / (maximum - minimum)
		depth = depth.clip(0, 255)
		return depth

	def __depthToRGB(self, depth):
		"""
		Transforms values between 0 and 255 to
		gray-scale RGB pixels
		"""
		depth+= (depth << 8) + (depth << 16) + (255 << 24)
		return depth

	class KinectError(RuntimeError):
		"""
		Kinect-specific exception: communication is wrong
		"""
		def __init__(self, arg):
			self.args = [arg]