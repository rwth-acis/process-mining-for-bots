# process-mining-for-bots

This framework provides modules that can be used to do various process mining tasks on bot models

## Installation

1. Clone this repository
2. (Optional) Create a virtual environment using `python -m venv venv`
3. Install the requirements using `pip install -r requirements.txt`

## Usage

### Parsing a bot model

This python code snippet shows how to parse a bot model and get the corresponding Petri net for a sample bot model, `hotelBot.json`:

```python
import json
from utils.bot.parse_lib import get_parser
import pm4py

botmodel = json.loads(open('./utils/bot/assets/hotelBot.json').read())
parser = get_parser(botmodel)

net,im,fm = parser.to_petri_net()
pm4py.view_petri_net(net,im,fm)
```
