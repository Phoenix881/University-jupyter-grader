def unpackNotebook(filepath: str):
    # Take one .ipynb and turns it into two files
    # .txt with all cell text content and
    # .pdf with all .png content combined
    # And then stores them in "app/temp" directory
    from nbconvert import ASCIIDocExporter
    from PIL import Image
    import nbformat
    import os 

    notebook_unicode = open(filepath, "r", encoding="utf-8").read()
    notebook_Obj = nbformat.reads(s=notebook_unicode, as_version=4)

    # Instantiate it
    rst_exporter = ASCIIDocExporter()
    # Convert the notebook to RST format
    (body, resources) = rst_exporter.from_notebook_node(notebook_Obj)

    # Write ASCII Doc file 
    # filepath[:-6] removes last 6 characters, namely ".ipynb" part
    text_file = os.path.join("app", "temp", f"{filepath[13:-6]}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(body)

    # Write images to png files
    image_pathes: list[str] = []
    for image in resources['outputs'].keys():
        file_name: str = image
        file_path = os.path.join("app", "temp", file_name)
        with open(file=file_path, mode="wb") as f:
            f.write(resources['outputs'][file_name])
        image_pathes.append(file_path)

    # Merge multiple .png into one .pdf
    pdf_path = os.path.join("app", "temp", f"{filepath[13:-6]}.pdf")
    images = [Image.open(image) for image in image_pathes]
        
    images[0].save(
        pdf_path, "PDF" ,resolution=100.0, save_all=True, append_images=images[1:]
    )

    for image in image_pathes:
        os.remove(image)

def encodePDF(pdf_path: str) -> str:
    # PDF location --> Base64 string
    import base64

    def encode_pdf_to_base64(pdf_path):
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')

    # Read and encode the PDF
    base64_pdf = encode_pdf_to_base64(pdf_path)
    data_url = f"data:application/pdf;base64,{base64_pdf}"

    return data_url

def getCellContent(txt_path: str) -> str:
    # TXT location --> Contents as string
    with open(txt_path, "r", encoding="utf-8") as file:
        content = file.read()
    return content