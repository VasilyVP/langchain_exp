import os
from pathlib import Path
from typing import Literal
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv(verbose=True)

DATA_DIR = Path(__file__).resolve().with_name("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

image_gen_model = "gemini-2.5-flash-image"


def _generate_image(prompt: str):
    from google import genai

    client = genai.Client()
    response = client.models.generate_content(
        model=image_gen_model,
        contents=[prompt],
    )

    for part in response.parts or []:
        if part.inline_data is None:
            continue

        image = part.as_image()
        return image

    return None


@tool
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news"] = "general",
) -> dict:
    """Search the web for current information.

    Args:
        query: The search query (be specific and detailed)
        max_results: Number of results to return (default: 5)
        topic: "general" for most queries, "news" for current events

    Returns:
        Search results with titles, URLs, and content excerpts.
    """
    try:
        from tavily import TavilyClient

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return {"error": "TAVILY_API_KEY not set"}

        client = TavilyClient(api_key=api_key)
        return client.search(query, max_results=max_results, topic=topic)
    except Exception as e:
        return {"error": f"Search failed: {e}"}


@tool
def generate_cover(prompt: str, slug: str) -> str:
    """Generate a cover image for a blog post.

    Args:
        prompt: Detailed description of the image to generate.
        slug: Blog post slug. Image saves to blogs/<slug>/hero.png
    """
    try:
        image = _generate_image(prompt)
        if image is None:
            return "No image generated"

        output_path = DATA_DIR / "blogs" / slug / "hero.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path))
        return f"Image saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"


@tool
def generate_social_image(prompt: str, platform: str, slug: str) -> str:
    """Generate an image for a social media post.

    Args:
        prompt: Detailed description of the image to generate.
        platform: Either "linkedin" or "tweets"
        slug: Post slug. Image saves to <platform>/<slug>/image.png
    """
    try:
        image = _generate_image(prompt)
        if image is None:
            return "No image generated"

        output_path = DATA_DIR / platform / slug / "image.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(output_path))
        return f"Image saved to {output_path}"
    except Exception as e:
        return f"Error: {e}"
