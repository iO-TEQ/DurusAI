# How to generate train.jsonl line

1) use message_template.json to create a expected Convo with the ai

2) do not change the first object, its the system prompt, tell the ai what and who it is.

3) the second object is the user prompt, asking the ai to do something.

4) the last object is the ai response to the user prompt.

recommended to give a user prompt and expected proposed_changes, then ask the ai agent to fill in the assistant message and steps

5) run the python script append_message_template.py to convert message_template to jsonl and append it
to train.jsonl



try to create simple examples (at least 15) for one component
