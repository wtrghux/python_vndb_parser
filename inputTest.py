import requests

LINK = "https://vndb.org/"
t = str(input("search: "))
response = requests.get(LINK + f"v?q={t}")

with open("test.html", "w", encoding="utf-8") as f:
    f.write(response.text)
