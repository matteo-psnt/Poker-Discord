from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain.memory import ConversationBufferMemory
from config.config import API_KEY
from game.poker import PokerGameManager
import json


class gptPlayer:
    def __init__(self):
        chat = ChatOpenAI(model_name="gpt-4") # type: ignore
        template = '''
        You are a proffesional poker bot who is playing a game of heads up Texas Hold'em aginst a human player. 
        You play optimally and will occasionally bluff. You will raise when you have a strong hand. 
        You will only go All-in if you have a very strong hand. You will fold if you think your opponent has a better hand. 
        And will call and check where appropriate. 
        Please reply in the following JSON format: {{"action": "your action", "raise_amount": your raise amount if applicable, "explanation": "your explanation for your action"}}
        Note: If the action you chose doesn't involve a raise, please do not include the "raise_amount" key in your JSON response.
        '''
        system_message_prompt = SystemMessagePromptTemplate.from_template(template)
        mesage_placeholder = MessagesPlaceholder(variable_name="chat_history")
        human_message_prompt = HumanMessagePromptTemplate.from_template("{input}")
        chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, mesage_placeholder, human_message_prompt])

        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

        self.chain = LLMChain(llm=chat, prompt=chat_prompt, memory=memory, verbose=True)
        
    def _extract_action(self, json_string, pokerGame: PokerGameManager):
        min_raise, max_raise = pokerGame.return_min_max_raise(1)
        try:
            json_data = json.loads(json_string)
            action = json_data['action'].capitalize()
            raise_amount = 0
            if action == "Raise":
                raise_amount = json_data['raise_amount']
                raise_amount = int(raise_amount)
                
                if action < min_raise:
                    print("Raise amount too small, raising to minimum")
                    action[1] = min_raise

                elif action > max_raise:
                    print("Raise amount too large, raising all-in")
                    action = "All-in"
                    raise_amount = pokerGame.players[1].stack
            
            return (action, raise_amount)
        except Exception as erro:
            print(erro)
            print("Returning default action")
            return ("Default", 0)

            


    def pre_flop_small_blind(self, pokerGame: PokerGameManager):
        # return Call, Raise, Fold or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.players[1].stack,
            'opponents_stack': pokerGame.players[0].stack,
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'amount_to_call': pokerGame.big_blind - pokerGame.small_blind
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        You are the small blind and it's your turn.
        It costs {amount_to_call} chips to call.
        What action would you take? (Call, Raise, All-in, or Fold)
        ---'''

        formatted_text = human_template.format(**inputs)
        response = self.chain.run(formatted_text)
        return self._extract_action(response, pokerGame)

    def pre_flop_big_blind(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.players[1].stack,
            'opponents_stack': pokerGame.players[0].stack,
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'amount_to_call': pokerGame.big_blind - pokerGame.small_blind
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        You are the small blind and it's your turn.
        It costs {amount_to_call} chips to call.
        What action would you take? (Check, Raise, or All-in)
        ---'''

        formatted_text = human_template.format(**inputs)
        response = self.chain.run(formatted_text)
        return self._extract_action(response, pokerGame)
    
    def first_to_act(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.players[1].stack,
            'opponents_stack': pokerGame.players[0].stack,
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards()
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        It's the {round} round and you're first to act. The community cards are {community_cards}.
        What action would you take? (Check, Raise, or All-in)
        ---'''

        formatted_text = human_template.format(**inputs)
        response = self.chain.run(formatted_text)
        return self._extract_action(response, pokerGame)
    
    def player_check(self, pokerGame: PokerGameManager):
        # return Check, Raise, or All-in
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.players[1].stack,
            'opponents_stack': pokerGame.players[0].stack,
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards()
        }

        human_template = """
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        It is the {round} round and the action checks to you. The community cards are {community_cards}.
        Based on this information, what action would you like to take? (Check, Raise, or All-in). Please provide no explanation for your action.
        ---
        """        
        
        formatted_text = human_template.format(**inputs)

        response = self.chain.run(formatted_text)
        return self._extract_action(response, pokerGame)
    
    def player_raise(self, pokerGame: PokerGameManager):
        # return Call, Raise, All-in, or Fold
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.players[1].stack,
            'opponents_stack': pokerGame.players[0].stack,
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards(),
            'opponent_raise': pokerGame.current_bet,
            'amount_to_call': pokerGame.current_bet - pokerGame.players[1].round_pot_commitment
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack and your opponent has {opponents_stack} chips.
        Your hand is {hand}. The pot is {pot} chips.
        It's the {round} round. The community cards are {community_cards}.
        Your opponent has raised to {opponent_raise} chips.
        It costs {amount_to_call} chips to call.
        What action would you take? (Call, Raise, All-in, or Fold)
        ---'''

        formatted_text = human_template.format(**inputs)

        response = self.chain.run(formatted_text)
        return self._extract_action(response, pokerGame)  

    def player_all_in(self, pokerGame: PokerGameManager):
        # return Call, or Fold
        amount_to_call = pokerGame.current_bet - pokerGame.players[1].round_pot_commitment
        if amount_to_call > pokerGame.players[1].stack:
            amount_to_call = pokerGame.players[1].stack
        inputs = {
            'small_blind': pokerGame.small_blind,
            'big_blind': pokerGame.big_blind,
            'stack': pokerGame.players[1].stack,
            'hand': pokerGame.players[1].return_long_hand(),
            'pot': pokerGame.current_pot,
            'round': pokerGame.round,
            'community_cards': pokerGame.return_community_cards(),
            'opponent_raise': pokerGame.current_bet,
            'amount_to_call': amount_to_call
        }

        human_template = '''
        The small blind is {small_blind} chips and the big blind is {big_blind} chips.
        You have {stack} chips in your stack.
        Your hand is {hand}. The pot is {pot} chips.
        It's the {round} round. The community cards are {community_cards}.
        Your opponent has gone all in for {opponent_raise} chips.
        It costs {amount_to_call} chips to call.
        What action would you take? (Call, or Fold)
        '''

        formatted_text = human_template.format(**inputs)

        response = self.chain.run(formatted_text)
        return self._extract_action(response, pokerGame)
