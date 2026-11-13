'''
Author: Zachary McCauley
Sources: w3schools.org, GPT-5.6 Luna
AI Disclosure: GPT-5.6 Luna was used to generate regular expression usage for parser
'''

import argparse
import re
from collections import defaultdict, deque

class Net:
   def __init__(self, name, constant = False):
      self.name = name
      self.isconstant = constant
      self.fanin = None
      self.fanout = None
      self.fanin2 = None
      self.fanout2 = None
      self.depth = None
      self.cc = None
      self.co = None
      self.distToOutputs = None
      self.rarity = None
      self.influence = None
   def setfanin(self, fanin):
      self.fanin = fanin
   def setfanout(self, fanout):
      self.fanout = fanout
   def setfanin2(self, fanin2):
      self.fanin2 = fanin2
   def setfanout2(self, fanout2):
      self.fanout2 = fanout2
   def setdepth(self, depth):
      self.depth = depth
   def setcc(self, controllability):
      self.cc = controllability
   def setco(self, observability):
      self.co = observability
   def setdistToOutputs(self, distToOutputs):
      self.distToOutputs = distToOutputs
   def setrarity(self, rarity):
      self.rarity = rarity
   def setinfluence(self, influence):
      self.influence = influence

class gate:
   def __init__(self, name, gate_type, inputs, out):
      self.name = name
      self.type = gate_type
      self.inputs = inputs
      self.out = out

class Netlist:
   def __init__(self, inputs, outputs, gates, nets):
      self.inputs = inputs
      self.outputs = outputs
      self.gates = gates
      self.nets = nets

      #Convenient lookup tables
      self.net_map = {net.name: net for net in nets}
      self.input_names = {self._name(net) for net in inputs}
      self.output_names = {self._name(net) for net in outputs}

      #Sequential gates are treated as boundaries. Their outputs act as starting points for combinational analysis
      self.combinational_gates = [
         gate for gate in gates
         if self._gate_type(gate) not in
         ("dff", "ff", "flipflop", "flip_flop")
      ]

      #Maps each net to the gate that drives it
      self.drivers = {}

      #Maps each net to the gates that consume it
      self.consumers = defaultdict(list)
      self._build_graph()

   # Helper methods

   #Return the name of a Net object or a net-name string
   def _name(self, net):
      return net.name if hasattr(net, "name") else str(net)

   #Return a normalized gate type
   def _gate_type(self, gate):
      return gate.type.lower()

   #Return a gate's input nets as a list of names
   def _gate_inputs(self, gate):
      return [self._name(net) for net in gate.inputs]

   #Return a gate's output net name
   def _gate_output(self, gate):
      return self._name(gate.out)

   #Store a calculated feature on the corresponding Net object
   def _set_feature(self, net_name, attribute, value):
      net = self.net_map[net_name]
      setattr(net, attribute, value)

   #Build driver and consumer relationships for combinational gates
   def _build_graph(self):
      for gate in self.combinational_gates:
         output = self._gate_output(gate)
         self.drivers[output] = gate

         for input_net in set(self._gate_inputs(gate)):
            self.consumers[input_net].append(gate)

   #Return combinational gates in topological order
   #Raises an error if the combinational portion of the netlist contains a cycle
   def _topological_order(self):
      indegree = {id(gate): 0 for gate in self.combinational_gates}
      gate_by_id = {id(gate): gate for gate in self.combinational_gates}

      for gate in self.combinational_gates:
         for input_net in self._gate_inputs(gate):
            driver = self.drivers.get(input_net)

            if driver is not None:
               indegree[id(gate)] += 1

      queue = deque(
         gate for gate in self.combinational_gates
         if indegree[id(gate)] == 0
      )

      order = []

      while queue:
         gate = queue.popleft()
         order.append(gate)

         output = self._gate_output(gate)

         for consumer in self.consumers[output]:
            indegree[id(consumer)] -= 1

            if indegree[id(consumer)] == 0:
               queue.append(consumer)

      if len(order) != len(self.combinational_gates):
         raise ValueError("Combinational cycle detected in the netlist.")

      return order

   #Calculate the number of immediate input nets for every net
   #Primary inputs and nets without a driving gate have fan-in 0
   def extract_fanin(self):
      for net in self.nets:
         driver = self.drivers.get(net.name)

         if driver is None:
               count = 0
         else:
               count = len(set(self._gate_inputs(driver)))

         self._set_feature(net.name, "fanin", count)

   #Calculate the number of gates that immediately consume each net
   def extract_fanout(self):
      for net in self.nets:
         count = len(self.consumers[net.name])
         self._set_feature(net.name, "fanout", count)

   #Calculate the number of unique upstream nets within two combinational logic levels
   #Level 1: nets directly feeding the net's driving gate
   #Level 2: nets feeding the gates that produce level-1 nets
   def extract_fanin2(self):
      for net in self.nets:
         visited = set()
         current_level = {net.name}

         for _ in range(2):
            next_level = set()

            for current_net in current_level:
               driver = self.drivers.get(current_net)

               if driver is None:
                  continue

               for input_net in self._gate_inputs(driver):
                  if input_net != net.name and input_net not in visited:
                     next_level.add(input_net)

            visited.update(next_level)
            current_level = next_level

         self._set_feature(net.name, "fanin2", len(visited))

   #Calculate the number of unique downstream nets within two combinational logic levels
   #Level 1: outputs of gates that consume this net
   #Level 2: outputs of gates that consume level-1 nets
   def extract_fanout2(self):
      for net in self.nets:
         visited = set()
         current_level = {net.name}

         for _ in range(2):
            next_level = set()

            for current_net in current_level:
               for consumer in self.consumers[current_net]:
                  output = self._gate_output(consumer)

                  if output != net.name and output not in visited:
                     next_level.add(output)

            visited.update(next_level)
            current_level = next_level

         self._set_feature(net.name, "fanout2", len(visited))

   #Calculate the maximum number of combinational gates between a net and its nearest primary-input or sequential boundary
   def extract_depth(self):
      depth = {}

      #Nets without combinational drivers are starting points
      for net in self.nets:
         if net.name not in self.drivers:
            depth[net.name] = 0

      for gate in self._topological_order():
         inputs = self._gate_inputs(gate)

         #An undriven input is treated as a starting point
         input_depths = [depth.get(input_net, 0) for input_net in inputs]

         output = self._gate_output(gate)
         depth[output] = 1 + max(input_depths, default=0)

      for net in self.nets:
         self._set_feature(net.name, "depth", depth.get(net.name, 0))

   #Calculate SCOAP-style controllability values
   #CC0: estimated cost of forcing a net to 0
   #CC1: estimated cost of forcing a net to 1
   #The values are stored as a tuple: (CC0, CC1)
   def extract_controllability(self):
      cc0 = {}
      cc1 = {}

      #Primary inputs and other undriven nets are starting points
      for net in self.nets:
         if net.name not in self.drivers:
            cc0[net.name] = 1
            cc1[net.name] = 1

      for gate in self._topological_order():
         gate_type = self._gate_type(gate)
         inputs = self._gate_inputs(gate)
         output = self._gate_output(gate)

         input_cc0 = [cc0.get(net, 1) for net in inputs]
         input_cc1 = [cc1.get(net, 1) for net in inputs]

         if gate_type == "and":
            out_cc0 = 1 + min(input_cc0)
            out_cc1 = 1 + sum(input_cc1)

         elif gate_type == "nand":
            out_cc0 = 1 + sum(input_cc1)
            out_cc1 = 1 + min(input_cc0)

         elif gate_type == "or":
            out_cc0 = 1 + sum(input_cc0)
            out_cc1 = 1 + min(input_cc1)

         elif gate_type == "nor":
            out_cc0 = 1 + min(input_cc0)
            out_cc1 = 1 + sum(input_cc1)

         elif gate_type == "not":
            out_cc0 = 1 + input_cc1[0]
            out_cc1 = 1 + input_cc0[0]

         elif gate_type == "buf":
            if inputs[0] == "0":
               out_cc0 = 1
               out_cc1 = float("inf")
            elif inputs[0] == "1":
               out_cc0 = float("inf")
               out_cc1 = 1
            else:
               out_cc0 = 1 + input_cc0[0]
               out_cc1 = 1 + input_cc1[0]

         elif gate_type in ("xor", "xnor"):
            #Dynamic programming calculates the cost of making
            #the parity of the inputs even or odd
            even_cost = 0
            odd_cost = float("inf")

            for c0, c1 in zip(input_cc0, input_cc1):
               new_even = min(even_cost + c0, odd_cost + c1)
               new_odd = min(odd_cost + c0, even_cost + c1)
               even_cost = new_even
               odd_cost = new_odd

               if gate_type == "xor":
                  out_cc0 = 1 + even_cost
                  out_cc1 = 1 + odd_cost
               else:
                  out_cc0 = 1 + odd_cost
                  out_cc1 = 1 + even_cost

         else:
            raise ValueError(f"Unsupported gate type for controllability: {gate_type}")

         cc0[output] = out_cc0
         cc1[output] = out_cc1

      for net in self.nets:
         self._set_feature(net.name, "cc", (cc0.get(net.name, 1), cc1.get(net.name, 1)))

   #Calculate SCOAP-style observability values
   #Primary outputs have CO = 0. For each gate, observability propagates backward from its output to its input nets
   def extract_observability(self):
      co = {net.name: float("inf") for net in self.nets}

      for output in self.output_names:
         if output in co:
            co[output] = 0

      #Controllability must already have been calculated
      cc = {
         net.name: net.cc
         for net in self.nets
      }

      order = self._topological_order()

      for gate in reversed(order):
         gate_type = self._gate_type(gate)
         inputs = self._gate_inputs(gate)
         output = self._gate_output(gate)
         output_co = co.get(output, float("inf"))

         if output_co == float("inf"):
            continue

         for i, input_net in enumerate(inputs):
            other_inputs = [j for j in range(len(inputs)) if j != i]

            if gate_type in ("and", "nand"):
               #Other inputs must be 1 to observe this input
               extra_cost = sum(cc[inputs[j]][1] for j in other_inputs)

            elif gate_type in ("or", "nor"):
               #Other inputs must be 0 to observe this input
               extra_cost = sum(cc[inputs[j]][0] for j in other_inputs)

            elif gate_type in ("not", "buf"):
               extra_cost = 0

            elif gate_type in ("xor", "xnor"):
               #Either value of each other input allows the selected input to affect the output
               extra_cost = sum(
                  min(cc[inputs[j]][0], cc[inputs[j]][1])
                  for j in other_inputs
               )

            else:
               raise ValueError(f"Unsupported gate type for observability: {gate_type}")

            candidate = output_co + 1 + extra_cost
            co[input_net] = min(co.get(input_net, float("inf")), candidate)

      for net in self.nets:
         value = co.get(net.name, float("inf"))

         #Use None for nets that cannot reach a primary output
         if value == float("inf"):
            value = None

         self._set_feature(net.name, "co", value)

   #Calculate the minimum number of combinational gate levels between each net and a primary output
   #Primary outputs have distance 0
   def extract_dist_to_outputs(self):
      distance = {net.name: float("inf") for net in self.nets}
      queue = deque()

      for output in self.output_names:
         if output in distance:
            distance[output] = 0
            queue.append(output)

      #Traverse backward through the combinational logic
      while queue:
         current_net = queue.popleft()
         driver = self.drivers.get(current_net)

         if driver is None:
            continue

         current_distance = distance[current_net]

         for input_net in self._gate_inputs(driver):
            new_distance = current_distance + 1

            if new_distance < distance.get(input_net, float("inf")):
               distance[input_net] = new_distance
               queue.append(input_net)

      for net in self.nets:
         value = distance[net.name]

         if value == float("inf"):
            value = None

         self._set_feature(net.name, "distToOutputs", value)

   #Calculate rarity using simulation results
   #simulation_samples should be a list of dictionaries
   #Each dictionary maps net names to their simulated values
   #Rarity = min(P(net=0), P(net=1))
   def extract_rarity(self, simulation_samples):  
      if not simulation_samples:
         raise ValueError("At least one simulation sample is required.")

      total_samples = len(simulation_samples)

      for net in self.nets:
         zero_count = 0
         one_count = 0

         for sample in simulation_samples:
            value = sample.get(net.name)

            if value == 0:
               zero_count += 1
            elif value == 1:
               one_count += 1

         p0 = zero_count / total_samples
         p1 = one_count / total_samples

         self._set_feature(net.name, "rarity", min(p0, p1))

   #Calculate the fraction of primary outputs structurally reachable from each net
   #This measures potential structural influence, not guaranteed Boolean influence
   def extract_influence(self):
      total_outputs = len(self.output_names)

      if total_outputs == 0:
         for net in self.nets:
            self._set_feature(net.name, "influence", 0)
         return

      for net in self.nets:
         visited = set()
         reachable_outputs = set()

         queue = deque([net.name])
         visited.add(net.name)

         while queue:
            current_net = queue.popleft()

            if current_net in self.output_names:
               reachable_outputs.add(current_net)

            for consumer in self.consumers[current_net]:
               output = self._gate_output(consumer)

               if output not in visited:
                  visited.add(output)
                  queue.append(output)

         influence = len(reachable_outputs) / total_outputs
         self._set_feature(net.name, "influence", influence)

   #Run all feature extraction algorithms
   #simulation_samples are required for rarity. All other features are calculated from the netlist structure
   def extract_features(self, simulation_samples=None):
      self.extract_fanin()
      self.extract_fanout()
      self.extract_fanin2()
      self.extract_fanout2()
      self.extract_depth()
      self.extract_controllability()
      #self.extract_observability()
      #self.extract_dist_to_outputs()
      #self.extract_influence()

      if simulation_samples is not None:
         self.extract_rarity(simulation_samples)

#Expand a vector declaration into individual net names
def expand_net(name, msb=None, lsb=None):
   name = name.strip()

   if msb is None:
      return [name]

   msb = int(msb)
   lsb = int(lsb)
   step = 1 if msb >= lsb else -1

   return [f"{name}[{i}]" for i in range(lsb, msb + step, step)]

#Determine whether a signal is a net rather than a constant
def is_net(signal):
   signal = signal.strip()

   return not re.fullmatch(r"\d+'[bBoOdDhH][0-9a-fA-F_xXzZ]+", signal)

#determine if a signal is a binary constant
def get_constant(signal):
   signal = signal.strip()

   if signal in ("1'b0", "1'b1"):
      return signal[-1]

   return None

def main():
   parser = argparse.ArgumentParser(description="Script to interpret netlist designs")
   parser.add_argument("filename", type=str, help="Name of netlist file")
   args = parser.parse_args()

   try:
      with open("./netlists/" + args.filename, "r") as f:
         verilog = f.read()
         #Remove comments
         verilog = re.sub(r"/\*.*?\*/", "", verilog, flags=re.DOTALL) #multi line comment /* ... */
         verilog = re.sub(r"//.*", "", verilog) #single line comment //
         #Extract only the top module
         module_match = re.search(r"\bmodule\s+\w+\s*\([^;]*\)\s*;(.*?)\bendmodule\b", verilog, re.DOTALL)

         if not module_match:
            raise ValueError("No module found")

         module = module_match.group(1)
         #Data collections
         nets = []
         inputs = []
         outputs = []
         gates = []
         net_names = set()

         def add_net(name):
            name = name.strip()

            #Ignore constants
            if re.fullmatch(r"\d+'[bBoOdDhH][0-9a-fA-F_xXzZ]+", name):
               return

            if name and name not in net_names:
               nets.append(Net(name))
               net_names.add(name)

         #Process individual statements
         statements = module.split(";")

         for statement in statements:
            statement = statement.strip()

            if not statement:
               continue

            #Input/output/wire declarations
            declaration = re.fullmatch(
               r"(input|output|wire|reg)\s+"
               r"(?:\[(\d+)\s*:\s*(\d+)\]\s*)?"
               r"(.+)",
               statement,
               re.DOTALL
            )

            if declaration:
               declaration_type = declaration.group(1)
               msb = declaration.group(2)
               lsb = declaration.group(3)
               names = declaration.group(4)

               for name in names.split(","):
                  name = name.strip()

                  for net_name in expand_net(name, msb, lsb):
                     add_net(net_name)

                     if declaration_type == "input":
                        if net_name not in inputs:
                           inputs.append(net_name)

                     elif declaration_type == "output":
                        if net_name not in outputs:
                           outputs.append(net_name)

               continue

            #Gate declarations
            gate_match = re.fullmatch(
               r"(nand|and|nor|or|not|buf|xor|xnor|dff)\s+"
               r"(\w+)\s*\((.*)\)",
               statement,
               re.DOTALL
            )

            if not gate_match:
               continue

            gate_type = gate_match.group(1)
            gate_name = gate_match.group(2)
            connections = gate_match.group(3)
            gate_inputs = []
            gate_output = None

            #DFF uses named connections
            if gate_type == "dff":
               ports = re.findall(r"\.(\w+)\s*\(\s*([^)]+)\s*\)", connections)

               for port, signal in ports:
                  signal = signal.strip()

                  if port == "Q":
                     gate_output = signal                     
                  elif is_net(signal):
                     gate_inputs.append(signal)
                  else:
                     signal = get_constant(signal)
                     if signal is not None:
                        gate_inputs.append(signal)

            elif gate_type == "buf":
               signals = [
                  signal.strip()
                  for signal in connections.split(",")
               ]
               
               if len(signals) < 2:
                  continue

               for signal in signals[:-1]:
                  if gate_output is None:
                     gate_output = [signal]
                  else:
                     gate_output.append(signal)
               
               if is_net(signals[-1]):
                  gate_inputs.append(signals[-1])
               else:
                  b_value = get_constant(signals[-1])
                  if b_value is not None:
                     gate_inputs.append(b_value)

            #Other gates use positional connections
            else:
               signals = [
                  signal.strip()
                  for signal in connections.split(",")
               ]

               if len(signals) < 2:
                  continue

               gate_output = signals[0]

               for signal in signals[1:]:
                  if is_net(signal):
                     gate_inputs.append(signal)
                  else:
                     signal = get_constant(signal)
                     if signal is not None:
                        gate_inputs.append(signal)

            if gate_output is None:
               continue

            #Add connections to net list
            if isinstance(gate_output, str):
               add_net(gate_output)
            else:
               for signal in gate_output:
                  if signal not in ("1", "0"):
                     add_net(signal)

            for signal in gate_inputs:
               if signal not in ("1", "0"):
                  add_net(signal)

            #Create gate object
            gates.append(gate(gate_name, gate_type, gate_inputs, gate_output))

         '''#Display results
         print("\nINPUTS:")
         for net in inputs:
            print(net)

         print("\nOUTPUTS:")
         for net in outputs:
            print(net)

         print("\nNETS:")
         for net in nets:
            print(net.name)

         print("\nGATES:")
         for g in gates:
            print(f"{g.name}: {g.type} Inputs={g.inputs} Output={g.out}")

         print("\nSUMMARY:")
         #design8.v should be 8,28,107,83
         print("Total inputs:", len(inputs))
         print("Total outputs:", len(outputs))
         print("Total nets:", len(nets))
         print("Total gates:", len(gates))'''

   except FileNotFoundError:
      print("File not found")
   except ValueError as error:
      print(error)

   extracted_netlist = Netlist(inputs, outputs, gates, nets)
   extracted_netlist.extract_features()

   #create csv output file
   outfile = re.sub(r'.[^.]+$', "", args.filename)
   with open(outfile + ".csv", "w") as fout:
      fout.write("Net_Name, immediate_fanin, immediate_fanout, level_2_fanin, level_2_fanout, depth, controllability, observability, distance_to_outputs, rarity, influence\n")
      for net in extracted_netlist.nets:
         fout.write(net.name)
         fout.write("," + str(net.fanin if net.fanin is not None else ""))
         fout.write("," + str(net.fanout if net.fanout is not None else ""))
         fout.write("," + str(net.fanin2 if net.fanin2 is not None else ""))
         fout.write("," + str(net.fanout2 if net.fanout2 is not None else ""))
         fout.write("," + str(net.depth if net.depth is not None else ""))
         fout.write(",CC0=" + str(net.cc[0] if net.cc is not None else "") + " CC1=" + str(net.cc[1] if net.cc is not None else ""))
         fout.write("," + str(net.co if net.co is not None else ""))
         fout.write("," + str(net.distToOutputs if net.distToOutputs is not None else ""))
         fout.write("," + str(net.rarity if net.rarity is not None else ""))
         fout.write("," + str(net.influence if net.influence is not None else "") + "\n")

if __name__ == "__main__":
    main()