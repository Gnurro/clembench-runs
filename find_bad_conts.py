""" Finding unwanted multi-line model outputs """

import os
import json


VERSION = "v1.5"

# remote API models to filter out:
REMOTE = ["claude-2", "claude-2.1", "claude-instant-1.2", "claude-v1.3", "command", "gpt-3.5-turbo-0613",
          "gpt-3.5-turbo-1106", "gpt-4-0314", "gpt-4-0613", "gpt-4-1106-preview", "claude-3-haiku-20240307",
          "claude-3-opus-20240229", "claude-3-sonnet-20240229", "gpt-3.5-turbo-0125", "gpt-4-0125-preview",
          "mistral-large-2402", "mistral-medium-2312"]

with open("model_registry.json", 'r', encoding='utf-8') as registry_file:
    model_registry = json.load(registry_file)

model_pairings = [model_pairing for model_pairing in os.listdir(VERSION) if os.path.isdir(os.path.join(VERSION, model_pairing))]


def split_dir(dir_str):
    return dir_str.split("-t0.0", 1)[0]


local_models = list()
local_set = set()

for model_pairing in model_pairings:
    model_name = split_dir(model_pairing)
    if model_name not in REMOTE:
        local_models.append(model_pairing)
        local_set.add(split_dir(model_pairing))

game_to_check = "privateshared"

bad_cont_weos_list = list()
bad_cont_neos_list = list()

bad_cont_models = set()


for local_model in local_models:
    for model_entry in model_registry:
        if model_entry['model_name'] == split_dir(local_model):
            cur_model_entry = model_entry

    levels = [level for level in os.listdir(os.path.join(VERSION, local_model, game_to_check))]
    for level in levels:
        episodes = [episode for episode in os.listdir(os.path.join(VERSION, local_model, game_to_check, level)) if
                    os.path.isdir(os.path.join(VERSION, local_model, game_to_check, level, episode))]
        for episode in episodes:
            episode_records = os.listdir(os.path.join(VERSION, local_model, game_to_check, level, episode))

            # open requests.json to get raw responses:
            with open(os.path.join(VERSION, local_model, game_to_check, level, episode, "requests.json"), 'r',
                  encoding="utf-8") as requests_file:
                episode_requests = json.load(requests_file)

            for request_num, response in enumerate(episode_requests):
                prompt = response['manipulated_prompt_obj']['inputs']
                full_raw_response = response['raw_response_obj']['response']

                if "output_split_prefix" in cur_model_entry:
                    raw_response = full_raw_response.rsplit(cur_model_entry["output_split_prefix"], 1)[1]
                else:
                    raw_response = full_raw_response.replace(prompt, "")

                if "\n" in raw_response:
                    bad_cont_models.add(split_dir(local_model))
                    log_txt = f"{split_dir(local_model)} {level} {episode} request {request_num}:\n{raw_response}"
                    if raw_response.endswith(cur_model_entry['eos_to_cull']):
                        bad_cont_weos_list.append(log_txt)
                    else:
                        bad_cont_neos_list.append(log_txt)

print(f"Models producing bad continuations: {bad_cont_models}")

print(f"Local models without bad continuations: {local_set-bad_cont_models}")

print(f"Bad continuations with EOS: {len(bad_cont_weos_list)}")
print(f"Bad continuations without EOS: {len(bad_cont_neos_list)}")

bad_cont_weos_file = f"{VERSION}_{game_to_check}_bad_conts_with_eos.txt"
bad_cont_neos_file = f"{VERSION}_{game_to_check}_bad_conts_without_eos.txt"

with open(bad_cont_weos_file, 'w', encoding='utf-8') as bad_cont_weos_out:
    bad_cont_weos_out.write("\n/////\n".join(bad_cont_weos_list))

with open(bad_cont_neos_file, 'w', encoding='utf-8') as bad_cont_neos_out:
    bad_cont_neos_out.write("\n/////\n".join(bad_cont_neos_list))
