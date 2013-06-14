#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
from PyQt4 import QtGui
import sys
from kinect import Kinect
from preview import Preview
from stl_writer import ASCIISTLWriter as STLWriter

STL_PATH = "objet.stl"

class Photomaton(QtGui.QMainWindow):
	"""
	Main window welcoming the user
	"""
	def __init__(self):
		"""
		Initialize the window
		"""
		QtGui.QMainWindow.__init__(self)
		# Internal state
		self.__kinect = Kinect()
		self.__objectData = None
		# Initialize the UI
		self.__mainWidget = None
		self.__previewImage = None
		self.__objectImage = None
		self.__captureButton = None
		self.__exportButton = None
		self.__initUI()
		# Events
		self.__captureButton.clicked.connect(self.__onCapture)
		self.__exportButton.clicked.connect(self.__onExport)

	def __initUI(self):
		"""
		Initialize the GUI
		"""
		# Layout
		layout = QtGui.QHBoxLayout()
		self.__mainWidget = QtGui.QWidget()
		self.__mainWidget.setLayout(layout)
		self.setCentralWidget(self.__mainWidget)

		# Kinect image
		vLayout = QtGui.QVBoxLayout()
		self.__previewImage = Preview(self.__kinect)
		vLayout.addWidget(QtGui.QLabel(u"Image directe :"))
		vLayout.addWidget(self.__previewImage)
		layout.addLayout(vLayout)

		# Object image
		vLayout = QtGui.QVBoxLayout()
		self.__objectImage = QtGui.QLabel()
		vLayout.addWidget(QtGui.QLabel(u"Objet à imprimer :"))
		vLayout.addWidget(self.__objectImage)
		vLayout.addStretch(1)
		self.__captureButton = QtGui.QPushButton(u"Photographier")
		vLayout.addWidget(self.__captureButton)
		self.__exportButton = QtGui.QPushButton(u"Exporter")
		vLayout.addWidget(self.__exportButton)
		layout.addLayout(vLayout)
		self.__refreshObjectImage()

		# Center the window
		geo = self.frameGeometry()
		geo.moveCenter(QtGui.QDesktopWidget().availableGeometry().center())
		self.move(geo.topLeft())
        # Title
		self.setWindowTitle("Photomaton")

	def __refreshObjectImage(self):
		"""
		Refresh the object image
		"""
		width = self.__kinect.objectWidth
		height = self.__kinect.objectHeight
		data = self.__kinect.rgb32Captured
		image = None
		if data is not None:
			self.__objectData = data.tostring()
			image = QtGui.QImage(self.__objectData, width, height, QtGui.QImage.Format_RGB32)
		else:
			image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
			image.fill(0)
		self.__objectImage.setPixmap(QtGui.QPixmap.fromImage(image))

	def __onCapture(self, event):
		"""
		Capture the image from the camera
		"""
		self.__kinect.capture()
		self.__refreshObjectImage()

	def __onExport(self):
		"""
		Export the selected image to STL
		"""
		shape = self.__kinect.stlCaptured
		if shape is None:
			return
		# Writes the STL file
		with open(STL_PATH, 'w') as fp:
			writer = STLWriter(fp)
			writer.add_faces(shape)
			writer.close()


def main():
    """
    Start the program
    """

    # Initialize the GUI
    app = QtGui.QApplication(sys.argv)
    window = Photomaton()

    # Start
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()