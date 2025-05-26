import uuid
from datetime import datetime
import requests
import os
from typing import Tuple, Optional
from dotenv import load_dotenv
load_dotenv()


def create_ics_file(events):
    """
    Takes an array of dictionaries, each containing 'title' and 'time_range' keys,
    and creates an ICS file with these events.
    Args:
        events (list): List of dictionaries, each with 'title' and 'time_range' keys.
                      The 'time_range' should be a tuple of (start_time, end_time),
                      where times are datetime objects or ISO format strings.
    Returns:
        str: The filename of the created ICS file (UUID + .ics)
    """
    # Generate a unique filename with UUID
    filename = f"{str(uuid.uuid4())}.ics"
    filepath = os.path.join("calendars", filename)

    # ICS file header
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Python Calendar Event Generator//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    # Add each event to the ICS content
    for event in events:
        title = event.get('title', 'Untitled Event')

        # Extract start and end times
        time_range = event.get(
            'time_range', [datetime.now().isoformat(), datetime.now().isoformat()])

        # Convert strings to datetime objects if necessary
        if isinstance(time_range[0], str):
            start_time = datetime.fromisoformat(
                time_range[0].replace('Z', '+00:00'))
        else:
            start_time = time_range[0]

        if isinstance(time_range[1], str):
            end_time = datetime.fromisoformat(
                time_range[1].replace('Z', '+00:00'))
        else:
            end_time = time_range[1]

        # Format times according to iCalendar spec (UTC format)
        start_time_str = start_time.strftime("%Y%m%dT%H%M%SZ")
        end_time_str = end_time.strftime("%Y%m%dT%H%M%SZ")

        # Create unique identifier for this event
        event_uuid = str(uuid.uuid4())

        # Add event details to ICS content
        ics_content.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{title}",
            f"DTSTART:{start_time_str}",
            f"DTEND:{end_time_str}",
            f"UID:{event_uuid}",
            f"DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}",
            "END:VEVENT"
        ])

    # Add calendar footer
    ics_content.append("END:VCALENDAR")

    # Join all lines and write to file
    with open(filepath, 'w') as f:
        f.write("\r\n".join(ics_content))

    return filename


def currency_conversion(base_currency: str, target_currency: str, amount: float, api_key: Optional[str] = None) -> Tuple[float, str]:
    """
    Convert an amount from a base currency to a target currency using the Exchange Rate API.

    Args:
        base_currency (str): The currency code to convert from (e.g., "USD")
        target_currency (str): The currency code to convert to (e.g., "EUR")
        amount (float): The amount to convert
        api_key (str, optional): Your Exchange Rate API key. If not provided, will look for EXCHANGE_RATE_API_KEY in environment variables

    Returns:
        Tuple[float, str]: A tuple containing the converted amount and the date of the last update

    Raises:
        ValueError: If the currency codes are invalid or the API request fails
        KeyError: If the API key is not provided and not found in environment variables
    """
    # Get API key from parameters or environment variables
    if not api_key:
        api_key = os.getenv("CURRENCY_API_KEY")

    if not api_key:
        raise KeyError(
            "API key not provided. Either pass the api_key parameter or set the EXCHANGE_RATE_API_KEY environment variable.")

    # Validate inputs
    base_currency = base_currency.upper()
    target_currency = target_currency.upper()

    if not isinstance(amount, (int, float)):
        raise ValueError("Amount must be a number")

    # Construct the API URL
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base_currency}"

    try:
        # Send GET request to the API
        response = requests.get(url)
        data = response.json()

        # Check if the request was successful
        if data.get("result") == "success":
            # Extract the conversion rates and update time
            conversion_rates = data["conversion_rates"]
            last_update_utc = data["time_last_update_utc"]

            # Check if the target currency exists in the response
            if target_currency not in conversion_rates:
                raise ValueError(
                    f"Invalid target currency code: {target_currency}")

            # Calculate the converted amount
            conversion_rate = conversion_rates[target_currency]
            converted_amount = amount * conversion_rate

            return converted_amount, last_update_utc
        else:
            # Handle API errors
            error_type = data.get("error-type", "unknown")
            if error_type == "unknown-code":
                raise ValueError(
                    f"Invalid base currency code: {base_currency}")
            else:
                raise ValueError(f"API Error: {error_type}")

    except requests.RequestException as e:
        raise ValueError(f"Failed to connect to Exchange Rate API: {str(e)}")
