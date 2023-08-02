# Claude - Streamlit Version
![CleanShot 2023-08-02 at 11.52.34@2x](https://p.ipic.vip/205jcl.png)

- Provide a simple Streamlit Version with ChatGPT and Claude API.

- You can build on top of it to accelerate your project progress.

- Deploy to Streamlit and share with your friends!

## Get Started

First, set up your local environment:

```bash
mkdir .streamlit
```

and create a file called `secrets.toml`, put your api-key inside:

```toml
OPENAI_API_KEY = "your-openai-api-key"
OPENAI_API_BASE = "https://api.openai.com/v1"
PROMPTLAYER_API_KEY = "your-promptlayer-api-key"
ANTHROPIC_API_KEY = "your-anthropic-api-key"
```

Note: I used [promptlayer](https://promptlayer.com) to log all my openai requests. You can disable it in `config.py` file.

To run this project in localhost, run bash command below:

```bash
streamlit run claude.py
```

## More Screenshots

![CleanShot 2023-08-02 at 12.17.32@2x](https://p.ipic.vip/a2bxfw.png)

![CleanShot 2023-08-02 at 12.20.20@2x](https://p.ipic.vip/3j47s1.png)

