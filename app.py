######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
from flask_login import AnonymousUserMixin
import datetime

# for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'cs460secretkey'  # Changed for Git!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''  # Abstracted out for Git upload!
app.config['MYSQL_DATABASE_DB'] = '460_project'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

class Anonymous(AnonymousUserMixin):
  def __init__(self):
    self.username = 'Guest'
    self.id = 0

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = Anonymous

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT email from Users")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)


# ROUTES----------------------------------------------------------------------------------------------------------------
@app.route('/profile')
@flask_login.login_required
def protected():
    data = getBio()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('profile.html', email=flask_login.current_user.id,
                           pop_tag1=mostUsedTag1(), pop_tag2=mostUsedTag2(), bio=data, p_count=getPhotoCount(),
                           c_count=getCommentCount(),
                           f_count=getFriendCount(), friends=getFriends(), photos=getUsersPhotos(uid),
                           message="Here's your profile")


# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('home.html', message='Welcome to Photoshare')


@app.route('/explore')
def explore():
    if flask_login.current_user.id == "Guest":
        return render_template('explore.html', activity_score=getMostActiveUsers(), pop_tag1=popularTag1(),
                               pop_tag2=popularTag2(),
                               pop_tag3=popularTag3(), pop_tag4=popularTag4(),
                               message='Explore')
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('explore.html', activity_score=getMostActiveUsers(), photos=getUsersPhotos(uid),
                               pop_tag1=popularTag1(), pop_tag2=popularTag2(),
                               pop_tag3=popularTag3(), pop_tag4=popularTag4(), recommendations=getRecommendations(),
                               message='Explore')


@app.route("/albums/", methods=['GET'])
@flask_login.login_required
def get_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('albums.html', albums=getUserAlbums(uid), message='Albums', supress='True')


@app.route("/photos/", methods=['GET'])
@flask_login.login_required
def get_photos():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('photos.html', photos=getUsersPhotos(uid), message='Photos', supress='True')


@app.route("/search", methods=['GET'])
def get_results():
    return render_template('search.html')


# ALBUM METHODS---------------------------------------------------------------------------------------------------------
def getAlbums():
    user = User()
    user.id = flask_login.current_user.id
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Albums WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()


@app.route("/albums/", methods=['POST'])
@flask_login.login_required
def create_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    a_name = request.form.get('a_name')
    if a_name in str(users):
        return render_template('albums.html', name=flask_login.current_user.id, message='Repeated album name!')
    doc = calcCurrent()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Albums (a_name, doc, user_id) VALUES ('{0}', '{1}', '{2}')".format(a_name, doc, uid))
    conn.commit()
    return render_template('albums.html', name=flask_login.current_user.id, message='New album created!',
                           albums=getUserAlbums(uid))


@app.route("/albums/", methods=['DELETE'])
@flask_login.login_required
def delete_album():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    del_name = request.form.get('del_name')
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Albums WHERE user_id = '{0}' AND a_name = '{1}'".format(uid, del_name))
    conn.commit()
    return render_template('albums.html', name=flask_login.current_user.id, message='Album deleted!',
                           albums=getUserAlbums(uid))


# USER METHODS----------------------------------------------------------------------------------------------------------
@login_manager.user_loader
def user_loader(email):
    users = getUserList()
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    users = getUserList()
    email = request.form.get('email')
    if not (email) or email not in str(users):
        return
    user = User()
    user.id = email
    cursor = mysql.connect().cursor()
    cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


# FRIEND METHODS--------------------------------------------------------------------------------------------------------
@flask_login.login_required
def getFriends():
    user = User()
    user.id = flask_login.current_user.id
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT f_email FROM Friends WHERE u_id = '{0}'".format(uid))
    return cursor.fetchone()


@app.route('/explore', methods=['POST'])
@flask_login.login_required
def addFriend():
    user = User()
    user.id = flask_login.current_user.id
    uid = getUserIdFromEmail(flask_login.current_user.id)
    email = request.form.get('f_email')
    if not (email) or email not in str(users):
        return render_template('explore.html', activity_score=getMostActiveUsers(), pop_tag1=popularTag1(),
                               pop_tag2=popularTag2(),
                               pop_tag3=popularTag3(), pop_tag4=popularTag4(), recommendations=getRecommendations(),
                               message='Email not in our database!')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Friends (u_id, f_email) VALUES ('{0}', '{1}')".format(uid, email))
    conn.commit()
    return render_template('profile.html', email=flask_login.current_user.id,
                           pop_tag1=mostUsedTag1(), pop_tag2=mostUsedTag2(), bio=getBio(), p_count=getPhotoCount(),
                           c_count=getCommentCount(),
                           f_count=getFriendCount(), friends=getFriends(), photos=getUsersPhotos(uid), message="Friend added!")


# SEARCH METHODS--------------------------------------------------------------------------------------------------------
@app.route("/search", methods=['GET'])
def searchByTag():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    tag_data = tagSearch()
    if tag_data:
        if flask_login.current_user.id == "Guest":
            return render_template('results.html', results=tag_data, message='Your Search Results')
        else:
            return render_template('results.html', results=tag_data, ownphotos=getUsersPhotos(uid), message='Your Search Results')


@app.route("/search", methods=['GET'])
def searchByAlbum():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    album_data = albumSearch()
    if album_data:
        if flask_login.current_user.id == "Guest":
            return render_template('results.html', results=album_data, message='Your Search Results')
        else:
            return render_template('results.html', results=album_data, ownphotos=getUsersPhotos(uid),
                                   message='Your Search Results')

@app.route("/search", methods=['GET'])
def searchByUser():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    up_data = userSearch()
    if up_data:
        if flask_login.current_user.id == "Guest":
            return render_template('results.html', results = up_data, message='Your Search Results')
        else:
            return render_template('results.html', results=up_data, ownphotos=getUsersPhotos(uid),
                                   message='Your Search Results')


@app.route("/search", methods=['GET'])
@flask_login.login_required
def searchOwnPicturesByTag():
    user = User()
    user.id = flask_login.current_user.id
    uid = getUserIdFromEmail(flask_login.current_user.id)
    query = request.form.get('query1')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT P.imgdata FROM Pictures WHERE tag1 = '{0}' OR tag2 = '{0}' OR tag3 = '{0}' OR tag4 = '{0}' AND user_id = '{1}'".format(
            query, uid))
    conn.commit()
    results = cursor.fetchall()
    return render_template('search.html', email=flask_login.current_user.id, ownphotos=getUsersPhotos(uid), ownsearch = results, message='Your Search Results')

def tagSearch():
    query = request.form.get('query1')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT P.imgdata FROM Pictures WHERE tag = '{0}'".format(query))
    conn.commit()
    return cursor.fetchall()


def albumSearch():
    query = request.form.get('query3')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT P.imgdata FROM Album as A, Picture as P WHERE a_name = VALUES('{0}') AND P.a_id = A.a_id".format(query))
    conn.commit()
    return cursor.fetchall()


def userSearch():
    query = request.form.get('query2')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT P.imgdata FROM Picture as P, Users as U WHERE U.user_id = P.user_id AND U.email = '{0}'".format(query))
    conn.commit()
    return cursor.fetchall()


# AUTHORIZATION (LOGIN/OUT AND REGISTER) METHODS------------------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    # The request method is POST (page is recieving data)
    email = flask.request.form['email']
    cursor = conn.cursor()
    # check if email is registered
    if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = email
            flask_login.login_user(user)  # okay login in user
            return flask.redirect(flask.url_for('protected'))  # protected is a function defined in this file

    # information did not match
    return render_template('home.html', message='That username/password does not match.', supress='True')


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('home.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register/", methods=['GET'])
def register():
    return render_template('register.html', supress='True')


@app.route("/register/", methods=['POST'])
def register_user():
    try:
        email = request.form.get('email')
        print(email)
        password = request.form.get('password')
        hometown = request.form.get('hometown')
        fname = request.form.get('firstname')
        lname = request.form.get('lastname')
        dob = request.form['birthday']
        gender = request.form['gender']

    except:
        print(
            "couldn't find all tokens")  # this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEmailUnique(email)
    if test:
        print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, gender, dob, hometown) "
                             "VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, fname,
                                                                                               lname, gender, dob,
                                                                                               hometown)))
        conn.commit()
        # log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('profile.html', email=flask_login.current_user.id,
                               photos=getUsersPhotos(flask_login.current_user.id),
                               pop_tag1=mostUsedTag1(), pop_tag2=mostUsedTag2(), bio=getBio(), p_count=getPhotoCount(),
                               c_count=getCommentCount(),
                               f_count=getFriendCount(), friends=getFriends(), message="Account Created!")
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))


# GET METHODS-----------------------------------------------------------------------------------------------------------
def getUsersPhotos(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata FROM Pictures WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]


def getUserAlbums(uid):
    cursor = conn.cursor()
    cursor.execute("SELECT a_name, doc FROM Albums WHERE user_id = '{0}'".format(uid))
    return cursor.fetchall()  # NOTE list of tuples, [(imgdata, pid), ...]


def getUserIdFromEmail(email):
    cursor = conn.cursor()
    cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
    try:
        return cursor.fetchone()[0]
    except:
        return None


def getMostActiveUsers():
    cursor = conn.cursor()
    cursor.execute("SELECT p_count + c_count, email FROM Users ORDER BY p_count + c_count DESC LIMIT 5")
    return cursor.fetchall()


@flask_login.login_required
def getRecommendations():
    recTag = mostUsedTag1()
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "Select P.imgdata From Pictures as P, Users as U Where P.tag1 = '{0}' AND P.user_id <> '{1}' LIMIT 6".format(
            recTag, uid))
    conn.commit()
    return cursor.fetchall()


def getAlbumId():
    name = request.form.get('album')
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "Select a_id From Albums as A, Users as U Where A.a_name = '{0}' AND A.user_id = '{1}' LIMIT 6".format(
            name, uid))
    conn.commit()
    return cursor.fetchone()[0]


# PHOTO METHODS---------------------------------------------------------------------------------------------------------
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        album = getAlbumId()
        tag1 = request.form.get('tag1')
        tag2 = request.form.get('tag2')
        tag3 = request.form.get('tag3')
        tag4 = request.form.get('tag4')
        print(caption)
        photo_data = base64.standard_b64encode(imgfile.read()).decode('utf-8')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Pictures (imgdata, user_id, caption, tag1, tag2, tag3, tag4, a_id) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}' )".format(
                photo_data, uid, caption, tag1, tag2, tag3, tag4, album))
        conn.commit()
        cursor.execute("UPDATE Users SET p_count = p_count + 1 WHERE user_id ='{0}'".format(uid))
        conn.commit()
        return render_template('photos.html', message='Photo uploaded!',
                               photos=getUsersPhotos(uid))
    # The method is GET so we return an  HTML form to upload the a photo.
    else:
        uid = getUserIdFromEmail(flask_login.current_user.id)
        return render_template('upload.html', albums=getUserAlbums(uid))


@app.route("/photos/", methods=['DELETE'])
@flask_login.login_required
def delete_photo():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    del_id = request.form.get('del_id')
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Pictures WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, del_id))
    conn.commit()
    return render_template('photos.html', name=flask_login.current_user.id, message='Photo deleted!',
                           photos=getUsersPhotos(uid))


@app.route("/photos/", methods=['POST'])
def comment():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    comment_text = request.form.get('comment_text')
    doc = calcCurrent()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Comments WHERE user_id = '{0}' AND c_text = '{1}' AND c_date = '{2}'".format(uid, comment_text,
                                                                                                  doc))
    conn.commit()
    cursor.execute("UPDATE Users SET c_count = c_count + 1 WHERE user_id ='{0}'".format(uid))
    conn.commit()
    return render_template('photos.html', name=flask_login.current_user.id, photos=getUsersPhotos(uid),
                           message='Comment posted!')


@app.route("/photos/", methods=['POST'])
def like(photo):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if checkLikes() == 'Y':
        return render_template('photos.html', name=flask_login.current_user.id, photos=getUsersPhotos(uid),
                               message='You have already liked this photo!')
    else:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, photo))
        conn.commit()
        cursor.execute("UPDATE Users SET likes = likes + 1 WHERE user_id ='{0}'".format(uid))
        conn.commit()
        cursor.execute("UPDATE Likes SET locked = 'Y' WHERE user_id = '{0}' AND picture_id = '{1}'".format(uid, photo))
        conn.commit()
        return render_template('photos.html', name=flask_login.current_user.id, photos=getUsersPhotos(uid),
                               message='Liked!')


# HELPER METHODS--------------------------------------------------------------------------------------------------------
def calcCurrent():
    return (datetime.datetime.now().strftime("%Y-%m-%d"))


def isEmailUnique(email):
    # use this to check if a email has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
        # this means there are greater than zero entries with that email
        return False
    else:
        return True


def popularTag1():
    cursor = conn.cursor()
    cursor.execute("SELECT tag1 FROM Pictures GROUP BY tag1 ORDER BY COUNT(tag1) DESC LIMIT 1")
    conn.commit()
    return cursor.fetchone()[0]


def popularTag2():
    cursor = conn.cursor()
    cursor.execute("SELECT tag2 FROM Pictures GROUP BY tag2 ORDER BY COUNT(tag2) DESC LIMIT 1")
    conn.commit()
    return cursor.fetchone()[0]


def popularTag3():
    cursor = conn.cursor()
    cursor.execute("SELECT tag3 FROM Pictures GROUP BY tag3 ORDER BY COUNT(tag3) DESC LIMIT 1")
    conn.commit()
    return cursor.fetchone()[0]


def popularTag4():
    cursor = conn.cursor()
    cursor.execute("SELECT tag4 FROM Pictures GROUP BY tag4 ORDER BY COUNT(tag4) DESC LIMIT 1")
    conn.commit()
    return cursor.fetchone()[0]


def mostUsedTag1():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tag1 FROM Pictures WHERE user_id = '{0}' GROUP BY tag1 ORDER BY COUNT(tag1) DESC LIMIT 1".format(uid))
    conn.commit()
    return cursor.fetchone()[0]


def mostUsedTag2():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT tag2 FROM Pictures WHERE user_id = '{0}' GROUP BY tag2 ORDER BY COUNT(tag2) DESC LIMIT 1".format(uid))
    conn.commit()
    return cursor.fetchone()[0]


def getPhotoCount():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT p_count FROM Users WHERE user_id = '{0}'".format(uid))
    conn.commit()
    return cursor.fetchone()[0]


def getCommentCount():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT c_count FROM Users WHERE user_id = '{0}'".format(uid))
    conn.commit()
    return cursor.fetchone()[0]


def getFriendCount():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT Count(f_email) FROM Friends WHERE u_id = '{0}'".format(uid))
    conn.commit()
    return cursor.fetchone()[0]


def getBio():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT first_name, last_name, gender, hometown, dob, email FROM Users WHERE user_id = '{0}'".format(uid))
    conn.commit()
    return cursor.fetchall()


def getLikes(photo):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(L.picture_id) FROM Pictures as P, Likes as L WHERE P.picture_id = '{0}' AND L.picture_id = '{1}' ".format(
            photo, photo))
    conn.commit()
    return cursor.fetchall()


def checkLikes(photo):
    uid = getUserIdFromEmail(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT locked FROM Likes WHERE picture_id = '{0}' AND user_id = '{1}' ".format(photo,
                                                                                        uid))
    conn.commit()
    status = cursor.fetchone()[0]
    return status

def openAlbum(album):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT P.imgdata FROM Album as A, Pictures as P WHERE A.a_name = '{0}' AND P.a_id IN "
        "(SELECT a_id FROM Albums WHERE a_name = '{0}')".format(album, album))
    conn.commit()
    cursor.fetchall()
    return flask.redirect(flask.url_for('photos', album=album))

