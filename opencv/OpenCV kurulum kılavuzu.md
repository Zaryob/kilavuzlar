---
sort: 1
---

# OpenCV Kurulum Kılavuzu


İnşaa bağımlılıklarını kurmak 
-----------------------------


## İlk adım olarak sisteminizi güncellemeniz önerilir

```
sudo apt-get update && sudo apt-get upgrade
```

## Ardından geliştirme araçlarını ve CMake aracını kurunuz:
```
sudo apt-get install build-essential cmake unzip pkg-config
```

## Görüntü kodekleri

(Hepsini kurmanız önerilir)
* Fotoğraf için (JPEG, PNG ve tiff formatı): ```sudo apt-get install libjpeg-dev libpng-dev libtiff-dev/```
* Video kayıt için: (Kamera kullanımında önerilir) ``` sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev```
* Video dosyaları için: (Temel video formatları ve h264) ```sudo apt-get install libxvidcore-dev libx264-dev```

## GUI Araçları
Gui araçlarını kullanacaksanız (Opencv ile pencere içerisinde çıktı almak gibi) GTK kurmanız önerilir
```
sudo apt-get install libgtk-3-dev 
```

GTK hatalarını yakalamak için 
```
sudo apt-get install libcanberra-gtk*
```

## Sayısal optimizasyon araçları

OpenCV'nin sayısal optimizayon araçları daha pürüzsüz sonuçlar almanızı sağlar ancak totalde hız düşmesine sebep olur. 
Bunu eklemek için:
```
sudo apt-get install libatlas-base-dev gfortran
```

## Python bindingleri

Python3 için
```
sudo apt-get install python3-dev
```

Python2 için
```
sudo apt-get install python-dev
```

# OpenCV kaynak Kodunu indirme

En yeni OpenCV sürümünü [Github Sayfası](https://github.com/opencv/opencv/releases) üzerinden belirleyin

Ardından wget ile bunları indirin:
```
cd ~
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.x.y.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.x.y.zip
```

Mevcut dizine çıkartın ve yeniden adlandırın:
```
unzip opencv.zip
unzip opencv_contrib.zip

mv opencv-4.0.0 opencv
mv opencv_contrib-4.0.0 opencv_contrib
```

# İnşaa

## Ana sisteme inşaa etmek
Eğer ki virtualenv ile uğraşmak istemiyorsanız benim yönetemimi deneyin.

### Numpy'i kurun
Kök sisteme kurmak için
```
sudo pip3 install numpy
```
kullanıcı için kurmak siterseniz de 
```
pip3 install numpy --user
```

## Virtualenv üzerine inşaa etmek

Virtualenv sayesinde ana sisteminize zarar vermeden python3 tımbırtılarını işletebilirsiniz. 

### Virtualenv'yi kurun

```
sudo pip install virtualenv virtualenvwrapper
sudo rm -rf ~/get-pip.py ~/.cache/pip
```

### Kabuk ortamınıza virtualenv'yi ekleyin

~/.profile dosyanızın içerisine virtualenv'yi ekleyerek her kabuk ortamını başlattığınızda virtualenv'ye kolayca ulaşabilirsiniz

```
echo -e "# virtualenv and virtualenvwrapper \
export WORKON_HOME=$HOME/.virtualenvs  \
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3 \
source /usr/local/bin/virtualenvwrapper.sh" >> ~/.profile
```

ve kabuk ortamınızı yeniden başlatın:

```
source ~/.profile
```

### VirtualEnv'ye girin

Yeni bir sanal python ortamı oluşturun:
```
mkvirtualenv cv -p python3
```
ve onun içerisine girin
```
workon cv
```

Bundan sonra her opencv ile çalışacağınız zaman ```workon cv``` diyerek cv isimli sanal ortama ulaşabilirsiniz.

### Numpy'i kurun

```
pip3 install numpy
```

## OpenCV'yi inşaa etmek


### Konfigürasyon
OpenCV geneli C++ kodlarından oluşan bir CMake projesidir. Bu sebeple derlememz gerekmekte. Mevcut kod düzeni koruyarak derleme yapmak için `build` isminde bir dizinde çalışmak daha mantıklıdır. Bu sebeple başta opencv klasörüne girip onun içerisinde build isminde bir inşaa dizini açmamız lazım.

```
cd ~/opencv
mkdir build
cd build
```

Ardından CMake konfigürasyonunu yapın:

```
cmake -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib/modules \
    -D ENABLE_NEON=ON \
    -D ENABLE_VFPV3=ON \
    -D BUILD_TESTS=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D BUILD_EXAMPLES=OFF ..
```

### İnşaa

Make aracı ile inşaa etmeye başlayalım
```
make
```

Eğer ki çok çekirdekli bir işlemciye sahipseniz komutunuzu

```
make -j{çekirdek sayınızın bir eksiği}
```
şeklinde yeniden oluşturun. Örneğin 4 çekirdekli bir işlemci için

```
make -j3
```
şeklinde yazabilirsiniz.

### Kurulum

```
sudo make install
sudo ldconfig
```

Bu komut virtualenv içerisinde iken opencv'nin python bindingini env içerisine kurar. Ancak C++ kütüphanesi ve ikili paylaşım kitaplıkları ana sisteme kurulur.