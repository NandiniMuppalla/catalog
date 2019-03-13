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
mcs_hub = session.query(MobileStore).all()


# login
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    mcs_hub = session.query(MobileStore).all()
    mcvs = session.query(MobileVersions).all()
    return render_template('login.html',
                           STATE=state, mcs_hub=mcs_hub, mcvs=mcvs)
    # return render_template('myhome.html', STATE=state
    # mcs_hub=mcs_hub,mcvs=mcvs)


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


@app.route('/')
def home():
    mcs_hub = session.query(MobileStore).all()
    return render_template('myhome.html', mcs_hub=mcs_hub)


# Book Category for admins
@app.route('/mobileStore')
def Mobilestore():
    try:
        if login_session['username']:
            name = login_session['username']
            mcs_hub = session.query(MobileStore).all()
            mcs = session.query(MobileStore).all()
            mcvs = session.query(MobileVersions).all()
            return render_template('myhome.html', mcs_hub=mcs_hub,
                                   mcs=mcs, mcvs=mcvs, uname=name)
    except:
        return redirect(url_for('showLogin'))


# Showing mobiles based on mobile category
@app.route('/mobileStore/<int:mcid>/AllMobiles')
def showMobiles(mcid):
    mcs_hub = session.query(MobileStore).all()
    mcs = session.query(MobileStore).filter_by(id=mcid).one()
    mcvs = session.query(MobileVersions).filter_by(mobilestoreid=mcid).all()
    try:
        if login_session['username']:
            return render_template('showMobiles.html', mcs_hub=mcs_hub,
                                   mcs=mcs, mcvs=mcvs,
                                   uname=login_session['username'])
    except:
        return render_template(
            'showMobiles.html', mcs_hub=mcs_hub, mcs=mcs, mcvs=mcvs)


# Add New mobile
@app.route('/mobileStore/addMobile', methods=['POST', 'GET'])
def addMobile():
    if request.method == 'POST':
        newMobile = MobileStore(
            name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(newMobile)
        session.commit()
        return redirect(url_for('Mobilestore'))
    else:
        return render_template('addMobile.html', mcs_hub=mcs_hub)


# Edit mobile Category
@app.route('/mobileStore/<int:mcid>/edit', methods=['POST', 'GET'])
def editMobileCategory(mcid):
    editmobile = session.query(MobileStore).filter_by(id=mcid).one()
    creator = getUserInfo(editmobile.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot edit this Mobile Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('Mobilestore'))
    if request.method == "POST":
        if request.form['name']:
            editmobile.name = request.form['name']
        session.add(editmobile)
        session.commit()
        flash("Mobile Category Edited Successfully")
        return redirect(url_for('Mobilestore'))
    else:
        # mcs_hub is global variable we can them in entire application
        return render_template('editMobileCategory.html',
                               mc=editmobile, mcs_hub=mcs_hub)


# Delete mobile Category
@app.route('/mobileStore/<int:mcid>/delete', methods=['POST', 'GET'])
def deleteMobileCategory(mcid):
    mc = session.query(MobileStore).filter_by(id=mcid).one()
    creator = getUserInfo(mc.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You cannot Delete this Mobile Category."
              "This is belongs to %s" % creator.name)
        return redirect(url_for('Mobilestore'))
    if request.method == "POST":
        session.delete(mc)
        session.commit()
        flash("Mobile Category Deleted Successfully")
        return redirect(url_for('Mobilestore'))
    else:
        return render_template(
            'deleteMobileCategory.html', mc=mc, mcs_hub=mcs_hub)


# Add New mobile version Details
@app.route('/mobileStore/addMobile/addMobileDetails/<string:mcname>/add',
           methods=['GET', 'POST'])
def addMobileDetails(mcname):
    mcs = session.query(MobileStore).filter_by(name=mcname).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(mcs.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't add new Mobile"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showMobiles', mcid=mcs.id))
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        edition = request.form['edition']
        specifications = request.form['specifications']
        color = request.form['color']
        rating = request.form['rating']
        mobiledetails = MobileVersions(
                              name=name, price=price,
                              edition=edition, specifications=specifications,
                              color=color,
                              rating=rating,
                              mobilestoreid=mcs.id,
                              user_id=login_session['user_id'])

        session.add(mobiledetails)
        session.commit()
        return redirect(url_for('showMobiles', mcid=mcs.id))
    else:
        return render_template('addMobileDetails.html',
                               mcname=mcs.name, mcs_hub=mcs_hub)


# Edit mobile version
@app.route('/mobileStore/<int:mcid>/<string:mcvname>/edit',
           methods=['GET', 'POST'])
def editMobile(mcid, mcvname):
    mc = session.query(MobileStore).filter_by(id=mcid).one()
    mobiledetails = session.query(MobileVersions).filter_by(name=mcvname).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(mc.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't edit this  Mobile"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showMobiles', mcid=mc.id))
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
        return redirect(url_for('showMobiles', mcid=mcid))
    else:
        return render_template('editMobile.html',
                               mcid=mcid, mobiledetails=mobiledetails,
                               mcs_hub=mcs_hub)


# Delte mobile version
@app.route('/mobileStore/<int:mcid>/<string:mcvname>/delete',
           methods=['GET', 'POST'])
def deleteMobile(mcid, mcvname):
    mc = session.query(MobileStore).filter_by(id=mcid).one()
    mobiledetails = session.query(MobileVersions).filter_by(name=mcvname).one()
    # See if the logged in user is not the owner of book
    creator = getUserInfo(mc.user_id)
    user = getUserInfo(login_session['user_id'])
    # If logged in user != item owner redirect them
    if creator.id != login_session['user_id']:
        flash("You can't delete this Mobile"
              "This is belongs to %s" % creator.name)
        return redirect(url_for('showMobiles', mcid=mc.id))
    if request.method == "POST":
        session.delete(mobiledetails)
        session.commit()
        flash("Deleted Mobiles Successfully")
        return redirect(url_for('showMobiles', mcid=mcid))
    else:
        return render_template('deleteMobiles.html',
                               mcid=mcid, mobiledetails=mobiledetails,
                               mcs_hub=mcs_hub)


# Logout from the session
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
                  headers={
                          'content-type':
                          'application/x-www-form-urlencoded'})[0]

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
@app.route('/mobileStore/JSON')
def allMobilesJSON():
    mobile = session.query(MobileStore).all()
    category_dict = [c.serialize for c in mobile]
    for c in range(len(category_dict)):
        mobiles = [i.serialize for i in session.query(
                 MobileVersions).filter_by(
                mobilestoreid=category_dict[c]["id"]).all()]
        if mobiles:
            category_dict[c]["mobile"] = mobiles
    return jsonify(MobileStore=category_dict)


@app.route('/mobileStore/mobile/JSON')
def categoriesJSON():
    mobiles = session.query(MobileStore).all()
    return jsonify(mobile=[c.serialize for c in mobiles])


@app.route('/mobileStore/mob/JSON')
def itemsJSON():
    mobiles = session.query(MobileVersions).all()
    return jsonify(mobiles=[i.serialize for i in mobiles])


@app.route('/mobileStore/<path:mobile_name>/mobile/JSON')
def categoryItemsJSON(mobile_name):
    mobile = session.query(MobileStore).filter_by(name=mobile_name).one()
    item = session.query(MobileVersions).filter_by(mobilestore=mobile).all()
    return jsonify(mobileEdtion=[i.serialize for i in item])


@app.route('/mobileStore/<path:mobile_name>/<path:edition_name>/JSON')
def ItemJSON(mobile_name, edition_name):
    mobileCategory = session.query(MobileStore).filter_by(name=mobile_name).one()
    mobileEdition = session.query(MobileVersions).filter_by(
           name=edition_name, mobilestore=mobileCategory).one()
    return jsonify(mobileEdition=[mobileEdition.serialize])

if __name__ == '__main__':
    app.secret_key = "super_secret_key"
    app.run(debug='true', port=8899)
