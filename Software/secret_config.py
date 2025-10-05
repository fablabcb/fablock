TELEGRAM_TOKEN = "insert-token-here"
TELEGRAM_CHAT_ID = -123456789

# base URL of the discourse installation
# Do not put a slash at the end of the base URL!
DISCOURSE_BASE_URL = "https://discourse.example"

# Discourse API keys can only be created by an administrator:
# -> admin panel -> extended -> API keys
#
# required permissions:
# - access the message bus (see below)
# - chat: create_message
#
# Using "granular" permissions did not work in the past because there was no
# option to allow access to the message bus.
# Perhaps it has been added (URL `/message_bus/:client_id/poll (POST)`)?
# Otherwise please grant global permissions for the bot user.
DISCOURSE_API_USERNAME = ""
DISCOURSE_API_KEY = ""

# The only way to determine the ID of a chat seems to be by checking the
# developer tools and see which URL is used when sending a message in chat.
# The URL is `/chat/:chat_id` (`POST`)
DISCOURSE_CHAT_ID = -1

# remove this line when you completed the configuration above
raise RuntimeError("configuration not completed")
