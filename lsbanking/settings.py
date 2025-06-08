from pathlib import Path
import os
import dj_database_url
import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.utils import cloudinary_url



from environ import Env
env = Env()
Env.read_env()
ENVIRONMENT = env('ENVIRONMENT', default='production')
USE_CLOUDINARY = env.bool('USE_CLOUDINARY', default=False)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == 'development':
    DEBUG = False
else:
    DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'grandelitecreditunion.com',]


CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.app",
    "https://grandelitecreditunion.com",
]



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    #Third Party Apps 
    'allauth',
    'allauth.account',
    # 'allauth.socialaccount', # Removed as per your confirmation

    #Apps 
    'accounts',
    'main',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware', 
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lsbanking.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lsbanking.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


POSTGRESS_LOCALLY = True
if ENVIRONMENT == 'production' or POSTGRESS_LOCALLY == True:
        DATABASES['default'] = dj_database_url.parse(env('DATABASE_URL'))



# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

#AUTH Settings 

AUTH_USER_MODEL = 'accounts.User'
SITE_ID = 1

# Allauth settings
ACCOUNT_AUTHENTICATION_METHOD = 'email' # Users log in with email
ACCOUNT_EMAIL_REQUIRED = True # Email is required for registration
ACCOUNT_USERNAME_REQUIRED = False # We are using email as username
ACCOUNT_USER_MODEL_USERNAME_FIELD = None # User model does not have a username field
ACCOUNT_EMAIL_VERIFICATION = 'optional' # Email verification is mandatory
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True # Log in user after email confirmation
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300 # 5 minutes
LOGIN_REDIRECT_URL = '/dashboard/' # Redirect to dashboard after login
ACCOUNT_LOGOUT_REDIRECT_URL = '/' # Redirect to landing page after logout
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SESSION_REMEMBER = True # Remember user session
ACCOUNT_FORMS = {
    'signup': 'accounts.forms.CustomSignupForm',
}

# For Session based logout 
# Auto logout users after 30 minutes (1800 seconds) of inactivity
SESSION_COOKIE_AGE = 1800  

# Refresh session expiry time on every request
SESSION_SAVE_EVERY_REQUEST = True


# Email backend for development (prints emails to console)

if ENVIRONMENT == 'development':
    EMAIL_BACKEND = env('DEV_EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
else:
    EMAIL_BACKEND = env('EMAIL_BACKEND')
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env.int('EMAIL_PORT')
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@yourdomain.com')
SITE_URL = env('SITE_URL', default='http://localhost:8000')






# ACCOUNT_LOGIN_METHODS = {'email'} # This is an old setting, replaced by ACCOUNT_AUTHENTICATION_METHOD
# ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*'] # This is handled by the form
# ACCOUNT_EMAIL_VERIFICATION = 'optional' # Changed to 'mandatory'



# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
if ENVIRONMENT == 'production' or USE_CLOUDINARY:
    # Cloudinary configuration
    CLOUDINARY = {
        'cloud_name': env('CLOUDINARY_CLOUD_NAME'),
        'api_key': env('CLOUDINARY_API_KEY'),
        'api_secret': env('CLOUDINARY_API_SECRET'),
    }

    cloudinary.config(**CLOUDINARY)

    # Media URL for Cloudinary
    MEDIA_URL = f"https://res.cloudinary.com/{CLOUDINARY['cloud_name']}/"
else:
    # Local media setup
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'


STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
