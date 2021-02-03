---
sort: 1
---

# VNC Server


## VNC Nedir

VNC (virtual network computing), ağ üzerinden bilgisayarınızın ekranını yönetmenizi sağlayan bir sunucu yazılımıdır. Özellikle digitalocean veya azure gibi clientlerde işleri kolaylaştırmak için kurulu olan dropletteki sistemde Xorg server açmak için kullanılır. VNC'nin kendi haberleşme protokolü ve port yapısı bulunmaktadır. Bu sayede tamamen güvenli ve sızmakara karşı dayanıklıdır.

## VNC Kurulumu

Debian tabanlı sistemler için kurulumu: 

Başta depolarımızı güncelleyelim:
{% highlight bash %}
$ sudo apt update
{% endhighlight %}

Tightvnc server paketini kuralım.
{% highlight bash %}
$ sudo apt install tightvncserver
{% endhighlight %}

Eğer bir masaüstü ortamına sahip değilseniz işleri kolaylaştırmak için xfce kurmanızı öneririm

{% highlight bash %}
$ sudo apt install xfce4 xfce4-goodies
{% endhighlight %}

## VNC Sunucusunu Yapılandırma

VNC sunucusunun kurulumun ardından çalıştırılarak ilk ayarlamalarını yapıyoruz

{% highlight bash %}
$ vncserver
{% endhighlight %}

Bu aşamada sizden uzaktan sunucuya bağlanmak için şifre belirlemenizi isteyecek. Şifre girerken girdiğiniz karakterler gösterilmeyecek. O sebeple şifre yazın mesajının ardından neye tıklarsanız tıklayın hareketlenme olmayacaktır

{% highlight bash %}
You will require a password to access your desktops.

Password:
Verify:
{% endhighlight %}

Hemen aynı adım içerisinde sizden ikinci bir şifre isteyip istemediğinizi soran bir mesaj gelecek. Bu ise yönetim koruması şifresi. Zaruri değil hatta uzak sunucu için ise koymamanızı tavsiye ederim. O yüzden ben atlayacağım 

{% highlight bash %}
auth:  file /home/zaryob/.Xauthority does not exist

New 'X' desktop is your_hostname:1

Creating default startup script /home/zaryob/.vnc/xstartup
Starting applications specified in /home/zaryob/.vnc/xstartup
Log file is /home/zaryob/.vnc/your_hostname:1.log
{% endhighlight %}

Böylece ilk yapılandırmayı yaptık ancak hala işimiz bitmedi. Farkettiğiniz gibi üstte .Xauthority dosyasının bulunmadığını yani XServer bağlantısı sağlanamadığını bize belirtiyor. Öncelikle vncserver'i kapatacağız ardından da bunun yapılandırmasını yapacağız.

## VNC Sunucusu için Masaüstü Ortamı yapılandırması

Başlangıç olarak vncserveri sonlandıralım.

{% highlight bash %}
$ vncserver -kill :1
{% endhighlight %}

{% highlight bash %}
Killing Xtightvnc process ID 17731
{% endhighlight %}

Değişiklikler öncesi vnc-xauth dosyasını yedekleyelim
{% highlight bash %}
$ mv ~/.vnc/xstartup ~/.vnc/xstartup.bak
{% endhighlight %}

Ardından da Xserver ayarlamasını yapalım.

{% highlight bash %}
$ cat >>~/.vnc/xstartup <<EOF
#!/bin/bash
xrdb $HOME/.Xresources
startxfce4 &
EOF
{% endhighlight %}

Burada ben startxfce4 yazarak önceki adımda kurduğum masaüstünü tetikleyen komuttur. Diğer masaüstü ortamları için ise araştırıp bulabilirsiniz.

Üstte yazdığımız betiği çalıştırılabilir hale getirelim 

{% highlight bash %}
$ sudo chmod +x ~/.vnc/xstartup
{% endhighlight %}

ve yeniden çalıştıralım

{% highlight bash %}
$ vncserver
{% endhighlight %}

yeniden çalıştırınca çıktımız da şu olacaktır.

{% highlight bash %}
New 'X' desktop is your_hostname:1

Starting applications specified in /home/zaryob/.vnc/xstartup
Log file is /home/zaryob/.vnc/your_hostname:1.log
{% endhighlight %}


## VNC Sunucuna Bağlantı Sağlamak

İki yöntem kullanabilirsiniz. Bunlar ssh komutu ile bağlantı sağlamak ve tigthvnc-viewer veya realvnc-viewer gibi bir vnc client'i ile bağlanmaktır

### SSH Kullanmak
GNU/Linux Dağıtımları için ssh komutu vnc sunucusuna bağlanmak için kullanılabilir.

{% highlight bash %}
ssh -L 5901:127.0.0.1:5901 -C -N -l zaryob sunucu_ip_adresi
{% endhighlight %}

`zaryob` buradaki benim kullanıcı adım siz de bunu kendi sunucunuzdaki kullanıcı adınız ile değiştirebilirsiniz. Bu ssh komutu bir pencere açarak sizi vnc sunucuna bağlayacaktır.
Bu ssh komutu tünelleme yaparak vnc sunucusuna bağlanacaktır.


### VNCViewer

İndirip kurduğunuz realvnc-viewer ya da tightvnc-viewer ile bağlantı yaparken ip adresinizin haricinde port bilginizi de :5901 olarak ayarlamanızı öneririm. Çünkü eğer başka bir ayarlama yapmadıysanız `Xvnc` tanımlamak gibi, varsayılan sunucu portu bu olacaktıır.
