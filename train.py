from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer

chatterbot = ChatBot("Charlyn",
                     storage_adapter="chatterbot.storage.MongoDatabaseAdapter",
                     logic_adapters=["chatterbot.logic.BestMatch",
                                     "chatterbot.logic.TimeLogicAdapter",
                                     "chatterbot.logic.MathematicalEvaluation"],
                     input_adapter="chatterbot.input.TerminalAdapter",
                     output_adapter="chatterbot.output.TerminalAdapter",
                     database="chatterbot")
chatterbot.set_trainer(ChatterBotCorpusTrainer)

chatterbot.train(
    "chatterbot.corpus.english"
)

