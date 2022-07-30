# Bitcoin Rate App
## Overview
This is the service for obtaining the latest Bitcoin price in Ukrainian Hryvnia (UAH).
The app was implemented using [FastAPI](https://fastapi.tiangolo.com/) - Python's web framework. <br>
There is ability to get the current Bitcoin rate, subscribe for an email notification with the given email address and send the actual BTC price to all previously subscribed users.<br>
No authentication is needed, so each user can perform any action.

## Available API endpoints
+ GET /rate - obtain the latest Bitcoin(BTC) price in UAH
+ POST /subscribe - provide an email address(formData) in order to get information about changing the BTC rate
+ POST /sendEmails - send the actual Bitcoin rate to all subscribed users

## Usage
```
git clone https://github.com/Voorhees2019/BTC_rate_app
cd BTC_rate_app/
docker build -t btc_app .
docker run --name btc_app_container -p 8000:8000 btc_app
```
