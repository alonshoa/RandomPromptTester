from PIL import Image

# image = {"assistant": Image.open("images/download.jpg"), "user": Image.open("images/test_img.jpg")}
image = {
    "user": "path/to/user/avatar.jpg",
    # "assistant": "path/to/default/assistant/avatar.jpg",
    "user": Image.open("images/download.jpg"),
    "default": Image.open("images/download_1.jpg"),
    "assistant_case 1": Image.open("images/download_1.jpg"),
    "assistant_case 2": Image.open("images/download_2.jpg"),
    "header_case 1": Image.open("images/ss_Picture1.png"),
    "header_case 2": Image.open("images/ss_Picture2.png"),
    "header_case 3": Image.open("images/ss_Picture3.png"),
    "header_case 4": Image.open("images/ss_Picture4.png"),
    # Add more case-specific images as needed
}

cases = {
    "select the case before start": [''],
    "case 1": [''],
    "case 2": [''],
    "case 3": [''],
    "case 4": [''],
}