# Image resizer

Image resizer api. Based on aiohttp/redis/multiprocessing.
Resize work running on different processes, work status stored in redis.
Writing for fun.


# How to install
Python version required: 3.7+
1. Recomended use venv or virtualenv for better isolation.\
   Venv setup example: \
   `python3 -m venv myenv`\
   `source myenv/bin/activate`
2. Install requirements: \
   `pip3 install -r requirements.txt` (alternatively try add `sudo` before command)
   
3. You need redis. Add to your environ `REDIS_HOST`(default-`localhost`), 
`REDIS_PORT`(default-`6379`), `REDIS_PASS`(default-`SetPass`) 

4. If it need - add to environ path to files dir `TEMP_FILES_PATH` (default - project root)


# How to run

`python3 main.py`

Then you can use this handlers for work
1) `/\` - `POST` request with `multipart` file. And you need add some query params : \
        1. `-s --scale` scale to resize image. \
        2. `-ws --width` width of out image. \
        3. `-hs --height` height of out image. 
   Attention! `scale` with `width/height` aren't incompatible!     
   Response example:
   ```
   {
    "id": "300c4865-6e04",
    "status": "ok"
   }
   ```
2) `/<id>/check` - `GET` request with id from above example.        
    You can see status of resize work.

3) `/<id>` - `GET` request with id from above example.  
    Load resized image.      

# TODO
Add logging, fix processes executor errors on start app, need some refactor
