from PyQt4 import QtGui

import sys

class Preview(QtGui.QLabel):
	"""
	Preview widget with a selection of the 
	interesting part of the image
	"""

	def __init__(self, kinect):
		QtGui.QLabel.__init__(self)
		self.__kinect = kinect
		self.__refresh = True
		self.__imageData = None
		self.__startPoint = None
		self.__selectRect = None
		self.__newRect = False
		self.__width = None
		self.__height = None
		# Initialization
		self.__setKinectPixmap()
		# Events
		self.__timer = self.startTimer(20)

	def pause(self):
		"""
		Stops refreshing the image
		"""
		self.__refresh = False

	def unpause(self):
		"""
		Starts refreshing the image
		"""
		self.__refresh = True

	def timerEvent(self, event):
		"""
		Timer to refresh the kinect preview image
		"""
		QtGui.QLabel.timerEvent(self, event)
		if self.__refresh:
			toUpdate = False
			try:
				toUpdate = self.__kinect.readDepth()
			except self.__kinect.KinectError:
				self.killTimer(self.__timer)
				QtGui.QMessageBox.critical(self, u"Kinect : connexion impossible", u"Connectez la Kinect correctement et relancez l'application.")
			if toUpdate:
				self.__setKinectPixmap()

	def mousePressEvent(self, event):
		"""
		Select rectange start
		"""
		QtGui.QLabel.mouseReleaseEvent(self, event)
		self.__startPoint = [event.x(), event.y()]

	def mouseMoveEvent(self, event):
		"""
		Select rectange change
		"""
		QtGui.QLabel.mouseMoveEvent(self, event)
		diffX = event.x() - self.__startPoint[0]
		diffY = event.y() - self.__startPoint[1]
		if abs(diffX) > 0 and abs(diffY) > 0:
			self.__newRect = True
			self.__selectRect = [self.__startPoint, [diffX, diffY]]

	def mouseReleaseEvent(self, event):
		"""
		Select rectange validation
		"""
		QtGui.QLabel.mouseReleaseEvent(self, event)
		if self.__newRect is False:
			return
		# Normalize the selected rectangle
		self.__normalizeRect()
		self.__kinect.selectRect(self.__selectRect)
		self.__newRect = False

	def __normalizeRect(self):
		"""
		Transforms the selected rectangle to 
		make it fit properly (limits and ratio)
		"""
		start = self.__selectRect[0]
		ratio = self.__kinect.selectRatio
		diffX = self.__selectRect[1][0]
		diffY = self.__selectRect[1][1]
		# Orientates the rectange properly to avoid negative values
		if diffX < 0:
			start[0]+= diffX
			diffX = -diffX
		if diffY < 0:
			start[1]+= diffY
			diffY = -diffY
		# Force the ratio of the rectange
		if diffY * ratio > diffX:
			start[0]-= (diffY * ratio - diffX) / 2
			diffX = diffY * ratio
		elif diffX / ratio > diffY:
			start[1]-= (diffX / ratio - diffY) / 2
			diffY = diffX / ratio
		# Reduce the rectangle if needed
		if diffX > self.__width or diffY > self.__height:
			if self.__width > self.__height / ratio:
				diffY = self.__height
				diffX = self.__height / ratio
			else:
				diffX = self.__width
				diffY = self.__width * ratio
		# Avoid negative start points
		if start[0] < 0:
			start[0] = 0
		if start[1] < 0:
			start[1] = 0
		# Avoid overflow start points
		if diffX + start[0] > self.__width:
			start[0] = self.__width - diffX
		if diffY + start[1] > self.__height:
			start[1] = self.__height - diffY
		# Sets the proper rectangle
		self.__selectRect = [start, [diffX, diffY]]

	def __setKinectPixmap(self):
		"""
		Transforms Kinect data into a QPixmap
		"""
		data = self.__kinect.rgb32Depth
		self.__width = data.shape[1]
		self.__height = data.shape[0]
		if self.__selectRect is None:
			self.__selectRect = ([0, 0], [self.__width, self.__height])
			self.__normalizeRect()
		self.__imageData = data.tostring()
		image = QtGui.QImage(self.__imageData, self.__width, self.__height, QtGui.QImage.Format_RGB32)
		painter = QtGui.QPainter()
		painter.begin(image)
		painter.setPen(QtGui.QPen(QtGui.QColor(0, 100, 200), 3))
		painter.drawRect(self.__selectRect[0][0], self.__selectRect[0][1], self.__selectRect[1][0], self.__selectRect[1][1])
		painter.end()
		self.setPixmap(QtGui.QPixmap.fromImage(image))