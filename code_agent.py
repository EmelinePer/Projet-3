import asyncio
import json
from playwright.async_api import async_playwright
from openai import OpenAI

# 1. DEEPSEEK CONNECTION
# Replace with your actual key
client = OpenAI(api_key="sk-ad6641ed81964b4cb2f6cd862cb919e0", base_url="https://api.deepseek.com")

async def ai_analyze_and_decide(elements, user_command, current_url):
    """The AI acts as a Brain: analyzing elements and deciding the next click"""
    prompt = f"""
    You are a web navigation expert. 
    CURRENT URL: {current_url}
    CLICKABLE ELEMENTS (Links/Buttons text): {elements}

    USER GOAL: "{user_command}"

    Instructions: Find the best element to click to reach the goal.
    Respond ONLY in JSON format:
    {{
        "analysis": "Short explanation of what you see on this specific site",
        "chat_response": "Your friendly response to the user",
        "action": "click",
        "target_text": "The exact or partial text of the button/link to click"
    }}
    """
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": "You are an autonomous web agent."},
                  {"role": "user", "content": prompt}],
        response_format={ 'type': 'json_object' }
    )
    return json.loads(response.choices[0].message.content)

async def main():
    async with async_playwright() as p:
        print("\n=== 🌐 UNIVERSAL WEB AGENT (ENGLISH VERSION) ===")
        
        target_url = input("🔗 Enter the URL to explore: ")
        if not target_url.startswith("http"):
            target_url = "https://" + target_url

        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"⏳ Loading {target_url}...")
        await page.goto(target_url)

        while True:
            user_input = input("\n👤 You: ")
            
            if user_input.lower() in ["exit", "quit", "stop"]:
                break

            # 1. OBSERVE: Get all visible interactive elements
            # We filter for visible elements only to help the AI
            elements = await page.query_selector_all("a, button")
            visible_texts = []
            for e in elements:
                if await e.is_visible():
                    t = await e.inner_text()
                    if t.strip(): visible_texts.append(t.strip()[:50])

            # 2. THINK: Ask the AI
            print("🧠 AI is thinking...")
            try:
                result = await ai_analyze_and_decide(visible_texts[:60], user_input, page.url)
                
                print(f"🤖 Agent: {result['chat_response']}")
                
                # 3. ACT: Improved clicking logic
                target = result['target_text']
                if target:
                    print(f"🖱️ Action: Attempting to click '{target}'...")
                    
                    # We use a more robust locator: has-text and case-insensitive
                    # This avoids the "Next ->" vs "Next" encoding issues
                    selector = f"text='{target}'"
                    
                    try:
                        # Try to click with a shorter timeout first
                        await page.click(selector, timeout=3000)
                        await page.wait_for_timeout(1000)
                    except:
                        # Fallback: Search for element containing the text more broadly
                        await page.locator(f"role=link >> text={target}").first.click()
                
            except Exception as e:
                print(f"🤖 Agent: I encountered an issue. Details: {e}")

        await browser.close()
        print("\n=== SESSION CLOSED ===")

if __name__ == "__main__":
    asyncio.run(main())