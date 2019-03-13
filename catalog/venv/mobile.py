from flask import Flask, render_template, url_for
from flask import request, redirect, flash, make_response, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mobile_dbsetup import Base, MobileStore, MobileVersions, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import datetime

engine = create_engine('sqlite:///mobile.db',
                       connect_args={'check_same_thread': False}, echo=True)
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = "MobileHub"

DBSession = sessionmaker(bind=engine)
session = DBSession()
# Create anti-forgery state token
tbs_cat = session.query(MobileStore).all()

#completed
# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    tbs_cat = session.query(MobileStore).all()
    tbes = session.query(MobileVersions).all()
    return render_template('login.html',
                           STATE=state, tbs_cat=tbs_cat, tbes=tbes)
    # return render_template('myhome.html', STATE=state
    # tbs_cat=tbs_cat,tbes=tbes)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px; border-radius: 150px;'
    '-webkit-border-radius: 150px; -moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output


# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception as e:
        print(e)
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session

#completed
# Home
@app.route('/')
def home():
    tbs_cat = session.query(MobileStore).all()
    return render_template('myhome.html', tbs_cat=tbs_cat)

#completed
# Book Category for admins
@app.route('/mobileStore')
def Mobilestore():
    try:
        if login_session['username']:
            name = login_session['username']
            tbs_cat = session.query(MobileStore).all()
            tbs = session.query(MobileStore).all()
            tbes = session.query(MobileVersions).all()
            return render_template('myhome.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes, uname=name)
    except:
        return redirect(url_for('showLogin'))

#completed
# Showing books based on book category
@app.route('/mobileStore/<int:tbid>/AllMobiles')
def showMobiles(tbid):
    tbs_cat = session.query(MobileStore).all()
    tbs = session.query(MobileStore).filter_by(id=tbid).one()
    tbes = session.query(MobileVersions).filter_by(mobilestoreid=tbid).all()
    try:
        if login_session['username']:
            return render_template('showMobiles.html', tbs_cat=tbs_cat,
                                   tbs=tbs, tbes=tbes,
                                   uname=login_session['username'])
    except:
        return render_template('showMobiles.html',tbs_cat=tbs_cat, tbs=tbs, tbes=tbes)
#completed
# Add New Book
@app.route('/mobileStore/addMobile', methods=['POST', 'GET'])
def addMobile():
    if request.method == 'POST':
        newbook = MobileStore(name=request.form['name'],
                           user_id=login_session['user_id'])
        session.add(newbook)
        session.commit()
        return redirect(url_for('Mobilestore'))
    else:
        return render_template('addMobile.html', tbs_cat=tbs_cat)
#completed

# Edit Book Category
@app.route('/mobileStore/<int:tbid>/edit', methods=['POST', 'GET'])
def editMobileCategory(tbid):
    editmobile = session.query(MobileStore).filter_by(id=tbid).one()
    creator = getUserInfo(editmobile.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Mobile Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('mobileStore'))
    if request.method == "POST":
        if request.form['name']:
            editmobile.name = request.form['name']
        session.add(editmobile)
        session.commit()
        flash("Mobile Category Edited Successfully")
        return redirect(url_for('Mobilestore'))
    else:
        # tbs_cat is global variable we can them in entire application
        return render_template('editMobileCategory.html',
                               tb=editmobile, tbs_cat=tbs_cat)


# Delete Book Category
@app.route('/mobileStore/<int:tbid>/delete', methods=['POST', 'GET'])
def deleteMobileCategory(tbid):
    tb = session.query(MobileStore).filter_by(id=tbid).one()
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Mobile Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('Mobilestore'))
    if request.method == "POST":
        session.delete(tb)
        session.commit()
        flash("Mobile Category Deleted Successfully")
        return redirect(url_for('Mobilestore'))
    else:
        return render_template('deleteMobileCategory.html', tb=tb, tbs_cat=tbs_cat)


# Add New Book Edition Details
@app.route('/mobileStore/addMobile/addMobileDetails/<string:tbname>/add',
           methods=['GET', 'POST'])
def addMobileDetails(tbname):
    tbs = session.query(MobileStore).filter_by(name=tbname).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(tbs.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new Mobile"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showMobiles', tbid=tbs.id))
    if  request.method == 'POST':
        name = request.form['name']
        price= request.form['price']
        edition = request.form['edition']
        specifications= request.form['specifications']
        color=request.form['color']
        rating = request.form['rating']
        mobiledetails = MobileVersions(name=name, price=price,
                              edition=edition, specifications=specifications,
                              color=color,
                              rating=rating,
                              mobilestoreid=tbs.id,
                              user_id=login_session['user_id'])
        
        session.add(mobiledetails)
        session.commit()
        return redirect(url_for('showMobiles', tbid=tbs.id))
    else:
        return render_template('addMobileDetails.html',
                               tbname=tbs.name, tbs_cat=tbs_cat)


# Edit Book Edition
@app.route('/mobileStore/<int:tbid>/<string:tbename>/edit',
           methods=['GET', 'POST'])
def editMobile(tbid, tbename):
    tb = session.query(MobileStore).filter_by(id=tbid).one()
    mobiledetails = session.query(MobieVersions).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this  Mobile"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showMobiles', tbid=tb.id))
    # POST methods
    if request.method == 'POST':
        mobiledetails.name = request.form['name']
        mobiledetails.price = request.form['price']
        mobiledetails.edition = request.form['edition']
        mobiledetails.specifications = request.form['specifications']
        mobiledetails.color = request.form['color']
        mobiledetails.rating = request.form['rating']
        session.add(mobiledetails)
        session.commit()
        flash("Mobile Edited Successfully")
        return redirect(url_for('showMobiles', tbid=tbid))
    else:
        return render_template('editMobile.html',
                               tbid=tbid, mobiledetails=mobiledetails, tbs_cat=tbs_cat)


# Delte Book Editon
@app.route('/mobileStore/<int:tbid>/<string:tbename>/delete',
           methods=['GET', 'POST'])
def deleteMobile(tbid, tbename):
    tb = session.query(MobileStore).filter_by(id=tbid).one()
    mobiledetails = session.query(MobileVersions).filter_by(name=tbename).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(tb.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this Mobile"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showMobiles', tbid=tb.id))
    if request.method == "POST":
        session.delete(mobiledetails)
        session.commit()
        flash("Deleted Mobile Successfully")
        return redirect(url_for('showMobiles', tbid=tbid))
    else:
        return render_template('deleteMobile.html',
                               tbid=tbid, mobiledetails=mobiledetails, tbs_cat=tbs_cat)


# Logout
@app.route('/logout')
def logout():
    access_token = login_session['access_token']
    print ('In gdisconnect access token is %s', access_token)
    print ('User name is: ')
    print (login_session['username'])
    if access_token is None:
        print ('Access Token is None')
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = login_session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = \
        h.request(uri=url, method='POST', body=None,
                  headers={'content-type': 'application/x-www-form-urlencoded'})[0]

    print (result['status'])
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("Successfully logged out")
        return redirect(url_for('showLogin'))
        # return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Json
@app.route('/Mobile/JSON')
def allMobilesJSON():
    mobile = session.query(MobileStore).all()
    category_dict = [c.serialize for c in mobile]
    for c in range(len(category_dict)):
        mobiles = [i.serialize for i in session.query(
                 MobileVersions).filter_by(mobilestoreid=category_dict[c]["id"]).all()]
        if mobiles:
            category_dict[c]["mobile"] = mobiles
    return jsonify(MobileStore=category_dict)


@app.route('/Mobile/mobile/JSON')
def categoriesJSON():
    mobiles = session.query(MobileStore).all()
    return jsonify(mobile=[c.serialize for c in mobiles])


@app.route('/Mobile/mobile/JSON')
def itemsJSON():
    mobiles = session.query(MobileVersions).all()
    return jsonify(editions=[i.serialize for i in mobiles])


@app.route('/mobileStore/<path:mobile_name>/mobile/JSON')
def categoryItemsJSON(mobile_name):
    mobile= session.query(MobileStore).filter_by(name=mobile_name).one()
    items = session.query(MobileVersions).filter_by(item=mobile).all()
    return jsonify(mobileEdtion=[i.serialize for i in items])


@app.route('/mobileStore/<path:mobile_name>/<path:edition_name>/JSON')
def ItemJSON(mobile_name, edition_name):
    mobileCategory = session.query(MobileStore).filter_by(name=mobile_name).one()
    mobileEdition = session.query(MobileVersions).filter_by(
           name=edition_name, mobilestore=mobileCategory).one()
    return jsonify(mobileEdition=[mobileEdition.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.run(debug='true', port=8888)
