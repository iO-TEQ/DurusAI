# Durus AI 

## Summary
Durus is a AI agent for Duro Control GUI. For only Mac computers, below are instructions to run Durus AI in a virtual environment. First, run an LLM (Large Language Model) server (port 9000). Then, Durus is a http server (port 8080) sending prompts to the LLM server.


## LLM Server Instructions
### MLX LM Server

1. Go to root directory in terminal.

might need to do this: create a hugging face account 
```
pip install -U "huggingface_hub[cli]"
huggingface-cli login
```

2. create a new virtual environment folder
```
mkdir -p ~/venvs
```

3. start a new virtual environment
```
/opt/homebrew/bin/python3.12 -m venv ~/venvs/llama3
source ~/venvs/llama3/bin/activate
```

4. install mlx-lm package
```
python -m pip install --upgrade pip
pip install "mlx-lm>=0.29.0"
```

5. confirm installation. (optional)
```
python - << 'PY'
import mlx_lm
print("mlx_lm version:", mlx_lm.__version__)
PY
```

6. run test script to load model and generate text. (optional)
```
python - << 'PY'
from mlx_lm import load, generate

model_id = "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit"

print("Loading model:", model_id)
model, tokenizer = load(model_id)
out = generate(model, tokenizer, prompt="Say hello in one short sentence.", verbose=True)
print("\n=== OUTPUT ===")
print(out)
PY
```

7. run the AI model server. in this instance, Meta-Llama-3.1-8B-Instruct-4bit, knowledge cutoff is December 2023. context length is 128k. Model Release Date July 23, 2024.

```
mlx_lm.server \
  --model mlx-community/Meta-Llama-3.1-8B-Instruct-4bit \
  --host 0.0.0.0 \
  --port 8080
```


## Durus API Instructions
### Python Fast API Server
1. In a new terminal, clone Durus https://github.com/iO-TEQ/DurusAI.git

2. Go to durus directory.

3. run virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```

4. install python packages
```
pip install -r requirements.txt
```

5. run the python fast api server
```
uvicorn main:app --host 0.0.0.0 --port 9000
```

## Run the RAG Layer Qdrant Server via docker
1. cd to /RAG
```bash 
cd RAG
```
1. run Qdrant
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -p 6334:6334 \
  -v "$(pwd)/qdrant_storage:/qdrant/storage:z" \
  qdrant/qdrant
```

2. install python packages in virtual env
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Build Rag Layer Server
```bash
python query_rag.py
```


## Train the AI Model

Generate Adapters -  small, efficient side modules that learn the patterns specific to your task.

jsonl format for all files
```
{"messages": [{"role": "system", "content": "}, {"role": "user", "content": ""}, {"role": "assistant", "content": ""}]}

```
/durusai_training
train.jsonl — examples the model learns from - needs 100+ lines
val.jsonl — optional validation set to monitor training progress - need 10% of train.jsonl size (new lines) 
test.jsonl — held-out examples for final evaluation (not uploaded)

### generating a jsonl for train or valid

1) create a json like the one below. for you user.content and assistant.content would be empty initially (example)
{
    "messages": [
        {
            "role": "system",
            "content": "You are an assistant for an HMI/tag editor on the Duro controller. You MUST respond with a single JSON OBJECT (not an array) and nothing else. The top-level JSON must have exactly these fields: message (string), steps (array of {title, details}), proposed_changes (object with hmi{views,general}, tags_to_add, components_to_add). Within proposed_changes, hmi, tags_to_add, and components_to_add can be empty if not needed."
        },
        {
            "role": "user",
            "content": "Task: Create a diagnosis screen with two labels at the top right with placeholder value Start and Stop. Name the view 'View'."
        },
        {
            "role": "assistant",
            "content": "{\"message\":\"Created a new diagnosis view named 'View_1' with two top-right labels: Start and Stop.\",\"steps\":[{\"title\":\"Create diagnosis view\",\"details\":\"Add a new HMI view named 'View_1' to show diagnosis controls.\"},{\"title\":\"Add Start/Stop labels\",\"details\":\"Place two labels in the top-right corner with placeholder text 'Start' and 'Stop'.\"}],\"proposed_changes\":{\"hmi\":{\"views\":[{\"id\":\"vw_bd136a03-0be14f12\",\"name\":\"View_1\",\"type\":\"view\",\"config\":{\"width\":1024,\"height\":760,\"style\":{},\"sizeMode\":\"normal\"},\"components\":[{\"id\":\"lbl_9b1c-5dc8\",\"viewId\":\"vw_bd136a03-0be14f12\",\"type\":\"label\",\"typeAbbr\":\"lbl_\",\"comptName\":\"start_lbl\",\"visibility\":true,\"w\":120,\"h\":60,\"y\":0,\"x\":784,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"zoom\",\"config\":{\"placeholder\":\"Start\",\"buttonMode\":\"false\",\"style\":{\"justify-content\":\"center\",\"align-items\":\"center\"}},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"text\":\"\",\"visibility\":\"\",\"color\":\"\"},\"events\":{\"click\":\"\"}},{\"id\":\"lbl_7272-d344\",\"viewId\":\"vw_bd136a03-0be14f12\",\"type\":\"label\",\"typeAbbr\":\"lbl_\",\"comptName\":\"stop_lbl\",\"visibility\":true,\"w\":120,\"h\":60,\"y\":0,\"x\":904,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"zoom\",\"config\":{\"placeholder\":\"Stop\",\"buttonMode\":\"false\",\"style\":{\"justify-content\":\"center\",\"align-items\":\"center\"}},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"text\":\"\",\"visibility\":\"\",\"color\":\"\"},\"events\":{\"click\":\"\"}}]}],\"general\":{\"viewsTree\":[{\"name\":\"View_1\",\"type\":\"view\",\"id\":\"vw_bd136a03-0be14f12\"}]}}},\"tags_to_add\":[],\"components_to_add\":[]}}"
        }
    ]
}

2) create a prompt and place it in the user.content.
Place 'Task: ' before the prompt
Place 'content: ' after Task Prompt with jsonstring of content you want to include 

(e.g. "context:\n{\"views\":[{\"id\":\"vw_default\",\"name\":\"MainView\",\"type\":\"view\",\"config\":{\"width\":1230,\"height\":800,\"style\":{\"fontFamily\":\"None\",\"font-weight\":\"none\",\"fontSize.px\":16,\"color\":\"#000000\",\"backgroundColor\":\"#ffffff\",\"borderRadius.px\":0,\"borderStyle\":\"solid\",\"borderColor\":\"#00000000\",\"borderWidth.px\":0,\"boxShadow\":\"0px 0px 0px 0px #000000\"},\"sizeMode\":\"zoom\"},\"components\":[{\"id\":\"nvw_9680-4dff\",\"viewId\":\"vw_6d6790f2-899a4dc8\",\"type\":\"view\",\"typeAbbr\":\"nvw_\",\"comptName\":\"good_view\",\"visibility\":true,\"w\":222.1410137943127,\"h\":155.08314023191144,\"y\":90,\"x\":355,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"zoom\",\"config\":{\"buttonMode\":\"false\",\"style\":{},\"varReplacement\":[{\"var\":\"status\",\"value\":\"\\\"Good\\\"\"}]},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"visibility\":\"UserInfo.Status == 1\",\"rotation\":\"\"},\"events\":{\"click\":\"\"}},{\"id\":\"btn_8b9b-c6a0\",\"viewId\":\"\",\"type\":\"button\",\"typeAbbr\":\"btn_\",\"comptName\":\"reset_button_btn\",\"visibility\":true,\"w\":110,\"h\":50,\"y\":440,\"x\":150,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"zoom\",\"config\":{\"behavior\":\"release\",\"text\":\"Reset Form\",\"style\":{\"borderRadius.px\":5},\"placeholderType\":\"text\"},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"text\":\"\",\"visibility\":\"\",\"color\":\"\"},\"events\":{\"click\":\"writeTag(\\\"UserInfo.name\\\", \\\"\\\") + writeTag(\\\"UserInfo.age\\\", 0)\",\"press\":\"\",\"release\":\"\"}},{\"id\":\"nvw_9cb5-bca5\",\"viewId\":\"vw_6d6790f2-899a4dc8\",\"type\":\"view\",\"typeAbbr\":\"nvw_\",\"comptName\":\"bad_view\",\"visibility\":true,\"w\":222.1410137943127,\"h\":155.08314023191144,\"y\":90,\"x\":110,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"zoom\",\"config\":{\"buttonMode\":\"false\",\"style\":{},\"varReplacement\":[{\"var\":\"status\",\"value\":\"\\\"Bad\\\"\"}]},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"visibility\":\"UserInfo.Status == 0\",\"rotation\":\"\"},\"events\":{\"click\":\"\"}},{\"id\":\"nvw_12cf-6190\",\"viewId\":\"vw_fb950e55-8a074f3a\",\"type\":\"view\",\"typeAbbr\":\"nvw_\",\"comptName\":\"user_form_view\",\"visibility\":true,\"w\":300,\"h\":100,\"y\":500,\"x\":50,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"normal\",\"config\":{\"buttonMode\":\"false\",\"style\":{}},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"visibility\":\"\",\"rotation\":\"\"},\"events\":{\"click\":\"\"}},{\"id\":\"btn_25ff-5dc9\",\"viewId\":\"\",\"type\":\"button\",\"typeAbbr\":\"btn_\",\"comptName\":\"change_status_btn\",\"visibility\":true,\"w\":150,\"h\":45,\"y\":30,\"x\":240,\"zIndex\":0,\"rotationAngle\":0,\"sizeMode\":\"zoom\",\"config\":{\"behavior\":\"release\",\"text\":\"Change Status\",\"style\":{\"borderRadius.px\":5},\"placeholderType\":\"text\"},\"animation\":{\"backgroundColor\":\"\",\"border\":\"\",\"text\":\"\",\"visibility\":\"\",\"color\":\"\"},\"events\":{\"click\":\"writeTagIfElse(UserInfo.Status == 1, \\\"UserInfo.Status\\\", 0, 1)\",\"press\":\"\",\"release\":\"\"}}]}],\"tags\":[]}")

3) generate the content you want the ai the response in the format of 
{
    "message": ...summary message...,
    "steps": [{"title": string, "details": string}],
    "proposed_changes": { "hmi": {"views": [], "general": {}}, "components_to_add": [], "tags_to_add": []}
}

4) convert step 3 json to jsonstring

5) place json string into assistant.content

6) convert step 1 json to jsonl

7) add jsonl to train.jsonl


Start Training
```
% python -m mlx_lm.lora \
  --model mlx-community/Meta-Llama-3.1-8B-Instruct-4bit \
  --data ./durusai_training_lora \
  --train \
  --batch-size 1 \
  --iters 200 \
  --adapter-path ./adapters \
  --mask-prompt \
  --max-seq-length 4096
```
This will take a long time, roughly one hour for 200 Iterations.

adapters will be created after training is completed. they are stored in /adapters (e.g 0000100_adapters.safetensors)

To use adapters, run 
```
mlx_lm.server \
  --model mlx-community/Meta-Llama-3.1-8B-Instruct-4bit \
  --adapter-path ./adapters \
  --host 0.0.0.0 \
  --port 8080
```

## Version Summary

### 0.1.0
 Docs are overwhelming the request to the 9000. 

 added POST http://127.0.0.1:9000/chat/stream.
 body example
{
  "prompt": "hello, my name is Edward",
  "conversation_id": "test-chat"
}

added POST http://127.0.0.1:9000/agent/build_view
body example 
{
  "device_id": "duro-1",
  "conversation_id": "tes3tt3d",
  "prompt": "Create a view with a label saying 'lol' in the center of the view.",
  "context": {
            "hmi": {
                "views": [
                    {
                        "id": "vw_default",
                        "name": "MainView",
                        "type": "view",
                        "config": {
                        "width": 1230,
                        "height": 800,
                        "style": {
                            "fontFamily": "None",
                            "font-weight": "none",
                            "fontSize.px": 16,
                            "color": "#000000",
                            "backgroundColor": "#ffffff",
                            "borderRadius.px": 0,
                            "borderStyle": "solid",
                            "borderColor": "#00000000",
                            "borderWidth.px": 0,
                            "boxShadow": "0px 0px 0px 0px #000000"
                        },
                        "sizeMode": "zoom"
                        },
                        "components": []
                    }
                ],
                "general": {
                    "defaultViewId": "vw_default",
                    "mainView": null,
                    "mainNavBtn": false,
                    "viewsTree": [
                        {
                        "name": "MainView",
                        "type": "view",
                        "id": "vw_default"
                        }
                    ]
                }
            }
    }
}
 
 **Current Problems** 
 - docs are too much for the prompt to take in. need to find a way to get the ai the knowledge for duro.
 
### 0.1.1 Build View only request
hmi component docs simplified. extracting keywords from prompt and retrieve related docs, reducing system prompt.

POST http://127.0.0.1:9000/agent/build_view
 body request:
 {
  "device_id": "duro-1-003",
  "conversation_id": "proj-1",
  "prompt": "Create a View with a label in the center with width 100 and height 30. label should say 'Done'",
  "context": {
    "controller_config": {}
  }
}

Response:
 {
    "message": "Created a new diagnosis view named 'View_1' with a label in the center saying 'Done'.",
    "steps": [
        {
            "title": "Create diagnosis view",
            "details": "Add a new HMI view named 'View_1' to show diagnosis controls."
        },
        {
            "title": "Add 'Done' label",
            "details": "Place a label in the center of the view with width 100 and height 30, and display the text 'Done'."
        }
    ],
    "proposed_changes": {
        "hmi": {
            "views": [
                {
                    "id": "vw_4a5c-8f6a",
                    "name": "View_1",
                    "type": "view",
                    "config": {
                        "width": 1024,
                        "height": 760,
                        "style": {},
                        "sizeMode": "normal"
                    },
                    "components": [
                        {
                            "id": "lbl_9b1c-5dc8",
                            "viewId": "vw_4a5c-8f6a",
                            "type": "label",
                            "typeAbbr": "lbl_",
                            "comptName": "done_lbl",
                            "visibility": true,
                            "x": 492,
                            "y": 375,
                            "w": 100,
                            "h": 30,
                            "sizeMode": "zoom",
                            "config": {
                                "placeholder": "Done",
                                "buttonMode": "false",
                                "style": {
                                    "justify-content": "center",
                                    "align-items": "center"
                                }
                            },
                            "animation": {
                                "backgroundColor": "",
                                "border": "",
                                "text": "",
                                "visibility": "",
                                "color": ""
                            },
                            "events": {
                                "click": ""
                            }
                        }
                    ]
                }
            ],
            "general": {
                "viewsTree": [
                    {
                        "name": "View_1",
                        "type": "view",
                        "id": "vw_4a5c-8f6a"
                    }
                ]
            }
        },
        "tags_to_add": {}
    }
}

### 0.1.2 Build view only request updated with trained ai model and rag layer.

POST http://127.0.0.1:9000/agent/build_view
 body request:
 {
  "device_id": "duro-1",
  "prompt": "Task: Create a view with a label displaying 'lol'.",
  "context": {
    "views": [
        
    ],
    "tags": [
      
    ]
  }
}

Response:
 {
    "message": "Created a view with a label displaying 'lol'.",
    "steps": [
        {
            "title": "Create View",
            "details": "Add an HMI view 'View_1' sized 1024x760 with zoom sizing."
        },
        {
            "title": "Add label component",
            "details": "Place a label (120x60 at 0,0) centered textually, displaying 'lol'."
        }
    ],
    "proposed_changes": {
        "hmi": {
            "views": [
                {
                    "id": "vw_421a-40bd",
                    "name": "View_1",
                    "type": "view",
                    "config": {
                        "width": 1024,
                        "height": 760,
                        "style": {},
                        "sizeMode": "zoom"
                    },
                    "components": [
                        {
                            "id": "lbl_1f06-3055",
                            "viewId": "",
                            "type": "label",
                            "typeAbbr": "lbl_",
                            "comptName": "Label_1",
                            "visibility": true,
                            "w": 120,
                            "h": 60,
                            "y": 0,
                            "x": 0,
                            "zIndex": 0,
                            "rotationAngle": 0,
                            "sizeMode": "zoom",
                            "config": {
                                "placeholder": "lol",
                                "buttonMode": "false",
                                "style": {
                                    "justify-content": "center",
                                    "align-items": "center",
                                    "fontFamily": "Arial",
                                    "font-weight": "normal",
                                    "fontSize.px": 16,
                                    "color": "#000000a3"
                                }
                            },
                            "animation": {
                                "backgroundColor": "",
                                "border": "",
                                "text": "",
                                "visibility": "",
                                "color": ""
                            },
                            "events": {
                                "click": ""
                            }
                        }
                    ]
                }
            ],
            "general": {
                "viewsTree": []
            }
        },
        "component_to_add": {},
        "tags_to_add": {}
    }
}