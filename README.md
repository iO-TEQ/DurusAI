# README 

## Summary
Run Durus AI in a virtual environment on port 9000. Run the AI Model on 8080. Durus AI send prompts to the AI Model.

### RUN Llama 3 locally via mlx by apple.
**for Mac computers only**

1. Be at root directory in terminal.

2. Deactivate any virtual environments
```
deactivate 2>/dev/null || true
echo "$VIRTUAL_ENV"
```

2. ```echo "$VIRTUAL_ENV"``` should be empty

3. create new virtual environment folder
```
rm -rf ~/venvs/llama3
mkdir -p ~/venvs
```

4. start new virtual environment
```
/opt/homebrew/bin/python3.12 -m venv ~/venvs/llama3
source ~/venvs/llama3/bin/activate
```

5. install mlx-lm package
```
python -m pip install --upgrade pip
pip install "mlx-lm>=0.29.0"
```

6. confirm installation. (optional)
```
python - << 'PY'
import mlx_lm
print("mlx_lm version:", mlx_lm.__version__)
PY
```

7. run test script to load model and generate text. (optional)
```
python - << 'PY'
from mlx_lm import load, generate

model_id = "mlx-community/Meta-Llama-3-8B-Instruct-4bit"

print("Loading model:", model_id)
model, tokenizer = load(model_id)
out = generate(model, tokenizer, prompt="Say hello in one short sentence.", verbose=True)
print("\n=== OUTPUT ===")
print(out)
PY
```

8. run the AI model server. in this instance, Meta-Llama-3-8B-Instruct-4bit, knowledge cutoff is march 2023. Model Release Date April 18, 2024.

```
mlx_lm.server \
  --model mlx-community/Meta-Llama-3-8B-Instruct-4bit \
  --host 0.0.0.0 \
  --port 8080
```


### How to setup and run Durus Server

1. create a new terminal and go to durus directory.
```
cd ../Durus
python3 -m venv .venv
source .venv/bin/activate
```

2. install python packages
```
pip install -r requirements.txt
```

3. run the ai agent. 
**Remember: MLX server must also be running on 8080 in the other terminal.**
```
uvicorn main:app --host 0.0.0.0 --port 9000
```


## Version Summary

### 0.3.0
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
 