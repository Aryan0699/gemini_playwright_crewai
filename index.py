from playwright.sync_api import sync_playwright
import time
import google.generativeai as genai
import os
from dotenv import load_dotenv
from crewai import Agent,Crew,Task
from crewai.tools import BaseTool
# from crewai.tools import tool
# from langchain.tools import tool
from crewai import LLM

load_dotenv()
################################################### Just testing gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model=genai.GenerativeModel("gemini-2.0-flash")

# print(model.generate_content("Hello how are you").text)

# with open("output.png","rb") as f:
#     image_bytes=f.read()
#     print(type(image_bytes))


# response = model.generate_content(
#     [
#         {"mime_type":"image/png","data":image_bytes},
#         "Try to extract text from image and interpret whether the login was sucessful or not."
#     ]
# )

# print(response.text)
##################################################################

print("-----------------------------------------")
class LoginTool(BaseTool):
     name: str="login_tool"
     description:str="A tool that logs into Notion using Playwright and returns the resulting message from the Google sign-in page."
     
     def _run(self) -> str:
        try:
            with sync_playwright() as playwright:
                browser=playwright.chromium.launch(headless=False,slow_mo=2000)
                context=browser.new_context()
                page=context.new_page()
                page.goto("https://www.notion.com/")
                login=page.get_by_role("link", name="Log in", exact=False)

                print(login)
                login.click()
                continuwithgoogle=page.locator("div.tx-uiregular-14-med",has_text="Continue with Google")
                print(continuwithgoogle)
                continuwithgoogle.highlight()

                with context.expect_page() as new_page_info:    
                    continuwithgoogle.click()
                google_page=new_page_info.value
                # print(google_page)
                input_box = google_page.locator("input[type='email']")
                if input_box.count() == 0:
                    print("❌ Input box not found")
                else:
                    print("✅ Input box found")
                input_box.fill("aryanj260506@gmail.com")

                Next=google_page.get_by_text("Next")
                Next.click()
                time.sleep(5)
                google_page.screenshot(path="output.png")
                # output=google_page.locator("div.dMNVAe")
                # output1=output.all_inner_texts()
                
                # result="".join(output1)
                # print(result)
                with open("output.png","rb") as f:
                    image_bytes=f.read()

                response=model.generate_content([
                    {
                        "mime_type":"image/png",
                        "data":image_bytes
                    },
                    "Try to extract text from image and interpret whether the login was sucessful or not and clearly state if successful or unsuccessful and also what went wrong."
                ])

                result=response.text
                print("result of tool : " ,result)
                return result
                
                
        
        except Exception as e:
            return "Error while login"
    
    
login_tool=LoginTool()

# login_tool=Tool.from_function(
#      name="Notion_Logger",
#      func=login_notion,
#      description="You will be instructed to login in to notion website and you should return text which you get from there"
# )

try:
    # Use CrewAI's native LLM class instead of LangChain
    llm = LLM(
        model="gemini/gemini-1.5-flash",
        api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.7
    )
    print("CrewAI LLM initialized successfully")
except Exception as e:
    print(f"LLM initialization failed: {e}")
    raise

agent=Agent(
     role="NotionWebsiteLogger",
     goal="You should log in into notion webiste and respond correctly in a stuctured way as per text received as a result",
     backstory="You are an expert in loggin into a website",
    tools=[login_tool],
    llm=llm,
    verbose=True
)


task=Task(
     description="Go and login for me in notion website",
     expected_output="A message that gives idea about the completion of event in a structured manner",
     agent=agent
)


crew=Crew(
     agents=[agent],
     tasks=[task],
     verbose=True

)

print("Attempting to log in to Notion...")
result = crew.kickoff()
print("\n--- Login Automation Result ---")
print(result)