import discord
import asyncio
from datetime import datetime, timedelta

from bot.config.logging_config import log_handler, console_handler
from bot.config.const import *
from bot.config.schemas import Voters

from bot.utils.proposal_utils import (
    get_proposal,
    remove_proposal,
    is_relevant_proposal,
    add_voter,
    remove_voter,
    get_voter,
    get_proposal_initiated_by,
)
from bot.utils.db_utils import DBUtil
from bot.utils.validation import validate_roles
from bot.utils.discord_utils import get_discord_client, get_message, send_dm
from bot.utils.formatting_utils import get_amount_to_print, get_discord_countdown_plus_delta

logger = logging.getLogger(__name__)
logger.setLevel(DEFAULT_LOG_LEVEL)
logger.addHandler(log_handler)
logger.addHandler(console_handler)

db = DBUtil()
client = get_discord_client()


async def is_valid_voting_reaction(payload):
    logger.debug("Verifying the reaction...")

    # Check if the reaction matches
    if payload.emoji.name != CANCEL_EMOJI_UNICODE:
        return False
    logger.debug("Emoji is correct")

    # Check if the user role matches
    guild = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not await validate_roles(member):
        return False
    logger.debug("Role is correct")

    reaction_channel = guild.get_channel(payload.channel_id)

    # A hotfix for discord forums (the None channel is returned when a reaction is added to a message in a forum; though it works fine in other functions that use ctx.message.channel.id, such as propose)
    if not reaction_channel:
        logger.debug("Seems like a forum message.")
        return

    # When adding reaction, check if the user has attempted to vote on a wrong message - either the original proposer message, or the bots reply to it, associated with an active proposal though (in order to help onboard new users)
    if payload.event_type == "REACTION_ADD":
        incorrect_reaction_proposal = get_proposal_initiated_by(payload.message_id)
        if incorrect_reaction_proposal:
            # Remove reaction from the message (only in channels that are allowed for bot to manage messages/reactions), in order not to confuse other members
            if reaction_channel.id in CHANNELS_TO_REMOVE_HELPER_MESSAGES_AND_REACTIONS:
                reaction_message = await reaction_channel.fetch_message(payload.message_id)
                await reaction_message.remove_reaction(payload.emoji, member)

            # Retrieve the relevant voting message to send link to the user
            voting_message = await get_message(
                client, VOTING_CHANNEL_ID, incorrect_reaction_proposal.voting_message_id
            )
            # Send private message to user
            dm_channel = await member.create_dm()
            await dm_channel.send(
                HELP_MESSAGE_VOTED_INCORRECTLY.format(voting_link=voting_message.jump_url)
            )

    # Check if this is a voting channel
    if reaction_channel.id != VOTING_CHANNEL_ID:
        return False
    logger.debug("Channel is correct")

    # Check if the reaction message is a relevant lazy consensus voting
    if not is_relevant_proposal(payload.message_id):
        return False
    logger.debug("Proposal is correct")
    return True


@client.event
async def on_raw_reaction_remove(payload):
    logger.debug("Removing a reaction: %s", payload.event_type)
    try:
        # Check if the reaction was made by valid user to a valid voting message
        if not await is_valid_voting_reaction(payload):
            return

        # Get the proposal (it was already validated that it exists)
        proposal = get_proposal(payload.message_id)

        # Error handling - retrieve the voter object from the DB
        voter = await get_voter(payload.user_id, payload.message_id)
        if not voter:
            logger.warning(
                "Warning: Unable to find in the DB a user whose voting reaction was presented on active proposal. channel=%s, message=%s, user=%s, proposal=%s",
                payload.channel_id,
                payload.message_id,
                payload.user_id,
                proposal,
            )
            return

        # Remove the voter from the list of voters for the grant proposal
        await remove_voter(proposal, voter)

    except Exception as e:
        try:
            # Try replying in Discord
            message = await get_message(client, payload.channel_id, payload.message_id)
            await message.reply(
                f"An unexpected error occurred when handling reaction removal. cc {RESPONSIBLE_MENTION}"
            )
        except Exception as e:
            logger.critical("Unable to reply in the chat that a critical error has occurred.")

        logger.critical(
            "Unexpected error in %s while removing vote (reaction), channel=%s, message=%s, user=%s",
            __name__,
            payload.channel_id,
            payload.message_id,
            payload.user_id,
            exc_info=True,
        )


async def cancel_proposal(proposal, reason, voting_message):
    # Extracting dynamic data to fill messages
    # Don't remove unused variables because messages text may change
    mention_author = proposal.author
    description_of_proposal = proposal.description
    list_of_voters = VOTERS_LIST_SEPARATOR.join(f"<@{voter.user_id}>" for voter in proposal.voters)
    original_message = await get_message(client, proposal.channel_id, proposal.message_id)
    link_to_voting_message = voting_message.jump_url
    link_to_initial_proposer_message = original_message.jump_url if original_message else None
    if not proposal.is_grantless:
        mention_receiver = proposal.mention
        amount_of_allocation = get_amount_to_print(proposal.amount)

    # Filling the response messages with different arguments based on the reason of cancelling
    if reason == ProposalResult.CANCELLED_BY_PROPOSER:
        if proposal.is_grantless:
            response_to_proposer = GRANTLESS_PROPOSAL_RESULT_PROPOSER_RESPONSE[reason].format(
                author=mention_author
            )
        else:
            response_to_proposer = GRANT_PROPOSAL_RESULT_PROPOSER_RESPONSE[reason].format(
                author=mention_author
            )
        log_message = "(by the proposer)"
    elif reason == ProposalResult.CANCELLED_BY_REACHING_THRESHOLD:
        if proposal.is_grantless:
            response_to_proposer = GRANTLESS_PROPOSAL_RESULT_PROPOSER_RESPONSE[reason].format(
                author=mention_author,
                threshold=LAZY_CONSENSUS_THRESHOLD,
                voting_link=link_to_voting_message,
            )
        else:
            response_to_proposer = GRANT_PROPOSAL_RESULT_PROPOSER_RESPONSE[reason].format(
                author=mention_author,
                threshold=LAZY_CONSENSUS_THRESHOLD,
                voting_link=link_to_voting_message,
            )
        log_message = "(by reaching threshold)"

    if reason == ProposalResult.CANCELLED_BY_PROPOSER:
        edit_in_voting_channel = PROPOSAL_CANCELLED_VOTING_CHANNEL[reason].format(
            author=mention_author, link_to_original_message=link_to_initial_proposer_message
        )
    elif reason == ProposalResult.CANCELLED_BY_REACHING_THRESHOLD:
        edit_in_voting_channel = PROPOSAL_CANCELLED_VOTING_CHANNEL[reason].format(
            threshold=LAZY_CONSENSUS_THRESHOLD,
            voters_list=list_of_voters,
            link_to_original_message=link_to_initial_proposer_message,
        )

    if original_message:
        await original_message.add_reaction(REACTION_ON_PROPOSAL_CANCELLED)
    # Reply in the original channel, unless it's not the voting channel itself (then not replying to avoid flooding)
    if original_message and voting_message.channel.id != original_message.channel.id:
        message = await original_message.reply(response_to_proposer)
        # Remove embeds
        await message.edit(suppress=True)
    # Edit the proposal in the voting channel; suppress=True will remove embeds
    await voting_message.edit(content=edit_in_voting_channel, suppress=True)

    # Add history item for analytics
    await db.add_proposals_history_item(proposal, reason)
    logger.debug(
        "Added history item, voting_message_id=%d, result=%s",
        proposal.voting_message_id,
        reason,
    )
    # Remove the proposal
    await remove_proposal(proposal.voting_message_id, db)
    logger.info(
        "Cancelled %s %s. voting_message_id=%d",
        "grantless proposal" if proposal.is_grantless else "proposal with a grant",
        log_message,
        proposal.voting_message_id,
    )


@client.event
async def on_raw_reaction_add(payload):
    """
    Cancel a grant proposal if a L3 member reacts with a :x: emoji to the original message or the confirmation message.
    Parameters:
        payload (discord.RawReactionActionEvent): The event containing data about the reaction.
    """

    try:
        logger.debug("Adding a reaction: %s", payload.event_type)

        # Check if it's a valid voting reaction
        if not await is_valid_voting_reaction(payload):
            # If not, check if the reaction is a heart emoji, to double it (just for fun)
            if payload.emoji.name in HEART_EMOJI_LIST:
                message = await get_message(client, payload.channel_id, payload.message_id)
                await message.add_reaction(payload.emoji)
            return

        # Don't allow to vote if recovery is in progress
        if db.is_recovery():
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

            # Replying in DM
            dm_channel = await member.create_dm()
            await dm_channel.send(VOTING_PAUSED_RECOVERY_RESPONSE)

            # Removing the reaction. Not checking for permissions to remove because they must be set
            # otherwise error should be thrown (this code should only run if the reaction was added
            # to the voting channel)
            reaction_message = await get_message(client, payload.channel_id, payload.message_id)
            await reaction_message.remove_reaction(payload.emoji, member)

            logger.info(
                "Rejecting the vote from %s because recovery is in progress.",
                member.mention,
            )
            return

        proposal = get_proposal(payload.message_id)

        # The voting message is needed to format the replies of the bot later
        voting_message = await get_message(client, payload.channel_id, payload.message_id)

        # Error/fraud handling - check if the user has already voted for this proposal
        voter = await get_voter(payload.user_id, payload.message_id)
        logger.debug("Voter: %s", voter)
        if voter:
            logger.warning(
                "Warning: Somehow the same user has managed to vote twice on the same proposal: channel=%s, message=%s, user=%s, proposal=%s, voter=%s",
                payload.channel_id,
                payload.message_id,
                payload.user_id,
                proposal,
                voter,
            )
            return
        logger.debug("User hasn't voted before")

        # Add voter to DB and dict
        await add_voter(
            proposal,
            Voters(user_id=payload.user_id, voting_message_id=proposal.voting_message_id),
        )
        logger.info(
            "Added vote of user_id=%s, total %d voters against voting_message_id=%d",
            payload.user_id,
            len(proposal.voters),
            proposal.voting_message_id,
        )

        #  Check whether the voter is the proposer himself, and then cancel the proposal
        if proposal.author == payload.member.mention:
            logger.debug("The proposer voted against, cancelling")
            await cancel_proposal(proposal, ProposalResult.CANCELLED_BY_PROPOSER, voting_message)
            return
        logger.debug("The proposer isn't the author of the proposal")

        # Check if the threshold is reached
        if len(proposal.voters) >= proposal.threshold:
            logger.debug("Threshold is reached, cancelling")
            await cancel_proposal(
                proposal, ProposalResult.CANCELLED_BY_REACHING_THRESHOLD, voting_message
            )
        # If not, DM user notifying that his vote was counted
        else:
            await send_dm(
                payload.guild_id,
                payload.user_id,
                HELP_MESSAGE_VOTED_AGAINST.format(
                    author=proposal.author,
                    countdown=get_discord_countdown_plus_delta(
                        proposal.closed_at - datetime.utcnow()
                    ),
                    cancel_emoji=CANCEL_EMOJI_UNICODE,
                    voting_link=voting_message.jump_url,
                ),
            )
    except Exception as e:
        try:
            # Try replying in Discord
            message = await get_message(client, payload.channel_id, payload.message_id)

            await message.reply(
                f"An unexpected error occurred when handling reaction adding. cc {RESPONSIBLE_MENTION}"
            )
        except Exception as e:
            logger.critical("Unable to reply in the chat that a critical error has occurred.")

        logger.critical(
            "Unexpected error in %s while voting (adding reaction), channel=%s, message=%s, user=%s",
            __name__,
            payload.channel_id,
            payload.message_id,
            payload.user_id,
            exc_info=True,
        )
