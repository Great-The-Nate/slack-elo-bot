Run the following commands to setup a virtual environment and install packages:

	python3 -m venv slack_env
	source slack_env/bin/activate
	pip install -r requirements.txt


Setup slack (https://api.slack.com/quickstart) and environment variables:

	export SLACK_SIGNING_SECRET=<your-signing-secret>
	export SLACK_BOT_TOKEN =<your-slack-bot-token>
	export VERIFICATION_TOKEN =<your-verification-token>

Then run 

	python elo_bot.py


If hosting locally, install ngrok and run on another window:

	ngrok http 3000
