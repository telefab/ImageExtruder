#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
from PyQt4 import QtGui
import sys
import os.path
from kinect import Kinect
from preview import Preview
from stl_writer import ASCIISTLWriter as STLWriter

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
		self.__kinect = Kinect() # This contains all the logic
		self.__objectData = None # Keep this to avoid refresh issues on the image
		self.__exportDirectory = os.path.expanduser('~') # Save directory
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
		# Select the filename
		filename = self.__kinect.exportFilename
		if filename is None:
			filename = QtGui.QFileDialog.getSaveFileName(self, 'Exporter en STL', self.__exportDirectory, 'Fichier STL (*.stl)')
			filename = str(filename)
			if filename == '':
				return
			self.__exportDirectory = os.path.dirname(filename)
		# Get the shape
		shape = self.__kinect.stlCaptured
		if shape is None:
			QtGui.QMessageBox.warning(self, u"Pas de capture", u"Capturez une image avant de l'exporter.")
			return
		# Writes the STL file
		with open(filename, 'w') as fp:
			writer = STLWriter(fp)
			writer.add_faces(shape)
			writer.close()
		# Confirm
		QtGui.QMessageBox.information(self, u"Modèle 3D prêt", u"Le modèle 3D a été exporté, il ne reste plus qu'à l'imprimer.")


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