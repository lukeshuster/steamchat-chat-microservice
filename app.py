from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import firestore
import threading
import time

# configuration
DEBUG = False

# instantiate the app
app = Flask(__name__)

app.config.from_object(__name__)

# Firestore init
# instantiate client
db = firestore.Client()

# enable CORS
CORS(app)
cors = CORS(app, resources={r'/*': {'origins': '*'}})
allDocs = {}
updateChat = threading.Event()

# Health Check
@app.route('/')
def health_check():
    return jsonify('success')

# Health Check
@app.route('/health')
def health_check2():
    return jsonify('success')

# Main chatRoom route
@app.route('/chat/add_chatRoom', methods=['POST'])
def add_chatRoom():
    appId = request.form.get("appId")
    doc_ref = db.collection('chatRooms').document(appId)
    doc_ref.set({
        'Game Name': request.form.get("gameName")
    })
    room_ref = db.collection('chatRooms').document(appId)
    # # # Get all current message from firestore and sent to front
    # doc_ref = room_ref.collection('messages').order_by('timestamp', direction=firestore.Query.ASCENDING).stream()
    #
    #
    # allDocs = [doc.to_dict() for doc in doc_ref]
    # print("Print one by one:")
    # for doc in allDocs:
    #     print(doc)
    # return jsonify(allDocs), 200

    # [START listen_for_changes]
    # Create an Event for notifying main thread.
    query_done = threading.Event()
    # Create a callback on_snapshot function to capture changes
    global allDocs
    global updateChat
    def on_snapshot(col_snapshot, changes, read_time):
        print(u'Callback received query snapshot.')
        print(u'Current messages ')

        global allDocs
        global updateChat
        allDocs = [change.document.to_dict() for change in changes if change.type.name == 'ADDED']
        for change in allDocs:
            print(change)
            print("message printed")
        query_done.set()
        updateChat.set()
        print("After set")
    col_query = room_ref.collection('messages')
    # Watch the collection query
    query_watch = col_query.on_snapshot(on_snapshot)
    # Wait for the callback captures the deletion.
    print("before timout")
    query_done.wait(timeout=60)
    print("After timeout")
    print("after unsub")
    updateChat.clear()
    return jsonify(allDocs)
# realtime updates to the chat
@app.route('/chat/updateChat', methods=['POST'])
def update_chat():
    global allDocs
    global updateChat
    updateChat.wait()
    updateChat.clear()
    return jsonify(allDocs)


# add message to database
@app.route('/chat/sendMessage', methods=['POST'])
def sendMessage():
    appId = request.form.get("appId")
    steamId = request.form.get("steamId")
    avatar_url = request.form.get("avatar_url")
    name = request.form.get("name")
    message = request.form.get("message")
    room_ref = db.collection('chatRooms').document(appId)
    ts = str(int(time.time()))
    message_ref = room_ref.collection('messages').document(ts)
    message_ref.set({
        'steamId': steamId,
        'avatar_url': avatar_url,
        'name': name,
        'message': message,
        'timestamp': ts,
        'displayTime': firestore.SERVER_TIMESTAMP
    })
    return jsonify({'test': 'no change'})


if __name__ == '__main__':
    app.run(host='0.0.0.0')
