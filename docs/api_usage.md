
## Using cURL

You can send a request:

```bash
curl -X POST "http://0.0.0.0:8081/mask-pii" \
     -H "Content-Type: application/json" \
     -d '{
        "text": "John Doe'\''s email is john.doe@example.com, his other email is johns.other.mail@example.com. ",
        "pii_config": {
            "first_name": {"mask": "[!FIRST-NAME!]"},
            "last_name": {"mask": "[!LAST-NAME!]"},
            "email": {"mask": "[!EMAIL!]"}
        }
    }'
```

Expected response:

```json
{
    "original_text": "John Doe's email is john.doe@example.com, his other email is johns.other.mail@example.com. ",
    "masked_text": "[!FIRST-NAME!] [!LAST-NAME!]'s email is [!EMAIL!], his other email is [!EMAIL!]. ",
    "detected_pii": [
        {
            "pii": "John",
            "type": "first_name"
        },
        {
            "pii": "Doe",
            "type": "last_name"
        },
        {
            "pii": "john.doe@example.com",
            "type": "email"
        },
        {
            "pii": "johns.other.mail@example.com",
            "type": "email"
        }
    ]
}
```

## Using Python

```python
import requests

url = "http://localhost:8000/mask-pii"
payload = {
    "text": "John Doe's email is john.doe@example.com, his other email is johns.other.mail@example.com. ",
    "pii_config": {
        "first_name": {"mask": "[!FIRST-NAME!]"},
        "last_name": {"mask": "[!LAST-NAME!]"},
        "email": {"mask": "[!EMAIL!]"}
    }
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.status_code} - {response.text}")
```

