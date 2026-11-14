---
translation_key: guide-arsiv-linux-sunucular-vnc-sunucusu
lang: tr
title: "VNC sunucusu"
permalink: /arsiv/linux/sunucular/vnc-sunucusu/
status: arsiv
reviewed: 2026-11-02
scope: "TightVNC ve Xfce; dağıtım sürümü belirtilmemiş."
archive_reason: "VNC güvenliği ve SSH tünelinin kullanımı hakkındaki açıklamalar düzeltilmeli; sunucunun dinleme adresi ve kimlik doğrulama ayarları doğrulanmalı."
redirect_from:
  - "/linux/vnc_server.html"
---

# VNC sunucusu


## VNC Nedir

VNC (virtual network computing), ağ üzerinden bilgisayarınızın ekranını yönetmenizi sağlayan bir sunucu yazılımıdır. Özellikle digitalocean veya azure gibi clientlerde işleri kolaylaştırmak için kurulu olan dropletteki sistemde Xorg server açmak için kullanılır. VNC'nin kendi haberleşme protokolü ve port yapısı bulunmaktadır. Bu, VNC'yi güvenli yapmaz: klasik VNC trafiği şifrelenmez ve parola doğrulaması zayıftır. VNC portunu internete açmayın; bağlantıyı yalnızca aşağıdaki SSH tüneli üzerinden kurun.

## VNC Kurulumu

Debian tabanlı sistemler için kurulumu:

Başta depolarımızı güncelleyelim:
```bash
sudo apt update
```

Tightvnc server paketini kuralım.
```bash
sudo apt install tightvncserver
```

Eğer bir masaüstü ortamına sahip değilseniz işleri kolaylaştırmak için xfce kurmanızı öneririm

```bash
sudo apt install xfce4 xfce4-goodies
```

## VNC Sunucusunu Yapılandırma

VNC sunucusunun kurulumun ardından çalıştırılarak ilk ayarlamalarını yapıyoruz

```bash
vncserver
```

Bu aşamada sizden uzaktan sunucuya bağlanmak için şifre belirlemenizi isteyecek. Şifre girerken girdiğiniz karakterler gösterilmeyecek. O sebeple şifre yazın mesajının ardından neye tıklarsanız tıklayın hareketlenme olmayacaktır

```
You will require a password to access your desktops.

Password:
Verify:
```

Hemen aynı adım içerisinde sizden ikinci bir şifre isteyip istemediğinizi soran bir mesaj gelecek. Bu, yalnızca izleme (view-only) parolasıdır. Zaruri değil hatta uzak sunucu için ise koymamanızı tavsiye ederim. O yüzden ben atlayacağım

```
auth:  file /home/zaryob/.Xauthority does not exist

New 'X' desktop is your_hostname:1

Creating default startup script /home/zaryob/.vnc/xstartup
Starting applications specified in /home/zaryob/.vnc/xstartup
Log file is /home/zaryob/.vnc/your_hostname:1.log
```
Böylece ilk yapılandırmayı yaptık ancak hala işimiz bitmedi. Farkettiğiniz gibi üstte .Xauthority dosyasının bulunmadığını yani XServer bağlantısı sağlanamadığını bize belirtiyor. Öncelikle vncserver'i kapatacağız ardından da bunun yapılandırmasını yapacağız.

## VNC Sunucusu için Masaüstü Ortamı yapılandırması

Başlangıç olarak vncserveri sonlandıralım.

```bash
vncserver -kill :1
```


```
Killing Xtightvnc process ID 17731
```

Değişiklikler öncesi vnc-xauth dosyasını yedekleyelim
```bash
mv ~/.vnc/xstartup ~/.vnc/xstartup.bak
```

Ardından da Xserver ayarlamasını yapalım.

```bash
cat > ~/.vnc/xstartup <<EOF
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF
```

Burada ben startxfce4 yazarak önceki adımda kurduğum masaüstünü tetikleyen komuttur. Diğer masaüstü ortamları için ise araştırıp bulabilirsiniz.

Üstte yazdığımız betiği çalıştırılabilir hale getirelim

```bash
sudo chmod +x ~/.vnc/xstartup
```

ve yeniden çalıştıralım

```bash
vncserver
```

yeniden çalıştırınca çıktımız da şu olacaktır.

```
New 'X' desktop is your_hostname:1

Starting applications specified in /home/zaryob/.vnc/xstartup
Log file is /home/zaryob/.vnc/your_hostname:1.log
```


## VNC Sunucuna Bağlantı Sağlamak

İki yöntem kullanabilirsiniz. Bunlar ssh komutu ile bağlantı sağlamak ve tigthvnc-viewer veya realvnc-viewer gibi bir vnc client'i ile bağlanmaktır

### SSH Kullanmak
GNU/Linux Dağıtımları için ssh komutu vnc sunucusuna bağlanmak için kullanılabilir.

```bash
ssh -L 5901:127.0.0.1:5901 -C -N -l zaryob sunucu_ip_adresi
```

`zaryob` buradaki benim kullanıcı adım siz de bunu kendi sunucunuzdaki kullanıcı adınız ile değiştirebilirsiniz. Bu komut pencere açmaz; yalnızca kendi bilgisayarınızdaki 5901 portunu sunucudaki VNC portuna taşıyan şifreli bir tünel kurar. Tünel açıkken VNC istemcinizi `localhost:5901` adresine bağlayın.


### VNCViewer

Sunucunun açık IP adresine doğrudan bağlanmak yerine yukarıdaki tüneli açıp istemciyi `localhost:5901` adresine yönlendirin. İndirip kurduğunuz realvnc-viewer ya da tightvnc-viewer ile bağlantı yaparken ip adresinizin haricinde port bilginizi de :5901 olarak ayarlamanızı öneririm. Çünkü eğer başka bir ayarlama yapmadıysanız `Xvnc` tanımlamak gibi, varsayılan sunucu portu bu olacaktıır.
