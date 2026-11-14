---
title: Installing LAMP
permalink: /en/arsiv/linux/sunucular/lamp-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: APT, Apache, MySQL and PHP; no distribution version specified.
archive_reason: Review the sample password and root authentication change. Post-install
  HTTP/PHP/database verification is missing.
lang: en
translation_key: guide-arsiv-linux-sunucular-lamp-kurulumu
translation_of: /arsiv/linux/sunucular/lamp-kurulumu/
translated: '2026-11-03'
---

# Installing LAMP

“LAMP” is a group of open source components commonly installed together to serve dynamic websites and web applications. Linux runs the Apache web server, site data is stored in MySQL, and PHP processes dynamic content.

## LAMP on Debian-based systems

The historical procedure follows these steps.

### Install Apache

Apache is a widely used open source web server with extensive documentation and a long history dating to the 1990s.

```bash
sudo apt update
sudo apt install apache2
```

If using ufw, allow the relevant HTTP and HTTPS ports:

```bash
sudo ufw allow in "Apache Full"
```

### Install MySQL Server

With the web server installed, install MySQL to organise and provide access to the site’s databases:

```bash
sudo apt install mysql-server
```

Run its initial configuration utility, which prompts for password-related settings:

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

Choose `Y` for yes if enabling the password-validation option shown in the prompt.

```
There are three levels of password validation policy:

LOW    Length >= 8
MEDIUM Length >= 8, numeric, mixed case, and special characters
STRONG Length >= 8, numeric, mixed case, special characters and dictionary file

Please enter 0 = LOW, 1 = MEDIUM and 2 = STRONG:
```

The example chooses option 1 for the medium policy:

```
Using existing password for root.

Estimated strength of the password: 100
Change the password for root ? ((Press y|Y for Yes, any other key for No) :
```

Answer `n` at the prompt shown in this example.

Inspect the MySQL users:

```bash
sudo mysql
```

This opens an SQL shell. Enter:

```sql
mysql> SELECT user,authentication_string,plugin,host FROM mysql.user;
```

Example output:

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

The output shows `auth_socket`. The original example switches authentication to a password. Replace `GUCLU_BIR_PAROLA` (“a strong password”) with a strong, unique password of your own; never use a guessable value such as `password`. Note that `mysql_native_password` is disabled by default in MySQL 8.4 and removed in 9.0, so this command fails on current releases.

```sql
mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'GUCLU_BIR_PAROLA';
```

Apply the privilege-table change:

```sql
mysql> FLUSH PRIVILEGES;
```

Check the table again:

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

### Install PHP

PHP executes scripts, accesses MySQL data and generates dynamic content for the web server. Apache requires additional PHP integration packages:

```bash
sudo apt install php libapache2-mod-php php-mysql
```

Inspect the active Apache directory-index configuration:

```bash
sudo nano /etc/apache2/mods-enabled/dir.conf
```

The file looks like:

```
<IfModule mod_dir.c>
    DirectoryIndex index.html index.cgi index.pl index.php index.xhtml index.htm
</IfModule>
```

Move index.php to the front of the list:

```
<IfModule mod_dir.c>
    DirectoryIndex index.php index.html index.cgi index.pl index.xhtml index.htm
</IfModule>
```

Restart Apache to activate the changes:

```
sudo systemctl restart apache2
```

The `php-cli` package is useful for running PHP from the command line:

```
sudo apt install php-cli
```

## Finishing

The LAMP components are now installed in the example. They provide a basis for hosting websites and web applications; the incomplete verification and authentication details remain listed in the archive warning.
