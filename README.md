# text-pii-masking

This project uses a large language model to detect and mask personal identifiable information (pii) in a string. The API provides two main functions:

- Extraction: Identifies PII substrings and their types from the provided text as per configuration.
- Masking: Replaces detected PII substrings with configurable mask tokens.


## Setup

Create a `.env` file in the project root directory:

```bash
OPENAI_API_KEY=**** # your API key
OPENAI_MODEL=gpt-4o-mini # any model available
BASE_URL=https://api.openai.com/v1
```

## Getting started

You can try out a demo with:

```bash
python demo.py
```

Start the server with:

```bash
python app.py
```

For usage examples, look [here](docs/api_usage.md).