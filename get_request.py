import time
import redis
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

def get_cache(img_format, img_res, client):
    # HASHES, NO DUPLICATES

    cache = 3 # assumption, find way to get length of cache entries
    for entry_val in range(cache):
        image = client.hgetall('entry{}'.format(entry_val))

        if image[b'format'].decode('utf-8') == img_format and image[b'resolution'].decode('utf-8') == str(img_res):
            bin_image = image[b'binary']
            dataBytesIO = BytesIO(bin_image)
            img = Image.open(dataBytesIO)
            img.show()

def get_db(img_format, img_res, client):
    url = 'https://www.masterofmalt.com/external_resources/dev_interview/product_images.zip'

    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(BytesIO(r.content)) # r.content is binary data
    images = z.namelist()
    for i in images:
        if i.endswith(img_format):  # nested if, not valid to image read folder
            image = Image.open(i) # PIL library for checking image dimension
            if image.size == img_res:  # (788 x 1024)
                image.show()
                image_filename = input("Save file as: ")
                print("Saving to current directory...")
                image.save(image_filename+".{}".format(img_format))

                print("Sending to cache...")
                byteImgIO = BytesIO()
                image.save(byteImgIO, "{}".format(img_format))
                byteImgIO.seek(0)
                image = byteImgIO.read()

                entry = {"image": "{}".format(image_filename), "format": "{}".format(img_format), "resolution": str(img_res), "binary": image}
                client.hmset("entry{}".format(i), entry)




def main():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)  # initialize client

    # user = user_input()
    user = ["png", (788,1024)]
    get_cache(user[0], user[1], redis_client)

    # get_db(user[0], user[1], redis_client)


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("Total time: {} seconds ".format(time.time()-start_time))