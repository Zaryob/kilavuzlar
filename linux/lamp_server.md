---
sort: 2
---

# LAMP sunucusu Kurulumu

"LAMP" dörtlüsü, bir sunucunun dinamik web sitelerini ve web uygulamalarını barındırmasını sağlamak için tipik olarak birlikte kurulan bir grup açık kaynaklı yazılımdır. Bu terim aslında Linux'u,  üzerine kurulan Apache web sunucusuyla site üretmeye hazır hale getirmeyi sağlar. Site verileri bir MySQL veritabanında saklanır ve dinamik içerik PHP tarafından işlenir.

## Debian Sistemlerinde LAMP Kurulumu

Aşağıdaki adımları izleyerek LAMP kurabilirsiniz.

### Apache Kurulumu

Apache web sunucusu, dünyanın en popüler web sunucuları arasındadır. Kendine özgü açık kaynak lisansı ve sağlam belgelendirmesi sayesinde kısa sürede popüler olmuştur ve 1990'lardan beri en popüler kullanılan web sunucusudur.

```bash
sudo apt update
sudo apt install apache2
```

Eğer ki ufw güvenlik duvarını kullanıyorsanız, Apache için HTTP ve HTTPS port çıkışlarına izin vermemiz lazım.

```bash
sudo ufw allow in "Apache Full"
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

PHP, dinamik içeriği görüntülemek için kodu işleyen birimdir. Kendisi aslında bir programlama dilidir. Komut dosyalarını çalıştırabilir, bilgi almak için MySQL veritabanlarınıza bağlanabilir ve işlenen içeriği görüntülemek için web sunucunuza aktarabilir. Apache PHP'ile çalışabilmek için ek modüle ihtiyaç duyar. Başta onları yükleyelim

```bash
sudo apt install php libapache2-mod-php php-mysql
```

Şimdi de aktif apache klasörülerinin listesini listeleyelim.

```bash
sudo nano /etc/apache2/mods-enabled/dir.conf
```

Bu dosya içeriği şu şekilde görünecektir.

```
<IfModule mod_dir.c>
    DirectoryIndex index.html index.cgi index.pl index.php index.xhtml index.htm
</IfModule>
```

bu içeriği index.php'yi öne alarak değiştirelim

```
<IfModule mod_dir.c>
    DirectoryIndex index.php index.html index.cgi index.pl index.xhtml index.htm
</IfModule>
```

Bütün bu değişimin aktive edilmesi için apache sunucusunu yeniden başlatalım.
```
sudo systemctl restart apache2
```

Eğer ki sunucunuzu debug etmek istiyorsanız `php-cli` paketini yüklenemniz önerilir.

```
sudo apt install php-cli
```

## Bitiriş
Artık bir LAMP sunucusuna sahip olduğunuza göre, daha sonra ne yapacağınız konusunda birçok seçeneğiniz var. Temel olarak, sunucunuza çoğu türde web sitesi ve web yazılımı yüklemeniz artık mümkün, güle güle kullanın.