import os
from dotenv import load_dotenv
def get_llms():
    
    

    from langchain_google_genai import ChatGoogleGenerativeAI
   

    load_dotenv()
    model_name=["gemini-flash-latest","gemini-3-flash-preview","gemini-3-pro-preview","gemini-flash-lite-latest"]
    api_key=os.getenv("GOOGLE_API_KEY")
    llms=[]
    for model in model_name:
        try:
            llm= ChatGoogleGenerativeAI(model=model,
                                                temperature=0.3,
                                                max_tokens=8000,
                                                timeout=None,
                                                max_retries=2,
                                                google_api_key=api_key,
                                            )
            llms.append(llm)
        except Exception as e:
            print("Exception", str(e))
    
    
    return llms

def get_deepseek_llm():
    from langchain_deepseek import ChatDeepSeek
    load_dotenv()
    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        # other params...
    )

    return llm