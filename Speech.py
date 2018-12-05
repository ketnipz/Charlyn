import discord
from chatterbot import ChatBot
from chatterbot.comparisons import levenshtein_distance

class Speech:
    def __init__(self, bot):
        self.bot = bot
        self.chatterbot = ChatBot("Charlyn",
                                  storage_adapter="chatterbot.storage.MongoDatabaseAdapter",
                                  logic_adapters=["chatterbot.logic.BestMatch"],
                                  input_adapter="chatterbot.input.VariableInputTypeAdapter",
                                  output_adapter="chatterbot.output.OutputAdapter",
                                  output_format="text",
                                  filters=["chatterbot.filters.RepetitiveResponseFilter"],
                                  statement_comparison_function=levenshtein_distance,
                                  database="chatterbot")

    async def on_message(self, message):
        messageContext = await self.bot.get_context(message)

        if not message.author.bot and not messageContext.valid and\
                message.type is discord.MessageType.default:
            if self.bot.user.mentioned_in(message):
                await message.channel.trigger_typing()

            message_content = message.clean_content.replace("@{}".format(self.bot.user.name), str()).strip()
            print("Processing {}".format(message_content))

            response = await self.bot.loop.run_in_executor(None, self.chatterbot.get_response, message_content,
                                                           message.author.id)

            if self.bot.user.mentioned_in(message):
                await message.channel.send(response)
                # TODO: Possibly stop typing here?
