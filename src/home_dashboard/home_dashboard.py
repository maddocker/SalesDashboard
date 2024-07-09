import os
import sys
from datetime import datetime
from decimal import Decimal
import pytz
from square.http.auth.o_auth_2 import BearerAuthCredentials
from square.client import Client

ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN')
TRANSACTION_LIMIT = 1000

DATETIME_FORMAT = "%I:%M %p, %m-%d-%Y"

def get_decimal_from_money(money: int):
    """
    Square stores money as `int` in cents. Use this function to convert into `Decimal`.
    """
    return round(Decimal(money / 100), 2)

def get_local_datetime(utc_datetime: datetime):
    return utc_datetime.astimezone(pytz.timezone('US/Central'))

def get_daily_totals(payments: list):
    daily_totals = {}
    for payment in payments:

        # Convert timestamp to Central Time
        payment_time_utc = datetime.fromisoformat(payment['created_at'])
        payment_time_local = get_local_datetime(payment_time_utc)
        payment_date_str = payment_time_local.date().isoformat()

        # Total transaction amount per day while removing refunds
        if not daily_totals.get(payment_date_str):
            daily_totals[payment_date_str] = get_decimal_from_money(payment['amount_money']['amount'])
        else:
            daily_totals[payment_date_str] += get_decimal_from_money(payment['amount_money']['amount'])
        if (refund := payment.get('refunded_money')):
            daily_totals[payment_date_str] -= get_decimal_from_money(refund['amount'])
        
    return daily_totals

def update_display_success(daily_totals: dict, last_transaction: datetime):
    # Refresh


    # Display: total sales for today and previous 6 days; timestamp of last
    # transaction; timestamp of this update
    for date, amount in daily_totals.items():
        print(f"Total for {date}: ${amount}")
    print("Last transaction: " + last_transaction.strftime(DATETIME_FORMAT))
    print("Updated: " + datetime.now().strftime(DATETIME_FORMAT))

def update_display_failure(message: str):
    # Refresh


    # Display: failure (connection/etc); timestamp of this update


    print(message)
    sys.exit(message)

def main():
    # Exit early with reason if access token not set as environment variable

    if not ACCESS_TOKEN:
        update_display_failure('Square access token not set')

    # Connect to Square
    client = Client(
        bearer_auth_credentials=BearerAuthCredentials(
            access_token=ACCESS_TOKEN
        ),
        environment='production'
    )

    # Get all payments (utilizes pagination; might go up to 100 over transaction limit)
    payments = []
    result = client.payments.list_payments()
    if result.is_success():
        while (result.body != {}):
            payments.extend(result.body.get('payments'))
            if result.cursor and len(payments) < TRANSACTION_LIMIT:
                result = client.payments.list_payments(cursor=result.cursor)
            else:
                break
    else:
        update_display_failure(result.errors)

    # Get daily totals for previous week
    daily_totals = get_daily_totals(payments)

    # Get timestamp of last transaction
    last_transaction_time = get_local_datetime(datetime.fromisoformat(payments[0]['created_at']))

    # Display dashboard
    update_display_success(daily_totals, last_transaction_time)

if __name__ == '__main__':
    main()