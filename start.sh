#!/bin/bash
# Start Redis server
redis-server &
# Start Flask app
python3 app.py