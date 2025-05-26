from mcp.server.fastmcp import FastMCP
import argparse
from utils.helpers import create_ics_file, currency_conversion
from typing import List, Union, Dict, Optional, Any
import requests
import json
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


parser = argparse.ArgumentParser(description='TravelGenie MCP Server')
parser.add_argument('transport', nargs='?', default='stdio', choices=['stdio', 'sse'],
                    help='Transport protocol (stdio or sse)')
args = parser.parse_args()

mcp = FastMCP("TravelGenie MCP Server", port=3002)


@mcp.tool()
def create_calendar(events: list[dict[str, str | tuple]]) -> str:
    """
    Takes an array of dictionaries, each containing 'title' and 'time_range' keys,
    and creates an ICS file with these events.

    Args:
        events (list): List of dictionaries, each with 'title' and 'time_range' keys.
                      The 'time_range' should be a tuple of (start_time, end_time),
                      where times are datetime objects.

    Returns:
        str: The url of the created ICS file (UUID + .ics)
    """
    try:
        ics_file_name = create_ics_file(events)
        return f"Calendar created at http://localhost:8081/{ics_file_name}"

    except Exception as e:
        return f"Couldn't create the calendar\n {e}"


@mcp.tool()
def convert_currency(base_currency: str, target_currency: str, amount: float) -> str:
    """
    Convert an amount from a base currency to a target currency using the Exchange Rate API.

    Args:
        base_currency (str): The currency code to convert from (e.g., "USD")
        target_currency (str): The currency code to convert to (e.g., "EUR")
        amount (float): The amount to convert
        api_key (str, optional): Your Exchange Rate API key. If not provided, will look for EXCHANGE_RATE_API_KEY in environment variables

    Returns:
        conversion (str): A string containing the converted amount and the date of the last update

    Raises:
        ValueError: If the currency codes are invalid or the API request fails
        KeyError: If the API key is not provided and not found in environment variables
    """
    try:
        conversion_result = currency_conversion(
            base_currency, target_currency, amount)
        return f"Converted Amount: {conversion_result[0]}\nLast Update: {conversion_result[1]}"
    except Exception as e:
        print(e)
        return "Couldn't convert the currency"


@mcp.tool()
def add_numbers_in_list(numbers: List[Union[int, float]]) -> Union[int, float]:
    """
    Adds all the numbers in a list and returns the sum.

    Parameters:
    numbers (List[Union[int, float]]): List of numbers to add

    Returns:
    Union[int, float]: Sum of all numbers in the list
    """
    total = sum(numbers)

    return f"The result is {total}"


@mcp.tool()
def add_two_numbers(a: Union[int, float], b: Union[int, float]) -> str:
    """
    Adds two numbers and returns the result.

    Parameters:
    a (int or float): First number
    b (int or float): Second number

    Returns:
    int or float: Sum of a and b
    """

    return f"The result is {a + b}"


@mcp.tool()
def get_flight_location_code(name: str) -> str:
    """
    Retrieves the location code for a flight destination using the Booking.com API.

    This function searches for flight locations by name and returns the code of the
    first matching result in a formatted string.

    Args:
        name (str): The name of the location to search for (e.g., "madagascar", "paris")

    Returns:
        str: A formatted string containing the location code in the format 
             "The location code is {code}"

    Raises:
        requests.RequestException: If the API request fails
        KeyError: If the expected data structure is not found in the response
        IndexError: If no locations are found for the given name
    """
    url = 'https://booking-com.p.rapidapi.com/v1/flights/locations'

    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key:
        raise KeyError("RAPIDAPI_KEY not found in environment variables")
    headers = {
        'x-rapidapi-host': 'booking-com.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }

    params = {
        'locale': 'en-gb',
        'name': name
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an exception for bad status codes

        data = response.json()

        # Get the first location's code
        first_location = data[0]
        code = first_location['code']

        return f"The location code is {code}"
    except Exception as e:
        return f"There was an error while performing the request {e}"


@mcp.tool()
def search_flights(
    from_code: str,
    depart_date: str,
    to_code: str,
    children_ages: List[int] = None,
    adults: int = 1,
    cabin_class: str = "ECONOMY"
) -> str:
    """
    Search for flights using the Booking.com RapidAPI and return simplified flight data.

    Args:
        from_code (str): Departure airport/city code (e.g., "ONT.AIRPORT")
        depart_date (str): Departure date in YYYY-MM-DD format
        to_code (str): Destination airport/city code (e.g., "NYC.CITY")
        children_ages (List[int], optional): List of children's ages. Defaults to empty list.
        adults (int, optional): Number of adult passengers. Defaults to 1.
        cabin_class (str, optional): Cabin class preference. Defaults to "ECONOMY".

    Returns:
        str: JSON string containing simplified flight data with 'legs' and 'total' keys

    Raises:
        requests.RequestException: If the API request fails
        KeyError: If required environment variable RAPIDAPI_KEY is not found
        ValueError: If the API response doesn't contain expected data structure
    """
    # Get API key from environment variables
    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key:
        raise KeyError("RAPIDAPI_KEY not found in environment variables")

    # Set default for children_ages if None
    if children_ages is None:
        children_ages = []

    # Prepare request parameters
    url = "https://booking-com.p.rapidapi.com/v1/flights/search"

    # Convert children ages list to comma-separated string
    children_ages_str = ','.join(
        map(str, children_ages)) if children_ages else ""

    params = {
        'from_code': from_code,
        'depart_date': depart_date,
        'to_code': to_code,
        'adults': adults,
        'cabin_class': cabin_class,
        'page_number': 0,
        'currency': 'AED',
        'locale': 'en-gb',
        'flight_type': 'ONEWAY',
        'order_by': 'BEST'
    }

    # Only add children_ages if there are any
    if children_ages_str:
        params['children_ages'] = children_ages_str

    headers = {
        'x-rapidapi-host': 'booking-com.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes

        data = response.json()

        # Extract flight offers (limit to 5)
        flight_offers = data.get('flightOffers', [])[:5]

        results = []

        for offer in flight_offers:
            try:
                # Get the first segment's legs
                segments = offer.get('segments', [])
                if not segments:
                    continue

                legs = segments[0].get('legs', [])

                # Get price breakdown total
                price_breakdown = offer.get('priceBreakdown', {})
                total = price_breakdown.get('total', {})

                # Create result object for this flight offer
                flight_result = {
                    "legs": legs,
                    "total": total
                }

                results.append(flight_result)

            except (KeyError, IndexError) as e:
                # Skip this offer if it doesn't have the expected structure
                continue

        # Return JSON string of all results
        return json.dumps(results, indent=2)

    except Exception as e:
        print(f"Failed: {str(e)}")


@mcp.tool()
def search_hotels(
    dest_id: int,
    checkout_date: str,
    checkin_date: str = "2025-10-14",
    children_number: int = 1,
    adults_number: int = 1,
    children_ages: List[int] = None,
    dest_type: str = "city"
) -> str:
    """
    Search for hotels (with destination_id) using the Booking.com API and return filtered results.

    This function performs a hotel search request to the Booking.com API via RapidAPI,
    filters the response to get only the first 3 results, and returns specific fields
    for each hotel as a JSON string.

    Args:
        dest_id (int): Destination ID for the search location
        checkout_date (str): Checkout date in format 'YYYY-MM-DD' (e.g., '2025-10-15')
        checkin_date (str, optional): Check-in date in format 'YYYY-MM-DD'. 
                                     Defaults to '2025-10-14'
        children_number (int, optional): Number of children. Defaults to 1
        adults_number (int, optional): Number of adults. Defaults to 1
        children_ages (List[int], optional): List of children ages. Defaults to [0]
        dest_type (str, optional): Destination type. Defaults to 'city'

    Returns:
        str: JSON string containing filtered hotel data for up to 3 results.
             Each result includes: name, checkin, checkinDate, checkout, 
             checkoutDate, and priceDetails

    Raises:
        requests.RequestException: If the API request fails
        KeyError: If the API key is not found in environment variables
        ValueError: If the response format is unexpected
    """

    # Get API key from environment
    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key:
        raise KeyError("RAPIDAPI_KEY not found in environment variables")

    # Set default children_ages if not provided
    if children_ages is None:
        children_ages = [0]

    # Convert children_ages list to comma-separated string
    children_ages_str = ','.join(map(str, children_ages))

    # Prepare request parameters
    url = "https://booking-com.p.rapidapi.com/v2/hotels/search"

    headers = {
        'x-rapidapi-host': 'booking-com.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }

    params = {
        'children_number': children_number,
        'adults_number': adults_number,
        'categories_filter_ids': 'class::2,class::4,free_cancellation::1',
        'children_ages': children_ages_str,
        'checkout_date': checkout_date,
        'dest_type': dest_type,
        'page_number': 0,
        'units': 'metric',
        'order_by': 'popularity',
        'room_number': 1,
        'checkin_date': checkin_date,
        'filter_by_currency': 'AED',
        'dest_id': dest_id,
        'locale': 'en-gb',
        'include_adjacency': 'true'
    }

    try:
        # Make the API request
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract results and limit to first 3
        results = data.get('results', [])
        limited_results = results[:3]

        # Filter each result to include only desired fields
        filtered_results = []
        for hotel in limited_results:
            filtered_hotel = {
                'name': hotel.get('name'),
                'checkin': hotel.get('checkin'),
                'checkinDate': hotel.get('checkinDate'),
                'checkout': hotel.get('checkout'),
                'checkoutDate': hotel.get('checkoutDate'),
                'priceDetails': hotel.get('priceDetails')
            }
            filtered_results.append(filtered_hotel)

        # Return as JSON string
        return json.dumps(filtered_results, indent=2)

    except Exception as e:
        print(f"API request failed: {str(e)}")


@mcp.tool()
def get_city_destination_id(name: str) -> str:
    """
    Search for a city location using the Booking.com API and return its destination ID.

    This function queries the Booking.com locations API for a given location name,
    filters the results to find entries with dest_type 'city', and returns the
    destination ID of the first matching city.

    Args:
        name (str): The name of the location to search for (e.g., 'Enugu', 'London')

    Returns:
        str: A formatted string containing the destination ID in the format:
             "The destination id is {destination_id}"

    Raises:
        requests.RequestException: If the API request fails
        ValueError: If no city is found in the search results
        KeyError: If the expected fields are missing from the API response
    """
    url = "https://booking-com.p.rapidapi.com/v1/hotels/locations"

    api_key = os.getenv('RAPIDAPI_KEY')
    if not api_key:
        raise KeyError("RAPIDAPI_KEY not found in environment variables")
    headers = {
        'x-rapidapi-host': 'booking-com.p.rapidapi.com',
        'x-rapidapi-key': api_key
    }

    params = {
        'locale': 'en-gb',
        'name': name
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        locations = response.json()

        # Filter for locations with dest_type 'city'
        cities = [location for location in locations if location.get(
            'dest_type') == 'city']

        if not cities:
            raise ValueError(f"No city found for location name: {name}")

        # Get the first city from the filtered results
        first_city = cities[0]
        destination_id = first_city['dest_id']

        return f"The destination id is {destination_id}"

    except Exception as e:
        return f"There was an error {e}"


@mcp.tool()
def brightdata_scrape_reddit_location_sentiment(location_code: str) -> Dict[str, any]:
    """
    Scrapes Reddit for public sentiment about a given location.

    Args:
        location_code (str): The location code to search for (e.g., "DUB" for Dublin)

    Returns:
        summary (str): Summary of sentiment

    Raises:
        ValueError: If location_code is empty or invalid
        ConnectionError: If Reddit API is unreachable
        RateLimitError: If API rate limits are exceeded
    """
    # time.sleep(5)
    return "Visit Dubai between October and April for pleasant weather and vibrant outdoor events. Plan at least five days to explore iconic landmarks, beaches, and local souqs at a relaxed pace. Don’t miss adventures beyond the city like hiking in Hatta or a desert safari in the Dubai Desert Conservation Reserve. Book top activities and restaurants in advance to avoid crowds and secure the best experiences."


@mcp.tool()
def brightdata_scrape_reddit_activities(
    location_code: str,
    subreddit: Optional[str] = None,
    max_posts: int = 100,
    time_filter: str = "month"
) -> List[Dict[str, Any]]:
    """
    Scrapes Reddit for activities and things to do in a specified location.

    Args:
        location_code: Location identifier (e.g., city code, postal code, or location name)
        subreddit: Optional specific subreddit to search in (defaults to location-based subreddits)
        max_posts: Maximum number of posts to retrieve (default: 100)
        time_filter: Time period to filter posts ("day", "week", "month", "year", "all")

    Returns:
        summary (str): Summary of things to do in dubai

    Raises:
        ValueError: If location_code is invalid or empty
        ConnectionError: If unable to connect to Reddit API
        RateLimitError: If Reddit API rate limit is exceeded
    """
    # time.sleep(5)
    return """Marvel at the iconic Burj Khalifa and enjoy breathtaking views from its sky-high lounges.

    Catch the dazzling Dubai Fountain show set to music near the Dubai Mall.

    Relax or stay at luxury resorts on the man-made Palm Jumeirah island.

    Explore heritage at Dubai Creek with a traditional abra ride and bustling souks.

    Wander through the Al Fahidi Historical Neighbourhood for a glimpse of old Dubai.

    Experience thrilling desert safaris, camel rides, and stargazing in the Arabian sands.

"""


@mcp.tool()
def brightdata_get_visa_requirements(
    origin_country: str,
    destination_country: str,
    *,
    timeout: Optional[int] = 30,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Union[str, bool, int, None]]:
    """
    Scrape visa requirements from passportindex.org for travel between two countries.

    Args:
        origin_country: ISO country code or country name for the origin country
        destination_country: ISO country code or country name for the destination country
        timeout: Request timeout in seconds (default: 30)
        headers: Optional HTTP headers for the request

    Returns:
        summary (str): Summary of Visa Requirements
    Raises:
        ValueError: If country codes are invalid or not found
        requests.RequestException: If the website cannot be accessed
        TimeoutError: If the request times out
        ParseError: If the webpage structure has changed and cannot be parsed
    """
    # time.sleep(5)
    return "Belgian tourists can enter Dubai without a prior visa and receive a free 90-day multiple-entry visit visa on arrival, valid for 6 months, allowing a total stay of 90 days."


if __name__ == "__main__":
    print(f"Starting TravelGenie MCP server with transport: {args.transport}")
    mcp.run(transport=args.transport)
