import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

#db_drop_and_create_all()

# CORS Headers 
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE')
    return response

## HELPER
def paginate(request,selection,items_per_page):
    page = request.args.get('page', 1, type=int)
    start = (page-1)*items_per_page
    end = start + items_per_page
    elements = [el.format() for el in selection]
    current_elements = elements[start:end]
    return(current_elements)

## ROUTES 
@app.route('/drinks',methods = ["GET"])
def get_drinks():
    drinks = Drink.query.order_by("id").all()
    if len(drinks)==0:
        abort(404)
    
    return(jsonify({
        "success":True,
        "drinks": [e.short() for e in drinks]
    }))

@app.route('/drinks-detail',methods = ["GET"])
@requires_auth(permission='get:drinks-detail')
def get_detailed_drinks():
    drinks = Drink.query.order_by("id").all()
    if len(drinks)==0:
        abort(404)
    
    return(jsonify({
        "success":True,
        "drinks": [e.long() for e in drinks]
    }))

@app.route('/drinks',methods = ["POST"])
@requires_auth(permission='post:drinks')
def add_new_drink():
    body = request.get_json()
    try:
        req_title = body.get("title",None)
        req_recipe = str(body.get("recipe",None))
        req_recipe = req_recipe.replace("\'", "\"")
        drink = Drink(title=req_title, recipe=req_recipe)
        drink.insert()  
    except:
        abort(422)
    
    return(jsonify({
        "success":True,
        "drinks": drink.long()
    }))

@app.route('/drinks/<id>',methods = ["PATCH"])
@requires_auth(permission='patch:drinks')
def update_drink(id):
    body = request.get_json()
    req_title = body.get("title",None)
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        drink.title = req_title
        drink.update()
    except:
        abort(404)

    return(jsonify({
        "success":True,
        "drinks": drink.long()
    }))

@app.route('/drinks/<id>',methods = ["DELETE"])
@requires_auth(permission='delete:drinks')
def delete_drink(id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        drink.delete()
    except:
        abort(404)

    return(jsonify({
        "success":True,
        "delete": drink.id
    }))


## Error Handling
@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False, 
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

@app.errorhandler(404)
def not_found(error):
    return (jsonify({
        "success": False, 
        "error": 404,
        "message": "Resource not found"
        }), 404)

@app.errorhandler(400)
def bad_request(error):
    return (jsonify({
        "success": False, 
        "error": 400,
        "message": "Bad request"
        }), 400)

@app.errorhandler(500)
def server_error(error):
    return (jsonify({
        "success": False, 
        "error": 500,
        "message": "Internal server error"
        }), 500)


@app.errorhandler(AuthError)
def auth_error(error):
    return (jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code)