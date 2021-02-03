---
sort: 2
---


# Caffe Kurulum Kılavuzu


Bağımlılıkları kurun: 
---------------------

```
sudo apt-get update && sudo apt-get upgrade

sudo apt-get install -y gfortran cython

sudo apt-get install -y libprotobuf-dev libleveldb-dev libsnappy-dev libhdf5-serial-dev protobuf-compiler git

sudo apt-get install --no-install-recommends -y libboost-all-dev

sudo apt-get install -y python-dev libgflags-dev libgoogle-glog-dev liblmdb-dev libatlas-base-dev python-skimage

sudo pip3 install pyzmq jsonschema pillow numpy scipy ipython jupyter pyyaml
```
# OpenCV'yi kurun:

Eğer depodaki sürümü kullanmak isterseniz
```
sudo apt install libopencv-dev
```
komutu ile kurulum yapabilirsiniz. Elle derleme yapıp en son sürüme sahip olmak için diğer sayfalarda yer alan Opencv kurulum kılavuzuna bakınız.

# Caffe'yi klonlayın:

```
git clone https://github.com/BVLC/caffe
```

# Caffeyi yapılandırın:

Caffe dizinine girip temel configurasyon dosyasını kullanarak ön hazırlık yapın:
```
cd caffe

cp Makefile.config.example Makefile.config

nano Makefile.config
```

## Gerekli olan Makefile.config dosyasını oluşturun

* (Raspberry pi için) `#CPU_ONLY := 1` yazan satırı `CPU_ONLY := 1` ile değiştirin.

* (Python2 için) `/usr/lib/python2.7/dist-packages/numpy/core/include` yazan satırı eğer pip ile gelen bir sürümü kullanıyorsanız `/usr/local/lib/python2.7/dist-packages/numpy/core/include` ile değiştirin. 

* (Python2 harici bir sürüm kullanmak için) Eğer python2 kullanmayacaksanız:

    ```
     PYTHON_INCLUDE := /usr/include/python2.7 \
    		/usr/lib/python2.7/dist-packages/numpy/core/include
    ```
    yazan kısmı
    ```
    # PYTHON_INCLUDE := /usr/include/python2.7 \
    #		/usr/lib/python2.7/dist-packages/numpy/core/include
    ```
    şeklinde satır başlarına `#` yazarak python2 desteğini kapatınız.
    
    * Python3 için:
    
    Aşağı satırlarda yer alan `Uncomment to use Python 3 (default is Python 2)` yazan satırın altındaki satırların başında yer alan `#` ibaresini kaldırın. Sonuç şöyle görünmelidir.
    
    ```
    PYTHON_LIBRARIES := boost_python3 python3.7m
    PYTHON_INCLUDE := /usr/include/python3.7m \
                     /usr/lib/python3.7/dist-packages/numpy/core/include
    ```
    
    * Anaconda için:
    Aşağı satırlarda yer alan 
    ```
    # Anaconda Python distribution is quite popular. Include path:
    # Verify anaconda location, sometimes it's in root.
    ```
    
    yazan satırın altındaki satırların başında yer alan `#` ibaresini kaldırın. Sonuç şöyle görünmelidir.
    
    ```
    ANACONDA_HOME := $(HOME)/anaconda  
    PYTHON_INCLUDE := $(ANACONDA_HOME)/include \
             $(ANACONDA_HOME)/include/python2.7 \
             $(ANACONDA_HOME)/lib/python2.7/site-packages/numpy/core/include

    ```
    
    Not: `$(HOME)/anaconda` ibaresini sizin anaconda kurulumunuz ile değiştirmneyi unutmayınız.
    
* Include ve library değişkenlerini değiştiriniz:
```
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial 
LIBRARY_DIRS := $(PYTHON_LIB) /usr/local/lib /usr/lib /usr/lib/arm-linux-gnueabihf/hdf5/serial/
```

Eğer opencv'yi kendi derlemenizden kullanacaksanız INCLUDE_DIRS ibaresi şöyle olmalıdır.

```
INCLUDE_DIRS := $(PYTHON_INCLUDE) /usr/local/include /usr/include/hdf5/serial /usr/local/include/opencv4/
```

## Gelişmiş Bazı Yapılandırmalar
Buradaki yapılandırmalar anlık olarak eklenmiştir. An itibari ile bu hatalar var mı diye kontrol etmek amacı ile hata kaydı olarak belirtilen  Github Issuelerini kontrol etmeyi unutmayınız.

### OpenCV 4.x hatası
An itibari ile OpenCV 4.x ile caffe derlenmemekte [hata kaydı](https://github.com/BVLC/caffe/issues/6652)
Eğer hata kaydı düzeltilmedi ise aşağıdaki yamayı uygulayın.

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

### CXX 11 hatası:
Bazı durumlarda c++ 11 öncesi destekleyen derleyicilerde sorun çıkmakta. Buna karşı derlemeye başlamadan önce Makefile dosyası içerisinde

```
CXXFLAGS += -pthread -fPIC $(COMMON_FLAGS) $(WARNINGS)
```
olan CXXFLAGS
```
CXXFLAGS +=  -std=c++11 -pthread -fPIC $(COMMON_FLAGS) $(WARNINGS)
```
olmalıdır [hata kaydı](https://github.com/BVLC/caffe/issues/6680)


### OpenCV imagecodecs hatası
OpenCV 4.x'i elle derledi iseniz

```
LIBRARIES += opencv_core opencv_highgui opencv_imgproc 
ifeq ($(OPENCV_VERSION), 3)
        LIBRARIES += opencv_imgcodecs
endif

```

olan kısmı 


```
LIBRARIES += opencv_core opencv_highgui opencv_imgproc  opencv_imgcodecs
```
yapmanızı öneririm.

## İnşaa adımları

Tüm kaynağı inşaa edin:

```
make all
```

Eğer gerkli görürseniz testleri işletin:
```
make test

make runtest
```

Python bindinglerini inşaa edin:
```
make pycaffe

python3 scripts/download_model_binary.py models/bvlc_googlenet
```

## Kurulum 


Protobuf python bindingini kurmak için: 
```
cd python

sudo python3 setup.py install
```
komutlarını işletin.

