import base64

with open("sample.txt", "rb") as f:
    data = f.read()
    file_data = data.encode("base64")
    print file_data
