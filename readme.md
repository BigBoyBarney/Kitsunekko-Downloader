# Kitsunekko Downloader

Kitsunekko Downloader is a Python script to download Japanese subtitles from Kitsunekko.

## Features

- **Full Download:** Download subtitles for all available anime in one go.
- **Since Last Download:** Download subtitles uploaded since the last run (if applicable).
- **Customisable:** Choose a custom date range to download subtitles.
- **Automatic Organizing:** Subtitles are organized into folders by anime.

## Dependencies

Before using Kitsunekko Downloader, ensure you have the following Python dependencies installed:

- [Python 3.*](https://www.python.org/downloads/): The script is written in Python.
- [Requests](https://pypi.org/project/requests/): To make HTTP requests.
- [Beautiful Soup](https://pypi.org/project/beautifulsoup4/): For HTML parsing.
- [Concurrent Futures](https://pypi.org/project/futures/): For concurrent execution.
- [Threading](https://docs.python.org/3/library/threading.html): For multi-threading support.

You can install the above dependencies using the following command:

```bash
pip install requests beautifulsoup4 futures
```

## Usage


1. **Clone the Repository:**
```bash
git clone https://github.com/BigBoyBarney/kitsunekko-downloader.git
```
2. **Navigate to the Project Directory:**
```bash
cd kitsunekko-downloader

```
3. **Run the Script:**
```bash
python kitsunekko-downloader.py
```

## Contributing

Contributions to the Kitsunekko Downloader project are welcome! Feel free to fork the repository, make improvements, and submit pull requests.

## License

This project is licensed under GNU General Public License v3.0.
