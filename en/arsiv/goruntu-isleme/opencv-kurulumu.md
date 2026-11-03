---
title: Building OpenCV from source
permalink: /en/arsiv/goruntu-isleme/opencv-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: OpenCV 4.0.0, Python 2 and historical APT package names.
archive_reason: Download versions are inconsistent, and x86/ARM build options are
  mixed. Rewrite the system-pip installation and virtual-environment linkage steps.
lang: en
translation_key: guide-arsiv-goruntu-isleme-opencv-kurulumu
translation_of: /arsiv/goruntu-isleme/opencv-kurulumu/
translated: '2026-11-03'
---

# Building OpenCV from source

## Install build dependencies

### Update the system

```
sudo apt-get update && sudo apt-get upgrade
```

### Install development tools and CMake

```
sudo apt-get install build-essential cmake unzip pkg-config
```

### Image and video codecs

The original notes suggest installing all of these:

* JPEG, PNG and TIFF: ```sudo apt-get install libjpeg-dev libpng-dev libtiff-dev```
* Video capture, including cameras: ``` sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev```
* Video files and H.264: ```sudo apt-get install libxvidcore-dev libx264-dev```
* Additional codecs: ```sudo apt-get install libdc1394-22-dev libtheora-dev libvorbis-dev yasm libopencore-amrnb-dev libopencore-amrwb-dev libxine2-dev```

### GUI tools

Install GTK if using graphical output such as an OpenCV window:

```
sudo apt-get install libgtk-3-dev libgtkglext1-dev
```

For GTK-related support:

```
sudo apt-get install libcanberra-gtk*
```

For Qt:

```
sudo apt-get install qt5-default
```

For VT:

```
sudo apt-get install libvtk6-dev
```

### Numerical optimisation tools

The original notes add OpenCV’s numerical libraries for numerical processing, while noting a possible performance trade-off:

```
sudo apt-get install libatlas-base-dev gfortran
```

### Optimisation and parallel processing

```
sudo apt-get install -y libtbb-dev libeigen3-dev
```

### Python bindings

For Python 3:

```
sudo apt-get install python3-dev
```

For Python 2:

```
sudo apt-get install python-dev
```

### Java bindings

```
sudo apt-get install -y ant default-jdk
```

## Download OpenCV sources

Choose a release on the [GitHub releases page](https://github.com/opencv/opencv/releases), then download with wget:

```
cd ~
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.x.y.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.x.y.zip
```

Extract and rename the directories:

```
unzip opencv.zip
unzip opencv_contrib.zip

mv opencv-4.0.0 opencv
mv opencv_contrib-4.0.0 opencv_contrib
```

## Build environment

### Install into the main system

The original notes offer this approach if not using virtualenv.

Install NumPy system-wide:

```
sudo pip3 install numpy
```

Or for the user:

```
pip3 install numpy --user
```

### Use virtualenv

A virtual environment isolates Python packages from the main system.

Install virtualenv:

```
sudo pip install virtualenv virtualenvwrapper
sudo rm -rf ~/get-pip.py ~/.cache/pip
```

Add it to the shell environment through ~/.profile:

```
echo -e "# virtualenv and virtualenvwrapper \
export WORKON_HOME=$HOME/.virtualenvs  \
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3 \
source /usr/local/bin/virtualenvwrapper.sh" >> ~/.profile
```

Reload the shell configuration:

```
source ~/.profile
```

Create a Python environment:

```
mkvirtualenv cv -p python3
```

Enter it:

```
workon cv
```

In later sessions, use ```workon cv``` to enter the environment named cv.

Install NumPy:

```
pip3 install numpy
```

## Build OpenCV

### Configure

OpenCV is predominantly C++ and uses CMake. Keep build output separate from the source by creating a `build` directory inside the OpenCV checkout:

```
cd ~/opencv
mkdir build
cd build
```

Configure with CMake:

```
cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D ENABLE_VFPV3=ON \
    -D WITH_OPENGL=ON \
    -D WITH_QT=ON \
    -D FORCE_VTK=ON \
    -D WITH_LIBV4L=ON \
    -D WITH_TBB=ON \
    -D WITH_GDAL=ON \
    -D WITH_FFMPEG=0 \
    -D WITH_XINE=ON \
    -D BUILD_TESTS=ON \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D ENABLE_PRECOMPILED_HEADERS=OFF \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D BUILD_EXAMPLES=ON ..
```

### Compile

Start Make:

```
make
```

For a multicore CPU, use a parallel build:

```
make -j{çekirdek sayınızın bir eksiği}
```

For example, on four cores:

```
make -j3
```

### Install

```
sudo make install
sudo ldconfig
```

When run in the virtual environment, this installs the Python binding there. The C++ libraries and shared binaries are installed in the main system.
