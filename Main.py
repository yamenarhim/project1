import os
import subprocess
import sys
import json

from flask import Flask,render_template,request,session,jsonify
from flask_session import Session
from flask_socketio import SocketIO, emit,join_room, leave_room , send

app = Flask(__name__)

#handeling Sessions
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#inititalizing SocketIO
socketio = SocketIO(app)

#context processor will provide the dict reurned to all the pages
@app.context_processor
def inject_user():
    """
    This function will count how many users are in the website and then send a variable for all pages for dijango to read.
    """
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)
    usersnames=list(users_data.keys())
    fr.close()

    number_of_users= str(len(usersnames))

    return dict(number_of_users=number_of_users)


def pairing_func(a,b):
    """
    This function takes two arguments and insures that the output is a unique number of these two numbers.
    """
    a1=(1/2)*(a+b)*(a+b+1)+b

    return a1


@app.route('/who_am_I',methods=['POST'])
def who_am_I():
    """
    This will tell the browser about the session that the user is currently in.
    """
    user=session["username"]
    print(user)

    return jsonify({"user":user})

#displaying pages
@app.route('/')
def home():
    """
    The home page will take the usernames that are signed up in this website.
    """
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)

    usersnames=list(users_data.keys())
    try:
        user=session["username"]
        log_in_state=session['isloggedin']
    except:
        log_in_state=False
        user=None

    if len(usersnames) <=1 and log_in_state:
        no_user=True
    elif len(usersnames)==0:
        no_user=True
    else:
        no_user=False

    return render_template('Home.html',usersnames=usersnames,log_in_state=log_in_state,current_user=user,no_user=no_user)


@app.route('/channels')
def channels():
    """
    Read the channels and then return in to the user.
    """
    with open(f'channels.json') as fr:
        channels_data= json.load(fr)


    channels_data=list(channels_data.keys())[1:]

    if len(channels_data) ==0:
        no_channels=True
    else:
        no_channels=False

    return render_template('Channels.html',channelsnames=channels_data,no_channels=no_channels)

#the functions below just render templates nothing interesting
@app.route('/signup')
def signup():
    return render_template('Signup.html',message="")

@app.route('/creatting_channel')
def creatting_channel():
    return render_template('channel create.html')

@app.route("/signin")
def signin():
    return render_template('signin.html')

#Handeling requests


#channels codes

#creating the channel
@app.route("/create_channel",methods=["POST"])
def create_channel():
    """
    Checks if the user have a session and sign them up if they aren't
    """
    #checks if the user is logged in
    if session.get("isloggedin") is None:
        return render_template('resaultpage.html',message="You can't create a channel if your are not signed in")

    #read the data inside channels file
    with open(f'channels.json') as fr:
        data= json.load(fr)
    fr.close()

    #checks the id sequencing
    try:
        id=data['id']
    except:
        data['id']=0
        id=0

    #get the information to save inside the file
    channel_name=request.form.get("channel_name")
    if len(channel_name)>30:
        return render_template('resaultpage.html',message="Max limit for channel name is 30 Charchter!!")

    data[channel_name]={"id":id}
    id+=1
    data['id']=id

    #add changes to usersbyid file
    with open(f'channels.json','w') as fw:
        json.dump(data,fw)

    return render_template('resaultpage.html',message="Success!!")

#User Joined to channel
@app.route("/load_channel",methods=["POST"])
def load_channel():
    """
    Take the channel name, Then look for it in the database, and send messages data to the user if he is in the channel.
    """
    data=request.form
    data=data.copy()

    channel=data["channel_name"]
    user=session['username']

    with open(f'channels.json') as fr:
        channels= json.load(fr)
    fr.close()

    try:
        channels[channel]["users"][user]
    except:
        try:
            if not(user in channels[channel]["users"]):
                channels[channel]["users"].append(user)
        except:
            channels[channel]["users"]=[]
            channels[channel]["users"].append(user)

    try:
        messages=channels[channel]["messages"]
    except:
        channels[channel]["messages"]=[]
        messages=[]


    with open(f'channels.json','w') as fw:
        json.dump(channels,fw)

    return jsonify({"messages":messages,"users":channels[channel]["users"],'current_user':user})

#User Sent A Message
@app.route("/save_channel_message",methods=["POST"])
def save_channel_message():
    """
    Takes the message and save it
    to do:
    1. Make restriction on the message length and type.
    """
    data=request.form
    data=data.copy()

    message=data['message']
    channel=data['channel']

    with open(f'channels.json') as fr:
        channels= json.load(fr)

    channels[channel]["messages"].append([session['username'],message])

    with open(f"channels.json",'w') as fw:
        json.dump(channels,fw)

    return "Saved Commander"

@app.route("/leave_room",methods=["POST"])
def leave_channel():
    """
    The user will leave the channel on request.
    """
    pass

#two people communcication code
#signing up function
@app.route("/resault",methods=["POST"])
def resault():
    """
    This function will recieve data from the signup fourm, and save user information to the database

    To do:
        1. Make restrictions on what data to be accepted.
            (The kind of user name  like no duplicate and how long-
              -username is and what password should be expected)
    """
    #checks if the user is logged in
    if not (session.get("isloggedin") is None):
        return render_template('resaultpage.html',message="You have already Signed Up please log out to Sing Up")

    #Read the data inside userbyid
    with open(f'usersbyid.json') as fr:
        print(fr)
        data= json.load(fr)
    fr.close()
    with open(f'usersbyusername.json') as fr:
        print(fr)
        usernames= json.load(fr)
    fr.close()
    usernames=list(usernames.keys())

    #checks the id sequencing
    try:
        id=data['id']
    except:
        data['id']=0
        id=0

    #get the information to save inside the file
    username=request.form.get("username")
    if username in usernames:
        return render_template('Signup.html',message="Username already exist")
    password=request.form.get("password")
    id+=1
    data['id']=id
    data['user'+str(id)]={"username":username,"password":password}

    """
    Here i am experming between two ways of saving data, i might end up using
    both of them which will be useful i think in large databases where i have to reach an information
    fast enough.
    """

    #add changes to usersbyid file
    with open(f'usersbyid.json','w') as fw:
        json.dump(data,fw)

    #read the data inside the usersbyusername file
    with open(f'usersbyusername.json') as fr:
        print(fr)
        data= json.load(fr)

    data[username]={"id":id,"password":password}
    users_data=data
    #Write changes to usersbyusername file
    with open(f'usersbyusername.json','w') as fw:
        json.dump(data,fw)

    return render_template('resaultpage.html',message="Success!!")


#signing in function
@app.route("/signedin",methods=["POST"])
def signedin():
    """
    takes data from the fourm and checks it with the database,returns a logged in session
    in case of success and an error message in case of an error
    """
    #here we use reaching by username becasue we have the username in our hands
    with open(f'usersbyusername.json') as fr:
        data= json.load(fr)

    #getteing information from the fourm
    username=request.form.get("username")
    password=request.form.get("password")

    #try to find the username inside the data and return error in case the program couldn't find it
    try:
        user=data[username]
        passw=user['password']
        if passw==str(password):
            session['isloggedin']=True
            session['username']=username
            print(session.get('username'))
            return render_template('resaultpage.html',message="You have been logged in")
        else:
            return render_template('resaultpage.html',message="check the data you have entered")
    except:
        return render_template('resaultpage.html',message="check the data you have entered")


#Saving messages to the server HDD
@app.route("/save_message",methods=["POST"])
def save_message():
    """
    This function recives data from javascript: "the message and the username of the two users that are talking to each other"
    -which the user that is logged in and that have a session is sending through the chat box- the function takes the two
    users id's and assign them a unique id using a pairing function.
    """

    #gets the data that has been sent by javascript function "send()" and makes it writtible
    data=request.form
    data=data.copy()
    message=data['message']
    user=session['username']

    #open the userbyusername to get information about the user data and message file to save messages to
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)
    with open(f"messages.json") as fw:
        users_messages= json.load(fw)

    #we close the file here after we took what we needed
    fw.close()
    fr.close()

    #information we need to save the message in a unique chat_id (explained in the function comment above)
    first_user_id = users_data[user]["id"]
    secound_user_id = users_data[data['other_user']]["id"]
    if first_user_id<secound_user_id:
        k1=first_user_id
        k2=secound_user_id
    else:
        k1=secound_user_id
        k2=first_user_id
    chat_id = str(pairing_func(k1,k2))
    print(chat_id )

    #try to find the conversation if they had chatted before and deals with the exception of new chat
    try:
        users_messages["messages"][chat_id].append((user,message))
        #print(users_messages["messages"][chat_id])
    except:
        try:
            users_messages["messages"][chat_id]=[]
        except:
            users_messages["messages"]={}
            users_messages["messages"][chat_id]=[]
        users_messages["messages"][chat_id].append((user,message))

    #save changes to the messages.json file
    with open(f"messages.json",'w') as fw:
        json.dump(users_messages,fw)

    #for testing purposes
     #print(users_messages["messages"][chat_id])
    #end of testing

    return "Recived Commander"

#loading chats and handeling their id's
@app.route("/load_chat",methods=["POST"])
def load_chat():
    """
    This function takes information from javascript:"the current username in session,
    and the requested chat for the person he wants to chat with",
    after getting the chat the function sends the data to make the javascript handle the view
    and dealing with the view of this data.
    """
    #get the data for the chat requested
    data=request.form
    data=data.copy()
    #print(list(data.keys()))

    #open files that we need information from
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)
    with open(f"messages.json") as fw:
        users_messages= json.load(fw)

    #gets the information to get the calculate the chat id (read the save_message() function description)
    user1_id=users_data[session['username']]['id']
    #print("user1_id: ",user1_id)
    user2_id=users_data[data['secound_user']]['id']
    #print("user2_id: ",user2_id)
    if user1_id<user2_id:
        k1=user1_id
        k2=user2_id
    else:
        k1=user2_id
        k2=user1_id
    chat_id = str(pairing_func(k1,k2))
    #print("chat_id",chat_id)
    #print(users_messages['messages'][chat_id])

    #tryies to know if the two users have chatted before
    try:
        messages=users_messages['messages'][chat_id]
    except:
        users_messages[chat_id]=[]
        messages=[]
    room='room-'+str(chat_id)

    return jsonify({'messages':messages})

@app.route("/sign_out",methods=["GET"])
def sign_out():
    """
    Clear the user session and return a Logged Out page
    """
    session.clear()
    return render_template('resaultpage.html',message="Logged Out!")

@app.route("/clear_chat_data",methods=["GET"])
def clear_chat_data():
    """
    Clear all the chat data if you are the Admin of the website.
    """
    print(session['username'])
    if session['username']=="yamenarhim5":
        with open(f"messages.json") as fw:
            users_messages= json.load(fw)
        users_messages["messages"]={}

        with open(f"messages.json",'w') as fw:
            json.dump(users_messages,fw)

        return render_template('resaultpage.html',message="You cleared data")
    return render_template('resaultpage.html',message="You are not allowed to do that")

@socketio.on('sign up')
def count_users():
    """
    This will update the users count when someone Sign Up.
    """
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)

    usersnames=list(users_data.keys())
    fr.close()

    number_of_users= str(len(usersnames))

    socketio.emit("new user",{"number_of_users":number_of_users},broadcast=True)

@socketio.on('joined room')
def joined_room(data):
    """
    This function takes information from javascript:"the current username in session,
    and the requested chat for the person he wants to chat with",
    after getting the chat the function sends the data to make the javascript handle the view
    and dealing with the view of this data.
    """
    #open files that we need information from
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)
    with open(f"messages.json") as fw:
        users_messages= json.load(fw)
    fr.close()
    fw.close()

    #gets the information to get the calculate the chat id (read the save_message() function description)
    user1_id=users_data[session['username']]['id']
    #print("user1_id: ",user1_id)
    user2_id=users_data[data['secound_user']]['id']
    #print("user2_id: ",user2_id)
    if user1_id<user2_id:
        k1=user1_id
        k2=user2_id
    else:
        k1=user2_id
        k2=user1_id
    chat_id = str(pairing_func(k1,k2))

    room='room-'+str(chat_id)
    join_room(room)
    emit("joined room",{"message":'user '+session['username']+' wants to chat with you'},room=room)

@socketio.on('new message')
def new_message(data):
    """
    When someone send a message it will recieve it and emit it to all users.
    """
    message=data['message']
    user=session['username']

    #open the userbyusername to get information about the user data and message file to save messages to
    with open(f'usersbyusername.json') as fr:
        users_data= json.load(fr)
    with open(f"messages.json") as fw:
        users_messages= json.load(fw)

    #we close the file here after we took what we needed
    fw.close()
    fr.close()

    #information we need to save the message in a unique chat_id (explained in the function comment above)
    first_user_id = users_data[user]["id"]
    secound_user_id = users_data[data['secound_user']]["id"]
    if first_user_id<secound_user_id:
        k1=first_user_id
        k2=secound_user_id
    else:
        k1=secound_user_id
        k2=first_user_id
    chat_id = str(pairing_func(k1,k2))
    room='room-'+chat_id

    emit("recived message",{"message":data['message'],'message sender':user},room=room)

@socketio.on('joined channel')
def joined_channel(data):
    """
    Do stuff when someone join the channel
    """
    with open(f'channels.json') as fr:
        channels= json.load(fr)

    room="channel-"+str(channels[data["channel"]]["id"])
    join_room(room)

    print(session['username']+'joined ' + room)
    emit("joined channel",{"message":"user: "+session['username']+"has joined the channel"},room=room)

@socketio.on('new channel message')
def new_channel_message(data):
    """
    emitt the channel message to the channel users.
    """
    with open(f'channels.json') as fr:
        channels= json.load(fr)

    room="channel-"+str(channels[data["channel"]]["id"])
    emit("new channel message",{"message":data["message"],"message sender":session['username']},room=room)

if __name__ == '__main__':
    """
    This code will execute if accessed dircectly and not imported
    This code will run the Flask app
    """
    app.debug = False

    x=subprocess.check_output("ipconfig",shell=True)
    x=x.decode()
    x=x.split('\n')
    z=0
    for n in x:
        a=n.find('192.168.1')
        if a != -1:
            a=n
            break
    x=a
    x=x[x.index('1'):x.index(x[-1])]

    app.run(debug=True,host=str(x))
