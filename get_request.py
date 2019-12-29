import time
import zipfile
import requests
from PIL import Image
from io import BytesIO

def user_input():
    parameters = []

    # GET IMAGE FORMAT
    img_format = input(str("Enter image format: png or jpeg: "))
    parameters.append(img_format.lower()) # makes str lowercase

    # GET IMAGE RESOLUTION INTO TUPLE
    img_res = input("Enter resolution: ")
    res = img_res.split(',')
    width, height = int(res[0]), int(res[1])
    res = [width, height]
    parameters.append(tuple(res))

    return parameters

def get_db(img_format, img_res):
    url = 'https://www.masterofmalt.com/external_resources/dev_interview/product_images.zip'

    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(BytesIO(r.content)) # r.content is binary data
    images = z.namelist()
    for i in images:
        if i.endswith(img_format):  # nested if, not valid to image read folder
            image = Image.open(i) # PIL library for checking image dimension
            if image.size == img_res:  # (788 x 1024)
                print(i)
                # image.show()


def main():
    user = user_input()
    get_db(user[0], user[1])


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("Total time: {} seconds ".format(time.time()-start_time))