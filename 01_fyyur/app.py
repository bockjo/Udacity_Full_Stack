#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
import pdb
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

#----------------------------------------------------------------------------#
# Models
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    
    return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
def removeDuplicates(lst): 
    return [t for t in (set(tuple(i) for i in lst))] 

@app.route('/venues')
def venues():
  query_data = Venue.query.order_by("id").all()
  locs = [(e.city,e.state) for e in query_data]
  locs = removeDuplicates(locs)
  
  #group-by city and state
  data = []
  for loc in locs:
    interim = {
      "city":loc[0],
      "state":loc[1],
      "venues":[]}

    for e in query_data:
      if (e.city,e.state) == loc:
          interim["venues"].append( {
            "id":e.id,
            "name":e.name,
            "num_upcoming_shows": len(e.shows)
          })
    data.append(interim)
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  search_term=request.form.get('search_term', '')
  q = Venue.query.order_by("id").all()
  data = []
  for e in q:
    if search_term.lower() in e.name.lower():
      data.append({
        "id": e.id,
        "name": e.name,
        "num_upcoming_shows": len([k for k in e.shows if k.start_time > datetime.now()])
      })

  response={
    "count": 1,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  d = Venue.query.get(venue_id)
  past_shows = db.session.query(Artist, Show).join(Show).join(Venue).\
      filter(
          Show.venue_id == venue_id,
          Show.artist_id == Artist.id,
          Show.start_time < datetime.now()
      ).\
      all()
  upcoming_shows = db.session.query(Artist,Show).join(Show).join(Venue).\
    filter(
      Show.venue_id == venue_id,
      Show.artist_id == Artist.id,
      Show.start_time > datetime.now()
    ).\
      all()

  data = {
    "id": d.id,
    "name":d.name,
    "genres": d.genres,
    "address":d.address,
    "city": d.city,
    "state":d.state,
    "phone": d.phone,
    "website":d.website,
    "facebook_link":d.facebook_link,
    "seeking_talent":d.seeking_talent,
    "image_link":d.image_link,
    "past_shows": [{
            'artist_id': artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
        } for artist, show in past_shows],
    "upcoming_shows": [{
      'artist_id': artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for artist, show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
 
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    address = request.form['address']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    seeking_talent = bool(request.form['seeking_talent'])
    seeking_description = request.form['seeking_description']

    el = Venue(name = name, city = city, state = state, address = address, phone = phone, image_link=image_link,
    facebook_link=facebook_link,genres=genres,website=website,seeking_talent=seeking_talent,seeking_description=seeking_description)
    print(el)
    #Add to database
    db.session.add(el)
    db.session.commit()
    #on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    #Rollback in case of error
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    abort(400)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  else:
    return render_template('pages/home.html')
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  #  BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist = Artist.query.order_by("id").all()
  data = []
  for e in artist:
    data.append({
      "id":e.id,
      "name":e.name
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  search_term=request.form.get('search_term', '')
  q = Artist.query.order_by("id").all()
  data = []
  for e in q:
    if search_term.lower() in e.name.lower():
      data.append({
        "id": e.id,
        "name": e.name,
        "num_upcoming_shows": len([k for k in e.shows if k.start_time > datetime.now()])
      })

  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

def fix_json_array(arr):
    if len(arr) > 1 and arr[0] == '{':
        arr = arr[1:-1]
        arr = ''.join(arr).split(",")
        return(arr)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  d = Artist.query.get(artist_id)

  past_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
      filter(
          Show.venue_id == Venue.id,
          Show.artist_id == Artist.id,
          Show.start_time < datetime.now()
      ).\
      all()

  upcoming_shows = db.session.query(Venue, Show).join(Show).join(Artist).\
      filter(
          Show.venue_id == Venue.id,
          Show.artist_id == Artist.id,
          Show.start_time > datetime.now()
      ).\
      all()

  data = {
    "id": d.id,
    "name": d.name,
    "genres": fix_json_array(d.genres),
    "city": d.city,
    "state": d.state,
    "phone": d.phone,
    "website": d.website,
    "facebook_link": d.facebook_link,
    "seeking_venue": d.seeking_venue,
    "seeking_description": d.seeking_description,
    "image_link": d.image_link,
    "past_shows": [{
      "venue_id":venue.id,
      "venue_name":venue.name,
      "venue_image_link":venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for venue, show in past_shows],
    "upcoming_shows": [{
      "venue_id":venue.id,
      "venue_name":venue.name,
      "venue_image_link":venue.image_link,
      "start_time": show.start_time.strftime("%m/%d/%Y, %H:%M")
    } for venue, show in upcoming_shows],
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  d = Artist.query.get(artist_id)
  artist={
    "id": d.id,
    "name": d.name,
    "genres": fix_json_array(d.genres),
    "city": d.city,
    "state": d.state,
    "phone": d.phone,
    "website": d.website,
    "facebook_link": d.facebook_link,
    "seeking_venue": d.seeking_venue,
    "seeking_description": d.seeking_description,
    "image_link": d.image_link
  }

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  a = Artist.query.get(artist_id)
  error = False
  try:
    a.name = request.form['name']
    a.city = request.form['city']
    a.state = request.form['state']
    a.phone = request.form['phone']
    a.image_link = request.form['image_link']
    a.facebook_link = request.form['facebook_link']
    a.genres = request.form.getlist('genres')
    a.website = request.form['website']
    a.seeking_venue = bool(request.form['seeking_venue'])
    a.seeking_description = request.form['seeking_description']
    #Commit to database
    db.session.commit()
    #on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except:
    #Rollback in case of error
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    abort(400)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  else:
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  d = Venue.query.get(venue_id)
  venue={
    "id": d.id,
    "name": d.name,
    "genres": fix_json_array(d.genres),
    "address": d.address,
    "city": d.city,
    "state": d.state,
    "phone": d.phone,
    "website": d.website,
    "facebook_link": d.facebook_link,
    "seeking_talent": d.seeking_talent,
    "seeking_description": d.seeking_description,
    "image_link": d.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # Take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  v = Venue.query.get(venue_id)
  error = False
  try:
    v.name = request.form['name']
    v.city = request.form['city']
    v.state = request.form['state']
    v.address = request.form['address']
    v.phone = request.form['phone']
    v.image_link = request.form['image_link']
    v.facebook_link = request.form['facebook_link']
    v.genres = request.form.getlist('genres')
    v.website = request.form['website']
    v.seeking_talent = bool(request.form['seeking_talent'])
    v.seeking_description = request.form['seeking_description']

    #Commit to database
    db.session.commit()
    #on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    #Rollback in case of error
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    abort(400)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
  else:
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    genres = request.form.getlist('genres')
    website = request.form['website']
    seeking_venue = bool(request.form['seeking_venue'])
    seeking_description = request.form['seeking_description']
    print(request.form.getlist('genres'))

    el = Artist(name = name, city = city, state = state, phone = phone, image_link=image_link,
    facebook_link=facebook_link,genres=genres,website=website,seeking_venue=seeking_venue,seeking_description=seeking_description)
    
    #Add to database
    db.session.add(el)
    db.session.commit()
    #on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    #Rollback in case of error
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    abort(400)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows

  shows = Show.query.order_by("id").all()
  data = []
  for e in shows:
    venue = Venue.query.get(e.venue_id)
    artist = Artist.query.get(e.artist_id)
    data.append({
      "venue_id": e.venue_id,
      "venue_name": venue.name,
      "artist_id": e.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": e.start_time
    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
    venue_id = request.form['venue_id']
    artist_id = request.form['artist_id']
    start_time = request.form['start_time']

    el = Show(venue_id = venue_id , artist_id = artist_id, start_time = start_time)
    
    #Add to database
    db.session.add(el)
    db.session.commit()
    #on successful db insert, flash success
    flash('Show  was successfully listed!')
  except:
    #Rollback in case of error
    db.session.rollback()
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()

  if error:
    abort(400)
    flash('An error occurred. Show could not be listed.')
  else:
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
