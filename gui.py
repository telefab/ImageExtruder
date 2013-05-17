#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
import sys
from extruder import *
from PIL import ImageQt, Image
from os import path

class MainWindow(QtGui.QMainWindow):
	"""
	Main window welcoming the user
	"""
	def __init__(self):
		"""
		Initialize the window
		"""
		QtGui.QMainWindow.__init__(self)
		# Internal state
		self.__imagePath = None
		self.__pixels = None
		self.__dominantColor = None
		self.__dominantColorRate = None
		self.__worker = None
		# initialize the UI
		self.__mainWidget = None
		self.__imageButton = None
		self.__imageLabel  = None
		self.__thresholdInput = None
		self.__widthInput = None
		self.__refreshButton = None
		self.__previewImage = None
		self.__unitInput = None
		self.__baseZInput = None
		self.__shapeZInput = None
		self.__exportButton = None
		self.__initUI()
		# Events
		self.__imageButton.clicked.connect(self.__selectImage)
		self.__refreshButton.clicked.connect(self.__refreshImage)
		self.__exportButton.clicked.connect(self.__exportImage)
		self.startTimer(1000)

	def timerEvent(self, event):
		"""
		Quick fix for a stupid display bug
		"""
		if self.__pixels is not None:
			self.__previewImage.setPixmap(QtGui.QPixmap(QtGui.QImage(ImageQt.ImageQt(self.__pixels))))

	def __initUI(self):
		"""
		Initialize the GUI
		"""
		# Layout
		layout = QtGui.QVBoxLayout()
		self.__mainWidget = QtGui.QWidget()
		self.__mainWidget.setLayout(layout)
		self.setCentralWidget(self.__mainWidget)

		# Browse images button
		hLayout = QtGui.QHBoxLayout()
		label = QtGui.QLabel(u"Image :")
		self.__imageLabel = QtGui.QLabel("aucune")
		hLayout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__imageLabel)
		layout.addLayout(hLayout)
		self.__imageButton = QtGui.QPushButton(u"Choisir une image")
		layout.addWidget(self.__imageButton)

		# Surface width input
		self.__widthInput = QtGui.QDoubleSpinBox()
		self.__widthInput.setDecimals(0)
		self.__widthInput.setMinimum(50)
		self.__widthInput.setMaximum(1000)
		self.__widthInput.setValue(PROFILE_AREA_WIDTH)
		hLayout = QtGui.QHBoxLayout()
		label = QtGui.QLabel(u"Largeur de la forme (px) :")
		hLayout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__widthInput)
		layout.addLayout(hLayout)

		# Threshold input
		self.__thresholdInput = QtGui.QDoubleSpinBox()
		self.__widthInput.setDecimals(0)
		self.__thresholdInput.setMinimum(0)
		self.__thresholdInput.setMaximum(300)
		self.__thresholdInput.setValue(COLOR_THRESHOLD)
		hLayout = QtGui.QHBoxLayout()
		label = QtGui.QLabel(u"Tolérance de détection des couleurs :")
		hLayout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__thresholdInput)
		layout.addLayout(hLayout)

		# Preview image
		self.__previewImage = QtGui.QLabel()
		self.__previewImage.setPixmap(QtGui.QPixmap(PROFILE_AREA_WIDTH, PROFILE_AREA_WIDTH))
		label = QtGui.QLabel(u"Forme détectée :")
		hLayout = QtGui.QHBoxLayout()
		layout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__previewImage)
		hLayout.addStretch(1)
		layout.addLayout(hLayout)

		# Refresh button
		self.__refreshButton = QtGui.QPushButton(u"Calculer la forme")
		layout.addWidget(self.__refreshButton)

		# Surface width input
		self.__unitInput = QtGui.QDoubleSpinBox()
		self.__unitInput.setDecimals(3)
		self.__unitInput.setMinimum(0.001)
		self.__unitInput.setMaximum(10)
		self.__unitInput.setValue(SHAPE_UNIT)
		hLayout = QtGui.QHBoxLayout()
		label = QtGui.QLabel(u"Taille d'un pixel (mm) :")
		hLayout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__unitInput)
		layout.addLayout(hLayout)

		# Surface width input
		self.__baseZInput = QtGui.QDoubleSpinBox()
		self.__baseZInput.setDecimals(0)
		self.__baseZInput.setMinimum(1)
		self.__baseZInput.setMaximum(100)
		self.__baseZInput.setValue(BASE_Z)
		hLayout = QtGui.QHBoxLayout()
		label = QtGui.QLabel(u"Hauteur de la base :")
		hLayout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__baseZInput)
		layout.addLayout(hLayout)

		# Surface width input
		self.__shapeZInput = QtGui.QDoubleSpinBox()
		self.__shapeZInput.setDecimals(0)
		self.__shapeZInput.setMinimum(1)
		self.__shapeZInput.setMaximum(100)
		self.__shapeZInput.setValue(SHAPE_Z)
		hLayout = QtGui.QHBoxLayout()
		label = QtGui.QLabel(u"Hauteur de la forme :")
		hLayout.addWidget(label)
		hLayout.addStretch(1)
		hLayout.addWidget(self.__shapeZInput)
		layout.addLayout(hLayout)

		# Export button
		self.__exportButton = QtGui.QPushButton(u"Exporter en STL")
		layout.addWidget(self.__exportButton)

		# Center the window
		geo = self.frameGeometry()
		geo.moveCenter(QtGui.QDesktopWidget().availableGeometry().center())
		self.move(geo.topLeft())
        # Title
		self.setWindowTitle("Profil 3D")

	def __selectImage(self, *args):
		"""
		Select an image
		"""
		filename = QtGui.QFileDialog.getOpenFileName(self, 'Choisir une image', '', 'Image (*.jpg *.jpeg *.png *.gif)')
		if filename != '':
			self.__imagePath = str(filename)
			self.__imageLabel.setText(path.basename(self.__imagePath))

	def __refreshImage(self, *args):
		"""
		Refresh the image
		"""
		if self.__imagePath is not None:
			self.__mainWidget.setEnabled(False)
			self.__worker = ParseWorker(self.__imagePath, self.__threshold, self.__width)
			self.__worker.finished.connect(self.__refreshImageDone)
			self.__worker.start()

	def __refreshImageDone(self, thread, dominantColor, dominantColorRate):
		"""
		The refresh action is done 
		"""
		self.__pixels = thread.pixels
		self.__dominantColor = dominantColor
		self.__dominantColorRate = dominantColorRate
		self.__previewImage.setPixmap(QtGui.QPixmap(QtGui.QImage(ImageQt.ImageQt(self.__pixels))))
		self.__mainWidget.setEnabled(True)

	def __exportImage(self, *args):
		"""
		Export an image
		"""
		if self.__pixels is not None:
			filename = QtGui.QFileDialog.getSaveFileName(self, 'Exporter en STL', '', 'Fichier STL (*.stl)')
			if filename != '':
				self.__mainWidget.setEnabled(False)
				self.__worker = ExtrudeWorker(filename, self.__pixels, self.__unit, self.__baseZ, self.__shapeZ)
				self.__worker.finished.connect(self.__exportImageDone)
				self.__worker.start()

	def __exportImageDone(self):
		"""
		The export action is finished
		"""
		self.__mainWidget.setEnabled(True)

	@property 
	def __width(self):
		return int(self.__widthInput.value())

	@property
	def __threshold(self):
		return int(self.__thresholdInput.value())

	@property
	def __unit(self):
		return self.__unitInput.value()

	@property
	def __baseZ(self):
		return int(self.__baseZInput.value())

	@property
	def __shapeZ(self):
		return int(self.__shapeZInput.value())

class ParseWorker(QtCore.QThread):
	"""
	Worker that runs the image parsing in the background
	"""

	# Finished signal
	finished = QtCore.pyqtSignal(QtCore.QThread, list, float, name="finished")

	def __init__(self, imagePath, threshold, width):
		"""
		Gets the parameters
		"""
		super(ParseWorker, self).__init__()
		self.__imagePath = imagePath
		self.__threshold = threshold
		self.__width = width
		self.__pixels = None

	def run(self):
		"""
		Runs the function
		"""
		self.__pixels, dominantColor, dominantColorRate = parseImage(self.__imagePath, self.__threshold, self.__width)
		self.finished.emit(self, dominantColor, dominantColorRate)

	@property
	def pixels(self):
		return self.__pixels

class ExtrudeWorker(QtCore.QThread):
	"""
	Worker that runs the image extrusion in the background
	"""

	# Finished signal
	finished = QtCore.pyqtSignal(name="finished")

	def __init__(self, filename, pixels, unit, baseZ, shapeZ):
		"""
		Gets the parameters
		"""
		super(ExtrudeWorker, self).__init__()
		self.__filename = filename
		self.__pixels = pixels
		self.__unit = unit
		self.__baseZ = baseZ
		self.__shapeZ = shapeZ

	def run(self):
		"""
		Runs the function
		"""
		extrudeToSTL(self.__filename, self.__pixels, self.__unit, self.__baseZ, self.__shapeZ)
		self.finished.emit()

def main():
    """
    Start the program
    """

    # Initialize the GUI
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()

    # Start
    window.show()
    sys.exit(app.exec_())
    

if __name__ == '__main__':
    main()