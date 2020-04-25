# Image resizer

Image resizer api. Based on aiohttp/redis/multiprocessing.
Resize work running on different processes, work status stored in redis, resized images - on localhost or Amazon S3.
Written for fun.



# How to install
Python version required: 3.7+
1. Recomended use venv or virtualenv for better isolation.\
   Venv setup example: \
   `python3 -m venv myenv`\
   `source myenv/bin/activate`
2. Install requirements: \
   `pip3 install -r requirements.txt` (alternatively try add `sudo` before command)
   
3. You need redis. Add to your environ `REDIS_HOST`(default-`localhost`), 
   `REDIS_PORT`(default-`6379`), `REDIS_PASS`(default-`SetPass`).\ 
   And you can set expiration time for redis: `REDIS_TIMEOUT` (default-stored indefinitely or until resized image is deleted).

4. If it need - add to environ path to files dir `TEMP_FILES_PATH` (default - project root)

5. By default resized images stored forever. If you want you can set `FILES_CLEAR` for delete resized image after sending to client.

6. By default files stored on localhost. If you want user Amazon S3 you need set additional ENV vars:
   - `AWS_BUCKET` - name of your bucket.
   - `AWS_FOLDER` - folder for resized images.
   - `AWS_ACCESS_KEY`
   - `AWS_SECRET_ACCESS`
   - `AWS_REGION` - your aws region (for example `eu-central-1`)
   - `AWS_CLEAR` - delete resized images from AWS after sending to client (default-False)
   - `AWS_SSL` - use or not SSL for connections to AWS (default-False)
   
5. For debug set something to `DEBUG` env.

# How to run

`python3 main.py`

Then you can use this handlers for work
1) `/api/v1/image` - `POST` request with `multipart` file. And you need add some query params : \
        1. `-s --scale` scale to resize image. \
        2. `-ws --width` width of out image. \
        3. `-hs --height` height of out image. \
   Attention! `scale` with `width/height` are incompatible!     
   Response example:
   ```
   {
    "id": "300c4865-6e04",
    "status": "ok"
   }
   ```
2) `/api/v1/image/<id>/check` - `GET` request with id from above example.        
    You can see status of resize work.

3) `/api/v1/image/<id>` - `GET` request with id from above example.  
    Load resized image.      

# Tests
Install test requirements `pip3 install -r test_requirements.txt` and run `python3 -m pytest`

# TODO
Some refactor, add errors handling for AWS connections.
