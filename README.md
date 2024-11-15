# Telegram Channels Monitor

This project is a Telegram Channels Monitor that allows you to track and monitor messages from various Telegram channels.

## Features

- Monitor multiple Telegram channels which post mint addresses for tokens to invest in
- List the newest mint addresses from the channels at the endpoint `/latest`.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/ConnorSwis/tg-crypto-monitor.git
    ```
2. Navigate to the project directory:
    ```bash
    cd telegram-channels-monitor
    ```
3. Install the required dependencies:
    ```bash
    poetry install
    ```

## Configuration

Create a `.env` file in the root directory of the project and add the following environment variables:

```env
# * means required
TG_APP_ID="* The id of your Telegram application"
TG_APP_HASH="* The hash of your Telegram application"
TG_PHONE="* The password of your Telegram account"
TG_PASSWORD="* The phone number of your Telegram account"
MONITORING_IDS="* The ids of the channels to monitor separated by commas"
SESSION_DIRECTORY="The local directory to store the session file. Default is ./session"
LIMIT_MSG="The number of messages to fetch from the channel each check. Default is 5"
MAX_MESSAGES="The maximum number of mint addresses to store at the endpoint. Default is 10"
PORT="The local port to run the FastAPI app. Default is 8000"

```

## Running the Application

1. Ensure you have Python installed on your system.
2. Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3. Run the FastAPI application:
    ```bash
    uvicorn main:app --reload
    ```

## API Endpoints

- `GET /latest`: Retrieve the latest messages.
- `POST /set_code`: Set the 5-digit code required for authentication.

## Logging

The application uses Python's logging module to log important events. Logs are output to the console.
