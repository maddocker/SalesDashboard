import os
import sys
import io
from datetime import datetime, timedelta
from decimal import Decimal
import matplotlib.pyplot as plt
from zoneinfo import ZoneInfo
from square.http.auth.o_auth_2 import BearerAuthCredentials
from square.client import Client
from PIL import Image, ImageDraw
import epaper

DAYS_TO_SHOW = 7

ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN')

DATETIME_FORMAT = "%I:%M %p, %x"

display = epaper.epaper('epd4in2b_V2').EPD()
blank_image = Image.new('L', (display.width, display.height), 255)

def get_decimal_from_money(money: int):
    """
    Square stores money as `int` in cents. Use this function to convert into `Decimal`.
    """
    return round(Decimal(money / 100), 2)

def show_update_timestamp(new_frame: Image):
    update_str = "Updated: " + datetime.now().strftime(DATETIME_FORMAT)
    draw = ImageDraw.Draw(new_frame)
    draw.text(
        (240, display.height - 20),
        update_str,
        fill=0
    )

def get_local_datetime(utc_datetime: datetime):
    return utc_datetime.astimezone(ZoneInfo('US/Central'))

def get_daily_totals(payments: list):
    daily_totals = {}
    for payment in payments:

        # Convert timestamp to Central Time
        payment_time_utc = datetime.fromisoformat(payment['created_at'])
        payment_time_local = get_local_datetime(payment_time_utc)
        payment_date_str = payment_time_local.date().strftime('%a %x')

        # Total transaction amount per day while removing refunds
        if not daily_totals.get(payment_date_str):
            daily_totals[payment_date_str] = get_decimal_from_money(payment['amount_money']['amount'])
        else:
            daily_totals[payment_date_str] += get_decimal_from_money(payment['amount_money']['amount'])
        if (refund := payment.get('refunded_money')):
            daily_totals[payment_date_str] -= get_decimal_from_money(refund['amount'])
        
    return daily_totals

def update_display_success(daily_totals: dict, last_transaction: datetime):
    last_trans_str = "Last transaction: " + last_transaction.strftime(DATETIME_FORMAT)

    # Configure and save bar graph
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.barh(daily_totals.keys(), daily_totals.values())
    ax.invert_yaxis()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for i in ax.patches:
        plt.text(
            i.get_width() + 0.2,
            i.get_y() + 0.5,
            '$' + str(i.get_width()),
            fontsize=10,
            fontweight='bold'
        )
    fig.tight_layout(h_pad=1.0)
    buf = io.BytesIO()
    fig.savefig(buf)
    buf.seek(0)

    # Display: total sales for today and previous 6 days; timestamp of last
    # transaction; timestamp of this update
    display.init()
    display.Clear()
    image = blank_image.copy()
    graph = Image.open(buf).resize((display.width, display.height))
    image.paste(graph, (0, -15))
    draw = ImageDraw.Draw(image)
    draw.text(
        (10, display.height - 20),
        last_trans_str,
        fill=0
    )
    show_update_timestamp(image)
    display.display(display.getbuffer(image), display.getbuffer(blank_image))
    display.sleep()

def update_display_failure(message: str):
    # Display: failure (connection/etc); timestamp of this update
    display.init()
    display.Clear()
    image = blank_image.copy()
    draw = ImageDraw.Draw(image)
    draw.text(
        (20, 150),
        message,
        fill=0
    )
    show_update_timestamp(image)
    display.display(display.getbuffer(image), display.getbuffer(blank_image))
    display.sleep()
    sys.exit(message)

def main():
    # Exit early with reason if access token not set as environment variable
    if not ACCESS_TOKEN:
        update_display_failure('SQUARE_ACCESS_TOKEN not set')

    # Connect to Square
    client = Client(
        bearer_auth_credentials=BearerAuthCredentials(
            access_token=ACCESS_TOKEN
        ),
        environment='production'
    )

    # Get datetime for one week ago (midnight)
    since_datetime = datetime.now() - timedelta(DAYS_TO_SHOW)
    since_datetime = get_local_datetime(since_datetime)
    since_datetime = since_datetime.replace(hour=0, minute=0, second=0)
    since = since_datetime.isoformat(timespec='seconds')

    # Get all payments since datetime (utilizes pagination)
    payments = []
    try:
        result = client.payments.list_payments(since)
        if result.is_success():
            while (result.body != {}):
                payments.extend(result.body.get('payments'))
                if result.cursor:
                    result = client.payments.list_payments(since, cursor=result.cursor)
                else:
                    break
        else:
            update_display_failure(result.errors)
    except Exception as e:
        update_display_failure(str(e))

    # Get daily totals for previous week
    daily_totals = get_daily_totals(payments)

    # Get timestamp of last transaction
    last_transaction_time = get_local_datetime(datetime.fromisoformat(payments[0]['created_at']))

    # Display dashboard
    update_display_success(daily_totals, last_transaction_time)

if __name__ == '__main__':
    main()