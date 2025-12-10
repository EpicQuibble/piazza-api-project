# Piazza Poll Auto-Responder

A Python-based automation tool that monitors a Piazza class and automatically responds to polls. This project extends the unofficial Piazza API with poll interaction capabilities that were previously unavailable.

## Overview

This bot continuously monitors a specified Piazza class for new polls and automatically submits responses based on your configuration. It implements human-like behavior patterns including randomized delays and timing variations to avoid detection.
> *Note: I am not sure if this is needed as I never ran into any rate limiting of any kind however be careful with this as we wouldnt want Piazza to disable this functionality.*

## Project Motivation
This project was created out of curiosity and a desire to learn more about web development, API reverse engineering, and automation. As a daily user of Piazza, I was interested in understanding how the platform works under the hood and exploring the technical challenges of interacting with an undocumented API. The project served as a practical learning experience in:

- Reverse engineering web applications and understanding network requests
- Working with session management and authentication flows
- Understanding and implementing respectful automation practices
- Extending existing libraries 
- Developing robust error handling and retry logic

## Key Features

- Automatic poll detection and response
- Configurable answer selection
- Human-like timing patterns with randomized delays
- Rate limit handling and retry logic
- Comprehensive logging and status reporting
- Duplicate answer prevention
- Support for closed poll detection

## About the Unofficial Piazza API

This project builds upon the [piazza-api](https://github.com/hfaran/piazza-api) Python package, an "Unofficial Client for Piazza's Internal API". The unofficial API provides a Python interface to interact with Piazza programmatically, handling authentication, session management, and basic content retrieval.

However, the existing piazza-api library has significant limitations when it comes to interactive features like polls. This project addresses those gaps.

## Contributions to the Unofficial Piazza API

This project makes several important contributions that extend the capabilities of the unofficial Piazza API:

### 1. Poll Voting Implementation

The most significant contribution is implementing poll voting functionality, which was completely absent from the standard piazza-api library. Through reverse engineering of Piazza's web interface network requests, I discovered and implemented the correct API endpoint and payload structure:

- Identified the `content.vote` RPC method
- Determined the correct payload format with `cid` (content ID) and `votes` array
- Implemented proper error handling for vote submission

### 2. Poll Status Detection

I developed comprehensive methods to determine poll state:

- Checking the `poll_is_closed` flag in the post configuration
- Verifying post status fields
- Detecting whether the current user has already voted using the `has_voted` data structure
- Parsing poll options from the nested `questions` and `answers` structure

### 3. Rate Limiting and Anti-Detection Measures

To work within standard rate limiting constraints, I implemented:
> *Note: This is only precautionary and was added to be nice to the servers.*

- Intelligent delays between post fetches (700-900ms)
- Retry logic for rate limit errors
- Randomized check intervals with 25% variation
- Human-like delays before vote submission (2-5 seconds)
- Browser-like User-Agent headers to avoid automated request detection

### 4. Enhanced Poll Data Extraction

I mapped out the complete poll data structure including:

- Poll options and their IDs
- Vote counts and totals
- Deleted option filtering
- Poll metadata and configuration

## Requirements

- Python 3.6 or higher
- piazza-api package

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install piazza-api
```

3. Create a configuration file by copying the template:

```bash
cp blank_config.py config.py
```

4. Edit `config.py` with your details:

```python
EMAIL = "your.email@example.com"
PASSWORD = "your_password"
CLASS_ID = "your_class_id"  # Found in the Piazza URL
POLL_ANSWER_INDEX = 1  # Which option to select (0 = first, 1 = second, etc.)
CHECK_INTERVAL = 40  # Check every 40 seconds
```

## Configuration Options

- `EMAIL`: Your Piazza account email
- `PASSWORD`: Your Piazza account password
- `CLASS_ID`: The unique identifier for your class (found in the Piazza class URL)
- `POLL_ANSWER_INDEX`: Zero-indexed option selection (0 for first option, 1 for second, etc.)
- `CHECK_INTERVAL`: Base interval in seconds between poll checks (actual interval is randomized)
- `VERBOSE`: Enable detailed logging output
- `SAVE_JSON`: Save poll data to JSON files (for debugging)
- `LIMIT`: Limit the number of posts to fetch (None for all posts)

## Usage

Run the bot:

```bash
python piazza-bot.py
```

The bot will:

1. Log in to Piazza using your credentials
2. Continuously monitor the class for new polls
3. Automatically respond to any unanswered, open polls
4. Log all actions and status information
5. Run indefinitely until stopped with Ctrl+C

## How It Works

1. **Authentication**: Uses the piazza-api library to authenticate and establish a session
2. **Session Sharing**: Shares session cookies between the high-level API and low-level RPC interface
3. **Poll Detection**: Fetches recent posts and identifies those marked as polls
4. **Status Checking**: Verifies each poll is open and hasn't been answered by the user
5. **Vote Submission**: Uses the discovered `content.vote` RPC method to submit responses
6. **Tracking**: Maintains a local set of answered polls to prevent duplicates

## Technical Implementation

The bot uses two layers of the piazza-api:

- **High-level API** (`Piazza` class): For authentication and basic post retrieval
- **Low-level RPC** (`PiazzaRPC` class): For direct API method calls, specifically `content.vote`

This dual approach was necessary because the high-level API doesn't expose poll voting functionality, requiring direct RPC calls with the correct payload structure.

## Limitations and Considerations

- This is an unofficial tool and may break if Piazza changes their API
- Automated poll responses may violate your institution's academic integrity policies
- Rate limiting safeguards is implemented but aggressive usage may still trigger detection
- The bot operates with the same permissions as your user account

## Ethical Considerations

This tool is provided for educational and research purposes. Users should:

- Understand their institution's policies on automation
- Consider the educational purpose of polls before automating responses
- Use responsibly and not abuse the automation capabilities
- Be aware that instructors may detect automated responses

> *Note: I am aware this tool can be used by students to bypass the educational purpose of polls. I highly discourage such use. Polls are often designed to gauge understanding, encourage participation, and facilitate learning. Automating responses defeats these purposes and undermines the educational experience for both yourself and your peers.*

## Troubleshooting

**Login fails**: Verify your credentials and that your account isn't using two-factor authentication

**Rate limiting errors**: Increase the `CHECK_INTERVAL` value or the delays in the code

**No polls detected**: Ensure the `CLASS_ID` is correct and that there are active polls in the class

**Already voted errors**: The bot correctly detects and skips these polls

## License

This project is provided as-is for educational purposes. The piazza-api library has its own license terms.

## Disclaimer

This tool is not affiliated with or endorsed by Piazza Technologies. Use at your own risk and in accordance with your institution's policies.
The author assumes no responsibility or liability for any consequences resulting from the use of this tool. This includes but is not limited to: academic integrity violations, account suspensions, policy violations, or any other issues that may arise. Users are solely responsible for understanding and complying with their institution's policies, Piazza's terms of service, and applicable laws. By using this tool, you accept full responsibility for any and all outcomes