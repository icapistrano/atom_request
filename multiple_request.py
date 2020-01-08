import time
import redis
import zipfile
import requests
from PIL import Image
from io import BytesIO


class User:
    def __init__(self):
        self.png, self.jpeg = [],[]

    def image_format(self):
        # GET IMAGE FORMAT
        img_format = input(str("Enter image format e.g. png or jpeg: "))
        if img_format == 'png' or img_format == 'jpeg':
            return img_format

        else:
            raise ValueError(img_format)

    def image_resolution(self):
        # GET IMAGE RESOLUTION INTO TUPLE #index error, value error
        img_res = input("Enter resolution e.g. 788, 1024: ")
        res = img_res.split(',')
        width, height = int(res[0]), int(res[1])
        res = [width, height]
        return tuple(res)

    def remove_duplicates(self, user_requests):
        # HASHES, NO DUPLICATES

        for i in user_requests:
            if i[0] == 'png': # make lists of resolutions with same format, as list are unhashable
                self.png.append(i[1])

            elif i[0] == 'jpeg':
                self.jpeg.append(i[1])

        user_requests.clear()

        png_list = list(dict.fromkeys(self.png))
        jpeg_list = list(dict.fromkeys(self.jpeg))

        if len(png_list) > 0:
            for png in png_list:
                user_requests.append(['png', png])

        if len(jpeg_list) > 0:
            for jpeg in jpeg_list:
                user_requests.append(['jpeg', jpeg])

        return user_requests

    def options(self, PIL_obj, entry):
        while True:
            option = input("Select option for image {}: 1(to view image[s]), 2(save image[s]), 3(move on)... ".format(entry))
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


def get_cache(req, client, user):
    # HASHES, NO DUPLICATES

    entries = client.keys('*') # gets all entries in cache
    print("Found {} images in cache".format(len(entries)))

    if len(entries) == 0:
        print("No images found in cache, checking image library...")
        get_db(req, client, user)

    else:
        start_time = time.time()
        global processing_time
        global found_image
        request_db= []

        for r in req: # enumerate not needed
            for entry in entries:
                image = client.hgetall(entry)

                if image[b'format'].decode('utf-8') == r[0] and image[b'resolution'].decode('utf-8') == str(r[1]):
                    if processing_time: # execute block once
                        print("It took {} seconds to retrieve image[s] that match request {} parameters in cache".format(round(time.time() - start_time, 3),r[2]+1)) #r[2] == index, r in enumerate
                        processing_time=False
                        found_image=True

                    bin_image = image[b'binary']
                    bytes_data_io = BytesIO(bin_image) # wrap data into wrapper
                    img = Image.open(bytes_data_io)
                    user.options(img, entry)

            if found_image == False:
                request_db.append(r) # for checking in image library

            processing_time = True # change to default every r iteration
            found_image = False

        if len(request_db) > 0:
            for i in request_db:
                print("No images in cache matched request {} parameters with format={} & resolution={}".format(i[2]+1, i[0], i[1]))

            print("Checking image library...")
            get_db(request_db, client, user)


def get_db(req, client, user):
    url = 'https://www.masterofmalt.com/external_resources/dev_interview/product_images.zip'

    start_time=time.time()

    param = {'Watermark':True}
    r = requests.get(url, stream=True, params=param)
    global processing_time
    global found_image
    no_image = []

    if r: # returns true/false, response 200 is good
        with zipfile.ZipFile(BytesIO(r.content)) as z: # r.content is binary data
            images = z.namelist()

            for r in req:
                for i in images:

                    if i.endswith(r[0]):  # NO i.endswith(r[0]) 'and' image.size==r[1], only open image with correct format
                        with z.open(i) as zip_mem:
                            image = Image.open(BytesIO(zip_mem.read()))
                            if image.size == r[1]:

                                if processing_time:
                                    print("It took {} seconds to retrieve image[s] that match request {} in image library".format(round(time.time() - start_time, 3), r[2]+1))
                                    processing_time = False
                                    found_image = True

                                user.options(image, i)

                                byte_image_io = BytesIO()
                                image.save(byte_image_io, "{}".format(r[0]))
                                byte_image_io.seek(0)
                                image = byte_image_io.read() # converted to byte for redis

                                print("Sending to cache for 5 minutes...")
                                entry = {"image": "{}".format(i), "format": "{}".format(r[0]), "resolution": str(r[1]), "binary": image}

                                client.hmset(i, entry)
                                client.expire(i, 300) # sets expiring time in seconds, 5 minutes

            if found_image == False:
                no_image.append(r) # for checking in image library

            processing_time=True
            found_image=False
    else:
        print("Invalid request to url")

    if len(no_image) > 0:
        for i in no_image:
            print("No images in image library matched request {} parameters with format={} & resolution={}".format(i[2]+1, i[0], i[1]))


def main():
    redis_client = redis.Redis(host='redis-12202.c59.eu-west-1-2.ec2.cloud.redislabs.com',
                               port=12202,
                               password = 'image_processing')  # initialize client
    image_requests = []
    user = User()

    try:
        while True:
            option = input("Select option: 1(request image), 2(move on)...")
            if int(option) == 1:
                image_format = user.image_format()
                image_res = user.image_resolution()
                image_request = [image_format, image_res]
                image_requests.append(image_request)
                print("")

            elif int(option) == 2:
                break

        len_image = len(image_requests)
        image_requests = user.remove_duplicates(image_requests)
        if len_image != len(image_requests):
            print("Removed request duplicates")

        for index, i in enumerate(image_requests):
            i.append(index)

        get_cache(image_requests, redis_client, user)

    except IndexError:
        print("Out of range, enter values in this format: '788 , 1024'")

    except ValueError as e:
        print("{} not expected. Type correctly".format(e))


if __name__ == '__main__':
    processing_time = True
    found_image = False
    main()
