# -*- coding: utf-8 -*-
"""
    Hybrid Dile Server
    ~~~~~~~~
    A data tile server
    :copyright: (c) 2016 by Raffaele Montella.
    :license: Apache 2.0, see LICENSE for more details.
"""

import time
import os
from hashlib import md5
from datetime import datetime
from pymongo  import MongoClient
from flask import Flask, request, session, url_for, redirect, jsonify,\
     render_template, abort, g, flash, _app_ctx_stack


# configuration
DATABASE = ''
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

# create our little application :)
app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE='test',
    COLLECTION='netcdf',
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('HYBRID_DILE_SERVER_SETTINGS', silent=True)

@app.teardown_appcontext
def close_database(exception):
    """Closes the database again at the end of the request."""
    top = _app_ctx_stack.top
    if hasattr(top, 'db'):
        top.db.close()


def connect_db():
    """Connects to the specific database."""
    client = MongoClient()
    db = client[app.config['DATABASE']]
    return db

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'db'):
        g.db = connect_db()
    return g.db

def init_db():
    """Initializes the database."""
    db = get_db()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')

@app.route('/')
def index():
    """Shows the home page
    """
    return render_template('layout.html')


@app.route('/discovery/dile/by/position/<float:lon>/<float:lat>')
def discovery_dile_by_position(lon,lat):
    query={}
    return jsonify(query_db(query))

@app.route('/discovery/dile/by/radius/<float:lon>/<float:lat>/<float:radius>')
def discovery_dile_by_range(lon,lat,radius):
    query={}
    return jsonify(query_db(query))

@app.route('/discovery/dile/by/bbox/<float:minLon>/<float:minLat>/<float:maxLon>/<float:maxLat>')
def discovery_dile_by_bbox(minLon,minLat,maxLon,maxLat):
    query= {
    "loc.geometry": {
        "$geoIntersects": {
            "$geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [ minLon, minLat ],
                        [ minLon, maxLat ],
                        [ maxLon, maxLat ],
                        [ maxLon, minLat ],
                        [ minLon, minLat ]
                    ]
                ]
                }
            }
        }
    }
    return jsonify(query_db(query))

def query_db(query):
    features=[]
    db = get_db()
    diles = db['netcdf'].find(query)
    for dile in diles:
        feature={
            "geometry": {
                "coordinates": [
                    [
                        [ -29.8828125, 33.7243396617476 ], 
                        [ -29.8828125, 45.5832897560063 ], 
                        [  -9.84375,   45.5832897560063 ], 
                        [  -9.84375,   33.7243396617476 ], 
                        [ -29.8828125, 33.7243396617476 ]
                    ]
                ], 
                "type": "Polygon"
            }, 
            "properties": {
                "uri": dile['uri']
            }, 
            "type": "Feature"
        }
        features.append(feature)
    result={
        "type": "FeatureCollection",
        "features": features
    }

    return result
