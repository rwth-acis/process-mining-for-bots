from openai import OpenAI
import pm4py
import os


def recommendations_from_event_log(log):
    prompt = "Here is a DFG of a chatbot conversation. Performance is how long a request took on average in seconds. Frequency is how often this edge has been traversed.\n"
    prompt += pm4py.llm.abstract_dfg(log)
    prompt += "\nList five improvements that can be made to the chatbot? Split the recommendations into ones for bot developers and backend specialists. Format your response as html\n\n"
    return prompt


def recommendations_for_intents(intents_df):
    prompt = "Knowing that a confidence score bigger than 0.9 is considered good. \n\n"
    prompt += "Here is a list of intents and the average bot confidence score:\n\n"
    for index, row in intents_df.iterrows():
        if row['intentKeyword'] is not None:
            prompt += f"{row['intentKeyword']}: {row['averageConfidence']}\n"
    prompt += "\n\What improvements can be made to the chatbot? Note that the training data is passed to Rasa to train. \n\n"
    prompt += "Format the response as html. Also include the list along with the confidence scores as a table\n\n"
    return prompt


def custom_prompt(inputPrompt, intents_df, log, net, initial_marking, final_marking):
    if ("`botModel`" in inputPrompt):
        # split the inputPrompt at `botModel` and insert the bot model
        prompt = inputPrompt.split("`botModel`")
        for i in range(len(prompt)):
            if i % 2 == 1:
                prompt[i] = pm4py.llm.abstract_petri_net(
                    net, initial_marking, final_marking)
        prompt = "".join(prompt)

    if ("`botIntents`" in prompt):
        # split the inputPrompt at `botIntents` and insert the bot intents
        prompt = "".join(prompt).split("`botIntents`")
        for i in range(len(prompt)):
            if i % 2 == 1:
                prompt[i] = ""
                for index, row in intents_df.iterrows():
                    if row['intentKeyword'] is not None:
                        prompt[i] += f"{row['intentKeyword']}: {row['averageConfidence']}\n"
        prompt = "".join(prompt)

    if ("`botLog`" in prompt):
        # split the inputPrompt at `botLog` and insert the bot log
        prompt = "".join(prompt).split("`botLog`")
        for i in range(len(prompt)):
            if i % 2 == 1:
                prompt[i] = pm4py.llm.abstract_dfg(log)

        prompt = "".join(prompt)

    return prompt


def find_subprocesses(net, initial_marking, final_marking):
    prompt = "Here is a chatbot conversation model:\n\n"
    prompt += pm4py.llm.abstract_petri_net(net, initial_marking, final_marking)
    prompt += "\n\What subprocesses can you identify for this chatbot?\n\n"
    return prompt


def describe_bot(net, initial_marking, final_marking):
    prompt = "Here is a chatbot conversation model:\n\n"
    prompt = pm4py.llm.abstract_petri_net(net, initial_marking, final_marking)
    prompt += "\n\Describe all the things that this bot can do\n\n"
    return prompt


def send_prompt(prompt, api_key, openai_model="gpt-3.5-turbo-1106"):
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(model=openai_model,
                                              messages=[
                                                  {"role": "system", "content": "You are a helpful Process Mining Expert. You are helping users improve their chatbot. Petri nets refer to the chatbot conversation model. DFG refers to the chatbot conversation model."},
                                                  {"role": "user",
                                                   "content": prompt}
                                              ])
    content = response.choices[0].message.content
    return content
