from pydantic import BaseModel

# Input-output model for chat messages
class ChatMessage(BaseModel):
    role: str
    content: str

# In deployment please specify 
# the model used, its encoding, 
# and the context window size
LLM_MODEL = ""
MODEL_ENCODING = ""
CONTEXT_WINDOW_LIMIT = 0 # tokens

# Extensive developer prompt with instructions on how
# the grading is done is removed in public repo
# for academic integrity 
# DEVELOPER_PROMPT = """"""
