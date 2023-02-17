from bot.utils.proposal_utils import get_proposal, remove_proposal
from bot.utils.db_utils import DBUtil
from bot.config.const import *
from bot.config.logging_config import log_handler, console_handler
from bot.utils.discord_utils import get_discord_client
from bot.utils.formatting_utils import get_amount_to_print


logger = logging.getLogger(__name__)
logger.setLevel(DEFAULT_LOG_LEVEL)
logger.addHandler(log_handler)
logger.addHandler(console_handler)

db = DBUtil()
client = get_discord_client()


async def grant(voting_message_id):
    try:
        try:
            proposal = get_proposal(voting_message_id)
        except ValueError as e:
            logger.error("Proposal not found. voting_message_id=%d", voting_message_id)
            return

        result = ProposalResult.ACCEPTED

        # Retrieve the original proposal message
        original_message = await get_message(client, proposal.channel_id, proposal.message_id)
        link_to_original_message = original_message.jump_url if original_message else None
        # Retrieve the voting message
        voting_message = await get_message(client, VOTING_CHANNEL_ID, proposal.voting_message_id)

        # Applying the grant if the proposal isn't grantless
        if not proposal.is_grantless:
            # Construct the grant message
            grant_message = GRANT_COMMAND_MESSAGE.format(
                prefix=DISCORD_COMMAND_PREFIX,
                grant_command=GRANT_APPLY_COMMAND_NAME,
                mention=proposal.mention,
                amount=get_amount_to_print(proposal.amount),
                description=proposal.description,
                voting_url=voting_message.jump_url,
            )

            # Apply the grant
            try:
                channel = client.get_channel(GRANT_APPLY_CHANNEL_ID)
                await channel.send(grant_message)
            except Exception as e:
                await voting_channel.send(
                    f"Could not apply grant for {proposal.mention}. cc {RESPONSIBLE_MENTION}",
                )
                logger.critical(
                    "An error occurred while sending grant message, voting_message_id=%d",
                    voting_message_id,
                    exc_info=True,
                )
                # Throwing exception further because if the grant failed to apply, we don't want to do anything else
                raise e

        # Add "accepted" reactions to all messages
        if original_message:
            await original_message.add_reaction(REACTION_ON_PROPOSAL_ACCEPTED)
        if voting_message:
            await voting_message.add_reaction(REACTION_ON_PROPOSAL_ACCEPTED)
            await voting_message.add_reaction(EMOJI_HOORAY)

        # Reply to the original proposal message, if it still exists, and if it wasn't send in the voting channel (to avoid flooding)
        if original_message and (voting_channel.id != original_channel.id):
            if not proposal.is_grantless:
                await original_message.reply(
                    PROPOSAL_WITH_GRANT_RESULT_PROPOSER_RESPONSE[result].format(
                        mention=proposal.mention,
                        amount=get_amount_to_print(proposal.amount),
                    )
                )
            else:
                await original_message.reply(
                    GRANTLESS_PROPOSAL_RESULT_PROPOSER_RESPONSE[result].format()
                )
        elif not original_message:
            logger.warning(
                "Warning: Looks like the proposer has removed the original proposal message. message_id=%d",
                proposal.message_id,
            )

        # Update the proposal results in the voting channel
        if voting_message:
            if not proposal.is_grantless:
                await voting_message.edit(
                    content=PROPOSAL_WITH_GRANT_RESULT_VOTING_CHANNEL_EDITED_MESSAGE.format(
                        amount=get_amount_to_print(proposal.amount),
                        mention=proposal.mention,
                        author=proposal.author,
                        result=PROPOSAL_WITH_GRANT_RESULT_VOTING_CHANNEL[result],
                        description=proposal.description,
                        # TODO#9 if original_message is None, message should be different
                        link_to_original_message=link_to_original_message,
                    )
                )
            else:
                await voting_message.edit(
                    content=GRANTLESS_PROPOSAL_RESULT_VOTING_CHANNEL_EDITED_MESSAGE.format(
                        author=proposal.author,
                        result=GRANTLESS_PROPOSAL_RESULT_VOTING_CHANNEL[result],
                        description=proposal.description,
                        # TODO#9 if original_message is None, message should be different
                        link_to_original_message=link_to_original_message,
                    )
                )
        else:
            # Handling the case when voting message was somehow removed from the channel
            if not proposal.is_grantless:
                await voting_channel.send(
                    ERROR_MESSAGE_PROPOSAL_WITH_GRANT_VOTING_LINK_REMOVED.format(
                        amount=get_amount_to_print(proposal.amount),
                        mention=proposal.mention,
                        link_to_original_message=f"Original message: {link_to_original_message}",
                        RESPONSIBLE_MENTION=RESPONSIBLE_MENTION,
                    )
                )
            else:
                await voting_channel.send(
                    ERROR_MESSAGE_GRANTLESS_PROPOSAL_VOTING_LINK_REMOVED.format(
                        author=proposal.author,
                        link_to_original_message=f"Original message: {link_to_original_message}",
                        RESPONSIBLE_MENTION=RESPONSIBLE_MENTION,
                    )
                )
            logger.warning(
                "Warning: The proposal message in the voting channel not found. voting_message_id=%d",
                voting_message_id,
            )

        # Add history item for analytics
        await db.add_history_item(proposal, result)
        logger.debug(
            "Added history item, voting_message_id=%d, result=%s",
            proposal.voting_message_id,
            result,
        )

        # Remove proposal from dictionary and DB
        try:
            await remove_proposal(voting_message_id, db)
        except ValueError as e:
            logger.critical(f"Error while removing proposal: {e}")
            return
        logger.info("Successfully approved proposal. voting_message_id=%d", voting_message_id)

    except Exception as e:
        try:
            # Try replying in Discord
            proposal = get_proposal(voting_message_id)
            channel = client.get_channel(proposal.channel_id)
            original_message = await channel.fetch_message(voting_message_id)

            await original_message.reply(
                f"An unexpected error occurred when approving the proposal. cc {RESPONSIBLE_MENTION}"
            )
        except Exception as e:
            logger.critical("Unable to reply in the chat that a critical error has occurred.")

        logger.critical(
            "Unexpected error in %s while approving the proposal, voting_message_id=%s",
            __name__,
            voting_message_id,
            exc_info=True,
        )
