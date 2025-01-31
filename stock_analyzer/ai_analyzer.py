# ai_analyzer.py

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
    # Remove code blocks
    text = re.sub(r'```.*?```', '', text, flags = re.DOTALL)

    # Remove inline code
    text = re.sub(r'`.*?`', '', text)

    # Remove headers (e.g., # Header, ## Header)
    text = re.sub(r'#{1,6}\s*', '', text)

    # Remove list bullets with bold (e.g., - **Text**)
    text = re.sub(r'^-\s*\*\*', '', text, flags = re.MULTILINE)

    # Remove bold and italics (e.g., **Text**, __Text__, *Text*, _Text_)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)  # Bold
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)  # Italic

    # Remove remaining list bullets (e.g., - Text, * Text)
    text = re.sub(r'^[-*]\s+', '', text, flags = re.MULTILINE)

    # Remove links but keep the display text (e.g., [Text](url))
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

    # Remove images (e.g., ![Alt Text](url))
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)

    # Remove any remaining Markdown characters like >, *, _, ~
    text = re.sub(r'[>*_~]', '', text)

    # Optionally, use BeautifulSoup to clean up any residual HTML tags
    soup = BeautifulSoup(text, "html.parser")
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

    # Prepare the system and user messages
    system_content = (
        "You are an Expert Investment Portfolio Strategist with extensive knowledge in financial analysis and market trends."
        " You are provided with key financial ratios of a stock and the latest news articles related to it."
        " Your task is to analyze both the financial data and the news trends to determine the stock's overall health."
    )

    user_content = (
        f"Here are the stock's key financial ratios:\n{ratios_str}\n\n"
        f"Here is the aggregated text content of the latest news articles related to this stock:\n{news_text}\n\n"
        "Given this information, please provide a detailed analysis with the following guidelines:\n"
        "1) Evaluate whether this stock is a healthy investment in terms of being high-return and low-risk.\n"
        "2) Analyze the provided news articles to identify and summarize the main trends and themes related to the stock, "
        "   highlighting specific details such as major events, strategic initiatives, regulatory changes, market developments, "
        "   and significant announcements. Discuss how these factors may impact the company's performance, valuation, and risk profile, "
        "   evaluating both positive and negative aspects and their influence on investor sentiment and the stock’s future trajectory.\n"
        "3) Provide a comprehensive assessment of the stock's health by combining your analysis of the financial ratios and the news trends. "
        "   Include a thorough response with in-depth insights that analyze the stock's risk-return profile and how recent news impacts its "
        "potential.\n\n"
        "**Important:** Please respond in plain text without using any Markdown formatting, such as headers (`#`), bold (`**`), or italics (`*`)."
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
        ]

    try:
        response = openai.ChatCompletion.create(
                model = "chatgpt-4o-latest",  # "chatgpt-4o-latest", "gpt-4o-mini", "o1-preview", "o1-mini", "o1"
                messages = messages,
                temperature = 0.0,  # Set to 0 for deterministic responses
                max_tokens = 1579,  # Increased to accommodate longer responses
                )

        # Extract the text out of the response
        assistant_message = response.choices[0].message["content"].strip()
        return strip_markdown(assistant_message)
    except Exception as e:
        return f"Oops, ChatGPT had an issue: {e}"