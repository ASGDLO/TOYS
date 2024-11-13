import redis

# Connect to Redis
redis_client = redis.StrictRedis(host='', port=6379, db=0, decode_responses=True)

# Retrieve all keys
keys = redis_client.keys('*')

# Print keys and their values depending on their type
for key in keys:
    key_type = redis_client.type(key)
    
    if key_type == 'string':
        value = redis_client.get(key)
    elif key_type == 'list':
        value = redis_client.lrange(key, 0, -1)
    elif key_type == 'set':
        value = redis_client.smembers(key)
    elif key_type == 'hash':
        value = redis_client.hgetall(key)
    elif key_type == 'zset':
        value = redis_client.zrange(key, 0, -1, withscores=True)
    else:
        value = f"Unsupported type: {key_type}"
    
    print(f"Key: {key}, Type: {key_type}, Value: {value}")

