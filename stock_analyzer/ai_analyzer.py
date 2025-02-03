import os
import openai
import pandas as pd
import re
from bs4 import BeautifulSoup


openai.api_key = os.getenv("OPENAI_API_KEY")


def strip_markdown(text: str) -> str:
    """
    Removes Markdown formatting from the text.
    :param text: The text containing Markdown.
    :return: Cleaned plain text.
    """
    text = re.sub(r'```.*?```', '', text, flags = re.DOTALL)  # Remove code blocks
    text = re.sub(r'`.*?`', '', text)  # Remove inline code
    text = re.sub(r'#{1,6}\s*', '', text)  # Remove headers (e.g., # Header, ## Header)
    text = re.sub(r'^-\s*\*\*', '', text, flags = re.MULTILINE)  # Remove list bullets with bold (e.g., - **Text**)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # Bold    # Remove bold and italics (e.g., **Text**, __Text__, *Text*, _Text_)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)  # Italic
    text = re.sub(r'^[-*]\s+', '', text, flags = re.MULTILINE)  # Remove remaining list bullets (e.g., - Text, * Text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links but keep the display text (e.g., [Text](url))
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)  # Remove images (e.g., ![Alt Text](url))
    text = re.sub(r'[>*_~]', '', text)  # Remove any remaining Markdown characters like >, *, _, ~
    soup = BeautifulSoup(text, "html.parser")  # Optionally, use BeautifulSoup to clean up any residual HTML tags
    return soup.get_text(separator = "\n").strip()


def clean_html(html_content: str) -> str:
    """
    Extracts and cleans text from HTML content.
    :param html_content: The raw HTML string.
    :return: Cleaned text extracted from HTML.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    # Get text
    text = soup.get_text(separator = "\n")

    # Break into lines and remove leading/trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # Drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    return text


def analyze_stock_with_news(ratios_table: pd.DataFrame, articles_html_all: str) -> str:
    """
    Sends the ratios_table and aggregated news HTML to ChatGPT and returns an assessment
    about whether the stock might be healthy, including analysis of financial ratios
    and news trends.
    """

    # Convert ratios_table to a more friendly string for ChatGPT
    ratios_str = ratios_table.to_string(index = False)

    # Clean the aggregated HTML to extract meaningful text
    news_text = clean_html(articles_html_all)

    # Limit the length of the financial ratios and news text if needed
    max_news_length = 7000  # Limit the news text length

    if len(news_text) > max_news_length:
        news_text = news_text[:max_news_length] + "..."

    # Prepare the system and user messages
    system_content = (
        "You are an Expert Investment Portfolio Strategist with extensive knowledge in financial analysis and market trends. "
        # "You are provided with Stock's Key Financial Ratios and Stock's Aggregated Latest News Articles."
        # "Your task is to analyze both the financial data and the news trends to determine the stock's overall health."
    )

    user_content = (
        f"The Stock's Key Financial Ratios:\n{ratios_str}\n\n"
        f"The Stock's Aggregated Latest News Articles:\n{news_text}\n\n"
        "Provide a detailed analysis with the following guidelines:\n"
        "1) Evaluate whether this stock is a healthy investment in terms of being high-return and low-risk.\n"
        "2) Analyze the provided news articles to identify and summarize the main trends and themes related to "
        "   the stock, highlighting specific details such as major events, strategic initiatives, regulatory changes, "
        "   and significant announcements.\n"
        "3) Provide a comprehensive assessment of the stock's health by combining your analysis of the financial "
        "   ratios and the news trends. Include a thorough response with in-depth insights that analyze the stock's risk-return profile."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]

    try:
        response = openai.ChatCompletion.create(
                model = "gpt-4o-mini",  # "chatgpt-4o-latest", "gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"
                messages = messages,
                temperature = 0.0,  # Set to 0 for deterministic responses
                max_tokens = 1200,  # Decrease max_tokens to prevent exceeding the limit
                # top_p = 0.3,  # Limits to top 30% probability mass
                frequency_penalty = 0.0,  # Strongly penalizes repeated tokens
                presence_penalty = 0.0  # Strongly penalizes reuse of topics
        )

        # Extract the text out of the response
        assistant_message = response.choices[0].message["content"].strip()
        return strip_markdown(assistant_message)
    except Exception as e:
        return f"Oops, ChatGPT had an issue: {e}"