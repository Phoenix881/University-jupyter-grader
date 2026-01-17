"""
Get response from LLM (OpenRouter API) based on user input.
User input is just a plain text, not analysis commands.
Output is the response from LLM, not analysis result.
Input: human_input (str) - user input text
Output: LLM response (str)
"""
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
async def get_response(human_input: list[ChatCompletionMessageParam]) -> str:
    from openai import OpenAI
    import os
    from utilities.models import LLM_MODEL, DEVELOPER_PROMPT

    try:
        OPEROUTER_API_KEY = os.environ.get("OPENROUTER_KEY")
    except:
        return "Sorry. Something went wrong with getting response from LLM (API key required)"

    try:
        client = OpenAI(
            base_url="", # add correct url for prod
            api_key=OPEROUTER_API_KEY,
        )
        
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "developer", "content": DEVELOPER_PROMPT},
                *human_input 
            ]
        )
        LLM_outputDICT: dict = completion.to_dict()
        LLM_output: str = LLM_outputDICT['choices'][0]['message']['content']

        return LLM_output
    except:
        return "Something went wrong with the request to the LLM. Please try again later."

"""
Get analysis of a Jupyter Notebook file using LLM (OpenRouter API).
Input: notebook_name (str) - name of the Jupyter Notebook file
Output: LLM analysis result (str)
"""
async def get_analysis(notebook_name: str) -> str:
    from openai import OpenAI
    import os
    from utilities.models import LLM_MODEL, DEVELOPER_PROMPT

    message: list = []
    try:
        message = notebookToLLMRequest(notebook_name=notebook_name)
    except:
        return "Sorry. Something went wrong with formatting your notebook for LLM"

    try:
        OPENROUTER_API_KEY = os.environ.get("OPENROUTER_KEY")
    except:
        return "Sorry. Something went wrong with getting response from LLM (API key required)"

    try:
        client = OpenAI(
            base_url="", # add correct url for prod
            api_key=OPENROUTER_API_KEY,
        )
        
        completion = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "developer", "content": DEVELOPER_PROMPT},
                message[0]
            ]
        )
        LLM_outputDICT: dict = completion.to_dict()
        LLM_output: str = LLM_outputDICT['choices'][0]['message']['content']

        return LLM_output
    except:
        return "Something went wrong with the request to the LLM. Please try again later."

"""
Convert a Jupyter Notebook file to a format suitable for LLM request.
Input: notebook_name (str) - name of the Jupyter Notebook file
Output: message (list) - formatted message (request) for LLM with all needed info
"""
def notebookToLLMRequest(notebook_name: str) -> list:
    # Will return list structure with embedded cell content 
    # and charts packed in one PDF file (base64 str) from one .ipynb notebook

    # .ipynb --> .txt + .pdf
    from os import path
    from utilities.parser import unpackNotebook as _unpackNotebook
    from utilities.parser import encodePDF as _encodePDF
    from utilities.parser import getCellContent as _getCellContent

    _unpackNotebook(filepath=path.join("app", "uploaded", notebook_name))

    # .txt --> str
    cellContent: str = _getCellContent(
        txt_path=path.join("app", "temp", f"{notebook_name[:-6]}.txt"))
    chartsPDF_filename: str = notebook_name[:-6]
    # .pdf --> base64 str
    chartsPDF_base64: str = _encodePDF(
        pdf_path=path.join("app", "temp", f"{notebook_name[:-6]}.pdf"))
    message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": cellContent
                },
                {
                    "type": "file",
                    "file": {
                        "filename": chartsPDF_filename,
                        "file_data": chartsPDF_base64
                    }
                }
            ]
        }
    ]

    return message