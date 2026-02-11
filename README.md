# Flask Finance Web App

This is a stock portfolio simulation web app built with Flask. Users can create an account, log in, look up stock prices, buy and sell shares, and view their transaction history.

Originally I built this project as part of Harvard’s CS50 course and later came back to it to fix stock quote integration and clean up parts of the code. It's helped me understand how a full web app fits together with authentication, database management, and API usage.

## Features

- User registration and login
- Stock quote lookup
- Buy and sell functionality
- Portfolio overview
- Transaction history
- SQLite database

## What I Learned

- Understand how Flask handles routing and templates  
- Implement user authentication and manage sessions  
- Work with a relational database (SQLite)  
- Integrate an external API for real-time data  
- Debug and improve existing code  

## Running the App

```bash
python -m venv venv
source venv/Scripts/activate
pip install -r requirements.txt
python -m flask run
```
