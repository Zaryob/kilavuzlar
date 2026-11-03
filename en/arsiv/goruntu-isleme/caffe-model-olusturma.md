---
title: Creating a model with Caffe
permalink: /en/arsiv/goruntu-isleme/caffe-model-olusturma/
status: arsiv
reviewed: 2026-11-02
scope: The weiliu89/caffe SSD branch, Pascal VOC and LMDB.
archive_reason: The referenced train/test/solver examples are missing. Dataset licensing,
  training/validation separation and output evaluation need to be completed.
lang: en
translation_key: guide-arsiv-goruntu-isleme-caffe-model-olusturma
translation_of: /arsiv/goruntu-isleme/caffe-model-olusturma/
translated: '2026-11-03'
---

# Creating a model with Caffe

These notes describe creating caffemodel files for object detection with OpenCV. Such models can be used for complex tasks including object or face detection.

The cleanliness of the dataset and the variety of relevant examples are important to the resulting model.

## 1. Install training tools

Check out the ssd branch of [weiliu89’s Caffe repository](https://github.com/weiliu89/caffe/tree/ssd). Its repository contains build instructions.

## 2. Prepare the training data

The overall process is: obtain images, convert annotations into Pascal VOC format, then build LMDB databases.

### a. Collect images

Find a face-image dataset with appropriate licensing. The original note does not distribute photographs for licensing reasons. Use varied, clearly labelled images, including different lighting and depth. Blurry, noisy or incorrectly classified images can degrade the model; favour clean, relevant data.

### b. Prepare Pascal VOC annotations

An existing dataset may already include Pascal VOC XML files, for example:

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

Create labelmap.prototxt using the object names in the dataset:

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

Each item must match an object name in the Pascal VOC annotations. Include every object class.

Arrange images and annotations as follows:

```text
images_val/0.jpg annotations_val/0.jpg.xml
```

### c. Create LMDB databases

Use create_data.sh under caffe/data/VOC0712 in the Caffe source tree. It calls create_annoset.py internally; inspect the arguments required by that script.

Prepare two separate databases: one for training images and another for validation images.

## 3. Train the detector

Training requires train.prototxt, test.prototxt and solver.prototxt. The original notes refer to examples beside the README, but those files are not present in this repository; this is recorded in the archive warning.

Edit train.prototxt and test.prototxt to use the actual database paths created in step 2.

Start training in the terminal:

```bash
mkdir -p snapshot
mkdir -p log
/path_for_caffe_build_dir/tools/caffe train -solver="solver.prototxt" -gpu 0 2>&1 | tee -a log/log.log
```

Depending on dataset size, training can take minutes, hours or days. Afterwards, use the .caffemodel produced under snapshot/.
