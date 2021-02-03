---
sort: 3
---

# LEMP sunucusu Kurulumu

"LEMP" dörtlüsü, LAMP dörtlüsünden farklı olarak Apache yerine Nginx kullanarak oluşturulan bir sunucu dörtlüsüdür. Linux'ta site oluştururken sitenizi Apache üzerinden değil, kurulan Nginx (Engine-X) web sunucusuyla site üretmeye hazır hale getirmeyi sağlar. 

## Debian Sistemlerinde LEMP Kurulumu

Aşağıdaki adımları izleyerek LEMP kurabilirsiniz.

### Nginx Kurulumu

Nginx web sunucusu, son dönemlerde popülerleşen, Apache alternatifi bir yazılımdır. Performans ve yapılandırma kolaylığı ile öne çıkmıştır

```bash
sudo apt update
sudo apt install nginx
```

Eğer ki ufw güvenlik duvarını kullanıyorsanız, Nginx için HTTP ve HTTPS port çıkışlarına izin vermemiz lazım. Ancak burada bir güzellik var. Nginx'in iki farklı yayın katmanı için ayrı ayrı ayar yapabiliyoruz. Bu katmanlarını ufw aracılığı ile görmek için

```bash
sudo ufw app list |grep Nginx
```
Bunun çıktısı şu şekilde olacaktır.

```
  Nginx Full
  Nginx HTTP
  Nginx HTTPS
```

`Nginx Full` Nginx'in her iki yayın kanalını, `Nginx HTTP` http (basit hypertext protokolü) kanalını, `Nginx HTTPS` https (SSL ile korunan hypertext protokolünü) temsil eder. Bunlardan birisini seçerek çalışmasına izin verelim. Ben Nginx Full'ü seçeceğim. Eğer ki http modunu seçerseniz sitenize `http://site_adresi` adresinden erişim sağlarken `https://site_adresi` adresi ile erişim sağlanamıyor.


```bash
sudo ufw allow in "Nginx Full"
```

### MySQL Server Kurulumu

Artık web sunucunuz hazır ve çalışır durumda olduğuna göre, MySQL'i kurmanın zamanı geldi. MySQL, bir veritabanı yönetim sistemidir. Temel olarak, sitenizin bilgileri depolayabileceği veritabanlarını düzenleyecek ve bunlara erişim sağlayacaktır. 

```bash
sudo apt install mysql-server
```

Ardından MySQL için ilk kurulumumuzu yapalım. Bu aşamada program bizden database için yapacağımız kurulumda şifre oluşturmamızı isteyecektir.

```bash
sudo mysql_secure_installation
```

```
VALIDATE PASSWORD PLUGIN can be used to test passwords
and improve security. It checks the strength of password
and allows the users to set only those passwords which are
secure enough. Would you like to setup VALIDATE PASSWORD plugin?

Press y|Y for Yes, any other key for No
```

Eğer yeni bir şifre oluşturacaksanız buna `evet` manasında `Y`ye tıklayın.

```
There are three levels of password validation policy:

LOW    Length >= 8
MEDIUM Length >= 8, numeric, mixed case, and special characters
STRONG Length >= 8, numeric, mixed case, special characters and dictionary file

Please enter 0 = LOW, 1 = MEDIUM and 2 = STRONG: 
```

Bu aşamada orta uzunlukta bir şifre oluşturalım, bu yüzden 1'e tıklayalım

```
Using existing password for root.

Estimated strength of the password: 100
Change the password for root ? ((Press y|Y for Yes, any other key for No) : 
```
buna da `n` diyelim. Böylece kurulum tamamlanmış oldu. 

Şimdi MySQL kullanıcılarını listeleyelim

```bash
sudo mysql
```
Bu bizim için bir SQL kabuk ortamı oluşturacaktır. Şimdi şunları yazalım.
```sql
mysql> SELECT user,authentication_string,plugin,host FROM mysql.user;
```

Çıktısı şu şekilde görünecektir
```
+------------------+-------------------------------------------+-----------------------+-----------+
| user             | authentication_string                     | plugin                | host      |
+------------------+-------------------------------------------+-----------------------+-----------+
| root             |                                           | auth_socket           | localhost |
| mysql.session    | *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE | mysql_native_password | localhost |
| mysql.sys        | *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE | mysql_native_password | localhost |
| debian-sys-maint | *FA769377A401A7D25BE1CA89AFF17BF607F876FF | mysql_native_password | localhost |
+------------------+-------------------------------------------+-----------------------+-----------+
4 rows in set (0.00 sec)
```

Burada göründüğü üzere `auth_socket` şifresi verelim. Burada 'password' bizim belirleyeceğimiz şifre olacak. Öntanımlı olarak ben `password` olarak belirledim.

```sql
mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'password';
```
Bu değişikliğin okunması için tablomuzu güncelleyelim

```sql
mysql> FLUSH PRIVILEGES;
```
Ve yeniden Tablomuzu kontrol edelim
```sql
mysql> SELECT user,authentication_string,plugin,host FROM mysql.user;
```

```
+------------------+-------------------------------------------+-----------------------+-----------+
| user             | authentication_string                     | plugin                | host      |
+------------------+-------------------------------------------+-----------------------+-----------+
| root             | *3636DACC8616D997782ADD0839F92C1571D6D78F | auth_socket           | localhost |
| mysql.session    | *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE | mysql_native_password | localhost |
| mysql.sys        | *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE | mysql_native_password | localhost |
| debian-sys-maint | *FA769377A401A7D25BE1CA89AFF17BF607F876FF | mysql_native_password | localhost |
+------------------+-------------------------------------------+-----------------------+-----------+
4 rows in set (0.00 sec)
```

### PHP Kurulumu

PHP, dinamik içeriği görüntülemek için kodu işleyen birimdir. Kendisi aslında bir programlama dilidir. Komut dosyalarını çalıştırabilir, bilgi almak için MySQL veritabanlarınıza bağlanabilir ve işlenen içeriği görüntülemek için web sunucunuza aktarabilir. LAMP'dan farklı olarak burada `php-fpm` paketi kurulması lazım.

```bash
sudo apt install php php-fpm php-mysql

```

Böylece kurulum işlemi tamamlandı.

## Bitiriş
Artık bir LEMP sunucusuna sahip olduğunuza göre, daha sonra ne yapacağınız konusunda birçok seçeneğiniz var. Temel olarak, sunucunuza çoğu türde web sitesi ve web yazılımı yüklemeniz artık mümkün, güle güle kullanın.