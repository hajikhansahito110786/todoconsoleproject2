# Setting Up AI Chatbot Credentials

This guide explains how to configure your chatbot with different AI services.

## Available AI Services

You can choose from the following AI services:

1. **OpenAI (GPT-3.5/4)** - Most popular option
2. **Anthropic (Claude)** - Good alternative with strong reasoning
3. **Google (Gemini)** - Google's advanced AI model

## Option 1: OpenAI Setup (Recommended for beginners)

### Step 1: Get an OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up for an account or log in
3. Navigate to "API Keys" in your dashboard
4. Click "Create new secret key"
5. Copy the key (it will look something like `sk-proj-...`)

### Step 2: Configure Your Environment
1. Open your `.env` file
2. Set `AI_SERVICE=openai`
3. Replace `your_openai_api_key_here` with your actual API key

```
AI_SERVICE=openai
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Step 3: Install Required Package
```bash
pip install openai
```

## Option 2: Anthropic Claude Setup

### Step 1: Get an Anthropic API Key
1. Go to https://www.anthropic.com/
2. Sign up for API access
3. Navigate to your account dashboard
4. Find the API keys section and create a new key
5. Copy the key

### Step 2: Configure Your Environment
1. Open your `.env` file
2. Set `AI_SERVICE=anthropic`
3. Replace `your_anthropic_api_key_here` with your actual API key

```
AI_SERVICE=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

### Step 3: Install Required Package
```bash
pip install anthropic
```

## Option 3: Google Gemini Setup

### Step 1: Get a Google API Key
1. Go to https://ai.google.dev/
2. Sign up for access to Gemini API
3. Go to Google Cloud Console
4. Enable the Gemini API
5. Create credentials and copy your API key

### Step 2: Configure Your Environment
1. Open your `.env` file
2. Set `AI_SERVICE=google`
3. Replace `your_google_api_key_here` with your actual API key

```
AI_SERVICE=google
GOOGLE_API_KEY=your-google-api-key-here
```

### Step 3: Install Required Package
```bash
pip install google-generativeai
```

## Free Tier Options

### 1. OpenAI
- Offers $5 in free credits for new users
- GPT-3.5 is relatively inexpensive to use

### 2. Anthropic Claude
- Offers a limited free tier
- Check their website for current offerings

### 3. Google Gemini
- Offers free usage up to certain limits
- Check their website for current offerings

### 4. Alternative: Hugging Face (Completely Free)
If you want a completely free solution, you can use Hugging Face models:

1. Install the transformers library:
```bash
pip install transformers torch
```

2. Modify the chat endpoint to use a local model (this would require code changes)

## Testing Your Setup

1. Make sure your `.env` file is properly configured
2. Restart your application
3. Send a test message to the `/chat` endpoint
4. Check the console for any error messages

## Security Best Practices

1. **Never commit your API keys** to version control
2. Keep your `.env` file in `.gitignore`
3. Use different keys for development and production
4. Regularly rotate your API keys
5. Monitor your API usage to avoid unexpected charges

## Troubleshooting

### Common Issues:
- "Invalid API key" - Double-check your key is copied correctly
- "Rate limit exceeded" - You may need to upgrade your plan or reduce usage
- "Module not found" - Make sure you've installed the required packages

### Verifying Installation:
```bash
pip list | grep -i openai
pip list | grep -i anthropic
pip list | grep -i google
```

## Running the Application

After setting up your credentials:

1. Make sure all required packages are installed:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app_with_chatbot.py
```

3. The chat endpoint will be available at `http://localhost:8000/chat`

## Example Usage

Once your chatbot is set up, you can send requests like:

```json
{
  "message": "How do I create a new todo?",
  "user_id": 1
}
```

The bot will respond with helpful instructions based on your AI service selection.