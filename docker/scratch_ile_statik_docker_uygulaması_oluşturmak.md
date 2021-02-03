---
sort: 2
---

# Statik Docker Uygulaması Oluşturma

Docker konteyner'larının en büyük dezavantajı kendi libc kütüphanesini veya uygulamalara ait diğer bağımlılıkların konteyner içerisinde olması gerekmektedir. Bunu aşmak için statik uygulamalar oluşturmak en kolay yollardan birisi.


## Bir Örnek

Bir uygulama örneği oluşturalım. Mesela, bir merhaba dünya kodu oluşturalım ve bunu `hello.cc` dosyası içerisine yazdıralım.
{% highlight c%}
#include<iostream>

using namespace std;
int main(){
    cout << "Merhaba, dünya!\n ";
    return 0;
}
{% endhighlight %}

GCC kullanarak bu kodu derleyelim

{% highlight bash%}
$ g++ -o hello hello.cc
{% endhighlight %}

Bu şekilde derlemiş olduğumuz kodlar dinamik olarak linklenmiş olur. Ve bu uygulamanın bağımlılıklarını `ldd` ile listeleyelim.

{% highlight bash%}

$ ldd hello
        linux-vdso.so.1 =>  (0x00007ffc0075c000)
        libstdc++.so.6 => /usr/lib/x86_64-linux-gnu/libstdc++.so.6 (0x00007f88c92d0000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f88c8f06000)
        libm.so.6 => /lib/x86_64-linux-gnu/libm.so.6 (0x00007f88c8bfc000)
        /lib64/ld-linux-x86-64.so.2 (0x0000558132cbf000)
        libgcc_s.so.1 => /lib/x86_64-linux-gnu/libgcc_s.so.1 (0x00007f88c89e6000)
{% endhighlight %}

Eğer ki bu kodu ikili dosyayı `scratch` docker imajı içerisinde çalıştırmaya çalışırsak muhtemel olarak hata alacağız ve çalışmayacak. Eğer çalışmasını istersek yukarıdaki bağımlılıkları imaj içerisine eklememiz gerekecek ve bu sebeple imaj şişecek.

 Ancak biz bu uygulamayı statik olarak linklersek bu hataya maruz kalmadan ve imajı şişirmeden ve bağımlılıklarla boğuşmadan ikili çalıştırılabilir dosyalar elde ederiz. Bunun için mevcut komut `-static` parametresi eklemek yeterlidir.

{% highlight bash%}
$ g++ -o hello -static hello.cc
{% endhighlight %}

Şimdi de bağımlılıkları kontrol edelim.
{% highlight bash%}
ldd hello
        not a dynamic executable
{% endhighlight %}

Bu şekilde statik derlenmiş ikili dosyalar docker imajı içerisinde ek bir dosyaya veya bağımlılığa ihtiyaç duymadan çalışır. Şimdi de bir Dockerfile oluşturalım.
{% highlight bash%}
$ cat >> Dockerfile <<EOF
FROM scratch
ADD hello /
CMD ["/hello"]
EOF
{% endhighlight %}

Bu Dockerfile ile bir imaj inşaa edelim.

{% highlight bash%}
$ docker build --tag hello .
{% endhighlight %}

Şimdi de docker imajını çalıştıralım.

{% highlight bash%}
$ docker run hello
Merhaba, dünya!
{% endhighlight %}

Örnekte gördüğünüz gibi daha küçük docker imajları oluşturmak veya  gereksiz bağımlılıklardan kurtulmak için bu yöntemi kullanabilirsiniz.