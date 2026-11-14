---
title: Installing LEMP
permalink: /en/arsiv/linux/sunucular/lemp-kurulumu/
status: arsiv
reviewed: 2026-11-02
scope: APT, Nginx, MySQL and PHP-FPM; no distribution version specified.
archive_reason: Nginx/PHP-FPM integration and site configuration are missing. Opening
  a firewall port does not establish TLS. The MySQL section duplicates the LAMP guide.
lang: en
translation_key: guide-arsiv-linux-sunucular-lemp-kurulumu
translation_of: /arsiv/linux/sunucular/lemp-kurulumu/
translated: '2026-11-03'
---

# Installing LEMP

“LEMP” uses Nginx instead of Apache in the Linux web-server stack. Nginx, pronounced “engine-x”, handles web requests.

## LEMP on Debian-based systems

The historical installation procedure is outlined below.

### Install Nginx

Nginx is an Apache alternative known for its performance and configuration model.

```bash
sudo apt update
sudo apt install nginx
```

When using ufw, inspect Nginx’s firewall profiles for HTTP and HTTPS:

```bash
sudo ufw app list |grep Nginx
```

Example output:

```
  Nginx Full
  Nginx HTTP
  Nginx HTTPS
```

`Nginx Full` permits both HTTP and HTTPS ports; `Nginx HTTP` permits HTTP, and `Nginx HTTPS` permits HTTPS. The example selects `Nginx Full`. Opening the HTTPS port alone does not configure TLS; this omission is recorded in the archive warning.

```bash
sudo ufw allow in "Nginx Full"
```

### Install MySQL Server

Install MySQL to organise and access application databases:

```bash
sudo apt install mysql-server
```

Run the initial configuration utility for password-related settings:

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

Choose `Y` for yes at the password-validation prompt shown here:

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

Answer `n` at the next prompt shown in this example.

Inspect the MySQL users:

```bash
sudo mysql
```

In the SQL shell, enter:

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

PHP executes scripts, retrieves database content and generates responses. Unlike the Apache example, this stack uses `php-fpm`:

```bash
sudo apt install php php-fpm php-mysql

```

This completes the package-installation part of the original notes.

## Finishing

The components form a basis for a LEMP server. Nginx/PHP-FPM integration and site configuration are missing from these archived notes and still need to be completed.
