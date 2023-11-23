import pika
from decouple import config
import subprocess
import couchdb
from app.models import DatabaseObject
from datetime import datetime
import os
from io import FileIO
from pathlib import Path
import time


def create_connection(retry_count=5):
    credentials = pika.PlainCredentials(username="user", password="password")
    parameters = pika.ConnectionParameters(
        host="message-queue", port=5672, credentials=credentials
    )

    while retry_count > 0:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            if channel:
                channel.queue_declare(queue="hello")
                return channel
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQP Connection Error: {e}")
            retry_count -= 1
            time.sleep(1)
        except pika.exceptions.ChannelError as e:
            print(f"Error creating channel: {e}")
            retry_count -= 1
            time.sleep(1)
        except pika.exceptions.ChannelClosed as e:
            print(f"Channel closed: {e}")
            retry_count -= 1
            time.sleep(1)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            retry_count -= 1
            time.sleep(1)

    raise Exception("Failed to establish connection to message queue")


def create_database(database_name):
    print("Creating database connection...")
    server_url = "http://admin:password@0.0.0.0:5984/"
    try:
        couchclient = couchdb.Server(server_url)
        print("Connected to CouchDB Server")
        try:
            db = couchclient.create(database_name)
            print(f"Database '{database_name}' created")
        except couchdb.http.PreconditionFailed:
            db = couchclient[database_name]
            print(f"Using existing database '{database_name}'")
        except Exception as e:
            print(f"Error creating/accessing database '{database_name}': {e}")
            raise
    except Exception as e:
        print(f"Cannot connect to CouchDB Server: {e}")
        raise

    return db


def save_data(database_name, params: DatabaseObject):
    try:
        print("Saving data to CouchDB...")
        db = create_database(database_name)
        document = {
            "SongName": params.SongName,
            "DateAdded": datetime.now(),
            "SongData": params.Data,
            "Song": params.Song,
        }
        result = db.save(document)
        print(f"Data saved successfully with ID: {result['id']}")
        return result
    except Exception as e:
        print(f"Error saving data to CouchDB: {e}")
        raise


def remove_files(json_file_path, audio_file_path):
    print("Removing files...")
    for file_path in [json_file_path, audio_file_path]:
        if file_path and file_path.exists():
            try:
                command = ["rm", "-rf", str(file_path)]
                subprocess.check_output(
                    command, shell=False, stderr=subprocess.STDOUT
                ).decode().strip()
                print(f"File removed: {file_path}")
            except Exception as e:
                print(f"Error removing file {file_path}: {e}")
                raise


def remove_files_and_save():
    print("Processing and saving data...")
    current_file_path = Path(
        subprocess.check_output("pwd", shell=False, stderr=subprocess.STDOUT)
        .decode()
        .strip()
    )
    audio_extensions = {".mp3", ".m4a", ".wav", ".webm"}

    files = os.listdir(current_file_path)

    json_file_path = None
    audio_file_path = None
    song_name = None

    for file in files:
        full_path = current_file_path / file

        if full_path.suffix.lower() == ".json":
            json_file_path = full_path
            song_name = full_path.stem.split("[")[0]

        elif full_path.suffix.lower() in audio_extensions:
            audio_file_path = full_path

    saved_object = None

    if json_file_path and audio_file_path:
        json_file = FileIO(json_file_path, mode="rb")
        audio_file = FileIO(audio_file_path, mode="rb")

        params = DatabaseObject(
            SongName=song_name,
            DateAdded=datetime.now(),
            Data=json_file.read(),
            Song=audio_file.read(),
        )

        try:
            saved_object = save_data("music-database", params)
            print(f"Saved object: {saved_object}")
            if saved_object is not None:
                remove_files(json_file_path, audio_file_path)
        except Exception as e:
            print(f"Error processing and saving data: {e}")
            raise

    return saved_object


def publish_url(url):
    try:
        channel = create_connection()
        channel.basic_publish(exchange="", routing_key="hello", body=url)

        return {"message": "Message sent successfully", "status_code": 200}
    except Exception as e:
        print(f"Error publishing message: {e}")
        return {"message": "Message not sent", "status_code": 404}


def callback(ch, method, properties, body):
    try:
        body_str = body.decode()
        command = ["yt-dlp", "--write-info-json", "-x", "--audio-format", "mp3"]
        command.extend(body_str.split())
        print(f"Running command: {' '.join(command)}")
        output = subprocess.check_output(command, shell=False, stderr=subprocess.STDOUT)
        print(f"Command output: {output.decode()}")

    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        success = remove_files_and_save()
        print(success)
    except Exception as e:
        print(f"An unexpected error occurred during callback: {e}")


def consume_url():
    try:
        channel = create_connection()
        channel.basic_consume(
            queue="hello", on_message_callback=callback, auto_ack=True
        )
        channel.start_consuming()
        return {"message": "Started consuming messages", "status_code": 200}
    except Exception as e:
        print(f"Error consuming messages: {e}")
        return {"An error occurred during consumption:": e}
