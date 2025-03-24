
## Using cURL

You can send a request:

```bash
curl -X POST "http://0.0.0.0:8081/mask-pii" \
     -H "Content-Type: application/json" \
     -d '{
    "texts": [
        "John Doe'\''s email is john.doe@example.com, his other email is johns.other.mail@example.com. ",
        "Peter Miller owns a very funny hat."
    ],
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
    "original_texts": [
        "John Doe's email is john.doe@example.com, his other email is johns.other.mail@example.com. ",
        "Peter Miller owns a very funny hat."
    ],
    "masked_texts": [
        "[!FIRST-NAME!] [!LAST-NAME!]'s email is [!EMAIL!], his other email is [!EMAIL!]. ",
        "[!FIRST-NAME!] [!LAST-NAME!] owns a very funny hat."
    ],
    "detected_pii": [
        [
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
        ],
        [
            {
                "pii": "Peter",
                "type": "first_name"
            },
            {
                "pii": "Miller",
                "type": "last_name"
            }
        ]
    ]
}
```

## Using Python

```python
import requests

url = "http://0.0.0.0:8081/mask-pii"
payload = {
    "texts": [
        "John Doe's email is john.doe@example.com, his other email is johns.other.mail@example.com. ",
        "Peter Miller owns a very funny hat."
    ],
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

