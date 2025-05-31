# base URL of the discourse installation
# Do not put a slash at the end of the base URL!
BASE_URL = "https://discourse.example"

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
API_USERNAME = ""
API_KEY = ""

# The only way to determine the ID of a chat seems to be by checking the
# developer tools and see which URL is used when sending a message in chat.
# The URL is `/chat/:chat_id` (`POST`)
CHAT_ID = -1

# To determine the badge id:
# 1) Find a user which already has the desired badge.
# 2) Go to `https://discourse.example/user-badges/{username}.json` in your browser (replacing `discourse.example` and the username respectively)
# 3) Find the `id` attribute in `badges`
REQUIRED_BADGE_ID = -1

# remove this line when you completed the configuration above
raise RuntimeError("configuration not completed")
