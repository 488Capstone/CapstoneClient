import os

from flask import (
    Flask,
    render_template,
    g
)



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'clientgui.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    #from flask import g
    @app.route('/')
    def first_page ():
        if g.user is None:
            #no user logged in, just show an intro page
            return render_template('first_page.html')
        else:
            return render_template('home.html')


    # initialize the db for this app
    from . import db
    db.init_app(app)

    #from current dir, import auth.py, then register the blueprint with the app
    from . import auth
    from . import main 
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    #DW 2021-09-14 - This doesn't work the way I thought
    #app.add_url_rule('/', endpoint='home')

    return app
