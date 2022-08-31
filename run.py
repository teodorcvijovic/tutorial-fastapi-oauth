import os
from pathlib import Path

import uvicorn
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi import Request
from starlette import status
from starlette.config import Config
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.responses import RedirectResponse

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Create the APP
app = FastAPI()

ALLOWED_HOSTS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth settings
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET') or None
if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Set up the middleware to read the request session
SECRET_KEY = os.getenv('SECRET_KEY') or None
if SECRET_KEY is None:
    raise 'Missing SECRET_KEY'
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

FRONTEND_URL = os.getenv('FRONTEND_URL') or 'http://127.0.0.1:8080/token'

# PART 1

# @app.get('/')
# def public(request: Request):
#     user = request.session.get('user')
#     if user:
#         name = user.get('name')
#         return HTMLResponse(f'<p>Hello {name}!</p><a href=/logout>Logout</a>')
#     return HTMLResponse('<a href=/login>Login</a>')
#
#
# @app.route('/logout')
# async def logout(request: Request):
#     request.session.pop('user', None)
#     return RedirectResponse(url='/')
#
#
# @app.route('/login')
# async def login(request: Request):
#     redirect_uri = request.url_for('auth')  # This creates the url for our /auth endpoint
#     return await oauth.google.authorize_redirect(request, redirect_uri)
#
#
# @app.route('/auth')
# async def auth(request: Request):
#     try:
#         access_token = await oauth.google.authorize_access_token(request)
#     except OAuthError:
#         return RedirectResponse(url='/')
#     user_data = await oauth.google.parse_id_token(request, access_token)
#     request.session['user'] = dict(user_data)
#     return RedirectResponse(url='/')


# PART 2

@app.get('/')
async def root():
    return HTMLResponse('<body><a href="/login">Log In</a></body>')


# @app.get('/token')
# async def token(request: Request):
#     return HTMLResponse('''
#                 <script>
#                 function send(){
#                     var req = new XMLHttpRequest();
#                     req.onreadystatechange = function() {
#                         if (req.readyState === 4) {
#                             console.log(req.response);
#                             if (req.response["result"] === true) {
#                                 window.localStorage.setItem('jwt', req.response["access_token"]);
#                             }
#                         }
#                     }
#                     req.withCredentials = true;
#                     req.responseType = 'json';
#                     req.open("get",
#                     "/auth/token?"+window.location.search.substr(1), true);
#                     req.send("");
#
#                 }
#                 </script>
#                 <button onClick="send()">Get FastAPI JWT Token</button>
#             ''')
#

@app.route('/login')
async def login(request: Request):
    redirect_uri = FRONTEND_URL  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.route('/token')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    user_data = await oauth.google.parse_id_token(request, access_token)
    # TODO: validate email in our database and generate JWT token
    jwt = f'valid-jwt-token-for-{user_data["email"]}'
    # TODO: return the JWT token to the user so it can make requests to our /api endpoint
    return JSONResponse({'result': True, 'access_token': jwt})


if __name__ == '__main__':
    uvicorn.run(app, port=8080)
