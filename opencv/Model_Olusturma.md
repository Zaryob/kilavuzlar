---
sort: 3
---

# Caffe ile Model Oluşturma

Bu belge caffemodel objelerinin nasıl oluşturulduğu konusunda detayli bilgiyi içermektedir.

Modeller opencv'de obje tanımlaması yapmak üzere kullanılanılan araçlardır. Opencv bu modelleri mevcut girdi ile karşılaştırarak karşımıza düzgün veriler çıkarmaktadır. Özellikle obje tanımlası veya yüz tanımlası gibi karmaşık işlemlerin hesaplanmasında bu veri setleri kullanılır.

Bu tip veri setlerinde en önemli olan şey elde ettiğimiz data setlerinin ne kadar temiz olduğu ve ne kadar çok ilişikli veri içerdiğidir.

Veri seti oluşturmak için aşağıdaki adımlar izlenir.

1. Veri ağı oluşturma (training) araçlarını kurmak 

Weiliu89'un caffe deposunun ssd branch'ini [Github linkini](https://github.com/weiliu89/caffe/tree/ssd)  kullanarak çekiniz. nşaa adımları depoda yer almakta.

2. Veri ağı içeriğini oluşturmak.
Veri ağı içeriğini aşağıdaki adımları izleyerek oluşturabilirsiniz:

(a)Orjinal yüz tanımlama veri seti içeriğini indirin -> (b) Fotoğraf alıntılarını uygun şekilde Pascal VOC formatına çevirin -> (c) LMDB veritabını oluşturun ve Pascal VOC formatındaki verileri kullanarak inşaa edin

a) Yüz içeriğine sahip veri setlerini bulun. Lisans sebebiyle herhangi bir fotoğraf paylaşamıyorum ancak Google üzerinde yer alan fotoğrafları kullanarak kendinize bir veri seti hazırlayın. Veri seti mümkün olduğunca farklı tiplerde veriler içermeli. Ayrıca net olmayan fotoğraflar, parazitler ve yanlış tasnif ettiğiniz veriler işlem sonucunda oluşacak veri setinizi bozabilir. Bu sebeple olduğunca temiz ve anlaşılır verileri kullanmaya özen gösterin. Ayrıca farklı parlaklık ve derinliğe sahip fotoğraflar da mutlaka kullanın. Blur'lu, aşırı odaklanmış ya da flu fotoğraflardan kaçının

b) Eğer ki hazır bir dataset kullanıyorsanız yüksek ihtimalle içerisinde bazı Pascal VOC formatında xml dosyaları yer alacaktır. Örneğin:

```
<annotation>
  <size>
    <width>300</width>
    <height>300</height>
  </size>
  <object>
    <name>face</name>
    <difficult>0</difficult>
    <bndbox>
      <xmin>100</xmin>
      <ymin>100</ymin>
      <xmax>200</xmax>
      <ymax>200</ymax>
    </bndbox>
  </object>
  <object>
    <name>face</name>
    <difficult>0</difficult>
    <bndbox>
      <xmin>0</xmin>
      <ymin>0</ymin>
      <xmax>100</xmax>
      <ymax>100</ymax>
    </bndbox>
  </object>
</annotation>
```

Veri setindeki obje isimlerini kullanarak bir labelmap.prototxt dosyası oluşturmanız gerekmekte. Bu dosyanın formatı şu şekildedir:
```
item {
  name: "none_of_the_above"
  label: 0
  display_name: "background"
}
item {
  name: "face"
  label: 1
  display_name: "face"
}
```
Burada her bir item yukarıdaki Pascal VOC içerisindeki object nesnesinin adlarından oluşmalıdır. Bütün object isimlerini içeren bir prototxt oluşturmak hayli önemlidir. O sebeple bütün obje isimlerini kaçırmadan tek tek yazın.


Bütün fotoğraf dosyaları ile Pascal VOC annotasyonları şu şekilde sıralanmalıdır:
images_val/0.jpg annotations_val/0.jpg.xml

c) LMDB oluşturmak için caffe/data/VOC0712 Caffe'nin kaynak kod dizininden create_data.sh aracını kullanmanız gerekir.
Bu komut dosyası, create_annoset.py dosyasını içinde çağırır, bu nedenle komut dosyasının argümanları olarak iletmeniz gerekenleri kontrol edin

2 farklı LMDB veritabanı hazırlamanız gerekir: biri eğitim görüntüleri, diğeri doğrulama görüntüleri için.

3. Dedektörünüzü eğitin

Eğitim için 3 dosyanızın olması gerekir: train.prototxt, test.prototxt ve solver.prototxt. Bu dosyaların örneklerini benioku dosyasıyla aynı dizinde bulabilirsiniz.
Ayrıca, LMDB veritabanlarınızın yollarını 2. adımda oluşturduğunuz gerçek veritabanlarıyla değiştirmek için train.prototxt ve test.prototxt'yi düzenlemeniz gerekir.

Şimdi her şey başlangıç eğitim süreci için yapıldı.
Terminal'de şu adımları tahip edin:
mkdir -p snapshot
mkdir -p log
/path_for_caffe_build_dir/tools/caffe train -solver="solver.prototxt" -gpu 0  2>&1 | tee -a log/log.log


Ve bekleyin. İşlemin tamamlanması yaklaşık olarak verilerin ne kadar büyüklükt olduğu ile alakalı olarak birkaç dakika ile birkaç saat hatta belki de birkaç gün sürecektir.

Bundan sonra, snapshot/alt dizinden çektiğiniz .caffemodel'inizi kullanabilirsiniz.
