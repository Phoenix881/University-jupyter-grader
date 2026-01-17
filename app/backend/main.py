import os
from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from utilities import models, chat_history, GPT_responder, cleaner

# Main FastAPI application
app = FastAPI()

# Mount the static files directory to our host (localhost)
app.mount("/static", StaticFiles(directory="app/frontend/static", html=True), name="static")

# Store chat history for LLM reference (LLM-memory)
chatHistory: list[models.ChatMessage] = []
# Store the list of files user uploaded
filesList: list[str] = []
# To keep track of what notebook is analyzed now
currentNotebook: int = 0
# To determine if user uploaded files or not
filesUploaded = False

# Serve initial starting page
@app.get("/")
async def serve_index():
    global chatHistory
    global filesUploaded

    chatHistory.clear()
    filesUploaded = False

    # Ensure temp directory exists
    temp_dir = os.path.join("app", "temp") 
    os.makedirs(temp_dir, exist_ok=True)

    # Ensure upload directory exists
    upload_dir = os.path.join("app", "uploaded") 
    os.makedirs(upload_dir, exist_ok=True)

    cleaner.clean(os.path.join("app", "temp"))  # Clean temp folder
    cleaner.clean(os.path.join("app", "uploaded")) # Clean uploaded folder

    return FileResponse(os.path.join("app", "frontend", "index.html"))

# Clear chat history, LLM's memory
@app.post("/clear-chat-history")
async def clear_chat_history():
    global chatHistory
    global filesUploaded

    chatHistory.clear() 
    filesUploaded = False

    cleaner.clean(os.path.join("app", "temp"))  
    cleaner.clean(os.path.join("app", "uploaded")) 

    return {"status": "success", "message": "Chat history cleared"}

# Send API request to a LLM and update the chat history
@app.post("/chatbot-answer")
async def chatbot_answer(message: models.ChatMessage):
    global chatHistory

    # Update history for using in this request endpoint
    chatHistory = chat_history.markNewMessage(chatHistory, message.role, message.content)
    chat_messages = chat_history.formatChatHistory(chatHistory)

    # human_inout is now a list of dictionaries with previous messages and the current one
    # print(chat_messages) # for dev purposes
    chatbot_response = await GPT_responder.get_response(human_input=chat_messages)

    # Update history for using in other request endpoints 
    response_message = models.ChatMessage(role="assistant", content=chatbot_response)
    chatHistory = chat_history.markNewMessage(chatHistory, "assistant", chatbot_response)
    tokens = chat_history.calculateTokens(chatHistory)

    # Store chaHistory content in new .txt file called history.txt
    history_file_path = os.path.join("app", "temp", "history.txt")
    with open(history_file_path, "w", encoding="utf-8") as history_file:
        for message in chatHistory:
            history_file.write(f"{message.role}: {message.content}\n")

    if tokens >= models.CONTEXT_WINDOW_LIMIT:
        chatbot_response += "<br><br>*SYSTEM WARNING*: Chat memory is full! Chatbot\'s responses are now unreliable and unpredictable. Chat memory refresh is strongly recommended!"
        response_message = models.ChatMessage(role="assistant", content=chatbot_response)
        return response_message

    return response_message

# File upload API endpoint
# Implemented robust error and edge cases handling
# Valid file(-s) is/are saved in the app/uploaded directory 
# File uploading is also included in the chat history
@app.post("/files-upload")
async def process_files(files: list[UploadFile]):    
    total_response: dict[str, dict[str, str | bool]] = {}
    global chatHistory

    upload_dir = os.path.join("app", "uploaded")

    cleaner.clean(os.path.join("app", "temp"))  
    cleaner.clean(os.path.join("app", "uploaded")) 

    global filesList
    filesList.clear()

    # Different checks & saving the files
    for file in files:
        # Check if file exists and has a filename
        if not file or not file.filename:
            total_response["Unknown"] = {"Saved": False, "Context": "No file provided"}
            continue

        file_name = file.filename.strip()
        
        # Validate filename 
        if not file_name or file_name.lower() == 'none':
            total_response["Invalid"] = {"Saved": False, "Context": "Invalid filename"}
            continue

        # Check file extension
        if not file_name.lower().endswith(".ipynb"):
            total_response[file_name] = {"Saved": False, "Context": "Not a valid Jupyter Notebook file (.ipynb required)"}
            continue
        
        # Sanitize filename to prevent path traversal
        safe_filename = os.path.basename(file_name)
        if safe_filename != file_name:
            total_response[file_name] = {"Saved": False, "Context": "Invalid filename, contains path separators"}
            continue
        
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Try to save the file
        try:
            content = await file.read()
            
            # Basic validation - check if file is not empty
            if len(content) == 0:
                total_response[file_name] = {"Saved": False, "Context": "File is empty"}
                continue
            
            # Check file size (limit to 24MB)
            if len(content) > 24 * 1024 * 1024:  # 24MB 
                total_response[file_name] = {"Saved": False, "Context": "File too large (max 10MB)"}
                continue
            
            with open(file_path, "wb") as f:
                f.write(content)
                
            total_response[file_name] = {"Saved": True, "Context": f"Saved to {safe_filename}"}
            
        except PermissionError:
            total_response[file_name] = {"Saved": False, "Context": "Permission denied - cannot save file"}
        except OSError as e:
            total_response[file_name] = {"Saved": False, "Context": f"File system error: {str(e)}"}
        except Exception as e:
            total_response[file_name] = {"Saved": False, "Context": f"Unexpected error: {str(e)}"}

    chatHistory = chat_history.markFileUpload(chatHistory, total_response)

    # Removes any duplicates, just a safety check
    # if user accidentally uploadede the same notebook twices
    cleaner.removeDuplicates(os.path.join("app", "uploaded"))

    # Include list of notebook files to the history for LLM reference
    for file in os.listdir(os.path.join("app", "uploaded")):
        if file != ".gitkeep" and file != ".DS_Store":
            filesList.append(file) 
    filesList = list(set(filesList)) 

    global filesUploaded
    filesUploaded = True

    global currentNotebook
    currentNotebook = 0

    return total_response

# API endpoint to enter file analysis cycle
@app.post("/analyze")
async def start_analysis():
    global filesList
    global currentNotebook
    global chatHistory

    # If user tries to use /start command before any files have been uploaded
    response_message: models.ChatMessage
    if filesUploaded == False:
        response_message = models.ChatMessage(
            role="assistant", content="No Jupyter Notebooks found. Make sure to send them first!")
        chatHistory = chat_history.markNewMessage(chatHistory, "user", "*/start*")
        chatHistory = chat_history.markNewMessage(chatHistory, "assistant", response_message.content)
        return response_message
    
    if currentNotebook >= len(filesList):
        response_message = models.ChatMessage(
            role="assistant", content="No more Notebooks left to analyze. If you have more, please upload them"
        )
        chatHistory = chat_history.markNewMessage(chatHistory, "user", "*/next*")
        chatHistory = chat_history.markNewMessage(chatHistory, "assistant", response_message.content)
        return response_message
    
    chatbot_response = await GPT_responder.get_analysis(filesList[currentNotebook])

    user_input = chat_history.markContentSending(filesList, currentNotebook)

    chatHistory = chat_history.markNewMessage(chatHistory, "user", user_input)
    chatHistory = chat_history.markNewMessage(chatHistory, "assistant", chatbot_response)

    response_message = models.ChatMessage(role="assistant", content=chatbot_response)
    
    tokens = chat_history.calculateTokens(chatHistory)
    print(tokens)
    if tokens >= models.CONTEXT_WINDOW_LIMIT:
        chatbot_response += "<br><br>*SYSTEM WARNING*: Chat memory is full! Chatbot\'s responses are now unreliable and unpredictable. Chat memory refresh is strongly recommended!"
        response_message = models.ChatMessage(role="assistant", content=chatbot_response)
        return response_message

    currentNotebook += 1

    return response_message