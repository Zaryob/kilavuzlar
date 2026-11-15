---
title: Building OpenCV from source
permalink: /en/arsiv/goruntu-isleme/opencv-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: OpenCV 4.0.0, Python 2 and historical APT package names.
archive_reason: Download versions are inconsistent, and x86/ARM build options are
  mixed. Rewrite the system-pip installation and virtual-environment linkage steps.
  In November 2026 only the ~/.profile command and two CMake options absent from OpenCV 4.0.0
  were corrected; the build was not repeated.
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

Note: package names on this page such as `libdc1394-22-dev`, `qt5-default`, `libvtk6-dev` and `python-dev` belong to the period of the notes; current Debian/Ubuntu releases may not have them or ship them under another name.

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

`libatlas-base-dev` and `gfortran` provide BLAS/LAPACK back ends that OpenCV can use for linear algebra. The original notes said they reduce overall speed; that claim was never measured, and the purpose of these libraries is to speed those operations up:

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

> **Warning:** Installing packages into the system Python with `sudo pip` can break the distribution’s own Python packages; current Debian/Ubuntu releases refuse it with an `externally-managed-environment` error. The commands below are kept as a historical record; today, use a virtual environment created with `python3 -m venv`.

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

Add it to the shell environment through ~/.profile. (The `echo -e` command in the original notes wrote a single line starting with `#` because of the trailing `\` characters, so nothing was exported; the form below appends the four lines separately.)

```
cat >> ~/.profile <<'EOF'
# virtualenv and virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
EOF
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

Configure with CMake. (The `FORCE_VTK` and `WITH_LIBV4L` options in the original notes do not exist in OpenCV 4.0.0 and are ignored; `WITH_VTK` and `WITH_V4L` replace them. `ENABLE_NEON` and `ENABLE_VFPV3` are ARM-only; remove them on x86.)

```
cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D ENABLE_VFPV3=ON \
    -D WITH_OPENGL=ON \
    -D WITH_QT=ON \
    -D WITH_VTK=ON \
    -D WITH_V4L=ON \
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
