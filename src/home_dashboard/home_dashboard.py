import os
from square.http.auth.o_auth_2 import BearerAuthCredentials
from square.client import Client

ACCESS_TOKEN = os.environ.get('SQUARE_ACCESS_TOKEN')
TRANSACTION_LIMIT = 1000

def get_daily_total():
    # Total transaction amounts while removing refunds
    pass

def update_display_success():
    # Refresh


    # Display: total sales for today and previous 6 days; timestamp of last
    # transaction; timestamp of this update


    pass

def update_display_failure():
    # Refresh


    # Display: failure (connection/etc); timestamp of this update


    pass

def main():
    # Exit early with reason if access token not set as environment variable


    # Connect to Square
    client = Client(
        bearer_auth_credentials=BearerAuthCredentials(
            access_token=ACCESS_TOKEN
        ),
        environment='production'
    )

    # Get all payments (utilizing pagination)
    result = client.payments.list_payments()
    if result.is_success():

    else:
        update_display_failure(result.errors)

    #print(len(result.body.get('payments')))

    # Get daily totals for previous week


    # Get timestamp of last transaction


    ## TESTING
    # Call API for result
    #result = client.payments.list_payments()

if __name__ == '__main__':
    main()