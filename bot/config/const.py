import logging
import os

from enum import Enum

PROJECT_ROOT = os.getcwd()

# Log
LOG_PATH = os.path.join(PROJECT_ROOT, "logs/consensus-bot.log")
LOG_FILE_SIZE = 1024 * 1024 * 10
DEFAULT_LOG_LEVEL = logging.DEBUG

# Database
DB_PATH = os.path.join(PROJECT_ROOT, "consensus-bot.db")
DB_HISTORY_PATH = os.path.join(PROJECT_ROOT, "consensus-bot-history.db")
GRANT_PROPOSALS_TABLE_NAME = "proposals"
VOTERS_TABLE_NAME = "voters"
PROPOSAL_HISTORY_TABLE_NAME = 'proposal_history'

# nltk datasets to download
NLTK_DATASETS_DIR = f"{PROJECT_ROOT}/nltk"
NLTK_DATASETS = ['averaged_perceptron_tagger', 'punkt', 'wordnet', 'words']

# urls
GITHUB_PROJECT_URL = "https://github.com/nisnevich/eco-discord-lazy-consensus-bot"

# =====================
# Bot related constants
# =====================

# Invite link with required permissions
# https://discord.com/api/oauth2/authorize?client_id=1061680925425012756&permissions=277025467456&scope=bot

GRANT_PROPOSAL_TIMER_SECONDS = 10  # 3 days is 259200
GRANT_PROPOSAL_TIMER_SLEEP_SECONDS = 1
LAZY_CONSENSUS_THRESHOLD = 2

ROLE_IDS_ALLOWED = (1063903240925749389,)
VOTING_CHANNEL_ID = 1067119414731886645
GRANT_APPLY_CHANNEL_ID = 1067127829654937692

DISCORD_COMMAND_PREFIX = "!"
GRANT_PROPOSAL_COMMAND_NAME = 'propose'
PROPOSAL_COMMAND_ALIASES = ['lazy', 'suggest', 'prop', 'consensus']
GRANT_APPLY_COMMAND_NAME = 'grant'
HELP_COMMAND_NAME = 'help-lazy'
EXPORT_COMMAND_NAME = 'export'
EXPORT_CSV_COMMAND_NAME = 'export-csv'
VOTERS_LIST_SEPARATOR = ", "
RESPONSIBLE_MENTION = "<@703574259401883728>"  # Nickname of a person who's responsible for maintaining the bot (used in some error messages to ping).
MAX_DESCRIPTION_LENGTH = 1600  # 1600 is determined experimentally; Discord API has some limitations, and this way we can make sure the app will not crash with discord.errors.HTTPException
MIN_DESCRIPTION_LENGTH = 30  # just some common sense value
MAX_PROPOSAL_AMOUNT = 100000000
MIN_PROPOSAL_AMOUNT = 250
MIN_ENGLISH_TEXT_DESCRIPTION_PROPORTION = 0.35

STOP_ACCEPTING_PROPOSALS_FLAG_FILE_NAME = "stopcock"
EMPTY_ANALYTICS_VALUE = "n/a"

# Emoji
REACTION_ON_BOT_MENTION = "👋"  # wave
# When the proposal is accepted, the bot will
REACTION_ON_PROPOSAL_ACCEPTED = "✅"  # green tick
REACTION_ON_PROPOSAL_CANCELLED = "🍃"  # leaves
CANCEL_EMOJI_UNICODE = "❌"  # ❌ (:x: emoji), unicode: \U0000274C
EMOJI_HOORAY = "🎉"
HEART_EMOJI_LIST = [
    "❤️",
    "♥️",
    "🖤",
    "💙",
    "🤎",
    "💝",
    "💚",
    "🧡",
    "💜",
    "💞",
    "🥰",
    "💖",
    "💕",
    "🤍",
    "💛",
    "💓",
    "💗",
    "💘",
    "💌",
    "😍",
    "❣️",
    "😻",
    "🫶",
    "❤️‍🔥",
    "😘",
]


class ProposalResult(Enum):
    ACCEPTED = 0
    CANCELLED_BY_REACHING_THRESHOLD = 1
    CANCELLED_BY_PROPOSER = 2

    def __str__(self):
        if self.value == ProposalResult.ACCEPTED.value:
            return 'Accepted'
        elif self.value == ProposalResult.CANCELLED_BY_REACHING_THRESHOLD.value:
            return 'Cancelled by reaching threshold'
        elif self.value == ProposalResult.CANCELLED_BY_PROPOSER.value:
            return 'Cancelled by proposer'


# ==============
# Messages texts
# ==============

# Validation error messages
GRANT_COMMAND_MESSAGE = """
{prefix}{grant_command} {mention} {amount} {description}. Voting: {voting_url}
"""
COMMAND_FORMAT_RESPONSE = """
Hey there, {author}! It looks like you're trying to use the !propose command, but something's not quite right with the syntax. No worries though, I've got you covered.

Here's how the command should look: `!propose @username amount reason`

- `@username`: the person you'd like to reward with points.
- `amount`: how many points you'd like to give.
- `reason`: a short explanation of why you're giving the grant. This message will be posted if the grant is applied.

Here are some examples to get you started:
`!propose @Cinderella 100 for saving the kingdom from the dragon`
`!propose @PrinceCharming 200 for taming the wild unicorn and bringing peace to the land`

Don't worry, we all make mistakes, just give it another try! To learn more in DM, type `!help-lazy`. And if you're still having trouble, feel free to reach out for help.
"""
ERROR_MESSAGE_NO_MENTIONS = "Where's the love?! You need to mention someone if you want to propose a grant! `!propose @mention 100 for a giant robot.`"
ERROR_MESSAGE_INVALID_COMMAND_FORMAT = "Oopsie! The command format is as important as the ingredients in a pizza. To make sure you got it right, type `!help-lazy`"
ERROR_MESSAGE_INVALID_USER = (
    "Hmmm, that user doesn't seem to be around here. Did you check under the couch?"
)
ERROR_MESSAGE_INVALID_AMOUNT = (
    "The amount must be a positive number. Example: `!propose @mention 100 for a giant robot.`"
)
ERROR_MESSAGE_NEGATIVE_AMOUNT = "Hold on, {amount} is not enough to even buy a pack of gum. The amount has to be positive, my friend."
ERROR_MESSAGE_OVERFLOW_AMOUNT = "Whoa there, looks like you're trying to request a whopper of a number! Better try again with a smaller amount before the numbers run away from us!"
ERROR_MESSAGE_LITTLE_AMOUNT = f"Whoa there, it looks like you're trying to vote for a pocket change. Minimum amount: {MIN_PROPOSAL_AMOUNT}."
ERROR_MESSAGE_EMPTY_AMOUNT = "The amount is like the cherry on top of a sundae, without it, your proposal just isn't sweet enough. `!propose @mention 100 for a unicorn farm.`"
ERROR_MESSAGE_INVALID_DESCRIPTION = "You know what they say, if you don't describe your grant proposal, how will anyone know how awesome it is? `!propose @mention 100 for a giant robot.`"
ERROR_MESSAGE_LENGTHY_DESCRIPTION = f"Please reduce the description length to less than {MAX_DESCRIPTION_LENGTH} characters. Like, who wants to read that much anyways?"
ERROR_MESSAGE_SHORTY_DESCRIPTION = f"Less is not always more, my friend. A tiny bit more detailed description would be greatly appreciated."
ERROR_MESSAGE_INCORRECT_DESCRIPTION_LANGUAGE = f"Looks like your proposal needs a little more time in English class. Let's make sure you described everything in the language of Shakespeare (English must be at least {100 * MIN_ENGLISH_TEXT_DESCRIPTION_PROPORTION}% of the text, but feel free to add a second language if you'd like. Just don't let it go over a total of {MAX_DESCRIPTION_LENGTH} characters, okay?)."
ERROR_MESSAGE_INVALID_ROLE = "It's only for Layer 3 members, but don't worry if you're not quite there yet! Getting the Layer 3 role is like reaching the top of a mountain, but the view from the top is oh-so-worth it! Plus, think of all the cool features you'll have access to once you get there. Keep climbing, Eco-warrior! :mountain: :eco_heart:"
ERROR_MESSAGE_PROPOSAL_WITH_GRANT_VOTING_LINK_REMOVED = "The {amount} grant for {mention} was applied, but I couldn't find the voting message in this channel. Was it removed? {link_to_original_message} cc {RESPONSIBLE_MENTION}"
ERROR_MESSAGE_GRANTLESS_PROPOSAL_VOTING_LINK_REMOVED = "The proposal by {author} is applied! However, I couldn't find the voting message in this channel. Was it removed? {link_to_original_message} cc {RESPONSIBLE_MENTION}"
PROPOSALS_PAUSED_RESPONSE = "Accepting new proposals was temporarily paused."

# Help messages
HELP_MESSAGE_NON_AUTHORIZED_USER = f"""
Listen up, my elite friend! This bot is for the exclusive use of the Layer 3 squad. It's like a secret handshake for making quick and easy decisions. Want to know more about it? Check out our top secret files on {GITHUB_PROJECT_URL}. But shhh, don't tell anyone else about it! 🤫
"""
HELP_MESSAGE_AUTHORIZED_USER = f"""
Hey there, are you ready to shake things up? Look no further, because the !propose command is here to save the day! 🎆

Here's how it works:

- Need a grant? Type anywhere: `!propose @username amount reason`. For example:
> !propose @JohnSnow 100 for saving the kingdom

- Have an idea but don't need a grant? Type whatever you want after "!propose":
> !propose to run a community meeting tonight at 20 UTC

- Your proposal will be sent straight to the `#L3-Voting` channel for all to see. And don't worry, you don't have to lift a finger after that - just make sure you explained your proposal clearly and let the magic happen! 🦥

- After {int(GRANT_PROPOSAL_TIMER_SECONDS / 60 / 60)} hours, if there's less than {LAZY_CONSENSUS_THRESHOLD} dissenters, BAM! You've got the green light. If you requested a grant, it will be automatically applied. 🚀 I will keep you all updated.

- If you disagree to any proposal, add the {CANCEL_EMOJI_UNICODE} reaction to it in `#L3-Voting`. Don't worry, you can change your mind later (unless it's too late). Bonus points if you tell us why you're against it! ⏱️

- Also, if you change your mind regarding your own proposal, just add {CANCEL_EMOJI_UNICODE} to it in `#L3-Voting` and poof! It's gone. Magic! 🎩

Before submitting a proposal, make sure to clearly explain the background and details of the proposal. Clearly state what actions will be taken if the proposal is approved. Avoid vague descriptions and submit proposals in the appropriate channel (such as `#layer3-points-granting`) to avoid cluttering the public channels. Use the lazy consensus responsibly.

So, don't be shy and get those creative juices flowing! Let's make Eco the best it can be with some fresh ideas! 🌟

For power users:
- Some shortcuts of `!propose` are: {", ".join(PROPOSAL_COMMAND_ALIASES)}
- Run `!export` to receive analytics.

For questions, ideas or partnership, reach out to {RESPONSIBLE_MENTION}. The project is looking for contributors and teammates.

{GITHUB_PROJECT_URL}
"""
HELP_MESSAGE_VOTED_INCORRECTLY = "Oops, you're adding your vote to the wrong message! It's like trying to put a puzzle piece in the wrong spot, it just doesn't fit! 😕 To make your vote count, please head to the correct voting message: {voting_link}."

# =====================
# Proposals with grants
# =====================


def NEW_PROPOSAL_WITH_GRANT_AMOUNT_REACTION(amount):
    if amount < 1000:
        return ":points:"
    if amount < 5000:
        return ":eco_bag:"
    if amount < 20000:
        return ":eco_bag_big::eco_bag_big:"
    return ":eco_bag_big::eco_bag_big::eco_bag_big::eco_bag_big::eco_bag_big:"


NEW_PROPOSAL_WITH_GRANT_SAME_CHANNEL_RESPONSE = """
Alright, let's make this happen! You're proposing to give {mention} {amount} points, but watch out! If {threshold} or more big wigs from Layer 3 vote against it, the deal's off. Anyone who objects can make their voices heard here: {voting_link}
"""
NEW_PROPOSAL_WITH_GRANT_VOTING_CHANNEL_MESSAGE = """
:eco_kyep: :eco_rocket: **Active grant proposal!** {amount_reaction}
{countdown} I will grant `{amount}` points to {mention}, unless {threshold} members react with {reaction} to this message. *If you need help, run !help-lazy command.*
`Proposed by:` {author}
`Goal:` {description}
"""  # Another version: {author} proposed giving {amount} points to {mention}. {threshold} votes against will cancel it. Use {reaction} to vote before {date_finish}.
PROPOSAL_WITH_GRANT_RESULT_VOTING_CHANNEL_EDITED_MESSAGE = """
The {amount} points grant for {mention} suggested by {author} {result}
Goal: {description}
It was proposed here: {link_to_original_message}
"""
PROPOSAL_WITH_GRANT_RESULT_VOTING_CHANNEL = {
    ProposalResult.ACCEPTED: "has been given! :tada:",
    ProposalResult.CANCELLED_BY_REACHING_THRESHOLD: "has been cancelled due to opposition from {threshold} members: {voters_list}",
    ProposalResult.CANCELLED_BY_PROPOSER: "has been cancelled by the proposer. :leaves:",
}
PROPOSAL_WITH_GRANT_RESULT_PROPOSER_RESPONSE = {
    ProposalResult.ACCEPTED: "Hooray! :tada: The grant has been given and {mention} is now richer by {amount} points!",
    ProposalResult.CANCELLED_BY_REACHING_THRESHOLD: "Sorry, {author}, but it looks like {threshold} members weren't on board with your proposal: {voting_link}. No hard feelings, though! Take some time to reflect, make some tweaks, and try again with renewed vigor. :eco_Peace:",
    ProposalResult.CANCELLED_BY_PROPOSER: "{author} has cancelled the proposal. :think:",
}

# =====================
# Grantless proposals
# =====================

NEW_GRANTLESS_PROPOSAL_SAME_CHANNEL_RESPONSE = "Nice one, but let's see what the community thinks! Anyone who objects can make their voices heard here: {voting_link}"
NEW_GRANTLESS_PROPOSAL_VOTING_CHANNEL_MESSAGE = """
:eco_kyep: :eco_rocket: **Active proposal!** :eco_raised_hand:
{countdown} this idea by {author} will have a green light, unless {threshold} members react with {reaction} to this message (for help type *!help-lazy*).

*Note: this proposal only approves certain actions, not a grant. If the text below states otherwise, it should be revoked and clarified. To allocate points, use '!propose @user amount reason', or other ways.*

`Suggestion:` {description}
"""
GRANTLESS_PROPOSAL_RESULT_VOTING_CHANNEL_EDITED_MESSAGE = """
The proposal by {author} {result}
Suggestion: {description}
It was proposed here: {link_to_original_message}
"""
GRANTLESS_PROPOSAL_RESULT_VOTING_CHANNEL = {
    ProposalResult.ACCEPTED: "has been accepted! :tada:",
    ProposalResult.CANCELLED_BY_REACHING_THRESHOLD: "has been cancelled due to opposition from {threshold} members: {voters_list}",
    ProposalResult.CANCELLED_BY_PROPOSER: "has been cancelled by the proposer. :leaves:",
}
GRANTLESS_PROPOSAL_RESULT_PROPOSER_RESPONSE = {
    ProposalResult.ACCEPTED: "Hooray! :tada: The proposal has been accepted!",
    ProposalResult.CANCELLED_BY_REACHING_THRESHOLD: "Sorry, {author}, but it looks like {threshold} members weren't on board with your proposal: {voting_link}. No hard feelings, though! Take some time to reflect, make some tweaks, and try again with renewed vigor. :eco_Peace:",
    ProposalResult.CANCELLED_BY_PROPOSER: "{author} has cancelled the proposal. :think:",
}
