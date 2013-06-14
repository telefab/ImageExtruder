Kinect photomaton
=================

**Scan your face using the Kinect and export an STL file to print.**

The main executable is **photomaton.py**.


* First select your face in the live preview window, then click "Capturer". 
* If you are happy with the result (image on the right), click "Exporter".
* The STL file is called "objet.stl" in the working directory (directory of the program).

Requirements
----------------

This program is written in Python 2. It requires some libraries:
python-freenect python-qt4 python-numpy python-scipy

It also requires a Kinect device to be connected to the computer.


Configuration
----------------

Settings about the detection maximum depth,
the object precision and size can be modified at the top of the **kinect.py** file.

Troubleshooting
----------------

If the program does not start, it probably has a problem to communicate with the Kinect.
Try to unplug it and plug it again. If it still does not work, try installing the freenect examples and
check if they work.

With Ubuntu 12.04, the Kinect is used automatically as a webcam, so it cannot be used by Freenect.
To fix this, type in a terminal:
```bash
sudo modprobe -r gspca_kinect
sudo modprobe -r gspca_main
```
Or to make it permanent, type as root:
```bash
echo "blacklist gspca_kinect" >> /etc/modprobe.d/blacklist.conf
```
