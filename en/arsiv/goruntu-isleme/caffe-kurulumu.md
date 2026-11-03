---
title: Installing Caffe
permalink: /en/arsiv/goruntu-isleme/caffe-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: BVLC Caffe, Python 2/3.7 and OpenCV 4 patches.
archive_reason: Python ABI paths and architecture-specific library directories are
  hard-coded. Verify dependencies, patches and tests in a pinned environment.
lang: en
translation_key: guide-arsiv-goruntu-isleme-caffe-kurulumu
translation_of: /arsiv/goruntu-isleme/caffe-kurulumu/
translated: '2026-11-03'
---

# Installing Caffe

## Install dependencies

```
sudo apt-get update && sudo apt-get upgrade

sudo apt-get install -y gfortran cython

sudo apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev libhdf5-serial-dev protobuf-compiler git

sudo apt-get install --no-install-recommends -y libboost-all-dev

sudo apt-get install -y python-dev libgflags-dev libgoogle-glog-dev liblmdb-dev libatlas-base-dev python-skimage

sudo pip3 install pyzmq jsonschema pillow numpy scipy ipython jupyter pyyaml
```

## Install OpenCV

To use the distribution package:

```
sudo apt install libopencv-dev
```

For a manually built version, see the [OpenCV installation notes](opencv-kurulumu.md).

## Clone Caffe

```
git clone https://github.com/BVLC/caffe
```

## Configure Caffe

Enter its directory and copy the default configuration:

```
cd caffe

cp Makefile.config.example Makefile.config

nano Makefile.config
```

## Prepare Makefile.config

* For Raspberry Pi, change `#CPU_ONLY := 1` to `CPU_ONLY := 1`.
* For Python 2 with a pip-installed NumPy, replace `/usr/lib/python2.7/dist-packages/numpy/core/include` with `/usr/local/lib/python2.7/dist-packages/numpy/core/include`.
* To disable Python 2, change:

    ```
     PYTHON_INCLUDE := /usr/include/python2.7 \
    		/usr/lib/python2.7/dist-packages/numpy/core/include
    ```

  to:

    ```
    # PYTHON_INCLUDE := /usr/include/python2.7 \
    #		/usr/lib/python2.7/dist-packages/numpy/core/include
    ```

  The leading `#` characters comment out Python 2 support.

* For Python 3, uncomment the lines below `Uncomment to use Python 3 (default is Python 2)`:

    ```
    PYTHON_LIBRARIES := boost_python3 python3.7m
    PYTHON_INCLUDE := /usr/include/python3.7m \
                     /usr/lib/python3.7/dist-packages/numpy/core/include
    ```

* For Anaconda, find:

    ```
    # Anaconda Python distribution is quite popular. Include path:
    # Verify anaconda location, sometimes it's in root.
    ```

  and uncomment the lines below it:

    ```
    ANACONDA_HOME := $(HOME)/anaconda
    PYTHON_INCLUDE := $(ANACONDA_HOME)/include \
             $(ANACONDA_HOME)/include/python2.7 \
             $(ANACONDA_HOME)/lib/python2.7/site-packages/numpy/core/include

    ```

  Replace `$(HOME)/anaconda` with your Anaconda installation path.

* Adjust the include and library variables:

```
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial
LIBRARY_DIRS := $(PYTHON_LIB) /usr/local/lib /usr/lib /usr/lib/arm-linux-gnueabihf/hdf5/serial/
```

For a manually built OpenCV, the example uses these INCLUDE_DIRS:

```
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial /usr/local/include/opencv4/
```

## Additional configuration

These workarounds reflect errors encountered when the original notes were written. Consult the linked issues to determine whether a fix still applies.

### OpenCV 4.x build error

See [the Caffe issue](https://github.com/BVLC/caffe/issues/6652). If the issue is unresolved in the chosen version, the original notes apply:

```
diff --git a/src/caffe/layers/window_data_layer.cpp b//src/caffe/layers/window_data_layer.cpp
index 1bf3760..f41169d 100644
--- a/src/caffe/layers/window_data_layer.cpp
+++ b/src/caffe/layers/window_data_layer.cpp
@@ -290,7 +290,7 @@ void WindowDataLayer<Dtype>::load_batch(Batch<Dtype>* batch) {
           image_database_cache_[window[WindowDataLayer<Dtype>::IMAGE_INDEX]];
         cv_img = DecodeDatumToCVMat(image_cached.second, true);
       } else {
-        cv_img = cv::imread(image.first, CV_LOAD_IMAGE_COLOR);
+        cv_img = cv::imread(image.first, cv::IMREAD_COLOR);
         if (!cv_img.data) {
           LOG(ERROR) << "Could not open or find file " << image.first;
           return;
diff --git a/src/caffe/test/test_io.cpp b//src/caffe/test/test_io.cpp
index c2c919e..b80df28 100644
--- a/src/caffe/test/test_io.cpp
+++ b/src/caffe/test/test_io.cpp
@@ -20,8 +20,8 @@ class IOTest : public ::testing::Test {};
 bool ReadImageToDatumReference(const string& filename, const int label,
     const int height, const int width, const bool is_color, Datum* datum) {
   cv::Mat cv_img;
-  int cv_read_flag = (is_color ? CV_LOAD_IMAGE_COLOR :
-    CV_LOAD_IMAGE_GRAYSCALE);
+  int cv_read_flag = (is_color ? cv::IMREAD_COLOR :
+    cv::IMREAD_GRAYSCALE);

   cv::Mat cv_img_origin = cv::imread(filename, cv_read_flag);
   if (!cv_img_origin.data) {
diff --git a//src/caffe/util/io.cpp b/caffe-1.0/src/caffe/util/io.cpp
index 835d2d4..941fd38 100644
--- a/src/caffe/util/io.cpp
+++ b/src/caffe/util/io.cpp
@@ -73,8 +73,8 @@ void WriteProtoToBinaryFile(const Message& proto, const char* filename) {
 cv::Mat ReadImageToCVMat(const string& filename,
     const int height, const int width, const bool is_color) {
   cv::Mat cv_img;
-  int cv_read_flag = (is_color ? CV_LOAD_IMAGE_COLOR :
-    CV_LOAD_IMAGE_GRAYSCALE);
+  int cv_read_flag = (is_color ? cv::IMREAD_COLOR :
+    cv::IMREAD_GRAYSCALE);
   cv::Mat cv_img_origin = cv::imread(filename, cv_read_flag);
   if (!cv_img_origin.data) {
     LOG(ERROR) << "Could not open or find file " << filename;
@@ -179,8 +179,8 @@ cv::Mat DecodeDatumToCVMat(const Datum& datum, bool is_color) {
   CHECK(datum.encoded()) << "Datum not encoded";
   const string& data = datum.data();
   std::vector<char> vec_data(data.c_str(), data.c_str() + data.size());
-  int cv_read_flag = (is_color ? CV_LOAD_IMAGE_COLOR :
-    CV_LOAD_IMAGE_GRAYSCALE);
+  int cv_read_flag = (is_color ? cv::IMREAD_COLOR :
+    cv::IMREAD_GRAYSCALE);
   cv_img = cv::imdecode(vec_data, cv_read_flag);
   if (!cv_img.data) {
     LOG(ERROR) << "Could not decode datum ";
```

### C++11 error

To address a compiler-language-mode issue, change the Makefile CXXFLAGS from:

```
CXXFLAGS += -pthread -fPIC $(COMMON_FLAGS) $(WARNINGS)
```

to:

```
CXXFLAGS +=  -std=c++11 -pthread -fPIC $(COMMON_FLAGS) $(WARNINGS)
```

See [the issue](https://github.com/BVLC/caffe/issues/6680).

### OpenCV imagecodecs error

For a manually built OpenCV 4.x, change:

```
LIBRARIES += opencv_core opencv_highgui opencv_imgproc
ifeq ($(OPENCV_VERSION), 3)
        LIBRARIES += opencv_imgcodecs
endif

```

to:

```
LIBRARIES += opencv_core opencv_highgui opencv_imgproc  opencv_imgcodecs
```

## Build

Build all sources:

```
make all
```

Run tests if needed:

```
make test

make runtest
```

Build the Python bindings:

```
make pycaffe

python3 scripts/download_model_binary.py models/bvlc_googlenet
```

## Install

Install the protobuf Python binding:

```
cd python

sudo python3 setup.py install
```
