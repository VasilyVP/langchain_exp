from langchain.chat_models import init_chat_model

chat_model = init_chat_model("openai:gpt-5.4-nano", temperature=0)
