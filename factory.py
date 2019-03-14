# model.py
import random
from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid, SingleGrid # an agent take a whole cell
from astar import astar as astar
from pyswip import Functor, Variable, Query, call, Prolog

task_over = False

class RobotAgent(Agent):
    """ An agent with fixed initial wealth."""
    def __init__(self, unique_id, model, type, tasks, fmap, boxes):
        super().__init__(unique_id, model)
        self.uid = unique_id
        self.type = type
        self.stuff = 0
        self.fmap = fmap
        self.next = True
        self.tasks = tasks
        self.target = self.tasks.pop(0)
#        self.possible_steps = astar(fmap, self.pos, self.target)
        self.possible_steps = []
        self.passed = []
        self.renew = False
        self.createDB(boxes)

    def createDB(self, boxes):
        # create boxes' database
        self.swi = Prolog()

        for i in range(len(self.fmap)):
          for j in range(len(self.fmap)):
            if (self.fmap[i][j] == 1
                ):
              self.swi.assertz('wall('+str((i,j))+')')

        for pos in boxes[1]:
          s = str(pos)
          self.swi.assertz('full('+s+')')

    def findPath(self):
        if self.renew:
          new_pos = self.model.grid.get_neighborhood(
                    self.pos, True, False, 1)
          candi_pos = [x for x in new_pos 
                           if (not bool(list(self.swi.query(
                                          'full('+str(x)+')')))
                               and not bool(list(self.swi.query(
                                              'wall('+str(x)+')')))
                               )]
          if len(candi_pos) == 0:
            self.possible_steps = []
            self.new = False
            return

          candi_path = []
          for pos in candi_pos:
            candi_path.append(astar( self.fmap, pos, self.target))
          self.possible_steps = candi_path.pop(0)
          for path in candi_path:
            if len(self.possible_steps) > len(path):
              self.possible_steps = path
          print("from ", self.possible_steps[0], "to ", self.possible_steps[-1])
          self.renew = False

        if self.next:
          print("from ", self.pos, "to ", self.target)
          self.possible_steps = astar(self.fmap, self.pos, self.target)
          self.next = False

    def step(self):
        # The agent's step will go here.
        global task_over
        """
        check if need to recompute a path
        when the agent meets a full box or plans to next box
        it needs to stay and recompute a path
        """
        if task_over:
          return
        self.findPath()

        """
        # if not got the end
        #    if not box, go through
        #    else check if box is empty
        #        if it is empty , go through
        #        else stay to recompute a path
        # else take stuff away, update database, 
        #      stay and prepare for next target
        """
        x,y = next_pos = self.possible_steps[0]
        s = str(next_pos)
        if len(self.possible_steps)>1:
          if bool(list(self.swi.query('full('+s+')'))):
            print(s,"is full")
            self.renew = True
          else:
#          if bool(list(self.swi.query('go('+s+')'))):
            self.passed.append(self.possible_steps.pop(0))
            self.model.grid.move_agent(self, next_pos)
        elif len(self.possible_steps) <= 1:
          if len(self.possible_steps) == 1:
            cellmates = self.model.grid.get_cell_list_contents([next_pos])
            cellmates[0].stuff -= 1
            self.stuff += 1

            self.swi.retractall('full('+s+')')
#            if bool(list(self.swi.query('empty('+s+')'))):
            self.swi.assertz('empty('+s+')')

            self.passed.append(self.possible_steps.pop(0))
            self.model.grid.move_agent(self, next_pos)

          print(self.passed)
          if len(self.tasks) == 0:
            self.swi.retractall('full(_)')
            self.swi.retractall('wall(_)')
            task_over = True
          else:
            self.target = self.tasks.pop(0)
            self.next = True

class WallAgent(Agent):
    def __init__(self, unique_id, model, type):
      super().__init__(unique_id, model)
      self.uid = unique_id
      self.type = type

    def step(self):
      pass

class BoxAgent(Agent):
    def __init__(self, unique_id, model, type):
      super().__init__(unique_id, model)
      self.type = type
      self.uid = unique_id
      if self.type == 3: # full box
        self.stuff = 1
      else:
        self.stuff = 0

    def step(self):
      if self.stuff == 0:
        self.type = 2 # empty box


class FactoryModel(Model):
    """A model with some number of agents."""
    def __init__(self, N, num_task, num_empty, num_full):
        global task_over
        task_over = False
        # 1 means walls
        self.fmap = [[0,0,0,1,0,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,1,0,0,0],
                     [0,0,0,0,0,0,1,0,0,0],
                     [0,0,0,0,0,0,1,0,0,0],
                     [0,0,0,0,0,0,1,0,0,0]]

        self.height = self.width = len(self.fmap)
        self.grid = MultiGrid(self.width, self.height, False)
        self.running = True
        self.schedule = RandomActivation(self)
        self.ttl = 1

        empty = []
        full  = []
        # Create boxes
        while (len(empty)+len(full)) != (num_empty+num_full):
            x = random.randrange(self.width)
            y = random.randrange(self.height)
            if self.fmap[x][y] == 0:
                if len(empty)<num_empty and ((x,y) not in empty):
                    empty.append((x,y))
                elif (x,y) not in full and ((x,y) not in empty):
                    full.append((x,y))
        # [[empty boxes], [full boxes]]
        self.boxes = [empty,full]

        # Create tasks
        tasks = []
        while len(tasks) < N*num_task:
          for i in range(num_task):
            pos = random.choice(full)
            if pos not in tasks:
              tasks.append(pos)
        print("tasks are ",tasks)

        # Create Wall agents
        self.createWall()

        # Create box agents
        self.createBox()

        # Create Robot agents
        self.createRobot(N, num_task, tasks)

    def createWall(self):
        type = 1
        for i in range(self.height):
          for j in range(self.width):
            if (self.fmap[i][j] == 1):
              a = WallAgent(self.ttl, self, type)
              self.grid.place_agent(a,(i,j))
              self.schedule.add(a)
              self.ttl += 1

    def createBox(self):
        type = 2 # empty box
        for pos in self.boxes[0]:
          a = BoxAgent(self.ttl, self, type)
          self.grid.place_agent(a,pos)
          self.schedule.add(a)
          self.ttl += 1

        type = 3 # full box
        for pos in self.boxes[1]:
          a = BoxAgent(self.ttl, self, type)
          self.grid.place_agent(a,pos)
          self.schedule.add(a)
          self.ttl += 1

    def createRobot(self, num_agents, num_task, tasks):
        type = 0
        agents = []
        while len(agents) < num_agents:
            # add an agent into a random cell
            x = random.randrange(self.grid.width)
            y = random.randrange(self.grid.height)
            if (self.fmap[x][y] == 0 
                and (x,y) not in self.boxes[1]
                and (x,y) not in self.boxes[0]
                and (x,y) not in agents):
                a = RobotAgent(self.ttl, self, type,
                               tasks[:num_task], self.fmap, self.boxes)
                self.schedule.add(a)
                self.ttl += 1
                tasks = tasks[num_task:]
                self.grid.place_agent(a,(x,y))
                agents.append((x,y))
        print("start from ", agents)
#            self.grid.place_agent(a,(9,0))

    def step(self):
        '''Advance the model by one step.'''
        global task_over
        if not task_over:
          self.schedule.step()
        else:
          print("task over")
          self.running = False
