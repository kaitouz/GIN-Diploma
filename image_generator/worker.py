import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


import redis
import json
from PIL import Image  
import PIL  
import time


# from rq import Worker, Queue, Connection
# from redis import Redis


# # Setup Redis client
# redis_connection = Redis(host='redis', port=6379, db=0)
# queue = Queue('generate_tasks', connection=redis_connection)

# def process_task():
#     time.sleep(10)
#     with Connection(redis_connection):
#         worker = Worker(queue)
#         worker.work()


def generate_image(task_data):
    # Your code to generate an image based on the prompt
    logging.info(task_data)

    message_id  = json.loads(task_data)['message_id']
    prompt      = json.loads(task_data)['prompt']
    photos_path = json.loads(task_data)['photos_path']

    logging.info(f"Processing prompt: {prompt}")

    image = Image.open(f'../ImagesData/Storage/{photos_path[0]}.jpg')
    time.sleep(5)
    image.save(f'../ImagesData/Outputs/{photos_path[0]}.jpg')


    result = json.dumps({'message_id'   : message_id, 
                        'prompt'        : prompt, 
                        'generated_path'   : photos_path[0]})

    # redis_client.publish('result_queue', result)

    logging.info(f"Done prompt: {prompt}")
    return result


# process_task()