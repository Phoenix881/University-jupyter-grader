from utilities.models import ChatMessage as _ChatMessage
def markNewMessage(historySoFar: list[_ChatMessage], role: str, message: str) \
    -> list[_ChatMessage]:

    formattedMessage: _ChatMessage = _ChatMessage(role=role, content=message)
    historySoFar.append(formattedMessage)
    updatedHistory: list[_ChatMessage] = historySoFar

    return updatedHistory

# Create a log in chat history that user uploaded files and what files were saved
def markFileUpload(historySoFar: list[_ChatMessage], d: dict[str, dict[str, str | bool]], \
    role: str = "user") -> list[_ChatMessage]:

    filenames = []
    for (key, item) in d.items():
        if item['Saved'] == True:
            filenames.append(key)

    output = "*User uploaded files: "
    for i in range(0, len(filenames)):
        if i == 0:
            output += filenames[i]
        elif i == len(filenames) -1:
            output += ", " + filenames[i] + "*"
        else:
            output += ", " + filenames[i]

    formattedMessage: _ChatMessage = _ChatMessage(role=role, content=output)
    historySoFar.append(formattedMessage)
    updatedHistory: list[_ChatMessage] = historySoFar

    return updatedHistory

# Turn chat history into list of messages for LLM reference
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
def formatChatHistory(chat_history: list[_ChatMessage]) -> list[ChatCompletionMessageParam]:
    formatted_history = []
    for message in chat_history:
        if message.role == "user":
            formatted_history.append({"role": "user", "content": message.content})
        elif message.role == "bot" or message.role == "assistant":
            formatted_history.append({"role": "assistant", "content": message.content})
        else: # for dev purposes
            print("--- SOME SHIT HAPPENED ----")
            exit()
    return formatted_history

def markContentSending(filesList, currentNotebook) -> str:
    import utilities.parser as parser
    import os

    user_input = ""
    user_action = "*User used \"start\" command*\n"
    server_action = f"*Server sent to you the notebook \"{filesList[currentNotebook]}\"*\n"
    cell_content = parser.getCellContent(txt_path=os.path.join("app", "temp", f"{filesList[currentNotebook][:-6]}.txt"))

    user_input = \
        user_action + \
        server_action + \
        "Notebook\'s cell content + text outputs: \n" + \
        cell_content

    return user_input

from utilities.models import ChatMessage as ChatMessage
def calculateTokens(chat: list[_ChatMessage]) -> int:
    # Input: 
    # Output: 8
    import tiktoken
    from utilities.models import MODEL_ENCODING
    
    history = ""
    for message in chat:
        if message.role == "user":
            content: str = message.content
            history += f"user: {content}\n"
        if message.role == "bot" or message.role == "assistant":
            content: str = message.content
            history += f"assistant: {content}\n"

    encoding = tiktoken.get_encoding(MODEL_ENCODING)
    numberOfTokens: int = len(encoding.encode(history))
    
    return numberOfTokens