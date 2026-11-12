'''
Author: Zachary McCauley
Sources: w3schools.org, GPT-5.6 Luna
AI Disclosure: GPT-5.6 Luna was used to generate regular expression usage for parser
'''

import argparse
import re

class Net:
   def __init__(self, name):
      self.name = name
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
   def setc0(self, observability):
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
               ports = re.findall(
                  r"\.(\w+)\s*\(\s*([^)]+)\s*\)",
                  connections
               )

               for port, signal in ports:
                  signal = signal.strip()

                  if port == "Q":
                     gate_output = signal

                  elif is_net(signal):
                     gate_inputs.append(signal)

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

            if gate_output is None:
               continue

            #Add connections to net list
            add_net(gate_output)

            for signal in gate_inputs:
               add_net(signal)

            #Create gate object
            gates.append(gate(gate_name, gate_type, gate_inputs, gate_output))

        #Display results
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
         print("Total inputs:", len(inputs))
         print("Total outputs:", len(outputs))
         print("Total nets:", len(nets))
         print("Total gates:", len(gates))

   except FileNotFoundError:
      print("File not found")
   except ValueError as error:
      print(error)

if __name__ == "__main__":
    main()