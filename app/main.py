import os.path
from enum import Enum

import requests
from dotenv import find_dotenv, load_dotenv
from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

# load_dotenv("../.env")
load_dotenv(find_dotenv())

app = FastAPI()
db_filename = "db.txt"


class Envs:
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_FROM = os.getenv("MAIL_FROM")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_FROM_NAME = os.getenv("MAIN_FROM_NAME")


conf = ConnectionConfig(
    MAIL_USERNAME=Envs.MAIL_USERNAME,
    MAIL_PASSWORD=Envs.MAIL_PASSWORD,
    MAIL_FROM=Envs.MAIL_FROM,
    MAIL_PORT=Envs.MAIL_PORT,
    MAIL_SERVER=Envs.MAIL_SERVER,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


class Tags(Enum):
    rate = "rate"
    subscription = "subscription"


async def raise_third_party_exception(url: str):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=f"Something is wrong with the third-party API. Failed to fetch info from {url}",
    )


async def request_data(url: str):
    """Make a request to a third-party API and return its response or raise an exception."""
    response = requests.get(url)
    if response.status_code != 200:
        await raise_third_party_exception(url)
    return response.json()


async def get_currency_rate(from_currency_code: str, to_currency_code: str):
    """Return the latest exchange rate from *from_currency_code* to *to_currency_code*."""
    url = f"https://api.exchangerate.host/latest?base={from_currency_code}"
    data = await request_data(url)
    rate = data.get("rates").get(to_currency_code)
    return rate


async def get_btc_to_usd_rate():
    """Return the latest bitcoin rate in USD."""
    url = "https://api.coindesk.com/v1/bpi/currentprice.json"
    data = await request_data(url)
    btc_to_usd_rate = data.get("bpi").get("USD").get("rate_float")
    return btc_to_usd_rate


@app.get("/rate", tags=[Tags.rate])
async def read_btc_rate():
    """Get the latest bitcoin rate."""
    btc_to_usd_rate = await get_btc_to_usd_rate()
    usd_to_uah_rate = await get_currency_rate("USD", "UAH")
    return btc_to_usd_rate * usd_to_uah_rate


@app.post("/subscribe", tags=[Tags.subscription])
async def subscribe(email: EmailStr = Form()):
    """Subscribe for getting the latest bitcoin rate."""
    if os.path.isfile(db_filename):
        with open(db_filename, mode="r") as db:
            for (
                line
            ) in (
                db
            ):  # check line by line in order to prevent memory overflow if the file is large
                if email in line:
                    return JSONResponse(
                        status_code=status.HTTP_409_CONFLICT,
                        content={
                            "error": f"such email address already subscribed. No actions performed"
                        },
                    )

    with open(db_filename, mode="a") as db:
        db.write(email + "\n")
    return {"info": "email added"}


@app.post("/sendEmails", tags=[Tags.subscription])
async def send_emails(background_tasks: BackgroundTasks):
    """Send an email with a bitcoin rate to all subscribed email addresses."""
    if not os.path.isfile(db_filename):
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail="Unable to perform an action. No subscribed email addresses",
        )

    with open(db_filename, "r") as db:
        recipients = [line.strip() for line in db]

    btc_to_uah_rate = await read_btc_rate()
    message = MessageSchema(
        subject="Latest BTC rate",
        recipients=recipients,
        body=f"The current bitcoin price: {btc_to_uah_rate} ₴",
    )
    fm = FastMail(conf)
    background_tasks.add_task(fm.send_message, message)
    return JSONResponse(status_code=200, content={"message": "emails have been sent"})
