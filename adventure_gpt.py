import openai
import textwrap
import os
import json
#from tiktoken import Tokenizer, TokenizerException
import time
#from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

def parse_message(msg_str):
    msg_end = msg_str.find('{')
    plaintext = msg_str[:msg_end].strip()
    json_str = msg_str[msg_end:]
    json_obj = json.loads(json_str)
    return plaintext, json_obj


class AdventureGpt:
    """
    my class
    """
    def __init__(self, model="gpt-4", temperature=0.7, max_tokens=512, summary_frequency=3, session_id=None):
        # Load API key from environment variable
        openai.api_key = os.environ("OPENAI_API_KEY")

        # Load prompt from 'prompt.txt'
        with open("prompt.txt", "r") as file:
            self.system_prompt = file.read()

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = model
        self.cost_per_input_token = .03/1000
        self.cost_per_output_token = .12/1000
        self.summary_frequency = summary_frequency
        self.session_id = session_id or str(time.time())  # Default to a timestamp if not provided

        self.additional_guidelines = input("Please provide any additional guidelines, rules, or themes: ")

        # Update system message with additional user context
        self.system_message = {"role": "system", "content": self.system_prompt + " " + self.additional_guidelines}
        self.messages = [self.system_message]
        self.summarized_history = ""

        # Create instance-specific directory if it doesn't exist
        self.instance_directory = os.path.join("instances", self.session_id)
        if not os.path.exists(self.instance_directory):
            os.makedirs(self.instance_directory)

    def generate_response(self):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.get_relevant_messages(),
            max_tokens=self.max_tokens,
            n=1,
            stop=None,
            temperature=self.temperature,
        )
        return response.choices[0].message['content'].strip()

    def generate_summary(self, prompt):
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=prompt,
            max_tokens=self.max_tokens,
            n=1,
            stop=None,
            temperature=self.temperature,
        )
        return response.choices[0].message['content'].strip()

    def get_relevant_messages(self):
        if self.summarized_history:
            last_messages_after_summary = self.messages[-(len(self.messages) % self.summary_frequency):]
            return [self.system_message] + [{"role": "system", "content": self.summarized_history}] + last_messages_after_summary
        else:
            return self.messages

    def update_summarized_history(self):
        history_to_summarize = self.get_relevant_messages()  # Exclude system message
        with open("summary_prompt.txt", "r") as f:
            summary_prompt = f.read() + str(history_to_summarize)
        if len(self.messages) % self.summary_frequency == 0:
            self.summarized_history = self.generate_summary([{"role": "user", "content": summary_prompt}])

    def save_history(self):
        with open(os.path.join(self.instance_directory, "history.json"), "w") as file:
            json.dump(self.messages, file, indent=2)

        with open(os.path.join(self.instance_directory, "summarized_history.txt"), "w") as file:
            file.write(self.summarized_history)

    def get_interaction(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

        gpt_response = self.generate_response()

        self.messages.append({"role": "assistant", "content": gpt_response})

        # Save history
        self.save_history()

        self.update_summarized_history()

        return parse_message(gpt_response)
