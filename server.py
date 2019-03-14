# server.py
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from factory import FactoryModel
from mesa.visualization.UserParam import UserSettableParameter

def agent_portrayal(agent):
    portrayal = {
                 "Filled": "true",
                 "Layer": 0,
                 }

    if agent.type > 0:
      portrayal["Shape"] = "rect"
      portrayal["w"] = 0.5
      portrayal["h"] = 0.5
      if agent.type == 1: # wall
        portrayal["Color"] = "grey"
        portrayal["w"] = 0.8
        portrayal["h"] = 0.8
      elif agent.type == 2: # empty box
        portrayal["Color"] = "green"
      elif agent.type == 3: # full box
        portrayal["Color"] = "purple"

    if agent.type == 0:
      portrayal["Color"] = "red"
      portrayal["Shape"] = "circle"
      portrayal["r"] = 0.6
    return portrayal

task_slider = UserSettableParameter('slider', "Number of Task", 3, 1, 10, 1)
empty_slider = UserSettableParameter('slider', "Number of Empty Boxes", 10, 1, 45, 1)
full_slider = UserSettableParameter('slider', "Number of Full Boxes", 10, 1, 20, 1)

grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

times = 1
server = ModularServer(FactoryModel,
                       [grid],
                       "My Test Model",
                       {"N": 1, "num_task": task_slider,
                                "num_empty": empty_slider,
                                "num_full": full_slider})
time
