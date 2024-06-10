@Echo off

If Not Exist "venv\Scripts\activate.bat" (
  echo "No virtual environment found, creating one now"
  pip install virtualenv
  python -m venv venv
)

Call "venv\Scripts\activate.bat"
pip install -r requirements.txt > NUL

python -m coverage run -m pytest
python -m coverage report --include="%~dp0\utils\*,%~dp0\services\*,%~dp0\endpoints\*"
