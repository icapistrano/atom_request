import time
import redis
import zipfile
import requests
from PIL import Image
from io import BytesIO

class InputError(Exception):
    def __init__(self, message):
        # self.expression = expression
        self.message = message

class User:
    def __init__(self):
        pass

    def image_format(self):
        # GET IMAGE FORMAT
        img_format = input(str("Enter image format: png or jpeg: "))

        if img_format == 'png' or img_format == 'jpeg':
            return img_format

        else:
            raise ValueError(img_format)

    def image_resolution(self):
        # GET IMAGE RESOLUTION INTO TUPLE #index error, value error
        img_res = input("Enter resolution: ")
        res = img_res.split(',')
        width, height = int(res[0]), int(res[1])
        res = [width, height]
        return tuple(res)

    def options(self, PIL_obj, entry):
        while True:
            option = input("Select option for image {}: 1 (to view image[s]), 2 (save image[s]), 3 (move on)".format(entry))
            if int(option) == 1:
                print("Showing image")
                PIL_obj.show()

            elif int(option) == 2:
                print("Saving to current directory...")
                image_filename = input("Save file as: ")
                PIL_obj.save(image_filename + ".{}".format(PIL_obj.format))

            elif int(option) == 3:
                break

            else:
                print("{} not expected. Try again".format(option))


def get_cache(img_format, img_res, client, user):
    # HASHES, NO DUPLICATES

    entries = client.keys('*') # gets all entries in cache
    print("Found {} images in cache".format(len(entries)))

    if len(entries) == 0:
        raise InputError("No images found in cache, checking image library")

    else:
        start_time = time.time()
        global processing_time
        found_image = False
        for entry in entries:
            image = client.hgetall(entry)
            if image[b'format'].decode('utf-8') == img_format and image[b'resolution'].decode('utf-8') == str(img_res):
                if processing_time:
                    print("It took {} seconds to retrieve image[s] with matching parameters in cache".format(round(time.time() - start_time, 2)))
                    processing_time=False
                    found_image=True

                bin_image = image[b'binary']
                bytes_data_io = BytesIO(bin_image) # wrap data into wrapper
                img = Image.open(bytes_data_io)
                user.options(img, entry)

        if found_image == False:
            raise InputError("No images matched parameters in cache, checking image library") # throw exception to check db


def get_db(img_format, img_res, client, user):
    url = 'https://www.masterofmalt.com/external_resources/dev_interview/product_images.zip'

    start_time=time.time()
    r = requests.get(url, stream=True)
    global processing_time
    if r: # returns true/false, response 200 is good
        z = zipfile.ZipFile(BytesIO(r.content)) # r.content is binary data
        images = z.namelist()
        for i in images:
            if i.endswith(img_format):  # nested if, not valid to image read folder
                image = Image.open(i) # PIL library for checking image dimension
                if image.size == img_res:  # (788 x 1024)
                    if processing_time:
                        print("It took {} seconds to retrieve image[s] with matching parameters in image library".format(round(time.time() - start_time, 2)))
                        processing_time = False

                    user.options(image, i)

                    byte_image_io = BytesIO()
                    image.save(byte_image_io, "{}".format(img_format))
                    byte_image_io.seek(0)
                    image = byte_image_io.read()

                    print("Sending to cache for 5 minutes...")
                    entry = {"image": "{}".format(i), "format": "{}".format(img_format), "resolution": str(img_res), "binary": image}
                    client.hmset(i, entry)
                    client.expire(i, 300) # sets expiring time in seconds, 5 minutes

            else:
                print("No images found with matching parameters in image library")
    else:
        print("Invalid request to url")


def main():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)  # initialize client

    try:
        user = User()
        image_format = user.image_format()
        image_res = user.image_resolution()

        get_cache(image_format,image_res,redis_client, user)

    except IndexError:
        print("Out of range, enter values in this format: 'x , y'")

    except ValueError as e:
        print("{} not expected. Type correctly".format(e))

    except InputError as e:
        print(e.message)
        get_db(image_format, image_res, redis_client, user)


if __name__ == '__main__':
    processing_time = True
    main()
