import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.username = "johannes"
        self.database_path = f'postgresql://postgres:{self.username}@localhost:5432/{self.database_name}'
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

        self.new_question = {
            "question":"What is this app about?",
            "answer":"Playing a game",
            "difficulty":2,
            "category":1
        }
        self.wrong_format_question = {
            "answer":7,
            "difficulty":2,
            "category":2
        }

        #Add initial data
        new_cat = Category(type="Test")
        new_cat.insert()

        new_q = Question(question="How do you want to test the app?",answer="With Unittest",difficulty=2,category="1") 
        new_q.insert()
        self.test_question_id = new_q.id

        new_q = Question(question="Why am i created?",answer="to be deleted",difficulty=2,category="1") 
        new_q.insert()
        self.delete_question_id = new_q.id
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    Test definitions
    """
    def test_add_question(self):
        res = self.client().post("/questions",json=self.new_question)
        data = json.loads(res.data)
        question = Question.query.filter(Question.id==data["added_question_id"]).one_or_none()

        self.test_question_id = Question.id
        self.assertEqual(res.status_code,200)
        self.assertEqual(data["success"],True)
        self.assertEqual(question.format()["answer"],self.new_question["answer"])
    
    def test_422_add_question(self):
        res = self.client().post("/questions",json=self.wrong_format_question)
        data = json.loads(res.data)
        self.assertEqual(res.status_code,422)
        self.assertEqual(data["success"],False)
        self.assertEqual(data["message"],"Unprocessable entity")

    def test_retrieve_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code,200)
        self.assertEqual(data["success"],True)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(data["total_questions"])

    def test_404_retrieve_questions(self):
        res = self.client().get("/questions?page=1000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code,404)
        self.assertEqual(data["success"],False)
        self.assertEqual(data["message"],"Resource not found")

    def test_get_specific_category(self):
        
        res = self.client().get(f"/categories/1/questions") #/categories/<int:category_id>/questions
        data = json.loads(res.data)
        selection = Question.query.filter(Question.category == "1").all()
    
        self.assertEqual(res.status_code,200)
        self.assertEqual(data["success"],True)
        self.assertTrue(len(data["questions"]))

    def test_404_get_specific_category(self):
        res = self.client().get("/categories/100000/questions")
        data = json.loads(res.data)

        self.assertEqual(res.status_code,404)
        self.assertEqual(data["success"],False)
        self.assertEqual(data["message"],"Resource not found")

    def test_delete_question(self):
        res = self.client().delete(f"/questions/{self.delete_question_id}")
        data = json.loads(res.data)
        question = Question.query.filter(Question.id==self.delete_question_id).one_or_none()

        self.assertEqual(res.status_code,200)
        self.assertEqual(data["success"],True)
        self.assertEqual(data["deleted_question_id"],self.delete_question_id)
        self.assertEqual(question,None)

    def test_404_delete_question(self):
        res = self.client().delete("/questions/1000000")
        data = json.loads(res.data)

        self.assertEqual(res.status_code,404)
        self.assertEqual(data["success"],False)
        self.assertEqual(data["message"],"Resource not found")

    def test_search_question(self):
        res = self.client().post("/questions/search",json={"searchTerm":"app"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code,200)
        self.assertEqual(data["success"],True)
        self.assertTrue(len(data["questions"]))

    def test_400_search_question(self):
        res = self.client().post("/questions/search",json={"nothing":"sksaoamsls"})
        data = json.loads(res.data)

        self.assertEqual(res.status_code,400)
        self.assertEqual(data["success"],False)
        self.assertEqual(data["message"],"Bad request")


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()