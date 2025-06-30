import requests

data = {"name": "Cyberpunk 2077", "price": 49.99}
response = requests.post("http://localhost:8000/api/games", json=data)

print(response.status_code)
print(response.json())
