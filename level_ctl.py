"""
Cf.  https://www.plctalk.net/qanda/showthread.php?t=134893

Simple model of two tanks in series to limit flow variation to a process
using Proportional-only level control

"""

class PONLY_PID:
  """
Model a vertical cylindrical tank's level controlled by drain pump flow

          Nominal
Item       units
====      =======
Level     feet
Flow      gpm
Volume    gal
timestep  s

"""
  def __init__(self
              ,lolevel=0.0       ### Minimum level sensor signal
              ,hilevel=5.0       ### Maximum level sensor signal
              ,loflow=97.5       ### Pump flow at minimum level
              ,hiflow=117.5      ### Pump flow at maximum level
              ,fullvol=1000.0    ### Volume between min and max levels
              ,timescale=1./60.  ### Scale from flow to volume/timestep
              ,initlevel=None    ### Initial level
              ):
    ### Store input values
    (self.lolevel,self.hilevel,self.loflow,self.hiflow,self.fullvol
    ,) = map(float,(lolevel,hilevel,loflow,hiflow,fullvol,))
    self.timescale = float(timescale)

    if None is initlevel: self.netlevel = 0.0
    else                : self.netlevel = float(initlevel) - self.lolevel

    ### Calculate PID proportional gain and process gain
    self.PIDKp = (self.hiflow-self.loflow) / (self.hilevel-self.lolevel)
    self.processgain =  (self.hilevel-self.lolevel) / fullvol

  def outflow(self,level=None):
    """Calculate PID-controlled flow from level"""
    if None is level: return self.outflow(self.level())
    if level < self.lolevel: return self.loflow
    if level > self.hilevel: return self.hiflow
    return ((level-self.lolevel)*self.PIDKp)+self.loflow

  def level(self): return self.netlevel+self.lolevel

  def step(self,inflow,timestep):
    """Level calculation using implicit Euler integration"""
    netloflow = float(inflow) - self.loflow
    Knumerator = self.processgain * netloflow * timestep * self.timescale
    Kdenominator = self.processgain * self.PIDKp * timestep * self.timescale
    self.netlevel = (self.netlevel + Knumerator) / (1 + Kdenominator)
    return self.netlevel + self.lolevel

  def step_explicit(self,inflow,timestep):
    """Level calculation using explicit Euler integration"""
    netflow = float(inflow) - self.outflow()
    self.netlevel += self.processgain * netflow * timestep * self.timescale
    return self.netlevel + self.lolevel
########################################################################

if "__main__" == __name__:
  ### Tank 1:  1000gal over 5ft
  tp1 = PONLY_PID(initlevel=2.5)

  ### Tank 2:  2500gal over 6ft
  tp2 = PONLY_PID(hilevel=6,loflow=103,hiflow=105,fullvol=2500)
  #tp2 = PONLY_PID(hilevel=6,loflow=98.5,hiflow=116.5,fullvol=2500)

  ### Initialize arrays for half-second timestep over three 12h cycles
  timestep = 0.5
  N = int(12 * 3600 / timestep) * 3
  tims = [None] * N
  lvl1 = [None] * N
  out1 = [None] * N
  lvl2 = [None] * N
  out2 = [None] * N
  inf = [None] * N

  ### Run model at each timestep
  for i in range(N):

    ### Convert step to time in hours
    tims[i] = t = i * timestep / 3600.0

    ### 115gpm inflow for 3h out of every 12h
    inf[i] = inflow = ((t % 12.0) < 3) and 115 or 100

    ### Model inflow to Tank 1, get Pump 1 outflow
    lvl1[i] = tp1.step(inflow,timestep)
    out1[i] = outflow1 = tp1.outflow()
    ### Model tank 1 outflow as inflow to Tank 2, get Pump 2 outflow
    lvl2[i] = tp2.step(outflow1,timestep)
    out2[i] = tp2.outflow()

  ### Plot the data
  import matplotlib.pyplot as plt

  plt.plot(tims,lvl1,label='Tank 1 level')
  plt.plot(tims,lvl2,label='Tank 2 level')
  plt.xlabel('Time, h')
  plt.ylabel('Tank level, ft')
  plt.title(f"Tank 2 [min/max] flows = [{tp2.loflow},{tp2.hiflow}]")
  plt.legend(loc='center right')
  plt.show()

  plt.plot(tims,inf,label='Inflow')
  plt.plot(tims,out1,label='Pump 1 outflow')
  plt.plot(tims,out2,label='Pump 2 outflow')
  plt.xlabel('Time, h')
  plt.ylabel('Flow rate, GPM')
  plt.title(f"Tank 2 [min/max] flows = [{tp2.loflow},{tp2.hiflow}]")
  plt.legend(loc='center right')
  plt.show()
