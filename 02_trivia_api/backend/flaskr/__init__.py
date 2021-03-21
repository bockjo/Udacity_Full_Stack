import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate(request,selection,items_per_page):
    page = request.args.get('page', 1, type=int)
    start = (page-1)*items_per_page
    end = start + items_per_page
    elements = [el.format() for el in selection]
    current_elements = elements[start:end]
    return(current_elements)

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  cors = CORS(app)#, resources={r"*": {"origins": "*"}})

  # CORS Headers 
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,POST,DELETE')
      return response

  @app.route('/categories',methods = ["GET"])
  def retrieve_categories():
      categories = Category.query.order_by("id").all()
      if len(categories)==0:
          abort(404)
      
      return(jsonify({
          "success":True,
          "categories": {category.id: category.type for category in categories}
      }))


  '''
  @TODO: 
  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route("/questions",methods = ["GET"])
  def retrieve_questions():
    selection = Question.query.order_by("id").all()
    current_questions = paginate(request,selection,QUESTIONS_PER_PAGE)
    categories = Category.query.order_by("id").all()

    if len(current_questions)==0:
      abort(404)
    
    return(jsonify({
        "success":True,
        "questions":current_questions,
        "total_questions":len(selection),
        "categories":{category.id: category.type for category in categories},
        "current_category":None
    }))
  
  @app.route("/categories/<int:category_id>/questions",methods = ["GET"])
  def retrieve_question(category_id):
    categories = Category.query.order_by("id").all()
    categories = {category.id:category.type  for category in categories}

    selection = Question.query.filter(Question.category == category_id).all()
    current_questions = paginate(request,selection,QUESTIONS_PER_PAGE)
    
    if len(current_questions)==0:
      abort(404)
    
    return(jsonify({
        "success":True,
        "questions":current_questions,
        "total_questions":len(selection),
        "categories":categories,
        "current_category":categories[category_id]
    }))

  '''
  @TODO: 
  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  @app.route("/questions/<int:question_id>",methods = ["DELETE"])
  def delete_question(question_id):
    selection = Question.query.filter(Question.id == question_id).one_or_none()

    if selection is None:
      abort(404)
    selection.delete()
    
    return(jsonify({
        "success":True,
        "deleted_question_id":selection.id,
        "deleted_question":selection.question
    }))

  '''
  @TODO: 
  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route("/questions",methods = ["POST"])
  def add_question():
    body = request.get_json()

    question = body.get("question", None)
    answer = body.get("answer",None)
    difficulty = int(body.get("difficulty",None))
    category = int(body.get("category",None))
    
    try:
      new_q = Question(question=question,answer=answer,difficulty=difficulty,category=category) 
      new_q.insert()  
    except:
      abort(422)
  
    return(jsonify({
        "success":True,
        "added_question_id":new_q.id,
        "added_question":new_q.question
    }))

  '''
  @TODO: 
  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route("/questions/search",methods = ["POST"])
  def search_question():
    body = request.get_json()
    search_term = body.get("searchTerm",None)

    selection = Question.query.filter(Question.question.ilike(f"%{search_term}%")).all()
    current_questions = paginate(request,selection,QUESTIONS_PER_PAGE)

    if selection is None:
      abort(404)

    return(jsonify({
        "success":True,
        "questions":current_questions,
        "total_questions":len(selection),
        "current_category":None
    }))

  '''
  @TODO: 
  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route("/quizzes",methods = ["POST"])
  def play_quiz():

    #try:
    #Get parameters
    body = request.get_json()
    previous_questions = body.get("previous_questions",None)
    category = body.get("quiz_category",None)

    #Retrieve all questions from the given category that are not in previous_questions
    if category['type'] == 'click':
      available_questions = Question.query.filter(
          Question.id.notin_((previous_questions))).all()
    else:
      available_questions = Question.query.filter_by(
          category=category['id']).filter(Question.id.notin_((previous_questions))).all()
    #Return random question
    print(available_questions)
    if available_questions:
      idx = random.randrange(len(available_questions))
      return(jsonify({
            "success":True,
            "question":available_questions[idx].format()
            }))
    else:
      abort(422)
      

  '''
  Error handlers
  '''
  @app.errorhandler(404)
  def not_found(error):
      return (jsonify({
          "success": False, 
          "error": 404,
          "message": "Resource not found"
          }), 404)
  
  @app.errorhandler(422)
  def unprocessable(error):
      return (jsonify({
          "success": False, 
          "error": 422,
          "message": "Unprocessable entity"
          }), 422)

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
  
  
  return app

    