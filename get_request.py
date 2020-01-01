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
            print("Invalid image formatting. Must be 'png' or 'jpeg'")
            exit()  # automatically stop program

    def image_resolution(self):
        # GET IMAGE RESOLUTION INTO TUPLE #index error, value error
        img_res = input("Enter resolution: ")
        res = img_res.split(',')
        width, height = int(res[0]), int(res[1])
        res = [width, height]
        return tuple(res)


def get_cache(img_format, img_res, client):
    # HASHES, NO DUPLICATES

    entries = client.keys('*') # gets all entries in cache
    print("Found {} images in cache".format(len(entries)))

    if len(entries) == 0:
        raise InputError("No images found in cache, checking image library")

    else:
        for entry in entries:
            image = client.hgetall(entry)
            if image[b'format'].decode('utf-8') == img_format and image[b'resolution'].decode('utf-8') == str(img_res):
                bin_image = image[b'binary']
                bytes_data_io = BytesIO(bin_image) # wrap data into wrapper
                img = Image.open(bytes_data_io)
                img.show()
                image_filename = input("Save file as: ")
                print("Saving to current directory...")
                img.save(image_filename + ".{}".format(img_format))

            else:
                raise InputError("No images matched parameters in cache, checking image library") # throw exception to check db

        flag_condition = True
        return flag_condition

def get_db(img_format, img_res, client):
    url = 'https://www.masterofmalt.com/external_resources/dev_interview/product_images.zip'
    flag_condition = False

    r = requests.get(url, stream=True)
    if r: # returns true/false, response 200 is good
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

                    flag_condition = True
    else:
        print("Invalid request to url")

    return flag_condition


def main():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)  # initialize client
    flag = False
    try:
        user = User()
        image_format = user.image_format()
        image_res = user.image_resolution()
        # image_format = 'png'
        # image_res = (788, 1025)

        flag = get_cache(image_format,image_res,redis_client)

    except IndexError:
        print("Out of range, enter value like: 'x , y'")

    except ValueError:
        print("Not an integer, type correctly")

    except InputError as e:
        print(e.message)
        flag = get_db(image_format, image_res, redis_client)

    finally:
        if flag:
            print("Images have been saved in the current directory")
        else:
            print("No images have been found")

if __name__ == '__main__':
    start_time = time.time()
    main()
    print("Total time: {} seconds ".format(time.time()-start_time))
