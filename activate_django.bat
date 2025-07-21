@echo off
echo Activating virtual environment...
call env\Scripts\activate.bat

echo Starting Django server...
python manage.py runserver

pause
