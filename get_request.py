import time
import redis
import zipfile
import requests
from PIL import Image
from io import BytesIO

class User:
    def __init__(self):
        pass

    def image_format(self):
        # GET IMAGE FORMAT
        img_format = input(str("Enter image format: png or jpeg: "))

        if img_format == 'png' or img_format == 'jpeg':
            return img_format.lower()

        else:
            print("Invalid image formatting. Must be 'png' or 'jpeg'")

    def image_resolution(self):
        # GET IMAGE RESOLUTION INTO TUPLE #index error, value error
        try:
            img_res = input("Enter resolution: ")
            res = img_res.split(',')
            width, height = int(res[0]), int(res[1])
            res = [width, height]
            return tuple(res)

        except IndexError:
            print("Out of range, enter value with: x , y")

        except ValueError:
            print("Not an integer, type correctly")


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

    entries = client.keys('*') # gets all entries in cache
    print("Found {} images in cache".format(len(entries)))

    for entry in entries:
        image = client.hgetall(entry)
        if image[b'format'].decode('utf-8') == img_format and image[b'resolution'].decode('utf-8') == str(img_res):
            bin_image = image[b'binary']
            bytes_data_io = BytesIO(bin_image) # wrap data into wrapper
            img = Image.open(bytes_data_io)
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

                byte_image_io = BytesIO()
                image.save(byte_image_io, "{}".format(img_format))
                byte_image_io.seek(0)
                image = byte_image_io.read()

                print("Sending to cache...")
                entry = {"image": "{}".format(image_filename), "format": "{}".format(img_format), "resolution": str(img_res), "binary": image}
                client.hmset(image_filename, entry)
                client.expire(image_filename, 180) # sets expiring time in seconds, 3 minutes

def main():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)  # initialize client

    user = User()
    image_format = user.image_format()
    image_res = user.image_resolution()

    get_cache(image_format, image_res, redis_client)
    # get_db(image_format, image_res, redis_client)


if __name__ == '__main__':
    start_time = time.time()
    main()
    print("Total time: {} seconds ".format(time.time()-start_time))

