#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from sqlalchemy import func, and_, or_
from logging import Formatter, FileHandler
from flask_wtf import Form
from flask_migrate import Migrate
from datetime import date
from forms import *
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
#connect to a local postgresql database
app.config.from_object('config')
db = SQLAlchemy(app, session_options={"expire_on_commit": False})

## initialize of Migrations
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.String(5))
    seeking_description = db.Column(db.String(120))

    def __repr__(self):
      return f'<Id: {self.id} Name: {self.name} Genres {self.genres}>'

class Artist(db.Model):
    __tablename__ = 'Artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    address = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.String(5))
    seeking_description = db.Column(db.String(120))

class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, foreign_key=True)
    venue_id = db.Column(db.Integer, foreign_key=True)
    start_time = db.Column(db.DateTime)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
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

@app.route('/venues')
def venues():
  data = []
  # real venues data.
  # num_shows should be aggregated based on number of upcoming shows per venue.
  try:
    allLocations = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    for location in allLocations:
      obj = {}
      obj['venues'] = []
      obj['city'] = location[0]
      obj['state'] = location[1]
      venues = db.session.query(Venue.id, Venue.name).filter(Venue.city.like(obj['city']), Venue.state.like(obj['state'])).all()
      for venue in venues:
        venueObj = {}
        venueObj['id'] = venue[0]
        venueObj['name'] = venue[1]
        venueObj['num_upcoming_shows'] = db.session.query(func.count(Show.id)).filter(and_(Show.venue_id == venue[0], Show.start_time > date.today())).all()[0][0]
        obj['venues'].append(venueObj)
      data.append(obj);
  finally:
    db.session.close();

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  response = {}
  try:
    data = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike('%' + request.form.get('search_term', '') + '%')).all()
    response["count"] = len(data)
    response["data"] = []
    for venue in data:
      venueObj = {}
      venueObj["id"] = venue.id
      venueObj["name"] = venue.name
      venueObj["num_upcoming_shows"] = db.session.query(func.count(Show.id)).filter(Show.venue_id == venue.id, Show.start_time > date.today()).all()[0][0]
      response["data"].append(venueObj)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  data = {}
  try:
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    data["id"] = venue.id
    data["name"] = venue.name
    data["genres"] = venue.genres.replace('{', '').replace('}', '').split(",")
    data["address"] = venue.address
    data["city"] = venue.city
    data["state"] = venue.state
    data["phone"] = venue.phone
    data["website"] = venue.website
    data["seeking_talent"] = venue.seeking_talent
    data["seeking_description"] = venue.seeking_description
    data["facebook_link"] = venue.facebook_link
    data["image_link"] = venue.image_link

    data["past_shows"] = []
    shows = db.session.query(Show.artist_id.label('artist_id'), Artist.name.label('artist_name'), Artist.image_link.label("artist_image_link"), Show.start_time.label("start_time")).join(Artist, Artist.id == Show.artist_id).filter(Show.start_time < date.today(), Show.venue_id == venue_id).all()
    for show in shows:
      showObj = {}
      showObj["artist_id"] = show.artist_id
      showObj["artist_name"] = show.artist_name
      showObj["artist_image_link"] = show.artist_image_link
      showObj["start_time"] = datetime.strftime(show.start_time,"%Y-%m-%d %H:%M")
      data["past_shows"].append(showObj)


    data["upcoming_shows"] = []
    shows = db.session.query(Show.artist_id.label('artist_id'), Artist.name.label('artist_name'), Artist.image_link.label("artist_image_link"), Show.start_time.label("start_time")).join(Artist, Artist.id == Show.artist_id).filter(Show.start_time > date.today(), Show.venue_id == venue_id).all()
    for show in shows:
      showObj = {}
      showObj["artist_id"] = show.artist_id
      showObj["artist_name"] = show.artist_name
      showObj["artist_image_link"] = show.artist_image_link
      showObj["start_time"] = datetime.strftime(show.start_time,"%Y-%m-%d %H:%M")
      data["upcoming_shows"].append(showObj)

    data["past_shows_count"] = db.session.query(func.count(Show.id)).filter(and_(Show.venue_id == venue_id, Show.start_time < date.today())).all()[0][0]
    data["upcoming_shows_count"] = db.session.query(func.count(Show.id)).filter(and_(Show.venue_id == venue_id, Show.start_time > date.today())).all()[0][0]
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

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
    new_venue = Venue(name = request.form['name'], 
                      city = request.form['city'], 
                      state = request.form['state'], 
                      address = request.form['address'],
                      phone = request.form['phone'], 
                      image_link = request.form['image_link'],
                      facebook_link = request.form['facebook_link'], 
                      genres = request.form.getlist('genres'), 
                      website = request.form['website'],
                      seeking_talent = request.form['seeking_talent'],
                      seeking_description = request.form['seeking_description']
                     )
    #insert form data as a new Venue record in the db
    db.session.add(new_venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    if error:
      # on unsuccessful db insert, flash error
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  venue = {}
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    if error:
          # on unsuccessful db insert, flash error
      flash('An error occurred. Venue could not be deleted!')
    else:
      # on successful db insert, flash success
      flash('Venue was successfully deleted!')
    db.session.close

  return redirect(url_for("index"))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  try:
    data = db.session.query(Artist.id, Artist.name).all() 
  finally:
    db.session.close()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  response = {}
  try:
    data = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike('%' + request.form.get('search_term', '') + '%')).all()
    response["count"] = len(data)
    response["data"] = []
    for artist in data:
      artistObj = {}
      artistObj["id"] = artist.id
      artistObj["name"] = artist.name
      artistObj["num_upcoming_shows"] = db.session.query(func.count(Show.id)).filter(Show.artist_id == artist.id, Show.start_time > date.today()).all()[0][0]
      response["data"].append(artistObj)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given artist_id
  data = {}
  try:
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    data["id"] = artist.id
    data["name"] = artist.name
    data["genres"] = artist.genres.replace('{', '').replace('}', '').split(",")
    data["address"] = artist.address
    data["city"] = artist.city
    data["state"] = artist.state
    data["phone"] = artist.phone
    data["website"] = artist.website
    data["seeking_venue"] = artist.seeking_venue
    data["seeking_description"] = artist.seeking_description
    data["facebook_link"] = artist.facebook_link
    data["image_link"] = artist.image_link

    data["past_shows"] = []
    shows = db.session.query(Show.venue_id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label("venue_image_link"), Show.start_time.label("start_time")).join(Venue, Venue.id == Show.venue_id).filter(Show.start_time < date.today(), Show.artist_id == artist_id).all()
    for show in shows:
      showObj = {}
      showObj["venue_id"] = show.venue_id
      showObj["venue_name"] = show.venue_name
      showObj["venue_image_link"] = show.venue_image_link
      showObj["start_time"] = datetime.strftime(show.start_time,"%Y-%m-%d %H:%M")
      data["past_shows"].append(showObj)

    data["upcoming_shows"] = []
    shows = db.session.query(Show.venue_id.label('venue_id'), Venue.name.label('venue_name'), Venue.image_link.label("venue_image_link"), Show.start_time.label("start_time")).join(Venue, Venue.id == Show.venue_id).filter(Show.start_time > date.today(), Show.artist_id == artist_id).all()
    for show in shows:
      showObj = {}
      showObj["venue_id"] = show.venue_id
      showObj["venue_name"] = show.venue_name
      showObj["venue_image_link"] = show.venue_image_link
      showObj["start_time"] = datetime.strftime(show.start_time,"%Y-%m-%d %H:%M")
      data["upcoming_shows"].append(showObj)

    data["past_shows_count"] = db.session.query(func.count(Show.id)).filter(and_(Show.artist_id == artist_id, Show.start_time < date.today())).all()[0][0]
    data["upcoming_shows_count"] = db.session.query(func.count(Show.id)).filter(and_(Show.artist_id == artist_id, Show.start_time > date.today())).all()[0][0]
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = {}
  try:
    artist = db.session.query(Artist).filter(Artist.id == artist_id).first()
    db.session.commit()
  finally:
    db.session.close()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.address = request.form['address']
    artist.phone = request.form['phone']
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.genres = request.form.getlist('genres') 
    artist.website = request.form['website']
    artist.seeking_venue = request.form['seeking_venue']
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    if error:
      # on unsuccessful db update, flash error
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    else:
      # on successful db update, flash success
      flash('Artist ' + request.form['name'] + ' was successfully updated!')
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = {}
  try:
    venue = db.session.query(Venue).filter(Venue.id == venue_id).first()
    db.session.commit()
  finally:
    db.session.close()

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form.getlist('genres') 
    venue.website = request.form['website']
    venue.seeking_talent = request.form['seeking_talent']
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    if error:
      # on unsuccessful db update, flash error
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    else:
      # on successful db update, flash success
      flash('Venue ' + request.form['name'] + ' was successfully updated!')
    db.session.close()

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
    new_artist = Artist(name = request.form['name'], 
                        city = request.form['city'], 
                        state = request.form['state'], 
                        phone = request.form['phone'], 
                        facebook_link = request.form['facebook_link'], 
                        genres = request.form['genres'], 
                        image_link = request.form['image_link'],
                        website = request.form['website'],
                        seeking_venue = request.form['seeking_venue'],
                        seeking_description = request.form['seeking_description'])
    #insert form data as a new Artist record in the db
    db.session.add(new_artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    if error:
      # on unsuccessful db insert, flash error
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # num_shows should be aggregated based on number of upcoming shows per venue.
  data = [];
  try:
    shows = (db.session.query(Show.venue_id, Venue.name, Show.artist_id, Artist.name, Artist.image_link, Show.start_time).join(Venue, Venue.id == Show.venue_id).join(Artist, Artist.id == Show.artist_id).filter(Show.start_time > date.today()).all())
    for show in shows:
        showObj = {}
        showObj['venue_id'] = show[0]
        showObj['venue_name'] = show[1]
        showObj['artist_id'] = show[2]
        showObj['artist_name'] = show[3]
        showObj['artist_image_link'] = show[4]
        showObj['start_time'] = datetime.strftime(show[5],"%Y-%m-%d %H:%M")
        data.append(showObj)
  finally:
    db.session.close()

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
    new_show = Show(venue_id = request.form['venue_id'], 
                    artist_id = request.form['artist_id'], 
                    start_time = format_datetime(request.form['start_time']))
    #insert form data as a new Venue record in the db
    db.session.add(new_show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    if error:
      # on unsuccessful db insert, flash error
      flash('An error occurred. Show could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Show was successfully listed!')
    db.session.close()
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
